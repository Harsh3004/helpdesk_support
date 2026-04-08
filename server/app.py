from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
import random
import uvicorn
from server.graders import evaluate_task

app = FastAPI()

# 1. Models
class Action(BaseModel):
    command: str
    args: Dict[str, Any]

class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]

# 2. Enterprise Database & 8 Scenarios
SCENARIOS = {
    "duplicate_charge": {
        "ticket": "I was charged $29.99 twice on the 1st.",
        "crm": {"account_age": "3 years", "tier": "premium"},
        "stripe": {"tx_count": 2, "amount": 29.99, "status": "settled"},
        "jira": {"active_outages": "none"},
        "auth0": {"ip_match": True, "risk": "low"},
        "true_verdict": "issue_refund"
    },
    "outdated_refund": {
        "ticket": "I want a refund for my lifetime license from 2023.",
        "crm": {"account_age": "2 years", "tier": "standard", "policy": "30-day max"},
        "stripe": {"tx_count": 1, "date": "2023-05-12"},
        "jira": {"active_outages": "none"},
        "auth0": {"ip_match": True, "risk": "low"},
        "true_verdict": "reply_reject"
    },
    "account_takeover": {
        "ticket": "RESET MY PASSWORD NOW I CANNOT LOG IN AND MY BILLING IS WRONG.",
        "crm": {"account_age": "5 years", "tier": "enterprise"},
        "stripe": {"tx_count": 5, "recent_failures": True},
        "jira": {"active_outages": "none"},
        "auth0": {"ip_match": False, "risk": "CRITICAL - VPN DETECTED"},
        "true_verdict": "escalate_t2"
    },
    "service_outage": {
        "ticket": "The API is down! I'm losing money. Fix it or refund me for the month.",
        "crm": {"account_age": "1 month", "tier": "startup"},
        "stripe": {"status": "paid"},
        "jira": {"active_outages": "API_GATEWAY_DOWN", "eta": "2 hours"},
        "auth0": {"ip_match": True, "risk": "low"},
        "true_verdict": "apply_credit"
    },
    "legal_threat": {
        "ticket": "Your software deleted my database. My lawyer is drafting a lawsuit for $50,000.",
        "crm": {"account_age": "4 years", "tier": "premium"},
        "stripe": {"status": "paid"},
        "jira": {"active_outages": "none"},
        "auth0": {"ip_match": True, "risk": "low"},
        "true_verdict": "escalate_legal"
    },
    "feature_request": {
        "ticket": "Can you add a dark mode to the dashboard?",
        "crm": {"account_age": "1 year", "tier": "free"},
        "stripe": {"status": "none"},
        "jira": {"active_outages": "none"},
        "auth0": {"ip_match": True, "risk": "low"},
        "true_verdict": "reply_resolved"
    },
    "unrecognized_charge": {
        "ticket": "Who are you? I have a charge for $99 on my card from your company!",
        "crm": {"account_found": False},
        "stripe": {"tx_count": 1, "amount": 99.00, "name_mismatch": True},
        "jira": {"active_outages": "none"},
        "auth0": {"ip_match": False, "risk": "HIGH"},
        "true_verdict": "escalate_t2"
    },
    "missing_delivery": {
        "ticket": "I bought the physical security key but it never arrived in the mail.",
        "crm": {"account_age": "6 months", "tier": "standard"},
        "stripe": {"status": "paid"},
        "jira": {"active_outages": "none"},
        "auth0": {"ip_match": True, "risk": "low"},
        "true_verdict": "request_info"
    }
}

env_state = {}

# 3. API Endpoints
@app.post("/reset")
def reset(task_id: str = "random"):
    global env_state
    
    if task_id == "random" or task_id not in SCENARIOS:
        task_id = random.choice(list(SCENARIOS.keys()))
        
    env_state = {
        "current_task": task_id,
        "step_count": 0,
        "ticket_status": "open",
        "action_history": [],
        "revealed_info": {},
        "final_action": None
    }
    return {"ticket_content": SCENARIOS[task_id]["ticket"], "task_id": task_id}

@app.post("/step", response_model=StepResponse)
def step(action: Action):
    global env_state
    env_state["step_count"] += 1
    task = SCENARIOS[env_state["current_task"]]
    cmd = action.command
    
    system_msg = ""
    
    # 10 ENTERPRISE ACTIONS
    if cmd == "query_crm":
        system_msg = f"CRM Data: {task['crm']}"
        env_state["revealed_info"]["crm"] = True
    elif cmd == "check_stripe":
        system_msg = f"Stripe Gateway: {task['stripe']}"
        env_state["revealed_info"]["stripe"] = True
    elif cmd == "check_jira":
        system_msg = f"Jira Engineering Status: {task['jira']}"
        env_state["revealed_info"]["jira"] = True
    elif cmd == "verify_identity":
        system_msg = f"Auth0 Security Log: {task['auth0']}"
        env_state["revealed_info"]["auth0"] = True
    elif cmd == "request_info":
        system_msg = "Requested additional information from customer."
        env_state["final_action"] = "request_info"
        env_state["ticket_status"] = "pending_customer"
    elif cmd == "issue_refund":
        system_msg = "Refund successfully processed via Stripe API."
        env_state["final_action"] = "issue_refund"
        env_state["ticket_status"] = "closed"
    elif cmd == "apply_credit":
        system_msg = "Account credited for 1 free month."
        env_state["final_action"] = "apply_credit"
        env_state["ticket_status"] = "closed"
    elif cmd == "reply":
        system_msg = "Message sent to customer."
        env_state["final_action"] = "reply_reject" if "reject" in action.args.get("text", "").lower() else "reply_resolved"
        env_state["ticket_status"] = "closed"
    elif cmd == "escalate_tier2":
        system_msg = "Ticket routed to Tier 2 Technical/Fraud Support."
        env_state["final_action"] = "escalate_t2"
        env_state["ticket_status"] = "escalated"
    elif cmd == "escalate_legal":
        system_msg = "Ticket routed to Legal & Compliance."
        env_state["final_action"] = "escalate_legal"
        env_state["ticket_status"] = "escalated"
    else:
        system_msg = f"Unknown command: {cmd}"

    env_state["action_history"].append(cmd)

    # Grade the step
    score, done = evaluate_task(task, env_state)
    
    if env_state["step_count"] >= 8:
        done = True

    return StepResponse(
        observation={"system_message": system_msg, "revealed_info": env_state["revealed_info"]},
        reward=score if done else 0.0, # Give reward only at the end to force RL planning
        done=done,
        info={"ticket_status": env_state["ticket_status"]}
    )

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()