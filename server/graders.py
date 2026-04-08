"""
Deterministic Grader for Helpdesk Support
"""

def evaluate_task(task_id: str, env_state: dict):
    """
    Evaluates the environment state and returns a score strictly between (0, 1).
    Minimum score: 0.1
    Maximum score: 0.9
    """
    score = 0.1  
    done = False

    if task_id == "task_refund":
        if env_state.get("ticket_status") == "closed":
            done = True
            if env_state.get("refund_issued"):
                score += 0.5
            if env_state.get("crm_checked"):
                score += 0.2
            if env_state.get("reply_sent"):
                score += 0.1
                
    elif task_id == "task_reject_outdated":
        if env_state.get("ticket_status") == "closed":
            done = True
            if not env_state.get("refund_issued"):
                score += 0.5
            if env_state.get("crm_checked"):
                score += 0.2
            if env_state.get("reply_sent"):
                score += 0.1

    elif task_id == "escalation":
        if env_state.get("ticket_status") == "escalated":
            done = True
            if env_state.get("escalated"):
                score += 0.5
            if not env_state.get("refund_issued"):
                score += 0.2
            if env_state.get("crm_checked"):
                score += 0.1

    # Final organic clamp just to be mathematically bulletproof
    score = max(0.01, min(0.99, score))
    
    return score, done
