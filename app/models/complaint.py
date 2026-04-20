from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class Complaint(Base):
    """ORM model for complaint text items."""

    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    product_category = Column(String, nullable=True)
    problem_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    priority = relationship("Priority", back_populates="complaint", uselist=False)
