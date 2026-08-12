from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class EvidenceItem(BaseModel):
    text: str
    url: str

class CustomerOutput(BaseModel):
    primary_customer: str
    secondary_customer: Optional[str] = None
    reasoning: str
    evidence: List[EvidenceItem]
    confidence: float

class SwitchingTriggersOutput(BaseModel):
    trigger_list: List[str]
    explanation: str
    evidence: List[EvidenceItem]
    confidence: float

class EarlyAdoptersOutput(BaseModel):
    early_adopter_description: str
    why: str
    evidence: List[EvidenceItem]
    confidence: float

class AlternativesOutput(BaseModel):
    alternatives: List[Dict[str, Any]]
    confidence: float

class ProblemItem(BaseModel):
    problem: str
    frequency: str
    severity: str
    supporting_evidence: List[EvidenceItem]

class ProblemsOutput(BaseModel):
    problems: List[ProblemItem]
    confidence: float

class SolutionOutput(BaseModel):
    value_proposition: str
    solution_summary: str
    assumptions: List[str]
    risks: List[str]
    confidence: float
