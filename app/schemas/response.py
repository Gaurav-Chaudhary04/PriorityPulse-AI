from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ComplaintResponse(BaseModel):
    complaint_id: int


class AnalysisResponse(BaseModel):
    urgency: str
    impact: str
    systemic_risk: str
    confidence: float
    explanation: str
    entities: List[str]
    keywords: List[str]


class ScoreResponse(BaseModel):
    score: float
    level: str
    escalation_flag: bool
    urgency: str
    impact: str
    systemic_risk: str
    confidence: float
    explanation: str


class ExplanationResponse(BaseModel):
    urgency_reason: str
    impact_reason: str
    systemic_risk_reason: str
    score: float
    level: str
    escalation_flag: bool


class DashboardResponse(BaseModel):
    total_complaints: int
    high_priority_count: int
    escalated_cases_count: int
    latest_complaints: Optional[List[dict]] = None
