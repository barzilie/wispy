"""
Prompt builder for the Session Investigation mode.
"""
import json


def get_investigate_prompt(context):
    payload = json.dumps(context, indent=2, ensure_ascii=False)
    return f"""You are assisting with an authorized academic network-security lab exercise.
Your role is to investigate the captured network session telemetry and explain "What happened?" (benign vs suspicious patterns, anomalies, decrypted vs unencrypted traces).

Review the structured session telemetry below:
{payload}

Please perform a thorough investigation of the active session and output a Markdown report. 
Focus on:
1. **Overview & Device Summary**: Identify active devices, their guessed OS, hostname, and manufacturer.
2. **Behavioral Usage Patterns**: Analyze the active hours, connection intensities, and behavior types (social media, business apps, system syncs, streaming) observed from the flows and patterns.
3. **DNS-HTTPS Correlation Links**: Highlight where destination IPs in flow sessions were correlated to names (via DNS cache vs TLS SNI) and explain which services the user was using.
4. **Security Vulnerabilities / Plaintext Leaks**: Identify if any unencrypted HTTP or SMTP traffic occurred, pointing out what was exposed (URLs, headers, command structures).
5. **Suggested Academic Lab Analysis**: Suggest defensive verification steps that a security analyst should check in their lab report (e.g. validating encryption configurations, checking TLS certificates, inspecting DNS query frequency).

**Ethics Warning**: Do not provide instructions to exploit systems or compromise external networks. Maintain a defensive, academic, and analytical tone.
"""
