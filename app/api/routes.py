from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.complaint import Complaint
from app.models.priority import Priority
from app.schemas.request import AnalysisRequest, ComplaintRequest, ScoreRequest
from app.schemas.response import (
    AnalysisResponse,
    ComplaintResponse,
    DashboardResponse,
    ExplanationResponse,
    ScoreResponse,
)
from app.services.explainability import build_explainable_output
from app.services.llm_engine import analyze_complaint
from app.services.scoring import compute_score, format_priority_response

router = APIRouter()


@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(payload: ComplaintRequest, db: Session = Depends(get_db)) -> ComplaintResponse:
    """Store a new complaint and return its ID."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Complaint text cannot be empty.")

    complaint = Complaint(text=payload.text.strip(), created_at=datetime.utcnow())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return ComplaintResponse(complaint_id=complaint.id)


@router.post("/analyse", response_model=AnalysisResponse)
def analyse_complaint(payload: AnalysisRequest, db: Session = Depends(get_db)) -> AnalysisResponse:
    """Run NLP preprocessing and LLM-style analysis on a complaint text."""
    complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    analysis = analyze_complaint(complaint.text, db)

    return AnalysisResponse(
        urgency=analysis["urgency"],
        impact=analysis["impact"],
        systemic_risk=analysis["systemic_risk"],
        confidence=analysis["confidence"],
        explanation=analysis["explanation"],
        entities=analysis.get("entities", []),
        keywords=analysis.get("keywords", []),
    )


@router.post("/score", response_model=ScoreResponse)
def score_complaint(payload: ScoreRequest, db: Session = Depends(get_db)) -> ScoreResponse:
    """Calculate composite score, persist priority, return score details."""
    complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Analyze exists as dependency.
    analysis = analyze_complaint(complaint.text, db)
    score_data = compute_score(analysis["urgency"], analysis["impact"], analysis["systemic_risk"])

    explanation_data = build_explainable_output(analysis, score_data)

    existing_priority = db.query(Priority).filter(Priority.complaint_id == payload.complaint_id).first()
    explanation_json = {
        "analysis": analysis,
        "explainability": explanation_data,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if existing_priority:
        existing_priority.score = score_data["score"]
        existing_priority.level = score_data["level"]
        existing_priority.escalation_flag = score_data["escalation_flag"]
        existing_priority.urgency = analysis["urgency"]
        existing_priority.impact = analysis["impact"]
        existing_priority.systemic_risk = analysis["systemic_risk"]
        existing_priority.explanation_json = str(explanation_json)
    else:
        priority = Priority(
            complaint_id=complaint.id,
            score=score_data["score"],
            level=score_data["level"],
            escalation_flag=score_data["escalation_flag"],
            urgency=analysis["urgency"],
            impact=analysis["impact"],
            systemic_risk=analysis["systemic_risk"],
            explanation_json=str(explanation_json),
        )
        db.add(priority)

    db.commit()

    merged = format_priority_response(score_data, analysis)

    return ScoreResponse(**merged)


@router.get("/explanation/{complaint_id}", response_model=ExplanationResponse)
def get_explanation(complaint_id: int, db: Session = Depends(get_db)) -> ExplanationResponse:
    """Return structured explainability for priority decision."""
    priority = db.query(Priority).filter(Priority.complaint_id == complaint_id).first()
    if not priority:
        raise HTTPException(status_code=404, detail="Priority record not found. Call /score first.")

    # Interpret stored explanation_json if needed
    # We store string here, but not parse to avoid dependency.
    return ExplanationResponse(
        urgency_reason=f"Urgency assigned as '{priority.urgency}'.",
        impact_reason=f"Impact assigned as '{priority.impact}'.",
        systemic_risk_reason=(
            "Systemic risk detected based on historical patterns."
            if priority.systemic_risk == "detected"
            else "No systemic risk patterns detected."
        ),
        score=priority.score,
        level=priority.level,
        escalation_flag=priority.escalation_flag,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    limit: str = Query("5", regex=r"^(all|\d+)$", description="Number of complaints to return; use 'all' for no limit"),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Return summary metrics for complaint prioritization."""
    total = db.query(Complaint).count()

    high_priority_count = db.query(Priority).filter(Priority.level.in_(["high", "critical"])).count()
    escalated_cases_count = db.query(Priority).filter(Priority.escalation_flag.is_(True)).count()

    from sqlalchemy import case, desc

    # Multi-level priority sort: Critical > High > Medium > Low;
    # within same priority by score desc, then newest timestamp desc.
    priority_order = case(
        (Priority.level == "critical", 1),
        (Priority.level == "high", 2),
        (Priority.level == "medium", 3),
        (Priority.level == "low", 4),
        else_=5,
    )

    query = (
        db.query(Complaint, Priority)
        .outerjoin(Priority, Complaint.id == Priority.complaint_id)
        .order_by(priority_order, desc(Priority.score), Complaint.created_at.desc())
    )

    if limit != "all":
        limit_num = int(limit)
        if limit_num <= 0:
            raise HTTPException(status_code=400, detail="Limit must be positive or 'all'.")
        query = query.limit(limit_num)

    prioritized = query.all()

    latest_list = []
    for complaint, priority in prioritized:
        latest_list.append({
            "id": complaint.id,
            "text": complaint.text,
            "priority": priority.level if priority else "low",
            "score": priority.score if priority else 0.0,
            "timestamp": complaint.created_at.isoformat(),
        })

    return DashboardResponse(
        total_complaints=total,
        high_priority_count=high_priority_count,
        escalated_cases_count=escalated_cases_count,
        latest_complaints=latest_list,
    )
