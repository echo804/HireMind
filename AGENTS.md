# HireMind - AI 智能面试官平台

## 项目架构

针对 AI 面试场景的全栈应用：

- **后端**: FastAPI + SQLAlchemy (async) + LangChain + PostgreSQL (pgvector)
- **前端**: React 19 + TypeScript + Tailwind CSS v4 + Vite
- **基础设施**: Redis (缓存, 已启用)、本地文件存储（STORAGE_BACKEND=local，非 MinIO）

## 开发环境（重要）

项目存在**两份副本**，曾因"改了代码网页没变化"踩坑。现在以 **WSL 副本为唯一开发副本**：

- 运行副本：`\\wsl$\Ubuntu\home\echo\HireMind`（WSL 内路径 `~/HireMind`）——后端 uvicorn 与前端 vite 都以 **systemd 服务**运行在这份副本上
- D 盘工作区 `D:\codexproject\codexproject\HireMind`：仅备份/编辑用途，修改后需同步到 WSL 副本才生效
- 所有命令（npm install / build / dev / git / python）一律在 WSL 内执行：`wsl bash -c '...'`，不要用 Windows 侧 npm/git（node_modules 是 Linux 二进制）
- 工具（read_file/write_file/edit_file）可直接读写 UNC 路径 `\\wsl$\Ubuntu\home\echo\HireMind\...`
- WSL 网络依赖 keep-alive 进程（`wsl -d Ubuntu --exec sleep infinity`）保持 localhost 转发；掉线时网页打不开，需重启该进程

## 目录结构

```
HireMind/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config/settings.py      # 配置（.env, JWT_SECRET, STORAGE_BACKEND）
│   ├── common/                 # 公共模块
│   │   ├── model/base.py       # SQLAlchemy 基类
│   │   ├── result.py           # 统一 API 响应 Result[T]
│   │   ├── exception/          # 错误码 & 全局异常处理
│   │   └── auth/               # JWT 鉴权依赖（deps.py: get_current_user）
│   ├── infrastructure/         # 基础设施（db, redis, cache 封装, 文件存储）
│   └── modules/                # 业务模块
│       ├── auth/               # 用户注册/登录（JWT）
│       ├── resume/             # 简历解析与分析（上传/列表/详情/编辑）
│       ├── interview/          # 模拟面试（Agent + SSE 流式）
│       ├── knowledgebase/      # 知识库（RAG, pgvector, 语义搜索）
│       ├── schedule/           # 面试日程
│       └── settings/           # AI 模型配置（百炼/DeepSeek/OpenAI）
├── frontend/
│   └── src/
│       ├── pages/              # 页面组件（Home/Welcome/Login/Register/Resume*/Interview*/Settings/Schedule/KnowledgeBase*）
│       ├── components/         # 公共组件（Layout, ConfirmDialog, ErrorBoundary, Skeleton）
│       ├── contexts/           # React Context（Auth, Toast）
│       ├── api/                # API 客户端（client.ts 自动携带 JWT token）
│       ├── hooks/              # 自定义 hooks
│       └── App.tsx             # 路由定义
├── alembic/                    # 数据库迁移
├── docs/                       # 设计/测试/问题归档文档
├── scripts/                    # 启动、同步、验证脚本
├── settings_data/              # 用户 AI 配置（JSON）
├── uploads/                    # 文件存储目录
├── docker-compose.yml          # PostgreSQL + Redis（MinIO 未使用）
└── pyproject.toml              # Python 依赖
```

## 开发规范

### 后端

- 使用 async/await 和 async SQLAlchemy session
- 模块结构：`models.py` -> `schemas.py` -> `repository.py` -> `service.py` -> `router.py`
- 统一响应格式：`Result.success(data)` / `Result.error(code, message)`
- 异常通过 `BusinessException(ErrorCode, message)` 抛出（HTTP 状态码非统一 200）
- 所有 router 需要 `AsyncSession = Depends(get_db)` 注入
- 鉴权：`get_current_user` 从 JWT 解析 user_id；DEV 模式下可回退 `DEV_USER_ID`
- 高频读路径（简历列表、知识库列表/搜索）接入 Redis 缓存：`app/infrastructure/cache.py` 的 `cache_get/cache_set`（注意 `cache_set` 的 `data` 是 keyword-only 参数）
- 写操作后需主动失效相关缓存（如 `invalidate`）

### 前端

- 使用 Tailwind CSS v4（`@import "tailwindcss"`），类名不可动态拼接
- 对于条件样式的 Badge/状态标签，使用独立组件（如 `StatusBadge`）并硬编码完整类名
- API 调用通过 `api/client.ts`（自动携带 JWT token），禁止直接使用原生 `fetch`（SSE 流式消费除外）
- 页面组件放在 `pages/`，公共组件放在 `components/`
- Context 管理全局状态（Auth, Toast）
- 错误处理：`ErrorBoundary` 全局包裹；网络错误自动重试 1 次

### 运行

```bash
# 方式一：WSL systemd 服务（推荐，当前生效方式）
wsl bash -c "sudo systemctl restart hiremind-backend hiremind-frontend"

# 方式二：WSL 手动启动
wsl bash ~/HireMind/scripts/start_all.sh

# 方式三：Windows 侧 start.bat（需先确认 WSL keep-alive 进程存在）

# 访问 http://localhost:5173
```

注意：若网页打不开，先检查 WSL keep-alive 进程（`wsl -d Ubuntu --exec sleep infinity`）是否存活。

## 当前状态

- [x] 用户注册/登录（JWT 鉴权 + 路由守卫）
- [x] 简历上传（PDF/DOCX）与 AI 解析（使用用户 AI 配置）
- [x] 简历列表/详情/人工校正（编辑保存）
- [x] 模拟面试（文字版，AI 出题、逐题反馈、SSE 流式输出）
- [x] 面试复盘报告（逐题点评、维度雷达图、PDF 导出）
- [x] 知识库（文档上传、切片、向量化、语义搜索）
- [x] 面试日程（周视图、CRUD）
- [x] AI 模型配置（百炼 / DeepSeek / OpenAI）
- [x] 前端统一 API 客户端（自动 token）
- [x] 异常处理 HTTP 状态码（非统一 200）
- [x] Skeleton 骨架屏 + 全局 ErrorBoundary
- [x] 首页数据概览 / 欢迎页
- [x] Redis 缓存（简历列表、知识库列表/搜索）
- [ ] 语音面试（阿里云百炼 ASR/TTS）
- [ ] 简历去重检测增强
- [ ] SSE 断线重连 / 会话恢复（当前 answer-stream 一次性消费）
- [ ] 面试报告导出优化（PDF 中文样式）
