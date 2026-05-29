"""
Agentic module for session investigation and attack vector recommendations.
"""
from .client import run_agent


def investigate_session():
    """Analyzes the current session metadata (flows, DNS, TLS, mDNS) to provide an operational summary."""
    return run_agent(mode="investigate")


def recommend_attacks():
    """Analyzes the session metadata to suggest authorized academic lab attack pathways and defenses."""
    return run_agent(mode="recommend")
