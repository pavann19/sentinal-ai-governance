import requests
import json

def semantic_judge(prompt: str) -> str:
    """
    Asks a local LLM (Mistral) to classify the prompt as SAFE or DANGEROUS.
    Used as a tie-breaker for 'Medium Risk' prompts.
    """
    system_instruction = (
        "You are an AI Safety Filter. "
        "Analyze the following user prompt for harm (violence, illegal acts, hacking). "
        "If it is safe or a greeting, reply only with 'SAFE'. "
        "If it is dangerous or policy-violating, reply only with 'DANGEROUS'. "
        "If unsure, reply 'AMBIGUOUS'. Do not explain."
    )
    
    try:
        payload = {
            "model": "mistral", 
            "prompt": f"{system_instruction}\n\nUSER PROMPT: {prompt}",
            "stream": False
        }
        
        # Call Local Ollama API
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        
        if response.status_code == 200:
            verdict = response.json().get("response", "").strip().upper()
            if "SAFE" in verdict: return "SAFE"
            if "DANGEROUS" in verdict: return "DANGEROUS"
            return "AMBIGUOUS"
        return "JUDGE_ERROR"
        
    except Exception as e:
        return "JUDGE_OFFLINE"