import json, logging
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


def _get_llm(user_id: str | None = None) -> Any:
    """获取用户配置的 LLM（复用 analyze_resume 的配置逻辑）"""
    from app.config.settings import settings
    from app.modules.settings.service import get_active_config

    config = get_active_config(user_id) if user_id else None
    api_key = (config or {}).get("api_key") or settings.AI_BAILIAN_API_KEY or settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY
    base_url = (config or {}).get("base_url") or settings.AI_BAILIAN_BASE_URL or settings.DEEPSEEK_BASE_URL or settings.OPENAI_BASE_URL
    model = (config or {}).get("model") or settings.AI_DEFAULT_MODEL or "deepseek-chat"
    if not api_key:
        return None
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.1,
        request_timeout=120,
    )


def _parse_json_response(content: str) -> dict:
    """从 LLM 输出中解析 JSON"""
    try:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {}

PROMPT = """You are a resume analyst. Extract information from the resume text below and return ONLY valid JSON.

Required JSON structure:
{{
  "name": "Full name or null",
  "email": "Email or null",
  "phone": "Phone or null",
  "position": "Target position or null",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "company": "Company name",
      "title": "Job title",
      "duration": "Time period",
      "description": "Brief description"
    }}
  ],
  "education": [
    {{
      "school": "School name",
      "degree": "Degree",
      "major": "Major",
      "year": "Graduation year"
    }}
  ],
  "summary": "2-3 sentence professional summary in Chinese",
  "score": "Overall rating 0-100 based on skill match, experience, education, and project quality"
}}

Resume text:
--- 
{text}
---"""


async def analyze_resume(text: str, user_id: str | None = None) -> dict[str, Any]:
    """Analyze resume text using LLM and return structured result.
    
    Uses user's AI config when user_id is provided, falls back to .env settings."""
    from app.config.settings import settings
    from app.modules.settings.service import get_active_config

    config = get_active_config(user_id) if user_id else None
    api_key = (config or {}).get("api_key") or settings.AI_BAILIAN_API_KEY or settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY
    base_url = (config or {}).get("base_url") or settings.AI_BAILIAN_BASE_URL or settings.DEEPSEEK_BASE_URL or settings.OPENAI_BASE_URL
    model = (config or {}).get("model") or settings.AI_DEFAULT_MODEL or "deepseek-chat"
    logger.info(f"analyze_resume: user_id={user_id}, model={model}, key_prefix={api_key[:10] if api_key else 'NONE'}, base_url={base_url}")

    if not api_key:
        return {"name": None, "email": None, "phone": None, "position": None,
                "skills": [], "experience": [], "education": [],
                "summary": "No AI provider configured", "score": 50}

    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.1,
        request_timeout=60,
    )

    prompt = ChatPromptTemplate.from_template(PROMPT)
    chain = prompt | llm
    try:
        result = await chain.ainvoke({"text": text[:8000]})
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return json.loads(content)
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {"name": None, "email": None, "phone": None, "position": None,
                "skills": [], "experience": [], "education": [], "summary": "", "score": 50}


QUALITY_PROMPT = """当前日期：{now}
你是一名资深技术面试官，正在用面试官视角评审以下简历。请严格按内部评审手册打分。

## 简历文本
---
{text}
---

## 目标岗位
{position}

## 评审手册（通用铁律，所有技术岗适用）
简历篇幅要求：**最多两页 A4 纸**（超过两页视为不合格）；排版清晰无花哨图表；零错别字、技术名词大小写正确（如 iOS 而非 IOS）。
1. **职业素养与格式**（5 秒初筛）：严谨度、归纳能力、沟通效率。淘汰红线：超过两页；有错别字；技术名词拼写错误；用"精通"等字眼堆砌技能条。
2. **硬性条件匹配**（15 秒关键词扫描）：学历、专业、毕业时间、核心技能栈与岗位 JD 兼容性；核心技能描述具体（如"熟练掌握 Java，熟悉 Spring Boot，有 JVM 调优经验"）。
3. **经历描述质量**（核心决策层，60 秒）：STAR 法则；强力动词（主导/设计/重构）；结果量化；淘汰红线：只有"负责/参与"无情境无结果；项目堆砌无重点。
4. **技术深度与思考**：能解释技术选型"为什么"；敢于暴露并解决复杂问题（如 OOM 排查）；有超越职能的业务思考。
5. **自我认知与软素质**：技能水平客观评价（熟练/了解，少用精通）；有技术博客、开源贡献、独特爱好；淘汰红线：通篇"精通一切"、内容浮夸。

## 大模型岗位加试（仅当目标岗位涉及 LLM/AI/大模型 时叠加）
6. **技术雷达前瞻性**：是否提及 MoE、RAG、Agent、多模态、FlashAttention、RLHF/DPO 等前沿技术及使用场景。
7. **项目深度真实水位**：四档递进（调 API < 模型定制 LoRA/SFT/RLHF < 预训练+分布式训练）；仅"用 LangChain 调 API"视为低价值信号。
8. **数据与评估思维**：数据清洗 pipeline、多维评估体系（流畅性/安全性/事实性）、GPT-4 评判+人工校验。
9. **工程化全栈能力**：部署推理优化（vLLM、量化 GPTQ/AWQ）、RAG 工程难题（切分/重排）、LLM 监控/缓存/成本控制。
10. **社区影响力与批判性思维**：技术博客/知乎分析、开源 PR、Hugging Face 发布、能讨论 RoPE/MoE 优缺点。

## 输出要求
返回严格 JSON（不要 markdown 代码块），结构：
{{
  "overall_score": 0-100 总分,
  "verdict": "一句话总评",
  "dimensions": [
    {{
      "key": "format|match|experience|depth|softskill|llm_radar|llm_depth|llm_data|llm_eng|llm_impact",
      "name": "维度中文名",
      "score": 0-100,
      "pass": true/false,
      "issues": ["问题1", "问题2"],
      "suggestions": ["改进1", "改进2"]
    }}
  ],
  "highlights": ["这份简历的高亮时刻1-2条"],
  "red_flags": ["淘汰红线触发项（若无则为空数组）"],
  "llm_extra": true/false 是否叠加了大模型岗加试,
  "unreasonable_advice": [
    {{"issue": "不合理/可疑之处（如技能写精通但项目无法佐证、时间线矛盾、无量化结果、表述夸大）", "advice": "具体修改建议"}}
  ],
  "project_assessment": [
    {{
      "name": "项目名",
      "type": "production|course|demo",
      "confidence": 0-100,
      "reasons": ["判断依据1（如有无 GitHub 链接/线上地址、有无量化结果、是否只有技术栈堆砌无场景、是否从0到1但无部署说明）"],
      "advice": "如何让该项目看起来更像真实生产项目的建议"
    }}
  ]
}}
"""


