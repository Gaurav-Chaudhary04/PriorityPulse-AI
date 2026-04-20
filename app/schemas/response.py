from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ComplaintResponse(BaseModel):
    complaint_id: int


class ScoreBreakdown(BaseModel):
    systemic_risk: float
    urgency: float
    impact: float
    incident_match: float


class AnalysisResponse(BaseModel):
    priority: str
    scores: ScoreBreakdown
    context_analysis: str
    explanation: str
    entities: List[str] = []
    keywords: List[str] = []


class ScoreResponse(BaseModel):
    score: float
    level: str
    escalation_flag: bool
    advanced_scores: ScoreBreakdown
    context_analysis: str
    explanation: str


class ExplanationResponse(BaseModel):
    context_analysis: str
    reasoning: str
    score: float
    level: str
    escalation_flag: bool


class DashboardResponse(BaseModel):
    total_complaints: int
    high_priority_count: int
    escalated_cases_count: int
    latest_complaints: Optional[List[dict]] = None
