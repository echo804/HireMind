# HireMind - AI 智能面试官平台

## 项目架构

针对 AI 面试场景的全栈应用：

- **后端**: FastAPI + SQLAlchemy (async) + LangChain/LangGraph + PostgreSQL (pgvector)
- **前端**: React 19 + TypeScript + Tailwind CSS v4 + Vite
- **基础设施**: Redis (缓存), MinIO/S3 (对象存储)

## 目录结构

```
HireMind/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config/settings.py      # 配置（.env）
│   ├── common/                 # 公共模块
│   │   ├── model/base.py       # SQLAlchemy 基类
│   │   ├── result.py           # 统一 API 响应 Result[T]
│   │   └── exception/          # 错误码 & 全局异常处理
│   ├── infrastructure/         # 基础设施（DB, Redis, 文件存储）
│   └── modules/                # 业务模块
│       ├── auth/               # 用户注册/登录
│       ├── resume/             # 简历解析与分析
│       ├── interview/          # 模拟面试（Agent + LangChain）
│       ├── knowledgebase/      # 知识库（RAG, pgvector）
│       ├── schedule/           # 面试日程
│       └── settings/           # AI 模型配置
├── frontend/
│   └── src/
│       ├── pages/              # 页面组件
│       ├── components/         # 公共组件（Layout, ConfirmDialog）
│       ├── contexts/           # React Context（Auth, Toast）
│       ├── api/                # API 客户端
│       └── App.tsx             # 路由定义
├── docker-compose.yml          # PostgreSQL + Redis + MinIO
└── pyproject.toml              # Python 依赖
```

## 开发规范

### 后端

- 使用 async/await 和 async SQLAlchemy session
- 模块结构：`models.py` -> `schemas.py` -> `repository.py` -> `service.py` -> `router.py`
- 统一响应格式：`Result.success(data)` / `Result.error(code, message)`
- 异常通过 `BusinessException(ErrorCode, message)` 抛出
- 所有 router 需要 `AsyncSession = Depends(get_db)` 注入
- DEV 模式下使用固定 `DEV_USER_ID`，后续接入 JWT 鉴权

### 前端

- 使用 Tailwind CSS v4（`@import "tailwindcss"`），类名不可动态拼接
- 对于条件样式的 Badge/状态标签，使用独立组件（如 `StatusBadge`）并硬编码完整类名
- API 调用通过 `api/client.ts`（自动携带 JWT token），禁止直接使用原生 `fetch`
- 页面组件放在 `pages/`，公共组件放在 `components/`
- Context 管理全局状态（Auth, Toast）

### 运行

```bash
# 方式一：双击项目根目录 start.bat
# 方式二：在 WSL 中运行
wsl bash ~/HireMind/scripts/start_all.sh

# 访问 http://localhost:5173
```

## 当前状态

- [x] 用户注册/登录（JWT 鉴权 + 路由守卫）
- [x] 简历上传（PDF/DOCX）与 AI 解析（使用用户 AI 配置）
- [x] 模拟面试（文字版，AI 出题与评估）
- [x] 知识库（文档上传、切片、向量化、语义搜索）
- [x] 面试日程（周视图、CRUD）
- [x] AI 模型配置（百炼 / DeepSeek / OpenAI）
- [x] 前端统一 API 客户端（自动 token）
- [x] 异常处理 HTTP 状态码（非统一 200）
- [x] Skeleton 骨架屏加载态
- [x] 首页数据概览
- [x] 面试报告 PDF 导出
- [ ] 语音面试（阿里云百炼 ASR/TTS）
- [ ] 简历去重检测增强
- [ ] Redis 缓存实际启用
- [ ] 面试流式输出（SSE）
