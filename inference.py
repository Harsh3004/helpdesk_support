"""
Enterprise Support World Model v2.0 - Evaluation Script
Supports Session-Based State and Procedural Scenarios.
"""
import os
import json
import urllib.request
import urllib.error

# --- CONFIGURATION ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:7860")

def call_llm_api(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    if HF_TOKEN: headers["Authorization"] = f"Bearer {HF_TOKEN}"
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": "You are an Enterprise AI Agent. Output strictly JSON."},
                     {"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{API_BASE_URL}/chat/completions", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))['choices'][0]['message']['content']
    except Exception: return ""

def run_task(task_type: str):
    print(f"[START] task={task_type}", flush=True)
    
    # 1. RESET: Capture the unique session_id
    try:
        req = urllib.request.Request(f"{ENV_URL}/reset?task_type={task_type}", method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
            session_id = res["session_id"] # Critical for v2.0
    except Exception as e:
        print(f"[END] task={task_type} score=0.01 steps=0", flush=True)
        return

    ticket_content = res.get("ticket", "")
    done = False
    step = 0
    history = []
    total_score = 0.0

    while not done and step < 8:
        step += 1
        prompt = (
            f"Ticket: {ticket_content}\nHistory: {history}\n\n"
            f"Tools: query_crm, check_stripe, verify_identity, check_outages\n"
            f"Decision Actions: approve_refund, deny_request, escalate\n"
            f"Respond in JSON: {{\"command\": \"action_name\", \"args\": {{}}}}"
        )
        
        response_text = call_llm_api(prompt)
        try:
            action_data = json.loads(response_text)
            action_data["session_id"] = session_id # Attach session_id to every step
        except Exception:
            action_data = {"command": "deny_request", "session_id": session_id}
            
        try:
            data = json.dumps(action_data).encode('utf-8')
            req = urllib.request.Request(f"{ENV_URL}/step", data=data, headers={'Content-Type': 'application/json'}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                step_res = json.loads(response.read().decode('utf-8'))
            
            reward = step_res["reward"]
            done = step_res["done"]
            total_score = step_res["info"]["total_score"]
            
            print(f"[STEP] step={step} reward={reward:.2f}", flush=True)
            history.append(f"Used '{action_data['command']}'. Result: {step_res['observation']['message']}")
        except Exception: break
        
    print(f"[END] task={task_type} score={total_score:.2f} steps={step}", flush=True)

if __name__ == "__main__":
    for t in ["refund", "access_issue", "outage"]:
        run_task(t)