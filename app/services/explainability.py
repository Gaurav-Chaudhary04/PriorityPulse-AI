from typing import Dict


def build_explainable_output(analysis: Dict[str, object], score_data: Dict[str, object]) -> Dict[str, object]:
    """Create structured explainability reasons for each decision component."""
    urgency_reason = f"LLM-style analysis assigned urgency '{analysis['urgency']}' based on keyword and entity signals."
    impact_reason = f"Impact is '{analysis['impact']}' due to keywords and risk indicators present in complaint text."

    systemic_reason = (
        "Systemic risk detected from repeated issues in complaint history."
        if analysis.get("systemic_risk") == "detected"
        else "No systemic risk pattern detected in historical complaints."
    )

    return {
        "urgency_reason": urgency_reason,
        "impact_reason": impact_reason,
        "systemic_risk_reason": systemic_reason,
        "score": score_data["score"],
        "level": score_data["level"],
        "escalation_flag": score_data["escalation_flag"],
    }
