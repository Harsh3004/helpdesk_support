"""
Enterprise Helpdesk Deterministic Grader
"""

def evaluate_task(task_data: dict, env_state: dict):
    """
    Evaluates the environment state and returns a score strictly between (0, 1).
    Reward Structure:
    - Base effort: 0.1
    - Correct decision: +0.6
    - Proper investigation (querying APIs): +0.2
    - Efficiency penalty: -0.05 per unnecessary step
    """
    if env_state["ticket_status"] == "open" and env_state["step_count"] < 8:
        return 0.1, False # Not done yet
        
    score = 0.1  # Base score to strictly avoid 0.0
    done = True

    # 1. Correct Decision Component
    if env_state["final_action"] == task_data["true_verdict"]:
        score += 0.6
    
    # 2. Proper Investigation Component (Did they use the tools?)
    revealed = env_state["revealed_info"]
    investigation_bonus = 0.0
    
    if task_data["true_verdict"] == "issue_refund" and revealed.get("stripe") and revealed.get("crm"):
        investigation_bonus = 0.2
    elif task_data["true_verdict"] == "apply_credit" and revealed.get("jira"):
        investigation_bonus = 0.2
    elif task_data["true_verdict"] == "escalate_t2" and revealed.get("auth0"):
        investigation_bonus = 0.2
    elif task_data["true_verdict"] == "escalate_legal" and revealed.get("crm"):
        investigation_bonus = 0.2
    elif len(revealed) > 0: # General bonus for using tools
        investigation_bonus = 0.1
        
    score += investigation_bonus

    # 3. Efficiency Component
    # 3-4 steps is ideal. Penalize slightly if they spam tools.
    if env_state["step_count"] > 4:
        score -= 0.05 * (env_state["step_count"] - 4)

    # Final organic clamp just to be mathematically bulletproof
    score = max(0.01, min(0.99, score))
    
    return score, done