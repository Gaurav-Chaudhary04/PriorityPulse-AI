from typing import List, Optional
from pydantic import BaseModel


class ComplaintRequest(BaseModel):
    text: str
    product_category: Optional[str] = None
    problem_description: Optional[str] = None


class AnalysisRequest(BaseModel):
    complaint_id: int
    active_system_incidents: List[str] = []


class ScoreRequest(BaseModel):
    complaint_id: int
    active_system_incidents: List[str] = []
