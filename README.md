# HireMind · AI 智能面试官

> 基于 AI 大模型的智能模拟面试平台 · 支持简历分析、知识库 RAG、语音面试

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite)
![FastAPI](https://img.shields.io/badge/FastAPI-0.140-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql)

---

## 项目简介

**HireMind** 是一款面向求职者的 AI 模拟面试平台。帮助用户在正式面试前通过 AI 模拟练习，提升面试表现。

### 核心功能

- **简历管理** — 上传简历，AI 自动解析提取关键信息
- **模拟面试** — AI 面试官根据简历和岗位方向智能提问
- **面试报告** — 多维能力评估 + 逐题点评 + 改进建议
- **知识库** — 上传面试相关资料，AI 结合知识库提问
- **面试日程** — 日历管理面试安排
- **系统设置** — 多模型 API 切换

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React 19 / TypeScript 5.6 / Vite 8 / Tailwind CSS 4 |
| **后端** | FastAPI / Python 3.14 / LangChain / SQLAlchemy 2.0 |
| **数据库** | PostgreSQL 18 + pgvector / Redis 8 |
| **AI** | DashScope Qwen / LangChain Agent |

## 快速开始

### 前置要求
- WSL2 (Ubuntu) + PostgreSQL 18 + Redis 8
- Python 3.12+
- Node.js 20+

### 启动服务
```bash
cd ~/HireMind
bash scripts/start_all.sh
```

后端: http://localhost:8000

前端: http://localhost:5173

## 项目结构

```
HireMind/
├── app/                    # 后端
│   ├── main.py             # 应用入口
│   ├── common/              # 通用能力
│   ├── infrastructure/      # 基础设施
│   └── modules/             # 业务模块
├── frontend/               # 前端
│   └── src/pages/          # 页面
├── scripts/                # 启动脚本
└── docker-compose.yml       # Docker 编排
```

---

## License

MIT

