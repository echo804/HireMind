import json, logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

NOW = datetime.now().strftime("%Y年%m月%d日")

SYSTEM_PROMPT = f"""当前日期：{NOW}

你是一名专业的AI面试官，根据候选人的简历和岗位方向进行面试。

简历信息：
{{resume_context}}

参考知识库内容：
{{knowledge_context}}

要求：
1. 每次只提一个问题，问题应与简历和方向匹配
2. 根据前一个回答决定追问方向或切换话题
3. 问题应具有技术深度，考察真实能力
4. 对候选人的回答给出简短反馈
5. 当达到 {{total}} 题时设置 is_final=true
6. 问题用中文提问

返回 JSON格式：
{{{{
  "question": "面试问题",
  "feedback": "对上一回答的简短反馈（首题可为空）",
  "is_final": false,
  "evaluation": "对上题回答的评分 1-10（首题为0）"
}}}}
"""

EVALUATION_PROMPT = f"""当前日期：{NOW}
你是面试评估专家，根据 {{direction}} 方向的面试记录进行综合评分。

评分标准：
- 90-100：基础扎实，表达清晰，有深度思考
- 70-89：基础良好，大部分回答正确
- 50-69：基础一般，部分回答有欠缺
- 30-49：基础薄弱，多数回答不理想
- 0-29：几乎未正确回答问题

返回 JSON格式：
{{{{
  "overall_score": "总分 0-100",
  "feedback": "综合评价2-3句话",
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["缺点1", "缺点2"],
  "suggestions": ["建议1", "建议2", "建议3"]
}}}}

面试记录：
{{transcript}}
"""


def _get_llm(settings):
    from app.modules.settings.service import get_active_config
    config = get_active_config()
    api_key = config.get("api_key") or ""
    base_url = config.get("base_url") or ""
    model = config.get("model") or settings.AI_DEFAULT_MODEL
    if api_key and base_url:
        return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0.7)
    return None


async def generate_question(settings, direction: str, total: int, question_count: int,
                            history: list[dict], resume_context: str = "", knowledge_context: str = "") -> dict:
    llm = _get_llm(settings)
    if not llm:
        return {"question": "无法连接AI服务", "feedback": "", "is_final": False, "evaluation": "0"}

    history_text = "\n".join(
        [f"Q: {h['question']}\nA: {h['answer']}" for h in history[-6:]]
    ) if history else ""

    if not resume_context:
        resume_context = "（未提供简历信息，按通用方向出题）"
    if not knowledge_context:
        knowledge_context = "（未启用知识库，仅凭简历和通用知识出题）"

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    chain = prompt | llm
    result = await chain.ainvoke({
        "direction": direction,
        "total": total,
        "resume_context": resume_context,
        "knowledge_context": knowledge_context,
        "question_count": question_count,
        "history": history_text,
    })

    try:
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to parse question: {e}")
        return {"question": "请介绍一下你的技术栈和项目经验", "feedback": "", "is_final": False, "evaluation": "5"}


async def evaluate_interview(settings, direction: str, transcript: list[dict]) -> dict:
    llm = _get_llm(settings)
    if not llm:
        return {"overall_score": 70, "feedback": "评估服务不可用", "strengths": [], "weaknesses": [], "suggestions": []}

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
                "strengths": ["完成面试"], "weaknesses": ["评估异常"],
                "suggestions": ["建议重新生成评估报告"]}