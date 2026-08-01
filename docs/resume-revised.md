## 屈杰
18791410621 | c100_0911@163.com | 21岁 | 应届生 | AI应用开发工程师
GitHub: github.com/echo804

---

## 教育背景

**西安交通大学城市学院** · 计算机科学与技术 · 本科 · 2023.09 - 2027.06

> 大三在读。大二开始自学 Python 后端和大模型应用开发，线上课程 + 项目驱动学习。能独立阅读英文技术文档（LangChain/PyMuPDF/React 官方文档）。

---

## 技术能力

> 删掉了"熟悉""掌握"等模糊词，每一项都可以经得起追问。

**后端开发**：Python / FastAPI / SQLAlchemy（async）/ Pydantic / JWT 鉴权 / RESTful API 设计
**大模型应用**：LangChain（LCEL + Prompt Template + ChatOpenAI 多模型适配）/ RAG（pgvector + text-embedding-v3 + 固定窗口切片）/ Function Calling / ReAct Agent
**模型对接**：OpenAI / DeepSeek / 阿里云百炼（DashScope）——均通过统一接口接入，实测可用
**数据库与中间件**：PostgreSQL + pgvector 向量检索 / Redis 缓存 / Alembic 迁移
**前端**：React 19 + TypeScript + Tailwind CSS v4 + Vite（能独立搭建和开发，非深度前端）
**工程化**：Docker Compose（基础设施编排）/ Git / Ruff 代码检查 / 模块化分层架构
**文档处理**：PyMuPDF（PDF 文本提取）/ python-docx（DOCX 解析）

---

## 项目经历

### HireMind — AI 智能面试官平台
2026.01 - 2026.07 | github.com/echo804/HireMind | **个人项目，独立全栈开发**

**做什么的**：上传简历 → AI 自动提取技能/经历 → 生成定制面试题 → 多轮对话面试 → AI 评分报告。适用于企业初筛面试场景。

**我具体做了什么**：

1. **多模型面试引擎**（~200 行核心代码）
   - 用 LangChain 的 `ChatPromptTemplate` + `ChatOpenAI` 构建 Prompt 管道
   - 设计 5 阶段面试大纲（项目深挖→专业考察→问题解决→生产场景→综合设计），LLM 按题号自动匹配阶段
   - 统一接口适配 OpenAI/DeepSeek/百炼，前端一键切换，无需改代码
   - 每轮对话上下文（简历 + 历史回答 + 知识库）全量写入 Prompt

2. **RAG 知识检索**（~150 行核心代码）
   - PDF/DOCX/TXT/MD → 固定窗口切片（1000 字符 + 150 重叠）→ text-embedding-v3 → pgvector
   - 面试中实时语义检索 TOP-3 相关片段，注入 Prompt 辅助出题
   - IVFFlat 索引优化检索速度

3. **AI 简历解析**
   - 调用 LLM 从 PDF/DOCX 原始文本提取结构化字段（姓名/技能/经历/教育）
   - 异步处理 + 百分比进度反馈（解析 30% → AI 分析 50% → 生成报告 100%）

4. **全栈架构**
   - 后端：`models → schemas → repository → service → router` 严格分层，`Result[T]` 统一响应
   - 前端：React 19 + Tailwind CSS v4 响应式 UI，Vite proxy 转发 API
   - 基础设施：Docker Compose（PostgreSQL + pgvector + Redis）

**踩过的坑**：
- 开发阶段 uvicorn `--reload` 会杀掉 `asyncio.create_task` 后台任务，最终改为上传秒返 + 详情页同步触发分析的方案
- WSL 双副本（Windows 编辑 / WSL 运行）导致反复出现「改了代码没生效」，写了同步脚本解决
- API Key 脱敏后用户保存设置会覆盖真实 Key，增加了掩码检测逻辑

---

### QualiGuard — AI 代码质量分析工具
2025.07 - 2026.06 | github.com/echo804/QualiGuard

**做什么的**：CLI 工具，用自然语言指令驱动 LLM 自动扫描 Python 代码 → 发现问题 → 自动修复 → 生成报告。

**我具体做了什么**：

1. **ReAct Agent 自主执行**（~300 行核心代码）
   - 定义 Thought-Action-Observation 循环：LLM 思考→调用工具→观察结果→决定下一步
   - 将 6 个核心能力（扫描/修复/读文件/搜索/报告/规则查询）封装为 OpenAI Function Calling 工具
   - 用户输入一句话（如"检查 app/ 目录的安全问题并修复"），Agent 自主编排多步工具调用

2. **量化评测系统**（~200 行核心代码）
   - 50 个测试场景覆盖安全/风格/复杂度/报告/综合/错误恢复 6 类
   - 指标：通过率、步数、Token 消耗、工具调用准确率
   - `qg eval --model deepseek` 一键切换模型对比

3. **多模型适配**
   - 基于 OpenAI SDK 统一接口，兼容 DeepSeek/Qwen/GLM 国产模型
   - 无需改 Agent 逻辑代码，仅换 `base_url` + `model` 即可切换

**技术栈**：Python · Typer CLI · OpenAI SDK · AST 分析 · Pydantic · Ruff · pytest

---

## 自我评价

> 每条附带可验证的事实，不写形容词。

- **全栈交付能力**：独立完成过从数据库设计到前端 UI 的完整项目（HireMind 17,000+ 行代码，React + FastAPI + PostgreSQL）
- **大模型应用落地**：能搭建从 Prompt 设计到 RAG 检索到多模型适配的完整 AI 应用链路，非纸上谈兵
- **问题解决实例**：遇到过 asyncio 后台任务被 uvicorn reload 杀死的问题，最终改为同步触发 + 前端轮询方案；处理过 WSL/Windows 双副本同步问题；排查过 pgvector IVFFlat 索引参数对查询性能的影响
- **自驱学习**：大二起自学 Python 后端 + LangChain + React，通过项目实践驱动学习，能独立查阅英文文档解决技术问题
- **代码规范意识**：项目遵循模块化分层架构，使用 Ruff 统一代码风格，commit message 语义化

---

## 附：GitHub 项目清单

| 项目 | 说明 | 技术关键词 |
|------|------|-----------|
| HireMind | AI 面试平台 | FastAPI, LangChain, RAG, pgvector, React |
| QualiGuard | AI 代码审查 CLI | Python, ReAct Agent, Function Calling, Typer |
