import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# Using a widely supported NVIDIA model
PREFERRED_MODELS = [
    "meta/llama-3.1-8b-instruct",
    "mistralai/mixtral-8x7b-instruct-v0.1",
    "nvidia/llama-3.1-nemotron-70b-instruct"
]

def has_nvidia_key() -> bool:
    return bool(NVIDIA_API_KEY and len(NVIDIA_API_KEY.strip()) > 10)

def test_nvidia_connection() -> Dict[str, Any]:
    if not has_nvidia_key():
        return {"status": "unconfigured", "message": "NVIDIA_API_KEY not set in .env"}
    
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY.strip()}",
        "Content-Type": "application/json"
    }
    for model_name in PREFERRED_MODELS:
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Ping"}],
            "max_tokens": 5,
            "temperature": 0.1
        }
        try:
            resp = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=5)
            if resp.status_code == 200:
                return {"status": "connected", "model": model_name}
        except Exception:
            continue
            
    return {"status": "fallback_active", "detail": "Using internal SOC explanation engine"}

def explain_cyber_event(event_summary: Dict[str, Any]) -> str:
    """
    Generates concise natural language cyber incident analysis.
    Tries NVIDIA API if available, with robust built-in heuristic fallback.
    """
    stage = event_summary.get("attack_stage", "NORMAL")
    joint_action = event_summary.get("joint_action", {})
    health = event_summary.get("network_health", 100)
    contained = event_summary.get("contained", False)
    scenario = event_summary.get("scenario", "Scenario 2")

    if has_nvidia_key():
        for model_name in PREFERRED_MODELS:
            try:
                prompt = (
                    f"You are an expert SOC AI Analyst for an academic cybersecurity viva presentation. "
                    f"Explain this simulation step concisely in 2 sentences for the evaluation panel:\n"
                    f"- Scenario: {scenario}\n"
                    f"- Attack Stage: {stage}\n"
                    f"- Joint Defensive Action: {joint_action}\n"
                    f"- Network Health: {health}%\n"
                    f"- Attack Contained: {contained}\n"
                    f"Explain why the multi-agent cooperative defense contained the attack."
                )
                headers = {
                    "Authorization": f"Bearer {NVIDIA_API_KEY.strip()}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 90,
                    "temperature": 0.3
                }
                resp = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=4)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception:
                pass

    # Built-in High-Fidelity Local Explanation Engine (Always works 100% reliably)
    if contained:
        return (
            f"Attack successfully contained during the {stage} phase. The decentralized agents coordinated actions "
            f"({', '.join(f'{k}: {v}' for k, v in joint_action.items())}) to quarantine compromised nodes and protect the critical core at {health}% network health."
        )
    elif stage == "NORMAL":
        return "Network baseline normal. All three decentralized defender agents are actively monitoring telemetry and establishing communication baselines."
    elif stage == "RECONNAISSANCE":
        return "Early port reconnaissance detected on ingress nodes. Agent 1 raised alarm and broadcast threat metrics to neighboring defenders."
    elif stage == "LATERAL MOVEMENT":
        return f"Adversary attempting lateral movement into Segment B. Agent 2 responded with coordinated defensive posture to block privilege escalation."
    elif stage == "TARGET ATTEMPT":
        return f"Adversary converging on Critical Server segment. Agent 3 executed defensive containment protocol to avert catastrophic system compromise."
    else:
        return f"Simulation active at stage '{stage}'. Multi-agent policies executing joint defense with current health at {health}%."
