# 模拟面试功能测试报告（补充）

**补充日期**：2026-08-01（用户更新 key 后复测）
**状态**：AI 出题链路曾成功一次（真实基于简历的问题），但 AI key 服务不稳定 + 发现 P0 代码缺陷

---

## 1. 复测结果（key 更新后，共 4 轮）

| 轮次 | 时间 | 结果 |
|------|------|------|
| 第 1 轮 | 12:52 | ✅ **AI 出题成功**：首题基于简历（HireMind 项目），第 1-4 题 SSE 各 170~199 tokens，问题含追问逻辑（"请聚焦于你简历中的实际项目"）；第 5 题直接完成（设计如此）；**评估报告失败**（score=0 兜底） |
| 第 2 轮 | 12:58 | ❌ 全部 401（Incorrect API key），fallback 文案 |
| 第 3 轮 | 13:05 | ❌ 全部 401 |
| 第 4 轮 | 13:10 | ❌ 创建面试请求超时（300s，AI 调用挂起） |

**AI key 探测**（独立探测脚本，4 次）：200（12:52）→ 200（13:05，流式 6 chunks）→ 但后端调用同一配置时 401/超时。

## 2. 发现的问题

### BUG-07（P0，代码缺陷，确定）——评估报告永远失败
- **位置**：`app/modules/interview/agent.py` 的 `EVALUATION_PROMPT`（第 56-99 行）
- **根因**：该模板是 f-string，其中 JSON 示例 `"dimensions": {{`（第 85 行）与 `{{"index": 1...}}`（第 93 行）用了**两层**大括号。f-string 渲染后变成**单层** `{`，随后 `ChatPromptTemplate` 把 `"tech_depth"`、`"index"` 误解析为模板变量，抛：
  ```
  Input to ChatPromptTemplate is missing variables {'"\n    "tech_depth"', '"index"'}.
  Expected: ['\n    "tech_depth"', '"index"', 'direction', 'transcript']
  ```
- **对比**：`SYSTEM_PROMPT`（出题）的 JSON 示例全部用**四层**括号 `{{{{`/`}}}}`（正确），所以出题正常、评估必崩。
- **影响**：`evaluate_interview` 抛异常 → `answer_stream`/`end_session` 的 except 兜底 → 报告恒为 `score=0`、`dimensions={}`。**即使 AI key 有效，评估报告也无法生成**。
- **修复方向**（未改代码）：第 85/93 行的 `{{`/`}}` 改为 `{{{{`/`}}}}`（与 SYSTEM_PROMPT 一致）。

### ENV-04（环境，AI 网关不稳定）
- 用户配置的 key（前缀 `sk-ws-H`，provider=bailian，base=dashscope，model=deepseek-v4-flash）表现不稳定：同一配置探测 200 但后端连续调用 401/挂起。
- 疑似第三方中转/聚合服务（key 格式非官方 DeepSeek 或百炼），存在限流或节点不稳定。
- **建议**：更换为官方渠道签发的 key（DeepSeek `sk-` 或百炼 `sk-`），并在设置页确认 provider/model 匹配。

## 3. 功能框架结论（AI 正常时已验证）

| 功能 | 结果 |
|------|------|
| 创建面试（含简历） | ✅ 0.3~5.6s |
| SSE 流式出题 | ✅ token 逐字推送、问题落库、基于简历上下文、含追问 |
| 会话完成 5/5 | ✅ |
| PDF 导出 | ✅ 54~99KB（报告含内容时更大） |
| 前端 3 页面 | ✅ 200 |
| 评估报告 | ❌ BUG-07（模板转义）——需修复后才可验证 |

## 4. 复测指引（修复后）

1. 修复 BUG-07（EVALUATION_PROMPT 括号转义）
2. 更换稳定的官方 API key（网页设置页保存）
3. `bash ~/HireMind/scripts/smoke_start_backend.sh` + `wsl bash -c 'cd ~/HireMind && .venv/bin/python3 scripts/interview_test.py'`
4. 预期：出题 + 评估报告（score/dimensions/per_question）完整通过

> 附：全程未修改任何产品代码。
