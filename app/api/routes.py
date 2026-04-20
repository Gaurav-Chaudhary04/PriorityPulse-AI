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
    ScoreBreakdown
)
from app.services.llm_engine import analyze_complaint
from app.services.scoring import compute_score, format_priority_response

router = APIRouter()


@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(payload: ComplaintRequest, db: Session = Depends(get_db)) -> ComplaintResponse:
    """Store a new complaint and return its ID."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Complaint text cannot be empty.")

    complaint = Complaint(
        text=payload.text.strip(),
        product_category=payload.product_category,
        problem_description=payload.problem_description,
        created_at=datetime.utcnow()
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return ComplaintResponse(complaint_id=complaint.id)


@router.post("/analyse", response_model=AnalysisResponse)
def analyse_complaint(payload: AnalysisRequest, db: Session = Depends(get_db)) -> AnalysisResponse:
    """Run NLP preprocessing and SRE-constrained LLM analysis on a complaint."""
    try:
        complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        analysis = analyze_complaint(complaint, payload.active_system_incidents, db)

        return AnalysisResponse(
            priority=analysis.priority,
            scores=ScoreBreakdown(
                systemic_risk=analysis.systemic_risk_score,
                urgency=analysis.urgency_score,
                impact=analysis.impact_score,
                incident_match=analysis.incident_match_score
            ),
            context_analysis=analysis.context_analysis,
            explanation=analysis.explanation,
            entities=analysis.entities,
            keywords=analysis.keywords,
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Crash details: {traceback.format_exc()}")


@router.post("/score", response_model=ScoreResponse)
def score_complaint(payload: ScoreRequest, db: Session = Depends(get_db)) -> ScoreResponse:
    """Calculate explicit composite score, persist priority, return score details."""
    complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    analysis = analyze_complaint(complaint, payload.active_system_incidents, db)
    score_data = compute_score(analysis)

    existing_priority = db.query(Priority).filter(Priority.complaint_id == payload.complaint_id).first()
    
    if existing_priority:
        existing_priority.score = score_data["score"]
        existing_priority.level = score_data["level"]
        existing_priority.escalation_flag = score_data["escalation_flag"]
        existing_priority.urgency = analysis.urgency_score
        existing_priority.impact = analysis.impact_score
        existing_priority.systemic_risk = analysis.systemic_risk_score
        existing_priority.incident_match = analysis.incident_match_score
        existing_priority.context_analysis = analysis.context_analysis
        existing_priority.explanation_json = score_data["explanation"]
    else:
        priority = Priority(
            complaint_id=complaint.id,
            score=score_data["score"],
            level=score_data["level"],
            escalation_flag=score_data["escalation_flag"],
            urgency=analysis.urgency_score,
            impact=analysis.impact_score,
            systemic_risk=analysis.systemic_risk_score,
            incident_match=analysis.incident_match_score,
            context_analysis=analysis.context_analysis,
            explanation_json=score_data["explanation"],
        )
        db.add(priority)

    db.commit()

    merged = format_priority_response(score_data, analysis)

    return ScoreResponse(**merged)


@router.get("/explanation/{complaint_id}", response_model=ExplanationResponse)
def get_explanation(complaint_id: int, db: Session = Depends(get_db)) -> ExplanationResponse:
    """Return explicit explainability metrics for priority decision."""
    priority = db.query(Priority).filter(Priority.complaint_id == complaint_id).first()
    if not priority:
        raise HTTPException(status_code=404, detail="Priority record not found. Call /score first.")

    return ExplanationResponse(
        context_analysis=priority.context_analysis or "No explicit context analysis stored.",
        reasoning=priority.explanation_json,
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

    high_priority_count = db.query(Priority).filter(Priority.level.in_(["HIGH", "CRITICAL"])).count()
    escalated_cases_count = db.query(Priority).filter(Priority.escalation_flag.is_(True)).count()

    from sqlalchemy import case, desc

    priority_order = case(
        (Priority.level == "CRITICAL", 1),
        (Priority.level == "HIGH", 2),
        (Priority.level == "MEDIUM", 3),
        (Priority.level == "LOW", 4),
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
            "problem_description": complaint.problem_description or "",
            "category": complaint.product_category or "System",
            "priority": priority.level if priority else "LOW",
            "score": priority.score if priority else 0.0,
            "timestamp": complaint.created_at.isoformat() + "Z",
            "escalation_flag": priority.escalation_flag if priority else False,
            "metrics": {
                "urgency": priority.urgency if priority else 0.0,
                "impact": priority.impact if priority else 0.0,
                "systemic_risk": priority.systemic_risk if priority else 0.0,
                "incident_match": priority.incident_match if priority else 0.0
            },
            "context_analysis": priority.context_analysis if priority else "No analysis available",
            "explanation": priority.explanation_json if priority else "No explanation available"
        })

    return DashboardResponse(
        total_complaints=total,
        high_priority_count=high_priority_count,
        escalated_cases_count=escalated_cases_count,
        latest_complaints=latest_list,
    )
