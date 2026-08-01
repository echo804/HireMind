# <img src="frontend/public/favicon.svg" width="36" align="top"> HireMind · AI 智能面试官

<p align="center">
  <i>基于大语言模型的下一代智能模拟面试平台 — 让每一次练习都无限接近真实面试</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React 19">
  <img src="https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Vite-8-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/LangChain-1.0-1C3C3C?style=flat-square&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
</p>

---

## ✨ 为什么选择 HireMind？

面试是求职中最关键也最具挑战的环节。HireMind 将 **AI 大模型** 与 **RAG 知识增强** 深度融合，为你打造一位懂你简历、熟悉你的目标岗位、能给出深度反馈的专属 AI 面试官。不再是死记硬背面试题，而是通过**结构化的模拟面试 + 多维能力分析报告**，让你看清自己的优势与盲区，自信应对每一场真实面试。

---

## 🎯 核心能力

<table>
<tr>
<td width="50%">

### 📄 智能简历解析
上传 PDF、DOCX 或 TXT 简历，AI 自动提取并结构化你的**技能栈、项目经历、教育背景、工作履历**。解析进度实时可见，解析结果支持人工校准确认，确保 AI 面试官对你的了解准确无误。

</td>
<td width="50%">

### 🤖 AI 模拟面试
选择目标岗位方向与题数，AI 基于你的简历**个性化出题**。支持多轮追问、开放式回答，真实还原高压面试场景。面试过程流畅自然，AI 会根据你的回答动态调整后续问题难度与方向。

</td>
</tr>
<tr>
<td width="50%">

### 📊 多维能力报告
面试结束后自动生成**雷达图 + 综合评分 + 逐题点评 + 改进建议**的结构化报告。覆盖沟通表达、技术深度、项目经验、问题解决、学习能力等核心维度，让你精准定位提升方向。支持**一键导出 PDF**。

</td>
<td width="50%">

### 📚 知识库 RAG
上传岗位相关的技术文档、公司资料、行业报告，系统自动切片并向量化存储。面试时 AI 可关联知识库内容进行**深度提问**，模拟真实面试中基于特定领域知识的考察方式。

</td>
</tr>
<tr>
<td width="50%">

### 📅 面试日程管理
内置**周视图日历**，支持创建、编辑、删除面试安排。一目了然管理你的模拟面试计划，养成良好的面试准备节奏。

</td>
<td width="50%">

### 🔌 多模型切换
支持 **阿里云百炼 (Qwen)**、**DeepSeek**、**OpenAI** 三大 AI 提供商。API Key 加密存储、掩码显示，在设置页面一键切换，灵活选择最适合你场景的大模型。

</td>
</tr>
</table>

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                         HireMind 架构                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌──────────┐    HTTP/SSE     ┌──────────────┐                  │
│   │  React   │ ◄──────────────► │   FastAPI    │                  │
│   │  前端    │    localhost     │   后端       │                  │
│   │  :5173   │                 │   :8000      │                  │
│   └──────────┘                 └──────┬───────┘                  │
│                                       │                           │
│            ┌──────────────────────────┼──────────────────┐       │
│            │                          │                   │       │
│       ┌────▼────┐           ┌────────▼─────┐      ┌─────▼────┐  │
│       │PostgreSQL│           │    Redis     │      │  本地文件  │  │
│       │ +pgvector│          │   缓存/队列   │      │  存储      │  │
│       │  :5432   │           │    :6379     │      │  :9000   │  │
│       └─────────┘           └──────────────┘      └──────────┘  │
│                                       │                           │
│                          ┌────────────┼────────────┐             │
│                          │            │            │             │
│                     ┌────▼───┐  ┌─────▼────┐ ┌────▼────┐        │
│                     │ 百炼    │  │ DeepSeek │ │ OpenAI  │        │
│                     │ (Qwen)  │  │          │ │         │        │
│                     └────────┘  └──────────┘ └─────────┘        │
│                         LLM & Embedding 服务                      │
└──────────────────────────────────────────────────────────────────┘
```

**后端分层设计**

```
router.py  →  schemas.py  →  service.py  →  repository.py  →  models.py
  ↑ 路由层       ↑ 验证层        ↑ 业务层         ↑ 数据层         ↑ ORM 层
