"""
Pydantic Data Models for Enterprise Support Environment v2.0
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List

class EnterpriseAction(BaseModel):
    session_id: str = Field(description="Unique session identifier assigned during /reset")
    command: str = Field(description="The enterprise tool or decision action to execute")
    args: Dict[str, Any] = Field(default_factory=dict, description="Optional arguments for the command")

class EnterpriseObservation(BaseModel):
    message: str = Field(description="System response from the executed tool")
    revealed_info: List[str] = Field(description="List of systems the agent has successfully queried")

class StepResponse(BaseModel):
    observation: EnterpriseObservation
    reward: float = Field(description="Continuous reward bounded between 0.01 and 0.99")
    done: bool = Field(description="True if episode has reached a terminal state")
    info: Dict[str, Any] = Field(description="Additional debugging and scoring metrics")