"""HireMind 网页功能测试：前端页面可达性 + 各功能模块 API 全链路（模拟前端操作序列）。

在 WSL 内执行（.venv/bin/python3 scripts/web_test.py），需前端 5173 与后端 8000 已启动。
已知问题（BUG-01~05 / FE-01~04 / ENV-01）会标记为 EXPECTED-FAIL 并记录，不修改代码。
"""

import json
import re
import time
import uuid

import httpx

FRONT = "http://localhost:5173"
BASE = "http://localhost:8000"
results = []


def check(name: str, cond: bool, detail: str = "", expected_fail: bool = False):
    tag = "PASS" if cond else ("EXPECTED-FAIL" if expected_fail else "FAIL")
    results.append({"name": name, "tag": tag, "detail": detail})
    print(f"[{tag}] {name}  {detail}")


def parse_sse(text: str) -> list[dict]:
    events = []
    for line in text.split("\n"):
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except Exception:
                pass
    return events


# ==================== 前端页面可达性 ====================

def test_pages(c: httpx.Client):
    print("\n===== 页面可达性（vite dev server 5173）=====")
    # 首页 HTML 与 JS bundle
    r = c.get(f"{FRONT}/")
    html = r.text if r.status_code == 200 else ""
    check("GET / 页面", r.status_code == 200, f"http={r.status_code}")
    check("index.html 含 root 挂载点", '<div id="root">' in html or 'id="root"' in html)
    m = re.search(r'src="(/src/main\.tsx)"', html) or re.search(r'href="(/src/main\.tsx)"', html)
    if m:
        js = c.get(f"{FRONT}{m.group(1)}")
        check("主入口 main.tsx 可加载", js.status_code == 200, f"http={js.status_code}")
    else:
        check("主入口 main.tsx 可加载", False, "index.html 未找到 main.tsx 引用")

    routes = [
        ("/", "首页"), ("/login", "登录页"), ("/register", "注册页"),
        ("/resumes", "简历列表"), ("/interviews", "面试列表"), ("/settings", "系统设置"),
        ("/schedule", "面试日程"), ("/knowledge-base", "知识库"),
        ("/resumes/00000000-0000-0000-0000-000000000000", "简历详情"),
        ("/interviews/00000000-0000-0000-0000-000000000000", "面试聊天"),
        ("/interviews/00000000-0000-0000-0000-000000000000/report", "面试报告"),
        ("/knowledge-base/00000000-0000-0000-0000-000000000000", "知识库详情"),
    ]
    for path, name in routes:
        rr = c.get(f"{FRONT}{path}")
        check(f"路由 {name} ({path})", rr.status_code == 200, f"http={rr.status_code}")

    # vite proxy: 通过前端 5173 访问后端 API
    pr = c.get(f"{FRONT}/api/health")
    check("vite proxy /api 转发", pr.status_code == 200 and pr.json().get("status") == "ok",
          f"http={pr.status_code}")


# ==================== 功能模块 ====================

def test_auth_and_home(c: httpx.Client):
    print("\n===== Auth + 首页统计 =====")
    email = f"web_{uuid.uuid4().hex[:8]}@test.com"
    r = c.post(f"{BASE}/api/auth/register",
               json={"email": email, "password": "web12345", "nickname": "网页测试"})
    token = r.json()["data"]["token"] if r.status_code == 200 else ""
    check("注册（表单 POST /auth/register）", bool(token), f"http={r.status_code}")
    h = {"Authorization": f"Bearer {token}"}

    r = c.post(f"{BASE}/api/auth/login", json={"email": email, "password": "web12345"})
    check("登录（POST /auth/login）", r.status_code == 200 and bool(r.json()["data"]["token"]))
    check("登录错误密码", c.post(f"{BASE}/api/auth/login",
                              json={"email": email, "password": "wrong"}).status_code == 401,
          "401")

    # 首页统计：Home.tsx 并行调用 4 个列表接口
    checks = {
        "首页统计 /resumes": c.get(f"{BASE}/api/resumes", headers=h),
        "首页统计 /interviews": c.get(f"{BASE}/api/interviews", headers=h),
        "首页统计 /knowledge": c.get(f"{BASE}/api/knowledge", headers=h),
        "首页统计 /schedule/range": c.get(f"{BASE}/api/schedule/range",
                                          params={"start": "2027-01-01T00:00:00+00:00",
                                                  "end": "2027-01-08T00:00:00+00:00"},
                                          headers=h),
    }
    for name, resp in checks.items():
        check(name, resp.status_code == 200, f"http={resp.status_code}",
              expected_fail="knowledge" in name)  # BUG-01 列表缓存
    return email, h


