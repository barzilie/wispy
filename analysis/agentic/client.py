"""
Gemini API client interface using the official SDK.
"""
import google.generativeai as genai
from config import GOOGLE_API_KEY
from .context import build_agent_context
from .prompts.investigate import get_investigate_prompt
from .prompts.recommend import get_recommend_prompt

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

    # pick investigate vs recommend prompt
    if mode == "investigate":
        prompt = get_investigate_prompt(context)
    elif mode == "recommend":
        prompt = get_recommend_prompt(context)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    genai.configure(api_key=GOOGLE_API_KEY)

    try:
        # Strictly targeting flash-lite-latest
        model = genai.GenerativeModel("gemini-flash-lite-latest")
        response = model.generate_content(prompt)
        
        # The SDK natively handles the payload parsing 
        if response.text and response.text.strip():
            return response.text.strip()
            
        return "Could not generate agent analysis (Empty response from Gemini model)."
        
    except Exception as e:
        return f"Could not generate agent analysis ({str(e)}). Verify GOOGLE_API_KEY and model quotas."