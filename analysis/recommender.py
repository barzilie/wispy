"""
Backward-compatibility wrapper for the AI recommender, pointing to the analysis/agentic module.
"""
from analysis.agentic import recommend_attacks

def get_recommendations():
    """Wrapper function returning Gemini recommendations from the agentic package."""
    return recommend_attacks()


if __name__ == "__main__":
    print(get_recommendations())
