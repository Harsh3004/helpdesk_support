"""
Inference Script for Helpdesk Support Environment
=================================================
This script connects an LLM to the local OpenEnv API.
"""

import os
import requests
import json
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenEnv Competition Variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")

# Pointing to our local FastAPI server
ENV_URL = "http://127.0.0.1:7860"

def run_task(task_id: str, client: OpenAI):
    print(f"\n{'='*40}\nStarting Task: {task_id}\n{'='*40}")
    
    # 1. Resetting the environment and getting the first ticket
    try:
        res = requests.post(f"{ENV_URL}/reset?task_id={task_id}").json()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the environment. Is your FastAPI server running?")
        return

    ticket_content = res.get("ticket_content", "")
    print(f"CUSTOMER TICKET: {ticket_content}\n")
    
    done = False
    step = 0
    history = []
    total_reward = 0.0

    while not done and step < 5:
        step += 1
        
        # 2. Building the prompt for the LLM
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
        
        # 3. Calling the LLM
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful JSON-outputting support agent."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            
            # Sometimes smaller LLMs wrap JSON in markdown blocks. This strips them out safely.
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            action_data = json.loads(response_text)
            
            # --- Safety net in case the LLM forgets the 'args' dict ---
            if "args" not in action_data:
                action_data["args"] = {}
                
        except Exception as e:
            print(f"LLM Error: {e}")
            action_data = {"command": "reply", "args": {"text": "System error. Please hold."}}
            
        print(f"Step {step} - Agent Action: {action_data['command']}")
        if action_data['command'] == 'reply':
            print(f"Agent Reply Text: {action_data['args'].get('text', '')}")
        
        # 4. Sending the action to our Environment
        response = requests.post(f"{ENV_URL}/step", json=action_data)

        try:
            step_res = response.json()
        except Exception:
            print(f"\nCRITICAL ERROR: Local Server returned an invalid response.")
            print(f"Status Code: {response.status_code}")
            print(f"Raw Output: {response.text}")
            break
        
        if "reward" not in step_res:
            print(f"\nAPI Error from Server: {step_res}")
            break
            
        reward = step_res["reward"]
        done = step_res["done"]
        system_msg = step_res["observation"]["system_message"]
        
        total_reward = reward  
        history.append(f"Used '{action_data['command']}'. Result: {system_msg}")

    print(f"\nTask {task_id} Finished.")
    print(f"Final Status: {step_res['info']['ticket_status']}")
    print(f"Final Score: {total_reward} / 1.0")

if __name__ == "__main__":
    # Initializing the OpenAI client
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    tasks = ["task_refund", "task_reject_outdated", "escalation"]
    for t in tasks:
        run_task(t, client)