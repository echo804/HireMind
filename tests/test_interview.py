"""面试模块测试：SSE 流式回答、报告生成（dimensions/per_question）、异常分支。"""

import json
import uuid

import pytest

from app.modules.interview import service as interview_service


def _parse_sse(text: str) -> list[dict]:
    events = []
    for line in text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


async def _create_session(client, headers, total=2, use_knowledge=False):
    resp = await client.post("/api/interviews", json={
        "direction": "frontend",
        "interview_type": "text",
        "total_questions": total,
        "use_knowledge": use_knowledge,
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


@pytest.fixture
def mock_evaluate(monkeypatch):
    """Mock 评估报告生成（service 层 evaluate_interview）。"""
    async def fake_evaluate(settings, direction, transcript, user_id=None):
        return {
            "overall_score": 88, "feedback": "整体表现良好，技术基础扎实",
            "dimensions": {"tech_depth": 85, "tech_selection": 80, "problem_solving": 90,
                            "production": 75, "communication": 88},
            "per_question": [{"index": 1, "score": 8, "comment": "回答清晰"}],
            "strengths": ["技术扎实"], "weaknesses": ["深度略浅"],
            "suggestions": ["多阅读源码"],
        }

    monkeypatch.setattr(interview_service, "evaluate_interview", fake_evaluate)
    return fake_evaluate


# ---------- 创建会话 ----------

async def test_create_interview_first_question(client, registered_user, mock_ai):
    data = await _create_session(client, registered_user["headers"])
    assert data["status"] == "in_progress"
    assert data["current_question"] == 1
    assert data["questions_asked"][0]["question"]


@pytest.mark.xfail(reason="BUG-03: use_knowledge 触发 kb search，向量 SQL 在 asyncpg 下语法错误且事务未回滚，创建面试失败", strict=True)
async def test_create_interview_with_knowledge(client, registered_user, mock_ai):
    data = await _create_session(client, registered_user["headers"], use_knowledge=True)
    assert data["status"] == "in_progress"
    assert data["questions_asked"][0]["question"]


# ---------- SSE 流式回答 ----------

async def test_answer_stream_tokens_then_question(client, registered_user, mock_ai):
    h = registered_user["headers"]
    session = await _create_session(client, h, total=2)

    resp = await client.post(f"/api/interviews/{session['id']}/answer-stream",
                             json={"answer": "我的第一段回答"}, headers=h)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    tokens = [e["token"] for e in events if "token" in e]
    final = [e for e in events if "question_index" in e and "token" not in e]

    assert tokens, "应推送 token 流"
    assert len(final) == 1
    assert final[0]["question_index"] == 2
    assert final[0]["question"]  # 最终解析出的完整问题


async def test_answer_stream_completes_and_generates_report(client, registered_user, mock_ai, mock_evaluate):
    h = registered_user["headers"]
    session = await _create_session(client, h, total=2)

    # 第 1 题
    await client.post(f"/api/interviews/{session['id']}/answer-stream",
                      json={"answer": "回答一"}, headers=h)
    # 第 2 题（最后一题）
    resp = await client.post(f"/api/interviews/{session['id']}/answer-stream",
                             json={"answer": "回答二"}, headers=h)
    events = _parse_sse(resp.text)
    assert any("is_completed" in e for e in events)

    # 报告包含 dimensions / per_question
    report = await client.get(f"/api/interviews/{session['id']}/report", headers=h)
    assert report.status_code == 200, report.text
    rd = report.json()["data"]
    assert rd["score"] == 88
    assert "tech_depth" in rd["dimensions"]
    assert rd["per_question"]


async def test_answer_stream_session_not_found(client, registered_user, mock_ai):
    resp = await client.post(f"/api/interviews/{uuid.uuid4()}/answer-stream",
                             json={"answer": "x"}, headers=registered_user["headers"])
    events = _parse_sse(resp.text)
    assert events[0]["error"] == "面试会话不存在"


async def test_answer_stream_already_completed(client, registered_user, mock_ai):
    h = registered_user["headers"]
    session = await _create_session(client, h, total=1)
    await client.post(f"/api/interviews/{session['id']}/answer-stream",
                      json={"answer": "唯一回答"}, headers=h)

    # 会话已结束，再次回答
    resp = await client.post(f"/api/interviews/{session['id']}/answer-stream",
                             json={"answer": "再来"}, headers=h)
    events = _parse_sse(resp.text)
    assert events[0]["error"] == "面试已结束"


# ---------- 结束会话与报告 ----------

async def test_end_session_early_fallback_report(client, registered_user, mock_ai):
    h = registered_user["headers"]
    session = await _create_session(client, h, total=5)
    # 只回答 1 题就结束
    await client.post(f"/api/interviews/{session['id']}/answer-stream",
                      json={"answer": "回答一"}, headers=h)
    resp = await client.post(f"/api/interviews/{session['id']}/end", headers=h)
    assert resp.status_code == 200, resp.text

    report = await client.get(f"/api/interviews/{session['id']}/report", headers=h)
    rd = report.json()["data"]
    assert rd["score"] >= 0
    assert "仅回答" in rd["feedback"] or "评估" in rd["feedback"]


async def test_report_requires_completed(client, registered_user, mock_ai):
    h = registered_user["headers"]
    session = await _create_session(client, h, total=5)
    resp = await client.get(f"/api/interviews/{session['id']}/report", headers=h)
    assert resp.status_code == 409  # 未完成时禁止查看报告


async def test_list_and_get_session(client, registered_user, mock_ai):
    h = registered_user["headers"]
    session = await _create_session(client, h)

    lst = await client.get("/api/interviews", headers=h)
    assert any(s["id"] == session["id"] for s in lst.json()["data"])

    got = await client.get(f"/api/interviews/{session['id']}", headers=h)
    assert got.json()["data"]["id"] == session["id"]
