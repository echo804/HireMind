import json, logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

NOW = datetime.now().strftime("%Y年%m月%d日")

SYSTEM_PROMPT = f"""当前日期：{NOW}

你是一名资深技术面试官，正在面试一位{{direction}}方向的候选人。请严格按照以下面试大纲进行提问。

## 候选人简历
{{resume_context}}

## 参考知识库
{{knowledge_context}}

## 面试大纲（严格按阶段顺序覆盖）

| 阶段 | 题号范围 | 考察维度 | 提问要点 |
|------|---------|---------|---------|
| 一 | 第1-2题 | 简历项目深挖 | 核心项目架构、技术选型原因、为什么用A不用B、项目中你负责的部分及技术决策 |
| 二 | 第3-4题 | 岗位专业考察 | {{direction}}核心知识点、底层原理、常见陷阱、最佳实践 |
| 三 | 第5-6题 | 问题解决能力 | 开发中遇到过的难题及解决思路、如何定位bug、性能优化经验 |
| 四 | 第7-8题 | 生产场景题 | 线上故障排查、高并发处理、系统安全、数据一致性、部署运维等真实场景 |
| 五 | 第9-10题 | 综合设计 | 系统设计、架构演进、技术选型对比、团队协作与代码规范 |

**注意**：当前是第 {{question_count}} 题（共 {{total}} 题），请确保提问内容属于对应阶段的考察维度。如果总题数不足以覆盖所有阶段，优先保留阶段一、二、三。

## 提问要求
1. 问题基于简历中的技术栈和项目经验，不要问泛泛而谈的问题
2. 涉及具体技术时追问底层原理和源码实现
3. 根据候选人上一轮的回答质量，决定是深入追问还是切换到下一维度
4. 生产场景题要给出具体的上下文（如"假设你的服务在凌晨3点收到大量5xx报警，你会怎么做"）
5. 对回答给出1-2句简短专业的反馈
6. 到达第 {{total}} 题时 is_final=true

## 参考：候选人已使用技术栈
{{tech_stack}}

## 面试历史
{{history}}

返回 JSON（首题 feedback 和 evaluation 可为空）：
{{{{
  "question": "面试问题",
  "feedback": "对上一回答的反馈",
  "is_final": false,
  "evaluation": 0,
  "stage": "阶段名称（如一、二、三、四、五）"
}}}}
"""

EVALUATION_PROMPT = f"""当前日期：{NOW}
你是资深面试评估专家，根据 {{direction}} 方向面试记录进行综合评分。

## 评估维度（各0-100分）

| 维度 | 说明 |
|------|------|
| tech_depth | 技术深度：对核心概念、底层原理的掌握程度 |
| tech_selection | 技术选型：能否合理分析技术方案的优劣和适用场景 |
| problem_solving | 问题解决：面对难题时的分析思路、定位方法和解决方案 |
| production | 生产意识：对线上运维、性能优化、安全、高可用的理解 |
| communication | 表达沟通：能否清晰、有条理地阐述技术观点 |

## 评分标准
- 90-100：深度理解、表达精炼、有独到见解
- 70-89：基础扎实、回答正确、有一定深度
- 50-69：基本正确、但深度不够或表达一般
- 30-49：回答有明显错误或过于表面
- 0-29：未正确回答问题

对每道题给出 0-10 的单项评分和简短点评。

面试记录：
{{transcript}}

返回 JSON：
{{{{
  "overall_score": 85,
  "feedback": "综合评价2-3句话",
  "dimensions": {{
    "tech_depth": 80,
    "tech_selection": 75,
    "problem_solving": 82,
    "production": 70,
    "communication": 85
  }},
  "per_question": [
    {{"index": 1, "score": 8, "comment": "简短点评"}}
  ],
  "strengths": ["优势1", "优势2", "优势3"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["改进建议1", "改进建议2", "改进建议3"]
}}}}
"""


def _extract_tech_stack(resume_context: str) -> str:
    """从简历上下文中提取技术栈名称"""
    if not resume_context or "（未提供简历信息）" in resume_context:
        return "未提供"
    keywords = []
    for line in resume_context.split("\n"):
        if line.startswith("技能"):
            keywords.append(line)
        if line.startswith("经验"):
            keywords.append(line)
    return "\n".join(keywords) if keywords else "（请从简历中提取）"


def _get_llm(settings, user_id: str | None = None):
    from app.modules.settings.service import get_active_config
    config = get_active_config(user_id)
    api_key = config.get("api_key") or ""
    base_url = config.get("base_url") or ""
    model = config.get("model") or settings.AI_DEFAULT_MODEL
    if api_key and base_url:
        return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0.7)
    return None


async def generate_question(settings, direction: str, total: int, question_count: int,
                            history: list[dict], resume_context: str = "", knowledge_context: str = "",
                            user_id: str | None = None) -> dict:
    llm = _get_llm(settings, user_id)
    if not llm:
        return {"question": "无法连接AI服务", "feedback": "", "is_final": False, "evaluation": "0"}

    history_text = "\n".join(
        [f"第{h['index']}题 Q: {h['question']}\nA: {h['answer']}" for h in history[-6:]]
    ) if history else "（首题，直接开始）"

    if not resume_context:
        resume_context = "（未提供简历信息，按通用方向出题）"
    if not knowledge_context:
        knowledge_context = "（未启用知识库，仅凭简历和通用知识出题）"

    tech_stack = _extract_tech_stack(resume_context)

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    chain = prompt | llm
    result = await chain.ainvoke({
        "direction": direction,
        "total": total,
        "resume_context": resume_context,
        "knowledge_context": knowledge_context,
        "question_count": question_count,
        "history": history_text,
        "tech_stack": tech_stack,
    })

    try:
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to parse question: {e}")
        return {"question": "请介绍一下你的技术栈和项目经验", "feedback": "", "is_final": False, "evaluation": 5}


async def evaluate_interview(settings, direction: str, transcript: list[dict],
                            user_id: str | None = None) -> dict:
    llm = _get_llm(settings, user_id)
    if not llm:
        return {"overall_score": 70, "feedback": "评估服务不可用", "dimensions": {},
                "per_question": [], "strengths": [], "weaknesses": [], "suggestions": []}

    transcript_text = "\n".join(
        [f"第{i+1}题: {t['question']}\n回答: {t['answer']}" for i, t in enumerate(transcript)]
    )

    prompt = ChatPromptTemplate.from_template(EVALUATION_PROMPT)
    chain = prompt | llm
    result = await chain.ainvoke({"direction": direction, "transcript": transcript_text})

    try:
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to evaluate: {e}")
        return {"overall_score": 50, "feedback": "评估生成失败，请重试",
                "dimensions": {}, "per_question": [],
                "strengths": ["完成面试"], "weaknesses": ["评估异常"],
                "suggestions": ["建议重新生成评估报告"]}
