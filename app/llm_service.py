import json
import re

import httpx

from app.config import get_settings
from app.prompt_service import STYLE_NAMES, TOPICS


class PromptOptimizeError(RuntimeError):
    pass


SYSTEM_PROMPT = """你是一个专业的 AI 生图提示词优化专家，擅长为 Midjourney、Stable Diffusion、OpenAI Images、通用文生图模型整理稳定、清晰、可控的提示词。
你的任务是根据用户的创意、专题方向、视觉风格，以及当前 positive/negative 关键词，优化出更适合生图的中文关键词。
要求：
1. 只输出 JSON，不要输出解释、Markdown 或代码块。
2. JSON 必须包含 prompt 和 negative_prompt 两个字段。
3. prompt 只能是中文关键词短语，用中文逗号分隔，不要包含完整长句。
4. prompt 不要直接复述用户创意原句，不要包含用户创意里的主体句子；只补充画面质量、构图、光线、材质、风格、镜头、细节控制等关键词。
5. negative_prompt 只能是中文负面关键词，用中文逗号分隔，聚焦常见瑕疵、错位、低质量、文字水印、比例错误等。
6. 不要加入露骨、暴力、违法或不安全内容。
7. 保持简洁但有用，positive 约 18-32 个关键词，negative 约 10-22 个关键词。
"""


def _extract_json_object(raw: str) -> dict[str, str]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise PromptOptimizeError("LLM did not return JSON.")
        data = json.loads(match.group(0))

    prompt = str(data.get("prompt", "")).strip()
    negative_prompt = str(data.get("negative_prompt", "")).strip()
    if not prompt or not negative_prompt:
        raise PromptOptimizeError("LLM JSON must include prompt and negative_prompt.")
    return {"prompt": prompt, "negative_prompt": negative_prompt}


async def optimize_prompt(
    topic: str,
    style: str,
    idea: str,
    prompt: str,
    negative_prompt: str,
) -> dict[str, str]:
    settings = get_settings()
    if not settings.llm_api_key or not settings.llm_api_base_url or not settings.llm_model:
        raise PromptOptimizeError("LLM_API_KEY, LLM_API_BASE_URL and LLM_MODEL are required.")

    topic_name = TOPICS.get(topic, TOPICS["scifi"]).name
    style_name = STYLE_NAMES.get(style, style)
    user_prompt = f"""用户创意：{idea or "未提供"}
专题方向：{topic_name}
视觉风格：{style_name}
当前 Positive 关键词：{prompt or "未提供"}
当前 Negative 关键词：{negative_prompt or "未提供"}

请优化 positive/negative 关键词。再次强调：不要把用户创意原句直接写进 prompt，只输出 JSON。"""

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.45,
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{settings.llm_api_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.RequestError as exc:
        raise PromptOptimizeError(f"LLM API connection failed: {exc}") from exc

    if response.status_code >= 400:
        raise PromptOptimizeError(response.text)

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise PromptOptimizeError("LLM response did not include message content.")
    return _extract_json_object(content)


IDEA_SYSTEM_PROMPT = """你是一个生图创意策划专家，擅长根据专题方向和视觉风格，生成适合文生图模型的中文创意描述。
要求：
1. 只输出一条中文创意，不要输出解释、编号、JSON、Markdown 或引号。
2. 创意应包含主体、场景、氛围或关键视觉冲突，适合直接放进“你的创意”输入框。
3. 不要写成关键词列表，要写成一句自然中文短句。
4. 长度控制在 20-45 个中文字符左右。
5. 避免露骨、违法、血腥或不安全内容。
"""


async def generate_idea(topic: str, style: str) -> str:
    settings = get_settings()
    if not settings.llm_api_key or not settings.llm_api_base_url or not settings.llm_model:
        raise PromptOptimizeError("LLM_API_KEY, LLM_API_BASE_URL and LLM_MODEL are required.")

    topic_name = TOPICS.get(topic, TOPICS["scifi"]).name
    style_name = STYLE_NAMES.get(style, style)
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": IDEA_SYSTEM_PROMPT},
            {"role": "user", "content": f"专题方向：{topic_name}\n视觉风格：{style_name}\n请生成一条适合生图的中文创意。"},
        ],
        "temperature": 0.82,
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{settings.llm_api_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.RequestError as exc:
        raise PromptOptimizeError(f"LLM API connection failed: {exc}") from exc

    if response.status_code >= 400:
        raise PromptOptimizeError(response.text)

    data = response.json()
    idea = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    idea = re.sub(r"^[-\d.、\s]+", "", idea).strip().strip('"“”')
    if not idea:
        raise PromptOptimizeError("LLM response did not include idea content.")
    return idea.splitlines()[0].strip()

