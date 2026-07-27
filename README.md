# HireMind · AI 智能面试官

> 基于 AI 大模型的智能模拟面试平台 · 支持简历分析、知识库 RAG、多模型切换

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss)
![FastAPI](https://img.shields.io/badge/FastAPI-0.140-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis)

---

## 项目简介

HireMind 是一款面向求职者的 AI 智能模拟面试平台，旨在帮助用户在正式面试前通过 AI 模拟练习提升面试表现。系统支持简历自动解析、多岗位方向模拟面试、知识库 RAG 增强、多模型與提供商切换等功能。

### 核心功能

- **简历管理** — 上传 PDF/DOCX/TXT 简历，AI 自动解析提取技能、项目经历、教育背景等结构化信息
- **模拟面试** — AI 面试官根据简历和岗位方向智能出题，支持多轮追问与流式回答
- **面试报告** — 多维能力雷达图 + 综合评分 + 逐题点评 + 改进建议
- **知识库 RAG** — 上传文档自动切片向量化，面试时 AI 结合知识库资料提问
- **面试日程** — 日历视图管理面试安排
- **多模型支持** — 支持阿里云百炼 / DeepSeek / OpenAI 多个 AI 提供商

## 技术栈

### 前端

| 技术 | 用途 |
|------|------|
| **React 19** | UI 框架 |
| **TypeScript 5.6** | 类型安全 |
| **Vite 8** | 构建工具，内置 proxy 转发 API |
| **Tailwind CSS 4** | 原子化样式 |
| **React Router 7** | SPA 路由 |
| **Recharts** | 能力雷达图等数据可视化 |

### 后端

| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架，支持 async/await |
| **Python 3.14** | 运行环境 |
| **LangChain + LangGraph** | AI Agent 编排 |
| **SQLAlchemy 2.0 (async)** | ORM |
| **PostgreSQL 18 + pgvector** | 关系数据库 + 向量检索 |
| **Redis 8** | 缓存与异步队列 |
| **DashScope (Qwen)** | 大语言模型 API |

## 项目结构

```
HireMind/
├── app/                          # 后端
│   ├── main.py                   # FastAPI 入口
│   ├── config/settings.py        # 配置管理
│   ├── common/                   # 公共模块
│   │   ├── model/base.py        # SQLAlchemy 基类
│   │   ├── result.py            # 统一响应 Result[T]
│   │   └── exception/          # 错误码 & 全局异常处理
│   ├── infrastructure/           # 基础设施
│   │   ├── database.py          # 数据库连接
│   │   ├── redis.py             # Redis 连接
│   │   └── file/               # 文件存储
│   └── modules/                 # 业务模块
│       ├── auth/                 # 用户认证
│       ├── resume/               # 简历管理
│       ├── interview/            # 模拟面试
│       ├── knowledgebase/        # 知识库 RAG
│       ├── schedule/             # 面试日程
│       └── settings/             # 系统设置
├── frontend/                   # 前端
│   └── src/
│       ├── pages/               # 页面组件
│       ├── components/          # 公共组件
│       ├── contexts/            # React Context
│       ├── api/                 # API 封装
│       └── App.tsx              # 路由定义
├── scripts/                    # 启动脚本
├── docs/                       # 文档
└── docker-compose.yml           # Docker 编排
```

## 快速开始

### 前置要求

- WSL2 (Ubuntu) 或 Linux + PostgreSQL 18 (pgvector) + Redis 8
- Python 3.12+
- Node.js 20+

### 1. 启动基础设施

可使用 Docker Compose 一键启动数据库服务：

```bash
docker compose up -d
```

或直接安装（见操作文档）

### 2. 启动后端

```bash
cd ~/HireMind
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend && npm run dev
```

### 4. 访问

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

## 项目状态

- [x] 用户注册/登录
- [x] 简历上传（PDF/DOCX）与 AI 解析
- [x] 模拟面试（文字版，AI 出题与评估）
- [x] 知识库（文档上传、切片、向量化、语义搜索）
- [x] 面试日程（日历视图、CRUD）
- [x] AI 模型配置（百炼 / DeepSeek / OpenAI）
- [ ] JWT 鉴权与用户隔离
- [ ] 语音面试（阿里云百炼 ASR/TTS）
- [ ] 简历去重检测增强
- [ ] 面试报告导出 PDF

## License

MIT