```

每个业务模块独立分层，职责清晰，便于扩展与维护。全局统一异常处理 + `Result[T]` 响应格式，API 设计一致可靠。

---

## 🛠️ 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| **React** | 19 | UI 框架 — 函数组件 + Hooks |
| **TypeScript** | 5.6 | 类型安全，全量类型覆盖 |
| **Vite** | 8 | 构建工具，HMR 极速热更新，内置 API 代理 |
| **Tailwind CSS** | 4 | 原子化 CSS，`@import "tailwindcss"` 原生方式 |
| **React Router** | 7 | SPA 客户端路由 + 路由守卫 |
| **Recharts** | 2.15 | 能力雷达图、评分分布等数据可视化 |
| **react-big-calendar** | 1.18 | 面试日程周视图日历组件 |
| **Axios** | 1.11 | HTTP 客户端，统一拦截器自动携带 Token |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | 0.115+ | 异步 Web 框架，自动生成 OpenAPI 文档 |
| **Python** | 3.12+ | 运行环境，全面使用 async/await |
| **SQLAlchemy** | 2.0 | 异步 ORM，声明式模型定义 |
| **Pydantic** | 2.11+ | 请求/响应模型验证，配置管理 |
| **Alembic** | 1.17+ | 数据库迁移管理（待集成，当前使用 create_all） |

### AI & 文档处理

| 技术 | 用途 |
|------|------|
| **LangChain** | LLM 调用链编排（Prompt + ChatOpenAI），LangGraph 待集成 |
| **DashScope (百炼)** | 阿里云大模型 API — 文本生成 + Embedding |
| **DeepSeek** | DeepSeek 大模型 API 接入 |
| **OpenAI** | OpenAI GPT 系列 API 接入 |
| **pgvector** | PostgreSQL 向量扩展，知识库语义检索 |
| **PyMuPDF** | PDF 简历/文档文本提取 |
| **python-docx** | DOCX 简历/文档文本提取 |
| **WeasyPrint** | 面试报告 PDF 导出 |

### 基础设施

| 技术 | 用途 |
|------|------|
| **Docker Compose** | 一键编排 PostgreSQL + Redis + MinIO |
| **PostgreSQL 16** | 关系型数据库，存储所有业务数据 |
| **Redis 7** | 高性能缓存与会话管理 |
| **MinIO** | S3 兼容对象存储，简历文件与知识库文档 |

---

## 🚀 快速开始

### 前置要求

| 工具 | 最低版本 |
|------|----------|
| Docker & Docker Compose | 最新稳定版 |
| Python | 3.12+ |
| Node.js | 20+ |
| Git | 2.x |

> **Windows 用户**：推荐在 WSL2 (Ubuntu) 中运行。项目根目录也提供了 `start.bat` 作为 Windows 一键启动入口。

### 1. 克隆项目

```bash
git clone https://github.com/echo804/HireMind.git
cd HireMind
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 AI 服务 API Key（至少配置一个）：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hiremind

# 阿里云百炼
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# DeepSeek（可选）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# OpenAI（可选）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 3. 启动基础设施

```bash
docker compose up -d
```

一键启动 PostgreSQL（含 pgvector 向量扩展）、Redis、MinIO 三个服务。

### 4. 启动后端

```bash
# 创建虚拟环境（首次）
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e .

# 启动服务
uvicorn app.main:app --reload --port 8000
```

首次启动会自动创建数据库表。API 文档即地址：http://localhost:8000/docs

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 6. 开始使用