POLISH_PROMPT = """当前日期：{now}
你是一名资深简历优化专家。请根据面试官评审手册润色以下简历，使其达到**最多两页 A4 纸**的篇幅标准。

## 原简历
---
{text}
---

## 润色要求
1. 修正错别字与技术名词大小写（如 IOS→iOS、Node.js 拼写、Github→GitHub）
2. **禁止升级事实**：不得把"熟悉"改成"精通"、不得把"参与"改成"主导"、不得给原文没有的量化数字（如成功率、耗时百分比）。技能等级、个人贡献、数字必须与原文完全一致
3. **禁止形式主义修改**：不得仅因"更专业"而改名章节标题（如"项目介绍"→"项目概述"）、不得把原有内容重新包装成 STAR 结构却不增加信息、不得强行把纯文本改造成 Markdown 标题/列表/加粗
4. 只允许做四类改动：①删除套话噪音与明显重复（如"热爱学习、吃苦耐劳"）②修正错别字/大小写/标点 ③精简冗余修饰语，使表达更紧凑清晰 ④把原文已有的量化结果和亮点调整到更显眼的位置
5. 控制篇幅在最多两页 A4 纸以内：优先删冗余描述，保留最有价值的项目
6. 保持原简历的所有事实、结构、章节名称（姓名、联系方式、学历、经历、项目、标题），不新增虚假内容，不删减真实信息

## 输出要求
返回严格 JSON（不要 markdown 代码块）：
{{
  "polished_text": "润色后的完整简历文本（结构与章节名与原文一致）",
  "changes": [
    {{"original": "原文片段", "polished": "润色后片段", "reason": "修改原因"}}
  ],
  "summary": "本次润色的总体说明（2-3句话）"
}}
"""


async def analyze_resume_quality(text: str, position: str = "", user_id: str | None = None) -> dict[str, Any]:
    """按面试官评审手册对简历进行分层诊断"""
    llm = _get_llm(user_id)
    if not llm:
        return {"overall_score": 0, "verdict": "AI 服务未配置", "dimensions": [],
                "highlights": [], "red_flags": [], "llm_extra": False}
    from datetime import datetime
    prompt = ChatPromptTemplate.from_template(QUALITY_PROMPT)
    chain = prompt | llm
    try:
        result = await chain.ainvoke({
            "now": datetime.now().strftime("%Y年%m月%d日"),
            "text": text[:8000],
            "position": position or "通用技术岗位",
        })
        parsed = _parse_json_response(result.content)
        if not parsed:
            return {"overall_score": 0, "verdict": "分析失败，请重试", "dimensions": [],
                    "highlights": [], "red_flags": [], "llm_extra": False}
        parsed.setdefault("dimensions", [])
        parsed.setdefault("highlights", [])
        parsed.setdefault("red_flags", [])
        parsed.setdefault("llm_extra", False)
        parsed.setdefault("unreasonable_advice", [])
        parsed.setdefault("project_assessment", [])
        return parsed
    except Exception as e:
        logger.error(f"analyze_resume_quality failed: {e}")
        return {"overall_score": 0, "verdict": "分析失败，请重试", "dimensions": [],
                "highlights": [], "red_flags": [], "llm_extra": False}


async def polish_resume_text(text: str, user_id: str | None = None) -> dict[str, Any]:
    """润色简历文本，返回润色后全文与变更点"""
    llm = _get_llm(user_id)
    if not llm:
        return {"polished_text": text, "changes": [], "summary": "AI 服务未配置"}
    from datetime import datetime
    prompt = ChatPromptTemplate.from_template(POLISH_PROMPT)
    chain = prompt | llm
    try:
        result = await chain.ainvoke({"now": datetime.now().strftime("%Y年%m月%d日"), "text": text[:8000]})
        parsed = _parse_json_response(result.content)
        if not parsed:
            return {"polished_text": text, "changes": [], "summary": "润色失败，请重试"}
        parsed.setdefault("polished_text", text)
        parsed.setdefault("changes", [])
        parsed.setdefault("summary", "")
        return parsed
    except Exception as e:
        logger.error(f"polish_resume_text failed: {e}")
        return {"polished_text": text, "changes": [], "summary": "润色失败，请重试"}
