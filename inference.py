"""
Inference Script for Helpdesk Support Environment
"""

import os
import json
import urllib.request
import urllib.error
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:7860")

def run_task(task_id: str, client: OpenAI):
    print(f"START {task_id}")
    
    try:
        req = urllib.request.Request(f"{ENV_URL}/reset?task_id={task_id}", method="POST")
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: Could not connect to environment. {e}")
        return

    ticket_content = res.get("ticket_content", "")
    done = False
    step = 0
    history = []
    total_reward = 0.0

    while not done and step < 5:
        step += 1
        
        prompt = (
            f"You are a Level 1 Support Agent.\n"
            f"Customer Message: {ticket_content}\n"
            f"Action History: {history}\n\n"
            f"CRITICAL RULES:\n"
            f"1. You MUST verify policies by using 'query_crm' before taking financial actions.\n"
            f"2. If your Action History shows you already used 'query_crm', DO NOT use it again. Make a decision.\n"
            f"Choose exactly one action: 'query_crm', 'issue_refund', 'reply', or 'escalate'.\n"
            f"Respond STRICTLY in JSON format: {{\"command\": \"action_name\", \"args\": {{\"text\": \"your message\"}}}}"
        )
        
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a logical AI support agent. Always output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            action_data = json.loads(response_text)
            
            if "args" not in action_data:
                action_data["args"] = {}
                
        except Exception:
            action_data = {"command": "reply", "args": {"text": "System error."}}
            
        print(f"STEP {step} Action: {action_data['command']}")
        
        try:
            data = json.dumps(action_data).encode('utf-8')
            req = urllib.request.Request(f"{ENV_URL}/step", data=data, headers={'Content-Type': 'application/json'}, method="POST")
            with urllib.request.urlopen(req) as response:
                step_res = json.loads(response.read().decode('utf-8'))
        except Exception:
            print("Error: Step failed.")
            break
        
        if "reward" not in step_res:
            break
            
        reward = step_res["reward"]
        done = step_res["done"]
        system_msg = step_res.get("observation", {}).get("system_message", "")
        total_reward = reward  
        
        history.append(f"Used '{action_data['command']}'. Result: {system_msg}")
        
    print(f"END {task_id} Score: {total_reward}")

if __name__ == "__main__":
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    for t in ["task_refund", "task_reject_outdated", "escalation"]:
        run_task(t, client)
