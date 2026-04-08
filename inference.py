"""
Inference Script for Enterprise Helpdesk Environment - Zero Dependency Version
"""
import os
import json
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:7860")

def call_llm_api(prompt: str) -> str:
    url = f"{API_BASE_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
        
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a logical enterprise AI support agent. Always output valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except Exception:
        return ""

def run_task(task_id: str):
    print(f"[START] task={task_id}", flush=True)
    
    try:
        req = urllib.request.Request(f"{ENV_URL}/reset?task_id={task_id}", method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
    except Exception:
        print(f"[END] task={task_id} score=0.01 steps=0", flush=True)
        return

    ticket_content = res.get("ticket_content", "")
    done = False
    step = 0
    history = []
    total_reward = 0.1

    while not done and step < 8:
        step += 1
        
        # PROMPT FOR ENTERPRISE ACTIONS
        prompt = (
            f"You are an Enterprise Level 1 Support Agent.\n"
            f"Customer Message: {ticket_content}\n"
            f"Action History: {history}\n\n"
            f"CRITICAL RULES:\n"
            f"1. You MUST investigate before acting. Use tools like 'query_crm', 'check_stripe', 'check_jira', or 'verify_identity'.\n"
            f"2. Choose exactly ONE action: 'query_crm', 'check_stripe', 'check_jira', 'verify_identity', 'issue_refund', 'apply_credit', 'reply', 'request_info', 'escalate_tier2', or 'escalate_legal'.\n"
            f"Respond STRICTLY in JSON format: {{\"command\": \"action_name\", \"args\": {{\"text\": \"your message\"}}}}"
        )
        
        response_text = call_llm_api(prompt)
        
        try:
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            action_data = json.loads(response_text)
            if "args" not in action_data:
                action_data["args"] = {}
        except Exception:
            action_data = {"command": "reply", "args": {"text": "System error."}}
            
        try:
            data = json.dumps(action_data).encode('utf-8')
            req = urllib.request.Request(f"{ENV_URL}/step", data=data, headers={'Content-Type': 'application/json'}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                step_res = json.loads(response.read().decode('utf-8'))
                
            if "reward" not in step_res:
                print(f"[STEP] step={step} reward=0.01", flush=True)
                print(f"[STEP] step={step} reward={reward:.2f}", flush=True)
                break
                
            reward = step_res["reward"]
            done = step_res["done"]
            system_msg = step_res.get("observation", {}).get("system_message", "")
            total_reward = reward  
            
            print(f"[STEP] step={step} reward={reward:.2f}", flush=True)
            history.append(f"Used '{action_data.get('command')}'. Result: {system_msg}")
            
        except Exception:
            print(f"[STEP] step={step} reward=0.01", flush=True)
            break
        
    print(f"[END] task={task_id} score={total_reward:.2f} steps={step}", flush=True)

if __name__ == "__main__":
    try:
        # RUNNING NEW ENTERPRISE SCENARIOS
        for t in ["duplicate_charge", "account_takeover", "service_outage"]:
            run_task(t)
    except Exception:
        pass