| 服务 | 地址 |
|------|------|
| 🖥️ 前端页面 | [http://localhost:5173](http://localhost:5173) |
| 🔧 API 文档 (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| 📦 MinIO 控制台 | [http://localhost:9001](http://localhost:9001) |

> **一行启动**：如果你在 WSL 中，也可以直接运行 `bash scripts/start_all.sh` 一键启动全部服务。

---

## 📁 项目结构

```
HireMind/
│
├── app/                              # 🔧 后端应用
│   ├── main.py                       #   FastAPI 入口 — 路由注册、lifespan、CORS
│   ├── config/settings.py            #   配置管理 — .env → Pydantic Settings
│   ├── common/                       #   公共层
│   │   ├── auth/                     #     JWT 鉴权依赖
│   │   ├── ai/                       #     LLM 调用封装
│   │   ├── model/base.py             #     SQLAlchemy 声明式基类
│   │   ├── result.py                 #     Result[T] 统一响应模型
│   │   └── exception/                #     ErrorCode 错误码 + 全局异常处理器
│   ├── infrastructure/               #   基础设施层
│   │   ├── database.py               #     异步 PostgreSQL 连接
│   │   ├── redis.py                  #     Redis 连接
│   │   ├── file/                     #     MinIO / S3 文件存储
│   │   └── export/                   #     WeasyPrint PDF 导出
│   └── modules/                      #   业务模块（每个模块独立分层）
│       ├── auth/                     #     用户注册 / 登录
│       ├── resume/                   #     简历上传、AI 解析、管理
│       ├── interview/                #     模拟面试、AI 出题、报告生成
│       ├── knowledgebase/            #     文档上传、切片、向量化、语义搜索
│       ├── schedule/                 #     面试日程日历 CRUD
│       └── settings/                 #     AI 模型配置
│
├── frontend/                         # 🎨 前端应用
│   └── src/
│       ├── pages/                    #   页面组件
│       │   ├── Home.tsx              #     首页数据概览
│       │   ├── Login.tsx             #     登录
│       │   ├── Register.tsx          #     注册
│       │   ├── ResumeList.tsx        #     简历列表
│       │   ├── ResumeDetail.tsx      #     简历详情 & 解析进度
│       │   ├── InterviewList.tsx     #     面试列表
│       │   ├── InterviewChat.tsx     #     面试对话
│       │   ├── InterviewReport.tsx   #     面试报告
│       │   ├── KnowledgeBase.tsx     #     知识库管理
│       │   ├── KnowledgeBaseDetail.tsx #   知识库文档详情
│       │   ├── Schedule.tsx          #     面试日程日历
│       │   └── Settings.tsx          #     AI 模型配置
│       ├── components/               #   公共组件（Layout, Skeleton, ConfirmDialog）
│       ├── contexts/                 #   React Context（Auth, Toast）
│       ├── api/                      #   API 客户端（Axios + 拦截器）
│       └── App.tsx                   #   路由定义 + 路由守卫
│
├── scripts/                          # 🛠️ 运维脚本
│   ├── start_all.sh                  #   一键启动全部服务
│   ├── start_backend.sh              #   启动后端
│   ├── start_frontend.sh             #   启动前端
│   └── stop_all.sh                   #   停止全部服务
│
├── docs/                             # 📖 项目文档
│   ├── features.md                   #   功能清单与详情
│   └── guide.md                      #   用户操作指南
│
├── docker-compose.yml                # 🐳 PostgreSQL + Redis + MinIO
├── pyproject.toml                    # 🐍 Python 依赖与项目元数据
├── .env.example                      # 🔐 环境变量模板
├── start.bat                         # 🪟 Windows 一键启动
└── LICENSE                           # 📄 MIT License
```

---

## 🔌 API 概览

所有 API 以 `/api` 为前缀，返回统一 `Result[T]` 格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

| 模块 | 方法 | 端点 | 说明 |
|------|------|------|------|
| **认证** | `POST` | `/api/auth/register` | 用户注册 |
| | `POST` | `/api/auth/login` | 用户登录 |
| **简历** | `POST` | `/api/resumes/upload` | 上传简历文件 |
| | `GET` | `/api/resumes` | 简历列表 |
| | `GET` | `/api/resumes/{id}` | 简历详情 |
| | `DELETE` | `/api/resumes/{id}` | 删除简历 |
| | `POST` | `/api/resumes/batch-delete` | 批量删除 |
| **面试** | `POST` | `/api/interviews` | 创建面试 |
| | `POST` | `/api/interviews/{id}/answer` | 提交回答 |
| | `POST` | `/api/interviews/{id}/end` | 结束面试 |
| | `GET` | `/api/interviews/{id}/report` | 获取报告 |
| | `GET` | `/api/interviews/{id}/export-pdf` | 导出 PDF |
| | `DELETE` | `/api/interviews/{id}` | 删除面试 |
| **知识库** | `POST` | `/api/knowledge/upload` | 上传文档 |
| | `GET` | `/api/knowledge` | 文档列表 |
| | `GET` | `/api/knowledge/{id}/content` | 文档内容 |
| | `POST` | `/api/knowledge/search` | 语义搜索 |
| | `DELETE` | `/api/knowledge/{id}` | 删除文档 |
| **日程** | `POST` | `/api/schedule` | 创建日程 |
| | `PUT` | `/api/schedule/{id}` | 更新日程 |
| | `GET` | `/api/schedule/day` | 按日查询 |
| | `GET` | `/api/schedule/range` | 按范围查询 |
| | `DELETE` | `/api/schedule/{id}` | 删除日程 |
| **设置** | `GET` | `/api/settings` | 获取 AI 配置 |
| | `PUT` | `/api/settings` | 更新 AI 配置 |

> 完整交互式 API 文档请访问：http://localhost:8000/docs

---

## 🖼️ 界面预览

<p align="center">
  <i>截图即将推出 — 欢迎 Clone 体验完整交互</i>
</p>

<!--
| 首页概览 | 模拟面试 | 面试报告 |
|:---:|:---:|:---:|
| ![首页](docs/screenshots/home.png) | ![面试](docs/screenshots/interview.png) | ![报告](docs/screenshots/report.png) |

| 简历管理 | 知识库 | 面试日程 |
|:---:|:---:|:---:|
| ![简历](docs/screenshots/resume.png) | ![知识库](docs/screenshots/knowledge.png) | ![日程](docs/screenshots/schedule.png) |
-->

---

## 🗺️ 路线图

| 状态 | 功能 | 说明 |
|:---:|------|------|
| ✅ | 简历上传与 AI 解析 | PDF/DOCX/TXT 多格式支持，实时进度反馈 |
| ✅ | 模拟面试引擎 | AI 个性化出题 + 多轮追问 |
| ✅ | 多维能力报告 | 雷达图 + 评分 + 逐题点评 + PDF 导出 |
| ✅ | 知识库 RAG | 文档切片向量化 + 语义检索 |
| ✅ | 面试日程 | 周视图日历 CRUD |
| ✅ | 多模型切换 | 百炼 / DeepSeek / OpenAI |
| 🔄 | 语音面试 | ASR 语音输入 + TTS 语音播报 |
| 📅 | 简历去重检测 | 基于语义相似度的简历查重 |
| 📅 | 面试流式输出 | SSE 实时推送面试官提问 |

---

## 🤝 参与贡献

我们欢迎任何形式的贡献！无论是 Bug 报告、功能建议还是代码提交。

### 贡献流程

1. **Fork** 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 发起 **Pull Request**

### 开发规范

- 后端模块遵循 `router → schemas → service → repository → models` 分层架构
- 使用 async/await 和 async SQLAlchemy session
- API 响应统一使用 `Result[T]` 格式
- 前端使用 Tailwind CSS v4，类名不可动态拼接
- API 调用通过 `api/client.ts` 统一客户端，禁止直接使用 `fetch`

---

## 📄 License

本项目采用 [MIT License](LICENSE) 开源。

---

<p align="center">
  <b>HireMind</b> — 用 AI 的力量，让每一次面试准备都事半功倍 🚀
</p>
