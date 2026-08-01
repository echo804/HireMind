import sys, json
sys.path.insert(0, '/home/echo/HireMind')
from app.modules.resume.parser import parse_file
from app.modules.resume.analyzer import analyze_resume
import asyncio

async def test():
    path = '/mnt/d/codexproject/codexproject/HireMind/.reasonix/attachments/clipboard-20260729-124739.474457-000001.pdf'
    text, h = parse_file(path)
    print(f'TEXT: {len(text)} chars')
    try:
        result = await analyze_resume(text, user_id='00000000-0000-0000-0000-000000000000')
        print(f'RESULT: {json.dumps(result, ensure_ascii=False, indent=2)[:2000]}')
    except Exception as e:
        print(f'ANALYZE ERROR: {e}')

asyncio.run(test())
