"""简历列表缓存测试：缓存命中、删除后失效、搜索绕过缓存（service 层，规避后台异步任务）。"""

import uuid

import pytest

from app.modules.resume.models import ResumeEntity, ResumeStatus
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.service import ResumeService


async def _create_resume(db, user_id: str, name: str) -> ResumeEntity:
    entity = ResumeEntity(
        user_id=uuid.UUID(user_id),
        filename=f"{name}.pdf",
        file_path=f"./uploads/resumes/{uuid.uuid4()}.pdf",
        file_size=1024,
        file_type="pdf",
        status=ResumeStatus.DONE,
        name=name,
        position="前端工程师",
        skills=["React"],
        score=80,
    )
    repo = ResumeRepository(db)
    return await repo.create(entity)


@pytest.mark.xfail(reason="BUG-01: cache_set 的 data 为 keyword-only 参数，resume/service.py 位置传参导致 TypeError，列表缓存路径 500", strict=True)
async def test_list_resumes_caches_result(db):
    uid = str(uuid.uuid4())
    svc = ResumeService(db)
    await _create_resume(db, uid, "张三")

    # 首次 list 写入缓存
    items = await svc.list_resumes(uid)
    assert len(items) == 1 and items[0].name == "张三"

    # 再新增一条，缓存未失效时 list 仍返回旧缓存（验证缓存确实生效）
    await _create_resume(db, uid, "李四")
    items2 = await svc.list_resumes(uid)
    assert len(items2) == 1  # 缓存命中：只有缓存中的 1 条


@pytest.mark.xfail(reason="BUG-01: 同上，删除后 list_resumes 再次触发 cache_set TypeError，缓存失效逻辑无法验证", strict=True)
async def test_delete_resume_invalidates_cache(db):
    uid = str(uuid.uuid4())
    svc = ResumeService(db)
    r = await _create_resume(db, uid, "张三")
    await svc.list_resumes(uid)  # 写缓存

    await svc.delete_resume(uid, str(r.id))

    items = await svc.list_resumes(uid)
    assert items == []


async def test_search_bypasses_cache(db):
    uid = str(uuid.uuid4())
    svc = ResumeService(db)
    await _create_resume(db, uid, "王五")

    # 搜索带 query 参数，不走缓存，直接查库
    found = await svc.list_resumes(uid, query="王五")
    assert any(i.name == "王五" for i in found)


async def test_resume_not_found_for_other_user(db):
    uid_a, uid_b = str(uuid.uuid4()), str(uuid.uuid4())
    svc_a, svc_b = ResumeService(db), ResumeService(db)
    r = await _create_resume(db, uid_a, "张三")

    # 用户 B 不能获取用户 A 的简历
    try:
        await svc_b.get_by_id(uid_b, str(r.id))
        assert False, "应抛出 RESUME_NOT_FOUND"
    except Exception as e:
        assert "not found" in str(e).lower() or "不存在" in str(e)
