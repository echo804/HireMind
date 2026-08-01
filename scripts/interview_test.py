"""模拟面试功能测试：真实 AI（deepseek）+ 简历 214b3bc9（大模型应用开发.pdf）。

流程：创建面试(5题) → SSE 流式回答×5 → 结束 → 评估报告 → PDF 导出。
检查点：真实 AI 出题（非 fallback）、SSE token 流、问题基于简历技术栈、
历史上下文引用、报告维度完整性、PDF 导出。只记录问题不修改代码。
"""

import json
import time
import uuid
from pathlib import Path

import httpx

from app.common.auth import create_access_token

USER_ID = "f18f9bb6-45ea-41a5-9904-97e41245cdf3"
RESUME_ID = "214b3bc9-da5b-45f6-8eaa-7cfe422f9671"
BASE = "http://localhost:8000"

results = []
answers = [
    "我在大模型应用开发方向有较多实践。核心项目是构建 RAG 知识库问答系统，使用 LangChain 做文档加载、切片与向量检索，\
用 pgvector 存储向量，配合 Prompt 模板实现上下文增强回答；同时做过基于 Function Calling 的 Agent 工具调用，\
处理过幻觉抑制与长上下文截断问题。",
    "技术上我熟悉 Qwen、DeepSeek 等开源模型的 API 接入，会用 ChatOpenAI 兼容层统一调用；Embedding 用过 text-embedding 系列，\
检索策略上对比过向量相似度与混合检索（BM25 + 向量）的效果差异。",
    "遇到过的难点是知识库检索召回不准，我通过调整切片策略（按语义段落切分 + 重叠）、优化查询改写、引入 rerank 重排，\
把 top-5 命中率提升了约 20%；另外处理过流式输出的超时与重试。",
    "生产场景上，我做过一个高并发问答服务的性能优化：缓存热点查询、连接池调优、把 embedding 与 LLM 调用异步化，\
压测 QPS 从 20 提升到 80 左右；也处理过模型响应超时导致的用户体验问题。",
    "如果做系统设计，我会从数据层（文档清洗/切片/向量库选型）、检索层（多路召回+重排）、生成层（Prompt 模板/防注入/\
幻觉校验）、观测层（链路追踪/评估集）四层设计一个企业级 RAG 平台，并规划增量更新与权限隔离。",
]


def check(name, cond, detail="", expected_fail=False):
    tag = "PASS" if cond else ("EXPECTED-FAIL" if expected_fail else "FAIL")
    results.append({"name": name, "tag": tag, "detail": detail})
    print(f"[{tag}] {name}  {detail}")


def parse_sse(text):
    events = []
    for line in text.split("\n"):
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except Exception:
                pass
    return events


