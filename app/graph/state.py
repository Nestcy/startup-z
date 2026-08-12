from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class WorkflowState(BaseModel):
    idea: str
    customer: Optional[Dict[str, Any]] = None
    switching_triggers: Optional[Dict[str, Any]] = None
    early_adopters: Optional[Dict[str, Any]] = None
    alternatives: Optional[Dict[str, Any]] = None
    problems: Optional[Dict[str, Any]] = None
    solution: Optional[Dict[str, Any]] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)  # conversation buffer / memory
    founder_feedback: Dict[str, Any] = Field(default_factory=dict)
