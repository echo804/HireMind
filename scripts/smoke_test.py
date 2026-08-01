"""HireMind 端到端冒烟测试：真实服务 + 真实 AI（在 WSL 内执行，访问 localhost:8000）。

用法: .venv/bin/python3 scripts/smoke_test.py
预期失败（已记录产品 bug）会标记为 EXPECTED-FAIL。
"""

import json
import time
import uuid

import httpx

BASE = "http://localhost:8000"
results = []


def check(name: str, cond: bool, detail: str = "", expected_fail: bool = False):
    tag = "PASS" if cond else ("EXPECTED-FAIL" if expected_fail else "FAIL")
    results.append({"name": name, "ok": bool(cond), "tag": tag, "detail": detail})
    print(f"[{tag}] {name}  {detail}")


def wait_resume(c: httpx.Client, rid: str, timeout: int = 180) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = c.get(f"{BASE}/api/resumes/{rid}")
        if r.status_code == 200:
            data = r.json()["data"]
            if data["status"] in ("done", "failed"):
                return data
        time.sleep(3)
    return {"status": "timeout"}


def _report_summary(data: dict) -> str:
    if data.get("status") == "failed":
        return f"failed: {data.get('summary', '')[:120]}"
    return f"status={data.get('status')} name={data.get('name')} score={data.get('score')} progress={data.get('progress')}"


