import json
from typing import Optional

from groq import Groq

from app.core.config import settings

_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


HEALTH_DISCLAIMER = (
    "You are MediMate, a friendly health-information assistant. You are NOT a doctor "
    "and cannot diagnose conditions or prescribe treatment. Give clear, evidence-based "
    "general information, lifestyle and diet guidance, and help the user understand their "
    "reports and vitals trends. Always encourage the user to consult a licensed doctor for "
    "diagnosis, medication changes, or anything urgent. If the user describes symptoms that "
    "could be a medical emergency (e.g. chest pain, difficulty breathing, signs of stroke, "
    "severe bleeding, suicidal thoughts), tell them clearly to seek emergency care or call "
    "their local emergency number immediately, before anything else."
)


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
}


def language_instruction(language: str) -> str:
    """Returns an instruction telling the model which language to reply in.
    Defaults to English for any unrecognized code."""
    name = LANGUAGE_NAMES.get(language, "English")
    if name == "Hindi":
        return (
            "Respond entirely in Hindi (Devanagari script). Keep medical/food terms "
            "understandable — you may add the common English term in parentheses the "
            "first time a technical term appears, e.g. \u0930\u0915\u094d\u0924\u091a\u093e\u092a (blood pressure)."
        )
    return "Respond in clear, simple English."


def build_user_context(user) -> str:
    parts = []
    if user.age:
        parts.append(f"Age: {user.age}")
    if user.gender:
        parts.append(f"Gender: {user.gender}")
    if user.height_cm:
        parts.append(f"Height: {user.height_cm} cm")
    if user.weight_kg:
        parts.append(f"Weight: {user.weight_kg} kg")
    if user.has_diabetes:
        parts.append("Has diabetes: yes")
    if user.has_hypertension:
        parts.append("Has hypertension: yes")
    if user.other_conditions:
        parts.append(f"Other conditions: {user.other_conditions}")
    if user.allergies:
        parts.append(f"Allergies: {user.allergies}")
    return "; ".join(parts) if parts else "No profile details on file."


def chat_completion(messages: list[dict], user_context: str = "", language: str = "en") -> str:
    """messages: list of {"role": "user"|"assistant", "content": str}"""
    client = get_client()
    system_prompt = HEALTH_DISCLAIMER + "\n\n" + language_instruction(language)
    if user_context:
        system_prompt += f"\n\nKnown user profile: {user_context}"

    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "system", "content": system_prompt}, *messages],
        temperature=0.4,
        max_tokens=1024,
    )
    return completion.choices[0].message.content


def summarize_report(extracted_text: str, language: str = "en") -> str:
    client = get_client()
    prompt = (
        "Summarize the following medical report for a non-medical patient in plain language. "
        "Call out any values that are outside normal reference ranges, and note (without "
        "diagnosing) what they might commonly relate to. End with a reminder to discuss the "
        "full report with their doctor.\n\nReport text:\n" + extracted_text[:12000]
    )
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": HEALTH_DISCLAIMER + "\n\n" + language_instruction(language)},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )
    return completion.choices[0].message.content


def generate_diet_plan(
    user_context: str, goal: str, days: int, extra_notes: str = "", language: str = "en"
) -> dict:
    client = get_client()
    lang_note = (
        "Write all text values (goal, meal items, notes, general_tips) in Hindi (Devanagari "
        "script), but keep the JSON keys themselves in English exactly as shown below."
        if language == "hi"
        else "Write all text values in clear, simple English."
    )
    prompt = f"""
Create a {days}-day diet plan as STRICT JSON only (no markdown, no commentary, no code fences).
User profile: {user_context}
Goal: {goal or "general balanced health"}
Extra notes: {extra_notes or "none"}
Language: {lang_note}

Return JSON matching exactly this shape:
{{
  "goal": "string",
  "days": [
    {{
      "day": "Day 1",
      "meals": [
        {{"meal": "Breakfast", "items": ["..."], "notes": "..."}},
        {{"meal": "Lunch", "items": ["..."], "notes": "..."}},
        {{"meal": "Dinner", "items": ["..."], "notes": "..."}},
        {{"meal": "Snacks", "items": ["..."], "notes": "..."}}
      ]
    }}
  ],
  "general_tips": ["..."]
}}

If the user has diabetes, favor low glycemic-index foods and consistent carb timing.
If the user has hypertension, favor low-sodium options.
"""
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": HEALTH_DISCLAIMER + " Respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=3000,
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    return json.loads(raw)
