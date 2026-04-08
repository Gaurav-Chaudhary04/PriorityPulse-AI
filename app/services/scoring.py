from typing import Dict, Tuple


def compute_score(urgency: str, impact: str, systemic_risk: str) -> Dict[str, object]:
    """Compute priority score and derive level/escalation.

    Args:
        urgency (str): one of low, medium, high, critical.
        impact (str): one of low, medium, high.
        systemic_risk (str): detected or not_detected.

    Returns:
        Dict[str, object]: score, level, escalation.
    """
    urgency_values = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
    impact_values = {"low": 0.25, "medium": 0.5, "high": 1.0}
    systemic_values = {"not_detected": 0.0, "detected": 1.0}

    # explicit weights
    urgency_weight = 0.4
    impact_weight = 0.3
    systemic_risk_weight = 0.3

    u_val = urgency_values.get(urgency, 0.25)
    i_val = impact_values.get(impact, 0.25)
    s_val = systemic_values.get(systemic_risk, 0.0)

    # Weighted formula (urgency 40%, impact 30%, systemic risk 30%)
    base_score = u_val * 100 * urgency_weight + i_val * 100 * impact_weight + s_val * 100 * systemic_risk_weight

    # If systemic risk detected, amplify final score
    if systemic_risk == "detected":
        score = min(round(base_score * 1.5, 2), 100.0)
    else:
        score = round(base_score, 2)

    # Determine priority level with systemic guarantee
    if systemic_risk == "detected":
        level = "critical" if score >= 75 else "high"
    else:
        if score >= 85:
            level = "critical"
        elif score >= 65:
            level = "high"
        elif score >= 40:
            level = "medium"
        else:
            level = "low"

    escalation = True if systemic_risk == "detected" else level in {"high", "critical"} or score >= 70

    return {
        "score": score,
        "level": level,
        "escalation_flag": escalation,
    }


def format_priority_response(score_data: Dict[str, object], analysis: Dict[str, object]) -> Dict[str, object]:
    """Merge analysis and score into response format."""
    return {
        "score": score_data["score"],
        "level": score_data["level"],
        "escalation_flag": score_data["escalation_flag"],
        "urgency": analysis["urgency"],
        "impact": analysis["impact"],
        "systemic_risk": analysis["systemic_risk"],
        "confidence": analysis.get("confidence", 0.0),
        "explanation": analysis.get("explanation", ""),
    }