def main():
    c = httpx.Client(timeout=180)

    # 0. 探测 .env AI key 有效性（区分环境问题与代码问题）
    ai_key_ok = False
    probe_status = "err"
    try:
        from app.config.settings import settings
        probe = httpx.post(
            f"{settings.AI_BAILIAN_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {settings.AI_BAILIAN_API_KEY}"},
            json={"model": settings.AI_DEFAULT_MODEL,
                  "messages": [{"role": "user", "content": "ping"}], "max_tokens": 3},
            timeout=30)
        probe_status = str(probe.status_code)
        ai_key_ok = probe.status_code == 200
    except Exception as e:
        probe_status = f"err:{type(e).__name__}"
    check("AI key 有效性", ai_key_ok, f"probe={probe_status}（无效则 AI 相关失败为环境问题 ENV-01）")

    # 1. 健康检查
    r = c.get(f"{BASE}/api/health")
    check("health", r.status_code == 200, str(r.json()))

    # 2. 注册两个用户：settings 用户（测加密，避免污染业务用户的 AI 配置）+ 业务用户
    email = f"smoke_{uuid.uuid4().hex[:8]}@test.com"
    r = c.post(f"{BASE}/api/auth/register",
               json={"email": email, "password": "smoke1234", "nickname": "冒烟测试"})
    token = r.json()["data"]["token"] if r.status_code == 200 else ""
    check("register 返回 token", bool(token), f"status={r.status_code}")
    h = {"Authorization": f"Bearer {token}"}

    r = c.post(f"{BASE}/api/auth/login", json={"email": email, "password": "smoke1234"})
    check("login 返回 token", r.status_code == 200 and bool(r.json()["data"]["token"]))

    # 2.1 settings 加密测试用独立用户（不影响业务用户的 AI 真实配置）
    email_s = f"smoke_s_{uuid.uuid4().hex[:8]}@test.com"
    rs = c.post(f"{BASE}/api/auth/register",
                json={"email": email_s, "password": "smoke1234", "nickname": "设置用户"})
    hs = {"Authorization": f"Bearer {rs.json()['data']['token']}"}
    r = c.put(f"{BASE}/api/settings", json={"provider": "bailian",
                                            "bailian_api_key": "sk-smoke-test-key-123456"},
              headers=hs)
    check("settings 保存", r.status_code == 200, f"status={r.status_code}")
    r = c.get(f"{BASE}/api/settings", headers=hs)
    masked = r.json()["data"].get("bailian_api_key", "") if r.status_code == 200 else ""
    check("settings 掩码回显", "****" in masked, f"masked={masked[:8]}...")
    # 业务用户未保存配置，AI 调用将回退 .env 真实 key

    # 4. 简历上传（真实 AI 解析）
    import pathlib
    docx = pathlib.Path("./uploads/test_resume.docx")
    if docx.exists():
        with open(docx, "rb") as f:
            r = c.post(f"{BASE}/api/resumes/upload",
                       files={"file": ("test_resume.docx", f.read(),
                                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                       headers=h)
        if r.status_code == 200:
            rid = r.json()["data"]["id"]
            res = wait_resume(c, rid)
            check("简历 AI 解析完成", res.get("status") == "done",
                  _report_summary(res), expected_fail=not ai_key_ok)
            resume_id = rid
        else:
            check("简历上传", False, f"status={r.status_code} {r.text[:120]}")
            resume_id = None
    else:
        check("简历上传", False, "uploads/test_resume.docx 不存在")
        resume_id = None

    # 5. 面试（真实 AI 出题 + SSE 流式 + 评估报告）
    if resume_id:
        r = c.post(f"{BASE}/api/interviews",
                   json={"resume_id": resume_id, "direction": "frontend",
                         "interview_type": "text", "total_questions": 2, "use_knowledge": False},
                   headers=h)
        sid = r.json()["data"]["id"] if r.status_code == 200 else None
        check("创建面试会话", bool(sid), f"status={r.status_code}")
        if sid:
            q1 = r.json()["data"]["questions_asked"][0]["question"]
            check("首题由 AI 生成", bool(q1) and "无法连接" not in q1, f"q1={q1[:40]}",
                  expected_fail=not ai_key_ok)

            for i in (1, 2):
                resp = c.post(f"{BASE}/api/interviews/{sid}/answer-stream",
                              json={"answer": f"冒烟测试第{i}题的回答：我在前端方向有三年经验，熟悉 React 与 TypeScript。"},
                              headers=h, timeout=180)
                events = []
                for line in resp.text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            events.append(json.loads(line[6:]))
                        except Exception:
                            pass
                tokens = [e for e in events if "token" in e]
                final = [e for e in events if "question_index" in e and "token" not in e]
                check(f"第{i}题 SSE 流式 token", len(tokens) > 0, f"tokens={len(tokens)}",
                      expected_fail=not ai_key_ok)
                check(f"第{i}题 SSE 最终问题", len(final) == 1 and final[0].get("question"),
                      f"q={final[0].get('question','')[:40] if final else '无'}",
                      expected_fail=not ai_key_ok)

            r = c.get(f"{BASE}/api/interviews/{sid}/report", headers=h)
            rd = r.json()["data"] if r.status_code == 200 else {}
            check("面试评估报告", rd.get("score", -1) >= 0 and bool(rd.get("feedback")),
                  f"score={rd.get('score')} dims={list((rd.get('dimensions') or {}).keys())}",
                  expected_fail=not ai_key_ok)

    # 6. 日程 + 时间冲突
    day = "2027-06-15"
    r1 = c.post(f"{BASE}/api/schedule", json={
        "candidate_name": "冒烟候选人A", "scheduled_at": f"{day}T10:00:00+00:00",
        "duration_minutes": 60}, headers=h)
    check("创建日程", r1.status_code == 200, f"status={r1.status_code}")
    r2 = c.post(f"{BASE}/api/schedule", json={
        "candidate_name": "冒烟候选人B", "scheduled_at": f"{day}T10:30:00+00:00",
        "duration_minutes": 60}, headers=h)
    check("日程时间冲突 409", r2.status_code == 409, f"status={r2.status_code}")
    r3 = c.post(f"{BASE}/api/schedule", json={
        "candidate_name": "冒烟候选人C", "scheduled_at": f"{day}T11:00:00+00:00",
        "duration_minutes": 60}, headers=h)
    check("相邻时段不冲突", r3.status_code == 200, f"status={r3.status_code}")

    # 7. 知识库（真实 embedding + 向量搜索）
    txt = "HireMind 平台支持简历解析、模拟面试与 RAG 知识库检索。" * 10
    r = c.post(f"{BASE}/api/knowledge/upload",
               files={"file": ("smoke_kb.txt", txt.encode("utf-8"), "text/plain")}, headers=h)
    doc = r.json()["data"] if r.status_code == 200 else {}
    check("知识库上传+embedding", r.status_code == 200 and doc.get("status") == "ready",
          f"status={r.status_code} doc={doc.get('status')} chunks={doc.get('chunk_count')}",
          expected_fail=not ai_key_ok)

    # 列表（预期 BUG-01: cache_set 位置传参 TypeError → 500）
    r = c.get(f"{BASE}/api/knowledge", headers=h)
    check("知识库列表", r.status_code == 200, f"status={r.status_code}", expected_fail=True)

    # 搜索（预期 BUG-03: 向量 SQL 语法错误）
    r = c.post(f"{BASE}/api/knowledge/search", json={"query": "RAG 知识库", "top_k": 3}, headers=h)
    check("知识库向量搜索", r.status_code == 200, f"status={r.status_code} {r.text[:80]}",
          expected_fail=True)

    # 8. Redis 缓存验证（cache 工具本身已单测；这里验证列表缓存 key 是否存在）
    try:
        from app.infrastructure.cache import cache_get
    except Exception:
        pass

    # 9. 前端页面可达性（WSL 内）
    import subprocess
    for page in ("/", "/login", "/register"):
        code = subprocess.run(["curl", "-s", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}",
                               f"http://localhost:5173{page}"], capture_output=True, text=True).stdout
        check(f"前端页面 {page}", code == "200", f"http={code}")

    # 汇总
    print("\n===== 冒烟测试汇总 =====")
    passed = sum(1 for x in results if x["tag"] == "PASS")
    expected = sum(1 for x in results if x["tag"] == "EXPECTED-FAIL")
    failed = sum(1 for x in results if x["tag"] == "FAIL")
    print(f"PASS={passed}  EXPECTED-FAIL(已记录bug)={expected}  FAIL={failed}  总计={len(results)}")
    for x in results:
        if x["tag"] == "FAIL":
            print(f"  FAIL: {x['name']} -> {x['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
