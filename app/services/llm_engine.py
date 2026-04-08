import os
from dataclasses import dataclass
from typing import Dict

from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.services.nlp import detect_priority_signals, preprocess_text


@dataclass
class AnalysisResult:
    urgency: str
    impact: str
    systemic_risk: str
    confidence: float
    explanation: str


def _rule_based_analysis(text: str, db: Session) -> AnalysisResult:
    """Analyze complaint content using deterministic keyword rules and db heuristic."""
    text_lower = text.lower()

    # Detect signals via patterns
    signals = detect_priority_signals(text)
    urgency = signals["urgency"]
    impact = signals["impact"]
    systemic_risk = signals["systemic_risk"]

    # Use DB similarity to strengthen systemic detection.
    if db is not None and systemic_risk == "not_detected":
        matching = (
            db.query(Complaint)
            .filter(Complaint.text.ilike(f"%{text_lower[:50]}%"))
            .count()
        )
        if matching > 1:
            systemic_risk = "detected"

    # Base confidence 0.4 + 0.2 for each triggered dimension
    confidence = 0.4
    if urgency in ["critical", "high"]:
        confidence += 0.2
    if impact == "high":
        confidence += 0.2
    if systemic_risk == "detected":
        confidence += 0.2
    confidence = min(confidence, 1.0)

    explanation = (
        f"Detected urgency terms: {signals['signals']['urgency_matches']} ; "
        f"impact terms: {signals['signals']['impact_matches']} ; "
        f"systemic terms: {signals['signals']['systemic_matches']} ; "
        f"DB systemic boost: {systemic_risk}."
    )

    return AnalysisResult(
        urgency=urgency,
        impact=impact,
        systemic_risk=systemic_risk,
        confidence=confidence,
        explanation=explanation,
    )


def analyze_complaint(text: str, db: Session = None) -> Dict:
    """Main analyze entrypoint for LLM-based analysis with rule-based fallback."""
    if not text or not text.strip():
        raise ValueError("Complaint text must be non-empty")

    nlp_data = preprocess_text(text)

    analysis = None
    # Try LLM analysis if API key is available
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key

            prompt = (
                "Determine urgency, impact, systemic risk for a complaint. "
                "Return JSON with urgency: low/medium/high/critical, impact: low/medium/high, "
                "systemic_risk: detected/not_detected, confidence: 0-1, explanation: text. "
                f"Complaint: \"{text}\""
            )

            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.2,
            )
            raw = response.choices[0].text.strip()
            import json
            parsed = json.loads(raw)

            if parsed.get("confidence", 0) >= 0.5:
                analysis = AnalysisResult(
                    urgency=parsed.get("urgency", "low"),
                    impact=parsed.get("impact", "low"),
                    systemic_risk=parsed.get("systemic_risk", "not_detected"),
                    confidence=float(parsed.get("confidence", 0.0)),
                    explanation=parsed.get("explanation", ""),
                )
        except Exception as e:
            # Log locally and fallback to rule-based.
            print("LLM analysis failed, fallback to rule-based:", e)
            analysis = None

    if analysis is None:
        analysis = _rule_based_analysis(text, db)

    # If low confidence, use rule-based as extra safety
    if analysis.confidence < 0.45:
        fallback = _rule_based_analysis(text, db)
        if fallback.confidence > analysis.confidence:
            analysis = fallback

    return {
        "urgency": analysis.urgency,
        "impact": analysis.impact,
        "systemic_risk": analysis.systemic_risk,
        "confidence": analysis.confidence,
        "explanation": analysis.explanation,
        "entities": nlp_data["entities"],
        "keywords": nlp_data["keywords"],
    }
