"""HireMind 测试基础设施：独立测试库 hiremind_test + 每测试清理 + 客户端与 AI mock fixtures。

注意：本文件必须在 import app 之前设置 POSTGRES_DB 环境变量，
因为 app.infrastructure.database.engine 是模块级创建的。
"""

import os

# ---- 环境变量（pydantic-settings 环境变量优先于 .env）----
os.environ["POSTGRES_DB"] = "hiremind_test"
os.environ["LOG_LEVEL"] = "WARNING"

from pathlib import Path  # noqa: E402
from types import SimpleNamespace  # noqa: E402
import uuid  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.common.model.base import Base  # noqa: E402
from app.infrastructure.database import engine, async_session_factory  # noqa: E402
from app.infrastructure.redis import close_redis, get_redis, init_redis  # noqa: E402
from app.main import app  # noqa: E402

# import app.main 之后所有 model 已注册到 Base.metadata

# ---- 会话级：建表 + 初始化 Redis ----
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _db_setup():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    yield
    await close_redis()
    await engine.dispose()


# ---- 文件清理基线（session 开始时存在的文件不删）----
_SETTINGS_DIR = Path("./settings_data")
_UPLOAD_DIR = Path("./uploads/resumes")
_baseline_settings = {p.name for p in _SETTINGS_DIR.glob("*.json")} if _SETTINGS_DIR.exists() else set()
_baseline_uploads = {p.name for p in _UPLOAD_DIR.glob("*")} if _UPLOAD_DIR.exists() else set()


@pytest_asyncio.fixture(autouse=True)
async def _clean_db(_db_setup):
    """每个测试后清空全部表数据、Redis 测试缓存、新增的 settings/上传文件。"""
    yield
    # 1. 清空数据库表
    async with engine.begin() as conn:
        for t in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{t.name}" RESTART IDENTITY CASCADE'))
    # 2. 清理 Redis 测试缓存
    try:
        redis = get_redis()
        keys = await redis.keys("hiremind:*")
        if keys:
            await redis.delete(*keys)
    except Exception:
        pass
    # 3. 清理测试期间新增的 settings 与上传文件
    for f in _SETTINGS_DIR.glob("*.json"):
        if f.name not in _baseline_settings:
            f.unlink(missing_ok=True)
    for f in _UPLOAD_DIR.glob("*"):
        if f.name not in _baseline_uploads:
            f.unlink(missing_ok=True)


# ---- HTTP 客户端（ASGITransport，不触发 lifespan，建表由 _db_setup 负责）----
@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---- DB session（service 层直接测试用）----
@pytest_asyncio.fixture
async def db():
    async with async_session_factory() as session:
        yield session


# ---- 注册用户 + token ----
@pytest_asyncio.fixture
async def registered_user(client):
    email = f"user_{uuid.uuid4().hex[:10]}@test.com"
    resp = await client.post("/api/auth/register", json={
        "email": email, "password": "testpass123", "nickname": "测试用户",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data.get("token"), "注册响应应包含 token"
    return {
        "id": data["id"],
        "email": email,
        "token": data["token"],
        "headers": {"Authorization": f"Bearer {data['token']}"},
    }


# ---- AI mock ----
QUESTION_JSON = (
    '{"question": "请介绍你在前端方向的技术栈与项目经验", "feedback": "回答得不错", '
    '"is_final": false, "evaluation": 5, "stage": "一"}'
)
EVAL_JSON = (
    '{"overall_score": 88, "feedback": "整体表现良好，技术基础扎实", '
    '"dimensions": {"tech_depth": 85, "tech_selection": 80, "problem_solving": 90, '
    '"production": 75, "communication": 88}, '
    '"per_question": [{"index": 1, "score": 8, "comment": "回答清晰"}], '
    '"strengths": ["技术扎实", "表达清晰"], "weaknesses": ["深度略浅"], '
    '"suggestions": ["多阅读源码"]}'
)
RESUME_ANALYSIS = {
    "name": "张三", "email": "zhangsan@test.com", "phone": "13800000000",
    "position": "前端工程师", "skills": ["React", "TypeScript"],
    "experience": [{"company": "某公司", "title": "前端开发", "duration": "2020-2023",
                    "description": "负责核心模块开发"}],
    "education": [{"school": "某大学", "degree": "本科", "major": "计算机", "year": "2020"}],
    "summary": "三年前端开发经验", "score": 85,
}


class _FakeLLM:
    """模拟 ChatOpenAI：按调用参数区分问题生成与评估。"""

    async def ainvoke(self, *args, **kwargs):
        content = EVAL_JSON if "transcript" in kwargs else QUESTION_JSON
        return SimpleNamespace(content=content)

    async def astream(self, *args, **kwargs):
        # 拆成两个 token 模拟流式输出
        half = len(QUESTION_JSON) // 2
        for part in (QUESTION_JSON[:half], QUESTION_JSON[half:]):
            yield SimpleNamespace(content=part)


class _FakeEmbedResp:
    status_code = 200

    def json(self):
        return {"data": [{"index": 0, "embedding": [0.1] * 1024}]}


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, **kwargs):
        return _FakeEmbedResp()


@pytest.fixture
def mock_ai(monkeypatch):
    """Mock 全部 AI 外部调用：LLM 问题/评估、简历分析、知识库 embedding。"""
    import httpx as _httpx
    from app.modules.interview import agent as interview_agent
    import app.modules.resume.service as resume_service
    from app.modules.knowledgebase.service import KnowledgeService

    monkeypatch.setattr(interview_agent, "_get_llm", lambda settings, user_id=None: _FakeLLM())
    monkeypatch.setattr(resume_service, "analyze_resume", _fake_analyze_resume)
    monkeypatch.setattr(KnowledgeService, "_embed_chunks", _fake_embed_chunks)
    monkeypatch.setattr(KnowledgeService, "_get_api_config", _fake_get_api_config)
    monkeypatch.setattr(_httpx, "AsyncClient", _FakeAsyncClient)
    return {"question_json": QUESTION_JSON, "eval_json": EVAL_JSON}


async def _fake_analyze_resume(text: str, user_id: str | None = None):
    return dict(RESUME_ANALYSIS)


async def _fake_embed_chunks(self, chunks: list[str]) -> list[list[float]]:
    return [[0.1] * 1024 for _ in chunks]


async def _fake_get_api_config(self):
    return ("test-api-key", "https://fake.example/v1")
