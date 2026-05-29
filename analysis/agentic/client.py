"""
Gemini API client interface and fallback execution loop.
"""
import google.generativeai as genai
from config import GOOGLE_API_KEY
from .context import build_agent_context
from .prompts.investigate import get_investigate_prompt
from .prompts.recommend import get_recommend_prompt

_MODEL_CANDIDATES = (
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
)


def run_agent(mode="investigate"):
    """Runs the Gemini agent in either 'investigate' or 'recommend' mode."""
    if not GOOGLE_API_KEY:
        return (
            "No GOOGLE_API_KEY is configured. Add GOOGLE_API_KEY to your .env file "
            "to enable Gemini-based analysis."
        )

    context = build_agent_context()
    if not context or not context.get("devices"):
        return (
            "No active devices or network telemetry captured yet. "
            "Connect a target client to the rogue AP to begin collecting data."
        )

    # Pick prompt based on mode
    if mode == "investigate":
        prompt = get_investigate_prompt(context)
    elif mode == "recommend":
        prompt = get_recommend_prompt(context)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    genai.configure(api_key=GOOGLE_API_KEY)
    last_error = None

    for model_name in _MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            text = getattr(response, "text", None) or ""
            if not text.strip():
                # Fallback extraction from response candidates
                parts = getattr(response, "candidates", None) or []
                if parts:
                    content = getattr(parts[0], "content", None)
                    p = getattr(content, "parts", None) if content else None
                    if p:
                        text = "".join(getattr(x, "text", "") for x in p)
                        
            if text.strip():
                return text.strip()
            
            last_error = "Empty response from Gemini model"
        except Exception as e:
            last_error = str(e)
            continue

    return f"Could not generate agent analysis ({last_error}). Verify GOOGLE_API_KEY and model quotas."
