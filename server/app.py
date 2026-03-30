from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional
from server.graders import evaluate_task
import uvicorn

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

# 2. Database & State
MOCK_CRM_DB = {
    "task_refund": {"account_age": "3 years", "last_charge": "Duplicate $29.99 detected today", "policy": "Standard"},
    "task_reject_outdated": {"account_age": "2 years", "last_charge": "2 years ago", "policy": "No refunds after 30 days"},
    "escalation": {"account_age": "5 years", "last_charge": "Yesterday", "alert": "HIGH RISK - Legal threat detected"}
}

TICKETS = {
    "task_refund": "Hi Support, I just checked my credit card statement and I was charged $29.99 twice on the 1st of the month. Can you please refund the duplicate charge?",
    "task_reject_outdated": "Hello, I purchased a lifetime license for your software 2 years ago. I don't really use it anymore. Please issue a full refund to my original payment method.",
    "escalation": "YOUR UPDATE DELETED MY ENTIRE PROJECT DATABASE!! I DEMAND A FULL REFUND PLUS $500 FOR THE HOURS OF WORK I LOST! IF YOU DON'T FIX THIS I AM INVOLVING MY LAWYER. GET ME A MANAGER NOW!"
}

env_state = {
    "current_task": None,
    "step_count": 0,
    "ticket_status": "open",
    "refund_issued": False,
    "reply_sent": "",
    "escalated": False,
    "crm_checked": False
}

# 3. API Endpoints
@app.post("/reset")
def reset(task_id: str):
    global env_state
    env_state = {
        "current_task": task_id,
        "step_count": 0,
        "ticket_status": "open",
        "refund_issued": False,
        "reply_sent": "",
        "escalated": False,
        "crm_checked": False
    }
    return {"ticket_content": TICKETS.get(task_id, "Unknown ticket.")}

@app.post("/step", response_model=StepResponse)
def step(action: Action):
    global env_state
    env_state["step_count"] += 1
    reward = 0.0
    system_msg = "Action executed."
    
    # Process actions
    if action.command == "query_crm":
        env_state["crm_checked"] = True
        db_record = MOCK_CRM_DB.get(env_state["current_task"], {})
        system_msg = f"CRM DATA RETRIEVED: {db_record}"
        reward += 0.3
    elif action.command == "issue_refund":
        env_state["refund_issued"] = True
        system_msg = "Refund API called successfully."
        reward += 0.1 
    elif action.command == "reply":
        env_state["reply_sent"] = action.args.get("text", "")
        env_state["ticket_status"] = "closed"
        system_msg = "Reply sent to customer."
    elif action.command == "escalate":
        env_state["escalated"] = True
        env_state["ticket_status"] = "escalated"
        system_msg = "Ticket escalated to Tier 2."
    else:
        system_msg = f"Unknown command '{action.command}'."
        reward -= 0.1

    # Grade the step
    score, done = evaluate_task(env_state["current_task"], env_state)
    
    if done:
        reward += score
    elif env_state["step_count"] >= 5:
        done = True

    return StepResponse(
        observation={"system_message": system_msg},
        reward=reward,
        done=done,
        info={"ticket_status": env_state["ticket_status"]}
    )

# 4. OpenEnv Validation Entry Point
def main():
    """Entry point for the OpenEnv validator and multi-mode deployment."""
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()