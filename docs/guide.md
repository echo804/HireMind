# HireMind 操作指南

> 方便快速上手和日常使用这套 AI 智能面试系统

---

## 目录

1. [环境搭建](#环境搭建)
2. [启动与停止](#启动与停止)
3. [配置 AI 模型](#配置-ai-模型)
4. [模块使用指南](#模块使用指南)
   - [用户认证](#用户认证)
   - [简历管理](#简历管理)
   - [模拟面试](#模拟面试)
   - [知识库](#知识库)
   - [面试日程](#面试日程)
   - [系统设置](#系统设置)
5. [Git 工作流](#git-工作流)
6. [常见问题](#常见问题)

---

## 环境搭建

### 系统要求

| 组件 | 版本要求 |
|------|------|
| 操作系统 | Windows 11 + WSL2 (Ubuntu) 或 Linux |
| Python | 3.12+ |
| Node.js | 20+ |
| PostgreSQL | 14+ (需安装 pgvector 扩展) |
| Redis | 6+ |

### 数据库与 Redis 安装

如果使用 WSL2 Ubuntu，可以用以下命令安装：

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

### 项目代码

```bash
git clone https://github.com/echo804/HireMind.git
cd HireMind

# Python 虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis python-multipart python-dotenv pydantic-settings langchain langchain-community dashscope sqlalchemy-utils aiofiles PyMuPDF python-docx openai jinja2

# 前端依赖
cd frontend
npm install
cd ..
```

---
## 启动与停止

### 一键启动

提供了完整的启动脚本，会自动启动数据库、后端和前端：

```bash
cd ~/HireMind
bash scripts/start_all.sh
```

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 前端页面 | http://localhost:5173 |

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

---
## 配置 AI 模型

复制环境变量模板并填入 API Key：

```bash
cp .env.example .env
vim .env
```

主要配置项：

| 参数 | 说明 | 默认值 |
|------|------|------|
| `AI_BAILIAN_API_KEY` | 阿里云百炼 DashScope API Key | 必填 |
| `AI_BAILIAN_BASE_URL` | 百炼服务地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 可选 |
| `OPENAI_API_KEY` | OpenAI API Key | 可选 |
| `DATABASE_URL` | 数据库连接 | `postgresql+asyncpg://postgres:123456@localhost:5432/hiremind` |
| `REDIS_URL` | Redis 连接 | `redis://localhost:6379/0` |

如何获取阿里云百炼 API Key：

1. 访问 [aliyun.com/product/bailian](https://www.aliyun.com/product/bailian)
2. 登录后进入“百炼平台”
3. 点击右上角头像 → “API-KEY 管理”
4. 创建新的 API Key 并复制

推荐模型：`qwen3.5-flash`（快速、性价比高）

---
## 模块使用指南

### 用户认证

**注册**

1. 打开前端页面 http://localhost:5173/register
2. 填写用户名、邮箱、密码
3. 点击“注册”按钮
4. 注册成功后自动登录并跳转到首页

**登录**

1. 打开 http://localhost:5173/login
2. 输入邮箱和密码
3. 登录成功后页面右上角显示用户名

**注意**：当前版本使用 Cookie Session 管理登录状态。

### 简历管理

**上传简历**

1. 进入“简历管理”页面
2. 点击“上传简历”按钮
3. 选择 PDF 或 DOCX 文件
4. 系统自动解析简历并提取信息

**查看详情**

- 点击简历列表中的“查看”进入详情页
- 查看解析结果：技能标签、项目经历、教育背景
- 查看 AI 评估报告

**删除简历**

- 单个删除：点击简历对应的“删除”按钮
- 批量删除：勾选多个，点击“删除所选”

**支持格式**：PDF、DOCX、TXT

### 模拟面试

**创建面试**

1. 进入“模拟面试”页面
2. 点击“开始面试”
3. 选择岗位方向：
   - AI Agent 开发实习
   - 大语言模型研发
   - RAG 系统开发工程师
   - 前端开发实习
   - 后端开发实习
   - 数据科学 / ML 实习
   - Java 开发
   - 运维开发 (SRE/DevOps)
4. 选择关联简历（可选，推荐选择，AI 会根据简历定制问题）
5. 勾选“使用知识库”（可选，结合知识库资料提问）
6. 点击“开始”进入面试

**进行面试**

- AI 面试官会先提问，点击“回答”后输入你的回答
- 支持多轮对话，AI 会根据回答进行追问
- 可随时点击“结束面试”提前结束

**查看报告**

面试结束后自动生成报告，包含：
- 综合评分（0-100）
- 能力雷达图（技术能力、表达能力、逻辑思维、反应速度、综合素质）
- 逐题评价与解析
- 改进建议

**管理面试记录**

- 列表查看所有历史面试记录
- 支持单个删除和批量删除
- 点击“报告”查看已完成的面试详细报告

### 知识库

知识库允许你上传面试相关文档，面试时 AI 会自动查询相关内容并结合提问。

**上传文档**

1. 进入“知识库”页面
2. 点击“上传文档”按钮
3. 支持多文件选择，支持 PDF、DOCX、TXT、MD 格式
4. 上传后自动切片并向量化存储

**分类管理**

- 文档根据文件名前缀自动分类（如 `agent_xxx.md` 归入 AI Agent 分类）
- 支持按分类筛选查看

**搜索知识库**

- 在搜索框输入关键词
- 系统会进行语义搜索，返回匹配度最高的内容

**删除文档**

- 点击“删除”弹出确认对话框
- 点击“确定删除”后连同切片数据一起删除

### 面试日程

**添加日程**

1. 进入“面试日程”页面
2. 在日历上点击相应日期
3. 填写面试信息：标题、时间、公司、备注
4. 点击“保存”

**查看与管理**

- 日历视图查看月度安排
- 点击事件查看详情
- 支持编辑和删除已有事件

### 系统设置

在系统设置页面可以：

- 配置 AI 提供商（百炼 / DeepSeek / OpenAI）
- 切换不同的大语言模型
- 配置语音服务参数

配置会保存在数据库中，不会影响 `.env` 文件。

---
## Git 工作流

由于 WSL 网络环境原因，推荐以下流程：

```bash
# 1. WSL 中编辑代码并提交
cd ~/HireMind
git add .
git commit -m "feat: xxx"

# 2. 同步到 D 盘
cp .git/refs/heads/master /mnt/d/codexproject/codexproject/HireMind/.git/refs/heads/master

# 3. Windows PowerShell 推送
# cd D:\codexproject\codexproject\HireMind
# git push
```

如果 WSL 网络正常（如 Mirrored 模式），也可直接在 WSL 中推送：

```bash
git push
```

---
## 常见问题

### Q：前端报错 EACCES 或 ENOENT

原因：WSL 访问 Windows D 盘文件时权限错乱。
解决：重启 Vite 或将项目迁移到 WSL 文件系统。

### Q：WSL 无法访问网络

原因：代理仅监听 `127.0.0.1`，WSL NAT 模式无法访问。
解决：配置 `.wslconfig` 开启 Mirrored 模式或在代理软件中开启“允许局域网连接”。

### Q：注册后右上角没有显示用户名

解决：刷新页面或重新登录。

### Q：AI 回答乱码（显示问号）

原因：文件编码问题。
解决：使用 Python 脚本中转或将项目迁移到 WSL 文件系统。

### Q：如何更换 AI 模型

可在系统设置页面切换提供商和模型，或修改 `.env` 中的 `AI_BAILIAN_API_KEY`。

---

*最后更新：2026-07-27*
