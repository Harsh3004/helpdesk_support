from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
import random
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="Enterprise Support World Model v2.0")

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Enterprise Support World Model v2.0</title>
            <style>
                body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; line-height: 1.6; }
                .container { max-width: 900px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
                h1 { color: #3b82f6; border-bottom: 2px solid #334155; padding-bottom: 10px; }
                .status-badge { background: #10b981; color: white; padding: 4px 12px; border-radius: 9999px; font-size: 0.8rem; vertical-align: middle; }
                .section { margin-top: 25px; }
                code { background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #fbbf24; font-family: monospace; }
                .btn { display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin-top: 20px; font-weight: 600; }
                .btn:hover { background: #2563eb; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Enterprise Support World Model <span class="status-badge">Live</span></h1>
                <p>Welcome to the <strong>L1 Support Automation Environment</strong> for the Meta PyTorch Hackathon.</p>
                
                <div class="section">
                    <h3>Environment Architecture</h3>
                    <ul>
                        <li><strong>Action Space:</strong> 10 Professional Enterprise Actions (CRM, Stripe, Jira, Auth0 integration).</li>
                        <li><strong>Observation:</strong> Partial observability requiring multi-step investigation.</li>
                        <li><strong>Reward Logic:</strong> Continuous dense reward with efficiency penalties.</li>
                    </ul>
                </div>

                <div class="section">
                    <h3>API Documentation</h3>
                    <p>The environment endpoints are fully documented via Swagger UI. You can test <code>/reset</code> and <code>/step</code> directly in the browser.</p>
                    <a href="/docs" class="btn">View Interactive API Docs</a>
                </div>

                <div class="section">
                    <h3>Technical Manifest</h3>
                    <p>State Management: <code>Session-based isolation</code><br>
                    Scenario Engine: <code>Procedural Generation</code></p>
                </div>
            </div>
        </body>
    </html>
    """

app = FastAPI(title="Enterprise Support World Model v2.0")

# --- 1. SCHEMAS (Pydantic models for strict validation) ---
class Action(BaseModel):
    session_id: str
    command: str
    args: Dict[str, Any] = {}

class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]

# --- 2. PROCEDURAL ENGINE (Reasoning Gym Pattern) ---
class ScenarioGenerator:
    """Generates infinite variations of enterprise support scenarios."""
    TIERS = ["Free", "Standard", "Premium", "Enterprise"]
    RISK_LEVELS = ["Low", "Medium", "High", "Critical"]
    
    @staticmethod
    def generate(task_type: str):
        # Generates unique, non-repetitive data for every reset
        amount = round(random.uniform(10.0, 500.0), 2)
        return {
            "task_type": task_type,
            "customer_name": f"User_{random.randint(1000, 9999)}",
            "tier": random.choice(ScenarioGenerator.TIERS),
            "amount": amount,
            "auth0_risk": random.choice(ScenarioGenerator.RISK_LEVELS),
            "jira_outage": random.choice([True, False]),
            "stripe_status": random.choice(["Settled", "Pending", "Failed"])
        }

# --- 3. SESSION MANAGER (Calendar Env Pattern) ---
sessions: Dict[str, Dict[str, Any]] = {}

@app.post("/reset")
def reset(task_type: str = "random"):
    session_id = str(uuid.uuid4())
    types = ["refund", "billing_dispute", "access_issue", "outage"]
    if task_type == "random":
        task_type = random.choice(types)
        
    data = ScenarioGenerator.generate(task_type)
    
    sessions[session_id] = {
        "data": data,
        "step_count": 0,
        "revealed": set(),
        "ticket_status": "Open",
        "total_reward": 0.0
    }
    
    # Initial Observation (Partial Info)
    obs = {
        "ticket": f"Support request regarding {task_type}. Amount: ${data['amount']}",
        "session_id": session_id,
        "available_tools": ["query_crm", "check_stripe", "verify_identity", "check_outages"]
    }
    return obs

@app.post("/step", response_model=StepResponse)
def step(action: Action):
    s_id = action.session_id
    if s_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[s_id]
    session["step_count"] += 1
    data = session["data"]
    cmd = action.command
    
    # Action Logic with tool dependencies
    obs_msg = ""
    reward_delta = -0.01 # Dense Penalty: Every step costs a tiny bit of "compute"
    
    if cmd == "query_crm":
        session["revealed"].add("crm")
        obs_msg = f"CRM: Customer Tier: {data['tier']}. Name: {data['customer_name']}."
    elif cmd == "check_stripe":
        session["revealed"].add("stripe")
        obs_msg = f"Stripe: Transaction of ${data['amount']} is {data['stripe_status']}."
    elif cmd == "verify_identity":
        session["revealed"].add("auth0")
        obs_msg = f"Auth0: Security Risk Level: {data['auth0_risk']}."
    elif cmd == "check_outages":
        session["revealed"].add("jira")
        obs_msg = f"Jira: Active outages: {data['jira_outage']}."
    
    # Decision Terminal Actions
    done = False
    if cmd in ["approve_refund", "deny_request", "escalate"]:
        done = True
        # Advanced Multi-Component Reward Calculation
        reward_delta = calculate_reward(cmd, session)
        
    session["total_reward"] += reward_delta
    
    return StepResponse(
        observation={"message": obs_msg, "revealed_info": list(session["revealed"])},
        reward=reward_delta,
        done=done,
        info={"current_step": session["step_count"], "total_score": session["total_reward"]}
    )

def calculate_reward(cmd, session):
    # Expert Reward Formula: R = R_correct + R_investigation - R_efficiency
    data = session["data"]
    score = 0.1 # Base
    
    # 1. Correctness Logic
    if cmd == "approve_refund" and data["task_type"] == "refund" and data["stripe_status"] == "Settled":
        score += 0.5
    elif cmd == "escalate" and data["auth0_risk"] in ["High", "Critical"]:
        score += 0.5
        
    # 2. Investigation Quality (Bonus for using necessary tools)
    if "crm" in session["revealed"] and "stripe" in session["revealed"]:
        score += 0.2
        
    # 3. Efficiency Penalty
    score -= (session["step_count"] * 0.05)
    
    return round(max(0.01, min(0.99, score)), 2)