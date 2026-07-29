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


async def analyze_resume(text: str, user_id: str | None = None) -> dict[str, Any]:
    """Analyze resume text using LLM and return structured result.
    
    Uses user's AI config when user_id is provided, falls back to .env settings."""
    from app.config.settings import settings
    from app.modules.settings.service import get_active_config

    config = get_active_config(user_id) if user_id else None
    api_key = (config or {}).get("api_key") or settings.AI_BAILIAN_API_KEY or settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY
    base_url = (config or {}).get("base_url") or settings.AI_BAILIAN_BASE_URL or settings.DEEPSEEK_BASE_URL or settings.OPENAI_BASE_URL
    model = (config or {}).get("model") or settings.AI_DEFAULT_MODEL or "deepseek-chat"

    if not api_key:
        return {"name": None, "email": None, "phone": None, "position": None,
                "skills": [], "experience": [], "education": [],
                "summary": "No AI provider configured", "score": 50}

    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.1,
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
