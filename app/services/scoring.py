from typing import Dict, Optional, List


def compute_score(
    urgency: str,
    impact: str,
    systemic_risk: str,
    detected_context: Optional[str] = None,
    semantic_urgency: Optional[str] = None,
    semantic_impact: Optional[str] = None,
    semantic_systemic: Optional[str] = None,
    semantic_weight: float = 0.3,
) -> Dict[str, object]:
    """Compute priority score and derive level/escalation with hybrid semantic + keyword scoring.

    Args:
        urgency (str): Keyword-based urgency.
        impact (str): Keyword-based impact.
        systemic_risk (str): Keyword-based systemic risk.
        detected_context (Optional[str]): Context key applied from NLP.
        semantic_urgency (Optional[str]): Semantic-based urgency.
        semantic_impact (Optional[str]): Semantic-based impact.
        semantic_systemic (Optional[str]): Semantic-based systemic risk.
        semantic_weight (float): Weight for semantic signals (0.0 to 1.0).

    Returns:
        Dict[str, object]: score, level, escalation_flag, explanation.
    """
    explanation: List[str] = []

    urgency_allowed = {"low", "medium", "high", "critical"}
    impact_allowed = {"low", "medium", "high"}
    systemic_allowed = {"detected", "not_detected"}

    urgency_norm = (urgency or "").lower()
    impact_norm = (impact or "").lower()
    systemic_norm = (systemic_risk or "").lower()

    if urgency_norm not in urgency_allowed:
        explanation.append(f"Invalid urgency '{urgency}' normalized to 'low'")
        urgency_norm = "low"
    if impact_norm not in impact_allowed:
        explanation.append(f"Invalid impact '{impact}' normalized to 'low'")
        impact_norm = "low"
    if systemic_norm not in systemic_allowed:
        explanation.append(f"Invalid systemic_risk '{systemic_risk}' normalized to 'not_detected'")
        systemic_norm = "not_detected"

    urgency_values = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
    impact_values = {"low": 0.25, "medium": 0.5, "high": 1.0}
    systemic_values = {"not_detected": 0.0, "detected": 1.0}

    urgency_weight = 0.4
    impact_weight = 0.3
    systemic_risk_weight = 0.3

    # Compute keyword-based score
    u_val_kw = urgency_values[urgency_norm]
    i_val_kw = impact_values[impact_norm]
    s_val_kw = systemic_values[systemic_norm]
    base_score_kw = u_val_kw * 100 * urgency_weight + i_val_kw * 100 * impact_weight + s_val_kw * 100 * systemic_risk_weight

    # Compute semantic-based score if available
    base_score_sem = None
    if semantic_urgency and semantic_impact and semantic_systemic:
        u_val_sem = urgency_values.get(semantic_urgency.lower(), 0.25)
        i_val_sem = impact_values.get(semantic_impact.lower(), 0.25)
        s_val_sem = systemic_values.get(semantic_systemic.lower(), 0.0)
        base_score_sem = u_val_sem * 100 * urgency_weight + i_val_sem * 100 * impact_weight + s_val_sem * 100 * systemic_risk_weight
        explanation.append(f"Semantic signals: urgency={semantic_urgency}, impact={semantic_impact}, systemic={semantic_systemic}")

    # Hybrid base score: weighted average of keyword and semantic
    if base_score_sem is not None:
        base_score = base_score_kw * (1 - semantic_weight) + base_score_sem * semantic_weight
        explanation.append(f"Hybrid base score: keyword {base_score_kw:.2f} + semantic {base_score_sem:.2f} (weight {semantic_weight}) = {base_score:.2f}")
    else:
        base_score = base_score_kw
        explanation.append(f"Keyword-only base score: {base_score:.2f}")

    multiplier = 1.0
    if systemic_norm == "detected":
        if urgency_norm in {"high", "critical"}:
            multiplier = 1.3
            explanation.append("Systemic risk detected + high/critical urgency → multiplier 1.3 applied")
        else:
            multiplier = 1.2
            explanation.append("Systemic risk detected → multiplier 1.2 applied")
    else:
        explanation.append("No systemic risk multiplier applied")

    score = base_score * multiplier

    if detected_context:
        score += 10
        explanation.append(f"Detected context '{detected_context}' → context bonus +10")

    score = min(round(score, 2), 100.0)

    if score <= 30:
        level = "low"
    elif score <= 55:
        level = "medium"
    elif score <= 75:
        level = "high"
    else:
        level = "critical"

    escalation_flag = (
        systemic_norm == "detected" or urgency_norm == "critical" or score >= 70
    )

    explanation.append(f"Final score {score} → level '{level}'")
    if escalation_flag:
        explanation.append("Escalation triggered")
    else:
        explanation.append("No escalation")

    return {
        "score": score,
        "level": level,
        "escalation_flag": escalation_flag,
        "explanation": explanation,
        "urgency": urgency_norm,
        "impact": impact_norm,
        "systemic_risk": systemic_norm,
    }


def format_priority_response(score_data: Dict[str, object], analysis: Dict[str, object]) -> Dict[str, object]:
    """Merge analysis and score into response format."""
    score_explanation = []
    if isinstance(analysis.get("explanation"), list):
        score_explanation.extend(analysis["explanation"])
    elif isinstance(analysis.get("explanation"), str) and analysis.get("explanation"):
        score_explanation.extend(analysis["explanation"].split("\n"))

    if isinstance(score_data.get("explanation"), list):
        score_explanation.extend(score_data["explanation"])
    elif isinstance(score_data.get("explanation"), str) and score_data.get("explanation"):
        score_explanation.extend(score_data["explanation"].split("\n"))

    return {
        "score": score_data["score"],
        "level": score_data["level"],
        "escalation_flag": score_data["escalation_flag"],
        "urgency": analysis["urgency"],
        "impact": analysis["impact"],
        "systemic_risk": analysis["systemic_risk"],
        "confidence": analysis.get("confidence", 0.0),
        "explanation": "\n".join(score_explanation),
    }
