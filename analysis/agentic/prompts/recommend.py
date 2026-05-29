"""
Prompt builder for the Attack Recommendations mode.
"""
import json


def get_recommend_prompt(context):
    payload = json.dumps(context, indent=2, ensure_ascii=False)
    return f"""You are assisting with an authorized academic network-security lab exercise.
Your role is to formulate educational/defensive "next-step attack suggestions" based on the captured network telemetry.
This allows students to understand the risks of connecting to rogue Wi-Fi APs.

Review the structured session telemetry below:
{payload}

Please formulate an attack recommendations report in Markdown.
Focus on:
1. **Target Exposure Profile**: Assess the threat surface of each client device (hostname implications, OS vulnerabilities, hardware manufacturer flaws, Option 55 fingerprints).
2. **Behavioral Weaknesses / Lures**: Suggest social engineering or credential collection hooks based on their active browsing habits (e.g. if they visit specific apps or sites).
3. **Exploitation Vectors**:
   - For any unencrypted plaintext leaks (HTTP/SMTP), explain what an attacker can do (credential theft, session hijacking, relaying).
   - Suggest academic follow-ups for DNS redirection (fake portals, cache poisoning) or mDNS spoofing matching their discovered services.
4. **Defensive Remediations**: Provide concrete countermeasures for students to implement to secure these devices against the suggested attacks.

**Ethics Warning**: Do not provide specific malicious payloads, exploits, or step-by-step instructions targeting real-world networks. Keep the suggestions conceptual, high-level, and strictly framed for an educational laboratory context.
"""
