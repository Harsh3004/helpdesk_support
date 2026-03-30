def get_initial_ticket(task_id: str) -> str:
    if task_id == "task_refund":
        return "Hi Support, I just checked my credit card statement and I was charged $29.99 twice on the 1st of the month. Can you please refund the duplicate charge?"
    elif task_id == "task_reject_outdated":
        return "Hello, I purchased a lifetime license for your software 2 years ago. I don't really use it anymore. Please issue a full refund to my original payment method."
    elif task_id == "escalation":
        return "YOUR UPDATE DELETED MY ENTIRE PROJECT DATABASE!! I DEMAND A FULL REFUND PLUS $500 FOR THE HOURS OF WORK I LOST! IF YOU DON'T FIX THIS I AM INVOLVING MY LAWYER. GET ME A MANAGER NOW!"
    return "Generic support ticket."

def evaluate_task(task_id: str, state: dict) -> tuple[float, bool]:
    score = 0.0
    done = state["ticket_status"] in ["closed", "escalated"]

    if not done:
        return 0.0, False

    # --- EASY: ky Standard Refund ---
    if task_id == "task_refund":
        if state["refund_issued"] and state["ticket_status"] == "closed":
            score = 1.0 if state["crm_checked"] else 0.5 
        elif state["refund_issued"]:
            score = 0.2
            
    # --- MEDIUM: Policy Enforcement ---
    elif task_id == "task_reject_outdated":
        if state["refund_issued"]:
            score = 0.0
        elif state["ticket_status"] == "closed":
            reply = state["reply_sent"].lower()
            if any(word in reply for word in ["policy", "window", "time", "years", "cannot"]):
                score = 1.0 if state["crm_checked"] else 0.7 # Penalize guessing
            else:
                score = 0.6
                
    # --- HARD: Crisis Escalation ---
    elif task_id == "escalation":
        if state["refund_issued"]:
            score = 0.0
        elif state["escalated"]:
            score = 1.0 # In a crisis, immediate escalation without CRM is okay
        elif state["ticket_status"] == "closed":
            score = 0.2

    return score, done