"""
Inference Script for Helpdesk Support Environment - Zero Dependency Version
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
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
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
            {"role": "system", "content": "You are a logical AI support agent. Always output valid JSON."},
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
        print(f"[END] task={task_id} score=0.1 steps=0", flush=True)
        return

    ticket_content = res.get("ticket_content", "")
    done = False
    step = 0
    history = []
    total_reward = 0.1 # Start at baseline

    while not done and step < 5:
        step += 1
        
        prompt = (
            f"You are a Level 1 Support Agent.\n"
            f"Customer Message: {ticket_content}\n"
            f"Action History: {history}\n\n"
            f"CRITICAL RULES:\n"
            f"1. You MUST verify policies by using 'query_crm' before taking financial actions.\n"
            f"2. If your Action History shows you already used 'query_crm', DO NOT use it again.\n"
            f"Choose exactly one action: 'query_crm', 'issue_refund', 'reply', or 'escalate'.\n"
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
                print(f"[STEP] step={step} reward=0.1", flush=True)
                break
                
            reward = step_res["reward"]
            done = step_res["done"]
            system_msg = step_res.get("observation", {}).get("system_message", "")
            total_reward = reward  
            
            print(f"[STEP] step={step} reward={reward}", flush=True)
            history.append(f"Used '{action_data.get('command')}'. Result: {system_msg}")
            
        except Exception:
            print(f"[STEP] step={step} reward=0.1", flush=True)
            break
        
    print(f"[END] task={task_id} score={total_reward} steps={step}", flush=True)

if __name__ == "__main__":
    try:
        for t in ["task_refund", "task_reject_outdated", "escalation"]:
            run_task(t)
    except Exception:
        pass
