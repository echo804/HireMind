# HireMind 操作指南

> 方便快速上手和日常使用这套 AI 智能面试系统

---

## 目录

1. [环境搭建](#环境搭建)
2. [启动与停止](#启动与停止)
3. [配置 AI 模型](#配置-ai-模型)
4. [模块使用指南](#模块使用指南)
5. [开发规范](#开发规范)
6. [架构说明](#架构说明)
7. [Git 工作流](#git-工作流)
8. [项目路线图](#项目路线图)
9. [常见问题](#常见问题)

---

## 环境搭建

### 系统要求

| 组件 | 版本要求 | 备注 |
|------|------|------|
| 操作系统 | Windows 11 + WSL2 或 Linux | 推荐 Ubuntu 24.04 |
| Python | 3.12+ | 需安装 pip/venv |
| Node.js | 20+ | 推荐使用 pnpm |
| PostgreSQL | 14+ | 需安装 pgvector 扩展 |
| Redis | 6+ | 用于缓存与异步任务 |

### 数据库与 Redis 安装

**方案 A：Docker Compose （推荐）**

```bash
docker compose up -d
```

**方案 B：WSL 直接安装**

```bash
# PostgreSQL
sudo apt install postgresql postgresql-contrib -y
sudo service postgresql start

# pgvector 向量扩展
sudo apt install postgresql-18-pgvector -y

# 创建数据库
sudo -u postgres psql -c "CREATE DATABASE hiremind;"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '123456';"

# Redis
sudo apt install redis -y
sudo service redis-server start
redis-cli ping  # 应输出 PONG
```

### 项目代码与依赖

```bash
git clone https://github.com/echo804/HireMind.git
cd HireMind

# Python 虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis
pip install python-multipart python-dotenv pydantic-settings
pip install langchain langchain-community dashscope
pip install sqlalchemy-utils aiofiles PyMuPDF python-docx openai jinja2

# 前端依赖
cd frontend
npm install  # 或 pnpm install
cd ..
```

---
## 启动与停止

### 一键启动

```bash
cd ~/HireMind
bash scripts/start_all.sh
```

### 一键停止

```bash
bash scripts/stop_all.sh
```

### 单独启动

后端：
```bash
cd ~/HireMind
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

前端：
```bash
cd ~/HireMind/frontend
npx vite --host 0.0.0.0 --port 5173
```

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://localhost:5173 | 用户界面 |
| 后端 API | http://localhost:8000 | RESTful 接口 |
| API 文档 | http://localhost:8000/docs | Swagger UI |

---
## 配置 AI 模型

复制环境变量模板并填入 API Key：

```bash
cp .env.example .env
vim .env
```

### 配置项说明

| 参数 | 说明 | 默认值 |
|------|------|------|
| `AI_BAILIAN_API_KEY` | 阿里云百炼 DashScope API Key | 必填 |
| `AI_BAILIAN_BASE_URL` | 百炼服务地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `AI_BAILIAN_MODEL` | 百炼模型名 | `qwen3.5-flash` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 可选 |
| `OPENAI_API_KEY` | OpenAI API Key | 可选 |
| `DATABASE_URL` | 数据库连接串 | `postgresql+asyncpg://postgres:123456@localhost:5432/hiremind` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `UPLOAD_DIR` | 文件上传路径 | `./uploads` |

### 获取阿里云百炼 API Key

1. 访问 [aliyun.com/product/bailian](https://www.aliyun.com/product/bailian)
2. 登录后进入“百炼平台”
3. 右上角头像 → **API-KEY 管理**
4. 创建新的 API Key 并复制

### 推荐模型

- **日常使用**：`qwen3.5-flash`（快速、性价比高）
- **深度评估**：`qwen-max`（能力更强）

---
## 模块使用指南

### 用户认证

**注册**

1. 打开 http://localhost:5173/register
2. 填写用户名、邮箱、密码
3. 点击“注册”，注册成功后自动登录并跳转到首页

**登录**

1. 打开 http://localhost:5173/login
2. 输入邮箱和密码登录
3. 登录成功后右上角显示用户名

**注意**：当前使用 Cookie Session。

### 简历管理

**上传简历**

1. 进入“简历管理”页面
2. 点击“上传简历”，选择 PDF/DOCX/TXT 文件
3. 系统自动解析并提取技能、项目经历、教育背景

**查看与删除**

- 点击“查看”进入详情页查看解析结果和 AI 评估
- 点击“删除”删除单个简历
- 勾选多个后点击“删除所选”批量删除

### 模拟面试

**创建面试**

1. 进入“模拟面试”页面，点击“开始面试”
2. 选择岗位方向（AI Agent / 大模型 / RAG / 前端 / 后端 / Java / DevOps 等）
3. 选择关联简历（可选，推荐选择，AI 会根据简历定制问题）
4. 勾选“使用知识库”（可选，面试时结合知识库资料提问）
5. 点击“开始”进入面试

**进行面试**

- AI 面试官先提问，点击“回答”后输入你的回答
- 支持多轮对话，AI 会根据回答追问
- 可随时点击“结束面试”提前结束

**查看报告**

面试结束后自动生成报告，包含：
- 综合评分 (0-100)
- 能力雷达图（技术能力、表达能力、逻辑思维、反应速度、综合素质）
- 逐题评价与解析
- 改进建议

**管理面试记录**

- 列表查看所有历史面试
- 点击“报告”查看已完成的详细报告
- 支持单个删除和批量删除

### 知识库

知识库允许上传面试相关文档，面试时 AI 会自动查询相关内容。

1. 进入“知识库”页面，点击“上传文档”
2. 支持 PDF/DOCX/TXT/MD 格式，可多文件选择
3. 上传后自动切片并向量化存储
4. 文档根据文件名前缀自动分类
5. 支持语义搜索查找内容

### 面试日程

1. 进入“面试日程”页面
2. 在日历上点击相应日期添加事件
3. 填写标题、时间、公司、备注
4. 支持查看、编辑和删除已有事件

### 系统设置

在系统设置页面可以：

- 配置 AI 提供商（百炼 / DeepSeek / OpenAI）
- 切换不同的大语言模型
- 配置语音服务参数

配置保存在数据库中，不会影响 `.env` 文件。

---
## 开发规范

### 后端模块结构

每个业务模块遵循统一分层：

```
modules/{name}/
├── models.py      # SQLAlchemy 模型
├── schemas.py     # Pydantic 请求/响应模型
├── repository.py  # 数据库操作层
├── service.py     # 业务逻辑层
└── router.py      # API 路由
```

### 编码约定

- **异步优先**：使用 async/await 和 async SQLAlchemy session
- **统一响应**：`Result.success(data)` / `Result.error(code, message)`
- **异常处理**：通过 `BusinessException(ErrorCode, message)` 抛出，全局异常处理器捕获
- **依赖注入**：所有 router 通过 `AsyncSession = Depends(get_db)` 获取数据库会话
- **DEV 模式**：使用固定 `DEV_USER_ID`，后续接入 JWT 鉴权

### 前端约定

- **样式**：Tailwind CSS v4，类名不可动态拼接
- **条件样式**：Badge/状态标签使用独立组件并硬编码完整类名
- **API 调用**：通过 `fetch` + `/api/...`，Vite proxy 转发到后端
- **组件位置**：页面放 `pages/`，公共组件放 `components/`，全局状态用 Context

---
## 架构说明

### 面试 Agent 工作流

```
用户请求 → Router → Service
  → 读取简历 + 知识库内容
  → 构建 System Prompt（岗位方向、简历信息、知识库片段）
  → 调用 LLM API（流式输出）
  → 生成面试题 / 追问 / 评估报告
  → 存入数据库
  → 返回前端
```

### 知识库 RAG 流程

```
上传文档 → 解析文本 → 语义切片 → embedding 向量化 → 存入 pgvector
用户提问 → 向量检索（余弦相似度） → TopK 召回 → 重排序 → 注入 prompt → LLM 回答
```

### 错误码体系

| 范围 | 域 | 说明 |
|------|-----|------|
| 1xxx | Auth | 认证相关 |
| 2xxx | Resume | 简历相关 |
| 3xxx | Interview | 面试相关 |
| 4xxx | Knowledge | 知识库相关 |
| 5xxx | Schedule | 日程相关 |
| 9xxx | Common | 通用错误 |

---
## Git 工作流

由于 WSL 网络环境可能存在代理问题，推荐以下流程：

```bash
# 1. WSL 中编辑代码并提交
cd ~/HireMind
git add .
git commit -m "feat: 功能描述"

# 2. 同步到 D 盘
cat .git/refs/heads/master > /mnt/d/codexproject/codexproject/HireMind/.git/refs/heads/master

# 3. Windows PowerShell 推送
cd D:\codexproject\codexproject\HireMind
git push
```

---
## 项目路线图

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

---
## 常见问题

### Q：前端报错 EACCES 或 ENOENT

WSL 访问 Windows 文件系统时权限错乱。
解决：重启 Vite 或将项目迁移到 WSL 文件系统。

### Q：WSL 无法访问网络

代理仅监听 localhost，WSL NAT 模式无法访问。
解决：配置 `.wslconfig` 开启 Mirrored 模式或在代理软件中开启“允许局域网连接”。

### Q：AI 回答显示问号 / 乱码

文件编码问题。
解决：使用 Python 脚本中转或将项目迁移到 WSL 文件系统。

### Q：注册登录后右上角没显示用户名

解决：刷新页面或重新登录。

### Q：如何更换 AI 模型

可在系统设置页面切换，或修改 `.env` 中的 `AI_BAILIAN_API_KEY`。

---

*最后更新：2026-07-27*
