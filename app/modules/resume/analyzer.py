import json, logging
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

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


async def analyze_resume(text: str, llm=None) -> dict[str, Any]:
    """Analyze resume text using LLM and return structured result"""
    from app.config.settings import settings

    if llm is None:
        if settings.AI_BAILIAN_API_KEY:
            llm = ChatOpenAI(
                model=settings.AI_DEFAULT_MODEL,
                api_key=settings.AI_BAILIAN_API_KEY,
                base_url=settings.AI_BAILIAN_BASE_URL,
                temperature=0.1,
            )
        elif settings.DEEPSEEK_API_KEY:
            llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                temperature=0.1,
            )
        elif settings.OPENAI_API_KEY:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.1,
            )
        else:
            return {"name": None, "email": None, "phone": None, "position": None,
                    "skills": [], "experience": [], "education": [], "summary": "No AI provider configured", "score": 50}

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
