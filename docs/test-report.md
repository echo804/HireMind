# HireMind 测试报告

**测试日期**：2026-08-01
**测试对象**：代码编写会话修改的功能与代码（工作区未提交改动 + 最近 3 个 feat 提交）
**测试方式**：自动化测试（mock AI + 真实 DB/Redis）+ 端到端冒烟（真实服务 + 真实 AI 配置）
**测试环境**：WSL（Python 3.14 / PostgreSQL / Redis），独立测试库 `hiremind_test`

---

## 1. 测试范围

| 模块 | 本次修改内容 | 测试文件 |
|------|-------------|---------|
| Auth | JWT 签发/校验（新增 `app/common/auth/`）、注册/登录返回 token、DEV_USER_ID 回退 | `tests/test_auth.py` |
| Settings | API key Fernet 加密落盘、掩码回显、明文旧数据兼容 | `tests/test_settings.py` |
| Schedule | 时间冲突检测、用户数据隔离 | `tests/test_schedule.py` |
| Knowledgebase | Redis 缓存、鉴权接入、向量搜索 | `tests/test_knowledgebase.py` |
| Resume | 列表缓存与失效 | `tests/test_resume.py` |
| Interview | SSE 流式回答 `/answer-stream`、报告扩展（dimensions/per_question） | `tests/test_interview.py` |
| Cache | `cache_get/cache_set/invalidate_user_cache` | `tests/test_cache.py` |
| 前端 | `client.ts` 重试、`InterviewChat` SSE 消费、`ErrorBoundary` | tsc / vite build / oxlint |

## 2. 执行结果

### 2.1 后端自动化测试（62 用例）

```
52 passed, 10 xfailed（xfail 全部为已记录产品 bug）
```

| 文件 | 结果 | 说明 |
|------|------|------|
| test_auth.py | 11/11 通过 | JWT 有效期 7 天、伪造/篡改 token 拒绝、DEV 回退、数据隔离 |
| test_settings.py | 9/9 通过 | 密文落盘、掩码回显、掩码值不覆盖、旧数据兼容、用户隔离 |
| test_schedule.py | 10 通过 + 2 xfail | 冲突 409 / 相邻不冲突 / CANCELLED 跳过 / 编辑排除自身（xfail BUG-02） |
| test_knowledgebase.py | 3 通过 + 5 xfail | 上传/格式校验通过；缓存与搜索路径 xfail（BUG-01/03/04） |
| test_resume.py | 2 通过 + 2 xfail | 搜索绕过缓存、跨用户拒绝通过；缓存路径 xfail（BUG-01） |
| test_interview.py | 9 通过 + 1 xfail | SSE token 流→最终问题落库、报告、异常分支全通过；use_knowledge xfail（BUG-03） |
| test_cache.py | 6/6 通过 | 读写/TTL/模式删除/用户失效（真实 Redis） |

### 2.2 前端静态验证

| 检查项 | 结果 |
|--------|------|
| `oxlint` | ✅ 0 error / 10 warning（react-hooks 类） |
| `vite build` | ✅ 成功（44 modules，300KB JS） |
| `npm run build`（tsc -b） | ❌ 失败，见 FE-01 / FE-02 |

### 2.3 端到端冒烟测试（真实服务 + 真实 AI 配置）

**23 项：16 PASS / 6 EXPECTED-FAIL（已记录）/ 1 FAIL（环境问题）**

✅ 通过：健康检查、注册/登录、settings 加密保存与掩码回显、面试会话创建、SSE 流式传输框架、日程创建与时间冲突 409、相邻时段不冲突、前端 `/` `/login` `/register` 页面 200。
❌ AI 相关链路全部失败，根因为 **`.env` 百炼 API key 无效（401 invalid_api_key，ENV-01）**，非代码缺陷。修复 key 后需复测。
⚠️ 真实服务复现 BUG-01（`GET /api/knowledge`、`GET /api/resumes` 列表 500）。

## 3. 发现的问题清单（只记录，未修改代码）

### 后端（P0 = 阻断功能）

