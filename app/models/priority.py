from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class Priority(Base):
    """ORM model storing priority calculations and explainability details."""

    __tablename__ = "priorities"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False)
    score = Column(Float, nullable=False)
    level = Column(String, nullable=False)
    escalation_flag = Column(Boolean, nullable=False)
    urgency = Column(Float, nullable=False)
    impact = Column(Float, nullable=False)
    systemic_risk = Column(Float, nullable=False)
    incident_match = Column(Float, nullable=False, default=0.0)
    context_analysis = Column(Text, nullable=True)
    explanation_json = Column(Text, nullable=False)

    complaint = relationship("Complaint", back_populates="priority")
