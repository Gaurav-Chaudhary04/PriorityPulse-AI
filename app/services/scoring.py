from typing import Dict, List
from app.services.llm_engine import AnalysisResult


def compute_score(analysis: AnalysisResult) -> Dict[str, object]:
    """Compute explicit continuous priority score using SRE hybrid framework."""
    u = analysis.urgency_score
    i = analysis.impact_score
    s = analysis.systemic_risk_score
    m = analysis.incident_match_score

    # SRE Hybrid formula with meaning-weighted dimensions
    final_score = (
        0.35 * s + 
        0.15 * m + 
        0.25 * u + 
        0.25 * i
    )
    final_score_scaled = min(round(final_score * 100, 2), 100.0)

    # Establish Priority Thresholds heavily tied to the calculated final score
    if final_score >= 0.75:
        level = "CRITICAL"
    elif final_score >= 0.55:
        level = "HIGH"
    elif final_score >= 0.35:
        level = "MEDIUM"
    else:
        level = "LOW"

    escalation_flag = level == "CRITICAL" or final_score_scaled >= 75

    explanation = (
        f"Hybrid Formulation: LLM [U:{u:.2f}, I:{i:.2f}] + "
        f"Deterministic [S:{s:.2f}, M:{m:.2f}]. "
        f"Net Score: {final_score_scaled}."
        f"\n\nLLM Reasoning: {analysis.explanation}"
    )

    return {
        "score": final_score_scaled,
        "level": level,
        "escalation_flag": escalation_flag,
        "explanation": explanation
    }


def format_priority_response(score_data: Dict[str, object], analysis: AnalysisResult) -> Dict[str, object]:
    """Format final output mapping into schema structure."""
    return {
        "score": score_data["score"],
        "level": score_data["level"],
        "escalation_flag": score_data["escalation_flag"],
        "advanced_scores": {
            "urgency": analysis.urgency_score,
            "impact": analysis.impact_score,
            "systemic_risk": analysis.systemic_risk_score,
            "incident_match": analysis.incident_match_score,
        },
        "context_analysis": analysis.context_analysis,
        "explanation": score_data["explanation"]
    }