| 编号 | 严重度 | 位置 | 问题 | 证据 |
|------|--------|------|------|------|
| BUG-01 | P0 | `app/modules/resume/service.py:124`、`app/modules/knowledgebase/service.py:156,199` | `cache_set()` 的 `data` 为 keyword-only 参数，调用处位置传参 → `TypeError: cache_set() missing 1 required keyword-only argument: 'data'`，简历列表 / 知识库列表 / 搜索接口 500 | 自动化 xfail + 真实服务复现 |
| BUG-02 | P0 | `app/modules/schedule/service.py:63` | `uuid.UUID(entity.user_id)`：asyncpg 下 `entity.user_id` 已是 `asyncpg.UUID`，`uuid.UUID()` 抛 `AttributeError` → 编辑日程（PUT）500 | test_schedule 2 用例失败 |
| BUG-03 | P0 | `app/modules/knowledgebase/service.py:180-194` | `search()` 将向量以字符串拼入 `<=>` bind param，asyncpg 下 `PostgresSyntaxError: syntax error at or near ":"` → 知识库搜索不可用（真实环境被 ENV-01 的 401 提前挡住，单测已确认 SQL 错误） | test_search_returns_chunks 失败 |
| BUG-04 | P1 | `app/modules/knowledgebase/service.py:198` | search 缓存 key 为 `query_hash`（不含 user_id 前缀），`invalidate_user_cache` 的 pattern 匹配不到 → 删除文档后搜索缓存不失效 | 代码走查 + 测试断言（受 BUG-01/03 阻塞，待修复后复测） |
| BUG-05 | P1 | `app/modules/schedule/service.py:50,86` | `update()` / `delete()` 无用户归属校验，任意登录用户可修改/删除他人日程（越权） | test_update_other_users_event_is_cross_user |

### 前端

| 编号 | 严重度 | 位置 | 问题 |
|------|--------|------|------|
| FE-01 | P1 | `frontend/src/api/client.ts:15-17` | 构造参数属性（`public status`）与 `tsconfig.app.json` 的 `erasableSyntaxOnly` 冲突，TS1294 ×3 → `npm run build` 失败 |
| FE-02 | P2 | `InterviewList.tsx:39`、`InterviewReport.tsx:137,250`、`Schedule.tsx:23` | 4 处未使用变量（TS6133 `noUnusedLocals`） |

### 环境 / 依赖

| 编号 | 严重度 | 位置 | 问题 |
|------|--------|------|------|
| ENV-01 | P0 | `.env` | `AI_BAILIAN_API_KEY` 无效（百炼返回 401 invalid_api_key），所有真实 AI 功能（简历解析、面试出题/评估、知识库 embedding）不可用。**需在 .env 更新有效 key 后复测 AI 链路** |
| ENV-02 | P2 | `pyproject.toml` | `jose`（python-jose）与 `cryptography` 是新增代码的运行时依赖，未写入 dependencies（.venv312 实测缺少 jose） |
| ENV-03 | P3 | Windows 环境 | `weasyprint` 在 Windows 缺外部系统库，PDF 导出功能仅 WSL 可用 |

## 4. 建议修复顺序

1. **ENV-01**：更新 .env 百炼 key（否则 AI 链路无法验证）
2. **BUG-01**：`cache_set(..., data=...)` 改为关键字传参（3 处，一行修复，解除列表/搜索 500）
3. **BUG-02**：`uuid.UUID(entity.user_id)` 改为直接传 `entity.user_id`（一行修复）
4. **BUG-03**：search 向量参数加 `::vector` cast（`ORDER BY kc.embedding <=> :emb2::vector` 等）
5. **BUG-05**：update/delete 增加 `user_id` 校验；**BUG-04**：search 缓存 key 加入 user_id
6. **FE-01/FE-02**：去除参数属性或关闭 erasableSyntaxOnly；清理未使用变量
7. **ENV-02**：pyproject 补充 jose/cryptography 依赖

## 5. 复测指引

```bash
# 后端自动化测试（WSL）
cd ~/HireMind && .venv/bin/python3 -m pytest tests/ -v

# 端到端冒烟（WSL，需先修复 ENV-01）
bash ~/HireMind/scripts/smoke_all.sh

# 前端
cd frontend && npm run build && npx oxlint
```

> 附：本次仅测试与记录，未修改任何产品代码（`app/`、`frontend/src/` 保持原样）。