def main():
    c = httpx.Client(timeout=300)
    token = create_access_token(uuid.UUID(USER_ID))
    h = {"Authorization": f"Bearer {token}"}

    print("===== 1. 创建面试（简历 214b3bc9，5 题）=====")
    t0 = time.time()
    r = c.post(f"{BASE}/api/interviews", json={
        "resume_id": RESUME_ID, "direction": "大模型应用开发",
        "interview_type": "text", "total_questions": 5, "use_knowledge": False,
    }, headers=h)
    sid = r.json()["data"]["id"] if r.status_code == 200 else None
    check("创建面试", bool(sid), f"http={r.status_code} create={time.time()-t0:.1f}s")

    if not sid:
        print("创建失败，终止。", r.text[:200])
        return 1

    q1 = r.json()["data"]["questions_asked"][0]["question"]
    fallback_mark = "请介绍一下" in q1 and "技术栈" in q1
    check("首题由真实 AI 生成（非 fallback）", bool(q1) and not fallback_mark,
          f"q1={q1[:60]}...")

    print("\n===== 2. SSE 流式回答 ×5 =====")
    qa_records = []
    for i in range(1, 6):
        t1 = time.time()
        resp = c.post(f"{BASE}/api/interviews/{sid}/answer-stream",
                      json={"answer": answers[i - 1]}, headers=h)
        events = parse_sse(resp.text)
        tokens = [e for e in events if "token" in e]
        finals = [e for e in events if "question_index" in e and "token" not in e]
        question = finals[0].get("question", "") if finals else ""
        is_final = i == 5
        ok = resp.status_code == 200 and len(tokens) > 0 and bool(question)
        check(f"第{i}题 SSE（token 流 + 问题落库）", ok,
              f"http={resp.status_code} tokens={len(tokens)} 耗时={time.time()-t1:.1f}s")
        qa_records.append({"index": i, "question": question, "answer": answers[i - 1]})
        if question:
            print(f"    Q{i}: {question[:100]}")
        if is_final:
            # 最后一题：应触发完成 + 评估
            completed = any("is_completed" in e for e in events)
            check("第5题回答后会话完成", completed,
                  f"events={[e for e in events if 'is_completed' in e]}")
        if "error" in str(events):
            print(f"    !! 第{i}题异常事件: {[e for e in events if 'error' in e]}")

    # 问题质量检查：基于简历技术栈
    q_text = " ".join(q["question"] for q in qa_records if q["question"])
    kb_words = ["大模型", "RAG", "LangChain", "向量", "检索", "Agent", "Prompt", "切片", "模型", "应用"]
    hit = [w for w in kb_words if w in q_text]
    check("问题基于简历技术栈（大模型应用开发）", len(hit) >= 3, f"命中关键词={hit}")

    print("\n===== 3. 会话状态与报告 =====")
    sess = c.get(f"{BASE}/api/interviews/{sid}", headers=h)
    sd = sess.json()["data"] if sess.status_code == 200 else {}
    check("会话已完成", sd.get("status") == "completed",
          f"status={sd.get('status')} 题目数={sd.get('current_question')}/{sd.get('total_questions')}")

    rep = c.get(f"{BASE}/api/interviews/{sid}/report", headers=h)
    rd = rep.json()["data"] if rep.status_code == 200 else {}
    if rd:
        check("报告返回", bool(rd.get("feedback")), f"score={rd.get('score')}")
        dims = rd.get("dimensions", {})
        check("报告 5 维度完整", set(dims) >= {"tech_depth", "tech_selection", "problem_solving", "production", "communication"},
              f"dims={list(dims.keys())}")
        check("报告 per_question 明细", len(rd.get("per_question", [])) >= 1,
              f"per_question={len(rd.get('per_question', []))}")
        check("报告优势/不足/建议", all(len(rd.get(k, [])) > 0 for k in ("strengths", "weaknesses", "suggestions")),
              f"s={len(rd.get('strengths', []))} w={len(rd.get('weaknesses', []))} a={len(rd.get('suggestions', []))}")
        print(f"    反馈: {rd.get('feedback', '')[:80]}")
        print(f"    维度: {dims}")

    print("\n===== 4. PDF 导出 =====")
    pdf = c.get(f"{BASE}/api/interviews/{sid}/export-pdf", headers=h)
    if pdf.status_code == 200:
        path = Path("/tmp/interview_report.pdf")
        path.write_bytes(pdf.content)
        check("PDF 导出", len(pdf.content) > 1000, f"http={pdf.status_code} 大小={len(pdf.content)}B type={pdf.headers.get('content-type')}")
    else:
        check("PDF 导出", False, f"http={pdf.status_code} {pdf.text[:100]}")

    print("\n===== 汇总 =====")
    passed = sum(1 for x in results if x["tag"] == "PASS")
    failed = sum(1 for x in results if x["tag"] == "FAIL")
    print(f"PASS={passed}  FAIL={failed}  总计={len(results)}")
    for x in results:
        if x["tag"] == "FAIL":
            print(f"  FAIL: {x['name']} -> {x['detail']}")

    # 保存问答记录供报告使用
    Path("/tmp/interview_qa.json").write_text(
        json.dumps({"session_id": sid, "qa": qa_records, "report": rd}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
