"""
On-demand AI recommendations from session summary (devices + DNS) via Google Gemini.
Requires GOOGLE_API_KEY in the environment (.env).
"""

import json

import google.generativeai as genai

from analysis.storage import get_session_summary

# Prefer env from project root; config also loads .env when imported.
from config import GOOGLE_API_KEY

_MODEL_CANDIDATES = (
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
)


def _build_prompt(summary):
    payload = json.dumps(summary, indent=2, ensure_ascii=False)
    return f"""You are assisting with an authorized academic network-security lab exercise.
The student runs a controlled rogue AP in a lab and captured DHCP/DNS metadata only (no payloads).

Summarize risks implied by the telemetry, then list plausible next investigation steps
(what to verify in the lab report, what benign vs suspicious patterns mean).
Do not provide step-by-step instructions to attack unrelated third parties.
Keep the tone educational and defensive.

Session summary (JSON):
{payload}

Respond in Markdown with sections: Overview, Notable domains & devices, Suggested lab follow-ups, Ethics reminder."""


def get_recommendations():
    if not GOOGLE_API_KEY:
        return (
            "No GOOGLE_API_KEY is configured. Add GOOGLE_API_KEY to your .env file "
            "to enable Gemini-based recommendations."
        )

    summary = get_session_summary()
    if not summary:
        return "No devices or telemetry yet. Connect a test client to the lab AP and wait for DNS activity."

    genai.configure(api_key=GOOGLE_API_KEY)
    prompt = _build_prompt(summary)
    last_error = None

    for model_name in _MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = getattr(response, "text", None) or ""
            if not text.strip():
                parts = getattr(response, "candidates", None) or []
                if parts:
                    content = getattr(parts[0], "content", None)
                    p = getattr(content, "parts", None) if content else None
                    if p:
                        text = "".join(getattr(x, "text", "") for x in p)
            if text.strip():
                return text.strip()
            last_error = "Empty model response"
        except Exception as e:
            last_error = e
            continue

    return f"Could not generate recommendations ({last_error}). Check GOOGLE_API_KEY and model availability."


if __name__ == "__main__":
    print(get_recommendations())
