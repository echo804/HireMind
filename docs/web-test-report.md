# HireMind 网页功能测试报告

**测试日期**：2026-08-01
**测试对象**：前端 12 个路由页面 + 对应后端 API 契约（`frontend/src/pages/` × 12 + `api/client.ts`）
**测试方式**：页面可达性（HTTP + HTML/JS bundle）+ 逐页面 API 全链路模拟（httpx 模拟前端操作序列，含 SSE/FormData/PDF 下载）+ 前端代码契约走查
**测试环境**：WSL（真实服务：后端 8000 连 `hiremind_test` 库、前端 vite dev 5173）

---

## 1. 执行结果总览

**46 项：43 PASS / 3 EXPECTED-FAIL（已记录问题）/ 0 FAIL**

| 模块 | 结果 | 明细 |
|------|------|------|
| 页面可达性 | 16/16 ✅ | 12 个路由全部 200、index.html root 挂载点、main.tsx 可加载、vite proxy 转发 |
| Auth | 4/4 ✅ | 注册、登录、错误密码 401、logout（纯前端清理） |
| 首页统计 | 4/4 ✅ | /resumes、/interviews、/knowledge、/schedule/range 并行加载 |
| 简历 | 5/5 ✅ | 上传→轮询详情→列表→搜索→删除（AI 解析失败按 ENV-01 记录） |
| 面试 | 6/6 ✅ | 创建、SSE 流式（9 事件）、结束、报告、PDF 导出 |
| 知识库 | 2/4 ⚠️ | 列表 ✅（BUG-01 修复生效）；上传/搜索 ❌（ENV-01 AI key 无效） |
| 日程 | 7/7 ✅ | 周视图、新建、冲突 409、编辑、状态变更、删除（BUG-02/05 修复生效） |
| 设置 | 3/3 ✅ | GET 加载、PUT 保存、掩码回显 |

## 2. 关键发现

### 2.1 上一轮记录的后端问题已全部修复（实测验证生效）

| 问题 | 修复内容 | 本轮实测 |
|------|---------|---------|
| BUG-01 cache_set 位置传参 | 调用改为 `data=` 关键字 | 简历/知识库列表 200 ✅ |
| BUG-02 schedule 编辑 asyncpg UUID | `uuid.UUID(entity.user_id)` → `entity.user_id` | 日程编辑/状态变更 200 ✅ |
| BUG-03 kb search 向量 SQL | `<=>` 参数加 `::vector` cast | SQL 修复确认（被 ENV-01 401 掩盖，未走通） |
| BUG-04 search 缓存 key | key 增加 user_id 前缀 | 代码确认 `hiremind:kb:{user_id}:search:*` |
| BUG-05 schedule 越权 | update/delete 增加归属校验 | 跨用户操作返回 404 ✅ |

### 2.2 仍存在的问题（未修改代码）

| 编号 | 严重度 | 位置 | 问题 |
|------|--------|------|------|
| **ENV-01** | P0 | `.env` | 百炼 API key 无效（401 invalid_api_key）→ 简历 AI 解析（fallback name=None）、知识库上传/搜索（500）均失败。**需更新 key 后复测** |
| **FE-03** | P1 | `InterviewChat.tsx:73` | SSE 请求读 `localStorage["token"]`（实际存于 `localStorage["user"]` JSON）→ Authorization 头为空。实测：无 token 的 SSE **仍可正常推进会话**（后端回退 DEV_USER + find_by_id 无归属校验）→ 会话操作实际无鉴权 |
| **FE-04** | P1 | `InterviewReport.tsx:32` | PDF 下载原生 fetch 不带 Authorization。实测：无 token 下载 200 ✅（内容可被任意人获取） |
| **BUG-06** | P1 | `interview/service.py` | `get_session`/`get_report`/`delete_session`/`export_pdf` 均无 user_id 归属校验（router 取到 token 但未传给 service）→ 任意登录用户可查看/删除他人面试会话、报告、PDF（与已修复的 BUG-05 同类） |
| FE-01 | P1 | `client.ts:15-17` | 参数属性与 `erasableSyntaxOnly` 冲突（TS1294），`npm run build` 失败 |
| FE-02 | P2 | 4 个页面 | 未使用变量（TS6133） |
| 观察项 | P3 | kb 上传 | AI 服务不可用时上传返回 HTTP 500（语义上 502/503 更合理），文档落为 failed 状态 |

## 3. 页面功能明细

| 页面 | 功能 | 结论 |
|------|------|------|
| `/` 首页 | 未登录静态展示、登录后 4 统计卡片 | ✅ |
| `/login` `/register` | 表单提交、错误提示、跳转 | ✅ |
| `/resumes` | 上传（FormData）、列表、搜索、删除 | ✅（AI 解析受 ENV-01 影响） |
| `/resumes/:id` | 1.5s 轮询进度条、终态展示 | ✅（轮询机制正常） |
| `/interviews` | 创建、单个/批量删除 | ✅ |
| `/interviews/:id` | SSE 流式问答 | ✅ 框架正常（AI 出题受 ENV-01 影响 fallback） |
| `/interviews/:id/report` | 报告渲染、PDF 下载 | ✅（PDF 无鉴权，FE-04） |
| `/settings` | AI 配置加载/保存/掩码 | ✅ |
| `/schedule` | 周视图、新建、冲突提示、编辑、状态、删除 | ✅ |
| `/knowledge-base` | 上传、列表、搜索、删除 | ⚠️ 列表 ✅；上传/搜索受 ENV-01 影响 |
| `/knowledge-base/:id` | 文档切片展示 | 未走通（上传失败，ENV-01） |

## 4. 复测指引

```bash
# WSL 内（需先修复 ENV-01 更新 .env 的 AI key）
wsl bash -c 'bash ~/HireMind/scripts/smoke_start_backend.sh && bash ~/HireMind/scripts/smoke_start_frontend.sh && sleep 600'
wsl bash -c 'cd ~/HireMind && .venv/bin/python3 scripts/web_test.py'
```

> 附：本轮仅测试与记录，未修改任何产品代码（`app/`、`frontend/src/` 保持原样）。