def test_resume(c: httpx.Client, h: dict):
    print("\n===== 简历模块（上传→轮询→列表→搜索→删除）=====")
    docx = open("./uploads/test_resume.docx", "rb").read() if __import__("pathlib").Path("./uploads/test_resume.docx").exists() else None
    if not docx:
        check("简历上传", False, "test_resume.docx 不存在")
        return None
    r = c.post(f"{BASE}/api/resumes/upload",
               files={"file": ("test_resume.docx", docx,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
               headers=h)
    rid = r.json()["data"]["id"] if r.status_code == 200 else None
    check("简历上传（FormData）", bool(rid), f"http={r.status_code}")

    if rid:
        # 模拟 ResumeDetail 1.5s 轮询（AI 解析，ENV-01 key 无效 → failed/processing）
        last = None
        for _ in range(10):
            rr = c.get(f"{BASE}/api/resumes/{rid}", headers=h)
            if rr.status_code == 200:
                last = rr.json()["data"]
                if last["status"] in ("done", "failed"):
                    break
            time.sleep(1.5)
        check("简历详情轮询（processing→终态）", last is not None and last["status"] in ("done", "failed"),
              f"status={last.get('status') if last else None} name={last.get('name') if last else None} progress={last.get('progress') if last else None}",
              expected_fail=True)  # ENV-01: AI 解析失败

        lst = c.get(f"{BASE}/api/resumes", headers=h)
        check("简历列表", lst.status_code == 200, f"http={lst.status_code}")
        s = c.get(f"{BASE}/api/resumes", params={"q": "测试"}, headers=h)
        check("简历搜索 ?q=", s.status_code == 200, f"http={s.status_code}")
        d = c.delete(f"{BASE}/api/resumes/{rid}", headers=h)
        check("简历删除", d.status_code == 200, f"http={d.status_code}")
    return rid


def test_interview(c: httpx.Client, h: dict):
    print("\n===== 面试模块（创建→SSE→结束→报告→PDF）=====")
    # total=3：SSE 1 次后（current=2 <3）调用 end，验证正常结束路径
    r = c.post(f"{BASE}/api/interviews", json={
        "direction": "frontend", "interview_type": "text",
        "total_questions": 3, "use_knowledge": False}, headers=h)
    sid = r.json()["data"]["id"] if r.status_code == 200 else None
    check("创建面试（POST /interviews）", bool(sid), f"http={r.status_code}")

    if sid:
        # 第 1 题：正确 token 的 SSE（AI key 无效 → fallback，但流式框架应工作）
        resp = c.post(f"{BASE}/api/interviews/{sid}/answer-stream",
                      json={"answer": "网页测试回答一"}, headers=h)
        ev = parse_sse(resp.text)
        check("SSE 流式（带 token）", resp.status_code == 200 and len(ev) > 0,
              f"http={resp.status_code} events={len(ev)}",
              expected_fail=True)  # ENV-01: AI 出题失败，但框架应返回事件

        # FE-03 复现：前端 InterviewChat.tsx:73 读 localStorage["token"]（实际存于 user JSON）
        # → Authorization 头为空。后端 get_current_user_dev 回退 DEV_USER_ID，且会话
        # find_by_id 无归属校验 → 无 token 仍可操作会话（安全隐患，观察实际行为）
        resp2 = c.post(f"{BASE}/api/interviews/{sid}/answer-stream",
                       json={"answer": "模拟前端无token的SSE"})  # 不带 Authorization
        ev2 = parse_sse(resp2.text)
        check("FE-03: 前端 SSE 请求无有效 token（模拟）",
              len(ev2) == 0 or any("error" in e for e in ev2),
              f"events={len(ev2)} 首事件={ev2[0] if ev2 else '空'}",
              expected_fail=True)  # 真实前端行为观察：无鉴权即可操作，属安全隐患

        # 结束（此时 current=2 < total=3，answers=1，走正常兜底报告路径）
        end = c.post(f"{BASE}/api/interviews/{sid}/end", headers=h)
        check("结束面试（POST /end）", end.status_code == 200, f"http={end.status_code}")
        rep = c.get(f"{BASE}/api/interviews/{sid}/report", headers=h)
        rd = rep.json()["data"] if rep.status_code == 200 else {}
        check("面试报告（GET /report）", rep.status_code == 200 and rd.get("score", -1) >= 0,
              f"http={rep.status_code} score={rd.get('score')}",
              expected_fail=True)  # ENV-01: 评估失败兜底 score=0

        # PDF 导出：InterviewReport.tsx 原生 fetch 不带 Authorization（FE-04）
        pdf = c.get(f"{BASE}/api/interviews/{sid}/export-pdf")  # 模拟前端：无 token
        check("PDF 导出（无 token，FE-04 模拟）", pdf.status_code == 200,
              f"http={pdf.status_code} type={pdf.headers.get('content-type','')}",
              expected_fail=True)  # weasyprint 依赖系统库，可能失败


def test_knowledge(c: httpx.Client, h: dict):
    print("\n===== 知识库模块（上传→列表→搜索→详情→删除）=====")
    txt = "HireMind 平台支持 AI 简历解析与 RAG 知识库检索。" * 10
    r = c.post(f"{BASE}/api/knowledge/upload",
               files={"file": ("web_kb.txt", txt.encode(), "text/plain")}, headers=h)
    doc = r.json()["data"] if r.status_code == 200 else {}
    check("知识库上传（FormData）", r.status_code == 200 and doc.get("status") == "ready",
          f"http={r.status_code} status={doc.get('status')}",
          expected_fail=True)  # ENV-01: embedding 401

    lst = c.get(f"{BASE}/api/knowledge", headers=h)
    check("知识库列表（页面加载）", lst.status_code == 200, f"http={lst.status_code}",
          expected_fail=True)  # BUG-01

    sr = c.post(f"{BASE}/api/knowledge/search", json={"query": "RAG", "top_k": 5}, headers=h)
    check("知识库搜索（页面搜索框）", sr.status_code == 200, f"http={sr.status_code}",
          expected_fail=True)  # BUG-03 / ENV-01

    if doc.get("id"):
        dt = c.get(f"{BASE}/api/knowledge/{doc['id']}/content", headers=h)
        check("知识库详情 chunks", dt.status_code == 200 and bool(dt.json()["data"].get("chunks")),
              f"http={dt.status_code}")
        dl = c.delete(f"{BASE}/api/knowledge/{doc['id']}", headers=h)
        check("知识库删除", dl.status_code == 200, f"http={dl.status_code}")


def test_schedule_settings(c: httpx.Client, h: dict):
    print("\n===== 日程 + 设置模块 =====")
    day = "2027-08-10"
    rng = c.get(f"{BASE}/api/schedule/range",
                params={"start": "2027-08-09T00:00:00+00:00", "end": "2027-08-16T00:00:00+00:00"},
                headers=h)
    check("日程周视图（range）", rng.status_code == 200, f"http={rng.status_code}")

    r1 = c.post(f"{BASE}/api/schedule", json={
        "candidate_name": "网页候选人A", "scheduled_at": f"{day}T10:00:00+08:00",
        "duration_minutes": 60}, headers=h)
    e1 = r1.json()["data"] if r1.status_code == 200 else {}
    check("日程新建（表单）", r1.status_code == 200, f"http={r1.status_code}")

    r2 = c.post(f"{BASE}/api/schedule", json={
        "candidate_name": "冲突候选人", "scheduled_at": f"{day}T10:30:00+08:00",
        "duration_minutes": 60}, headers=h)
    check("日程时间冲突提示（409）", r2.status_code == 409, f"http={r2.status_code}")

    if e1.get("id"):
        up = c.put(f"{BASE}/api/schedule/{e1['id']}",
                   json={"candidate_name": "改名", "scheduled_at": f"{day}T11:00:00+08:00"},
                   headers=h)
        check("日程编辑（PUT）", up.status_code == 200, f"http={up.status_code}",
              expected_fail=True)  # BUG-02: asyncpg UUID AttributeError
        st = c.put(f"{BASE}/api/schedule/{e1['id']}", json={"status": "completed"}, headers=h)
        check("日程状态变更", st.status_code == 200, f"http={st.status_code}",
              expected_fail=True)  # BUG-02 同因
        dl = c.delete(f"{BASE}/api/schedule/{e1['id']}", headers=h)
        check("日程删除", dl.status_code == 200, f"http={dl.status_code}")

    # 设置
    g = c.get(f"{BASE}/api/settings", headers=h)
    check("设置加载（GET /settings）", g.status_code == 200, f"http={g.status_code}")
    p = c.put(f"{BASE}/api/settings", json={"provider": "deepseek", "deepseek_api_key": "sk-web-test"},
              headers=h)
    check("设置保存（PUT /settings）", p.status_code == 200, f"http={p.status_code}")
    g2 = c.get(f"{BASE}/api/settings", headers=h)
    masked = g2.json()["data"].get("deepseek_api_key", "") if g2.status_code == 200 else ""
    check("设置掩码回显", "**" in masked, f"masked={masked[:8]}...")


def main():
    c = httpx.Client(timeout=180)
    test_pages(c)
    email, h = test_auth_and_home(c)
    test_resume(c, h)
    test_interview(c, h)
    test_knowledge(c, h)
    test_schedule_settings(c, h)

    print("\n===== 网页功能测试汇总 =====")
    passed = sum(1 for x in results if x["tag"] == "PASS")
    expected = sum(1 for x in results if x["tag"] == "EXPECTED-FAIL")
    failed = sum(1 for x in results if x["tag"] == "FAIL")
    print(f"PASS={passed}  EXPECTED-FAIL(已记录问题)={expected}  FAIL={failed}  总计={len(results)}")
    for x in results:
        if x["tag"] == "FAIL":
            print(f"  FAIL: {x['name']} -> {x['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
