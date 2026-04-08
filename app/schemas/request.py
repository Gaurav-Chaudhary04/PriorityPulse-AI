from pydantic import BaseModel


class ComplaintRequest(BaseModel):
    text: str


class AnalysisRequest(BaseModel):
    complaint_id: int


class ScoreRequest(BaseModel):
    complaint_id: int
