---
title: Helpdesk Support Env
emoji: 🎫
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Ticket Flow Env: Level 1 Support Simulation

## Overview
`ticket-flow-env` is an OpenEnv-compliant environment simulating a real-world Customer Support triage system. AI agents act as Level 1 Support Engineers and must read incoming customer tickets, navigate company billing policies, and decide whether to issue refunds, reply to the customer, or escalate to human managers.

**Motivation:** Most RL environments focus on games or web-scraping. This environment tests an LLM's ability to balance customer satisfaction with strict corporate policy enforcement and crisis management.

## Action & Observation Spaces
- **Action Space:** JSON format requiring a `command` (`query_crm`, `issue_refund`, `reply`, `escalate`) and `args` (e.g., `{"text": "message"}`).
- **Observation Space:** JSON containing the `ticket_content`, `system_message` (feedback from the previous action), and `is_resolved` boolean.

## Tasks & Difficulty
1. **`task_refund` (Easy):** A standard duplicate charge. The agent must check the CRM, issue a refund, and close the ticket.
2. **`task_reject_outdated` (Medium):** A refund request for a 2-year-old order. The agent must deny the refund based on a 30-day policy and reply politely. 
3. **`escalation` (Hard):** A furious customer threatening legal action. The agent must NOT issue a refund and must safely escalate to a manager.

## Setup & Usage
1. Clone the repository and install dependencies: `pip install -r requirements.txt`
2. Run the environment locally: `uvicorn server.app:app --port 7860`
3. Run the baseline evaluation: `python inference.py`