import os
import re
from typing import Dict, List

import spacy
from spacy.lang.en import English

# Load spaCy model if available; fallback to simple tokenizer.
try:
    nlp_model = spacy.load("en_core_web_sm")
except Exception:
    nlp_model = English()
    nlp_model.add_pipe("sentencizer")


def preprocess_text(text: str) -> Dict[str, List[str]]:
    """Extract entities and keywords from a complaint text.

    Args:
        text (str): Raw complaint text.

    Returns:
        Dict[str, List[str]]: entities and keywords.
    """
    if not text or not text.strip():
        raise ValueError("Complaint text must be non-empty")

    if hasattr(nlp_model, "pipe") and nlp_model.meta.get("name") == "en_core_web_sm":
        doc = nlp_model(text)
        entities = [f"{ent.text}:{ent.label_}" for ent in doc.ents]
        keywords = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]
    else:
        # Simple fallback using regex
        entities = re.findall(r"\b[A-Z][a-z]+\b", text)
        tokens = re.findall(r"\w+", text.lower())
        stop_words = {"the", "and", "or", "a", "an", "to", "of", "in", "for", "on", "with", "is", "are"}
        keywords = [tok for tok in tokens if tok not in stop_words and len(tok) > 2]

    # Reduce duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return {
        "entities": entities,
        "keywords": unique_keywords,
    }


def detect_priority_signals(text: str) -> Dict[str, object]:
    """Detect systemic risk, impact, and urgency signals from complaint text."""
    text_lower = text.lower()

    systemic_terms = [
        "many users", "multiple users", "everyone", "all users", "system-wide",
        "platform issue", "widespread", "affecting users", "global issue"
    ]
    high_impact_terms = [
        "payment failure", "transaction failed", "money", "funds", "charge", "billing",
        "fraud", "security breach", "data loss", "account compromise"
    ]
    urgency_terms = [
        "urgent", "immediately", "critical", "asap", "as soon as possible",
        "emergency", "down", "broken"
    ]

    systemic_risk = any(term in text_lower for term in systemic_terms)
    impact = any(term in text_lower for term in high_impact_terms)
    urgency = any(term in text_lower for term in urgency_terms)

    return {
        "systemic_risk": "detected" if systemic_risk else "not_detected",
        "impact": "high" if impact else "low",
        "urgency": "critical" if urgency else "low",
        "signals": {
            "systemic_matches": [term for term in systemic_terms if term in text_lower],
            "impact_matches": [term for term in high_impact_terms if term in text_lower],
            "urgency_matches": [term for term in urgency_terms if term in text_lower],
        },
    }

