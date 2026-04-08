import os
import re
from typing import Dict, List, Optional
import spacy
from spacy.lang.en import English

# Load spaCy model if available; fallback to simple tokenizer.
try:
    nlp_model = spacy.load("en_core_web_sm")
except Exception:
    nlp_model = English()
    nlp_model.add_pipe("sentencizer")

NEGATION_WORDS = {"not", "no", "never", "isn't", "wasn't"}

urgency_phrases = [
    "needs immediate action", "risk of explosion", "emergency situation", "critical issue"
]
impact_phrases = [
    "data breach", "financial loss", "payment failure", "security compromise"
]
systemic_phrases = [
    "all users affected", "system-wide failure", "across multiple regions", "widespread issue"
]

context_map = {
    "gas leakage": {"urgency": "critical", "impact": "high", "systemic_risk": "detected"},
    "data breach": {"impact": "high", "systemic_risk": "detected"},
    "payment failure": {"impact": "high"},
    "slow internet": {"impact": "low"},
    "power outage": {"urgency": "high", "systemic_risk": "detected"},
}

# Reference sentences for semantic similarity
reference_sentences = {
    "system is completely down and users cannot access the service": {
        "urgency": "critical", "impact": "high", "systemic_risk": "detected"
    },
    "all users are affected and the issue is spreading across regions": {
        "urgency": "high", "impact": "high", "systemic_risk": "detected"
    },
    "a single user is experiencing a cosmetic bug with no functional impact": {
        "urgency": "low", "impact": "low", "systemic_risk": "not_detected"
    },
}

# Singleton for Sentence Transformer model
_sentence_transformer_model = None

def get_sentence_transformer_model():
    """Lazy load the Sentence Transformer model."""
    global _sentence_transformer_model
    if _sentence_transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            _sentence_transformer_model = None
    return _sentence_transformer_model


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


def detect_negation(tokens: List[str], keyword_index: int) -> bool:
    """Return True if keyword at keyword_index is negated within a 3-word window before it."""
    start = max(0, keyword_index - 3)
    for i in range(start, keyword_index):
        if tokens[i] in NEGATION_WORDS:
            return True
    return False


def match_phrases(text_lower: str, phrase_list: List[str]) -> List[str]:
    """Return all phrases from phrase_list found in text_lower."""
    return [phrase for phrase in phrase_list if phrase in text_lower]


def detect_priority_signals(text: str) -> Dict[str, object]:
    """Detect systemic risk, impact, and urgency signals from complaint text."""
    text_lower = text.lower().strip()
    if not text_lower:
        raise ValueError("Complaint text must be non-empty")

    tokens = re.findall(r"\w+", text_lower)

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

    systemic_risk = "not_detected"
    impact = "low"
    urgency = "low"
    detected_context = None
    explanation: List[str] = []

    # Phrase-level detection
    matched_urgency_phrases = match_phrases(text_lower, urgency_phrases)
    matched_impact_phrases = match_phrases(text_lower, impact_phrases)
    matched_systemic_phrases = match_phrases(text_lower, systemic_phrases)

    if matched_urgency_phrases:
        urgency = "critical"
        explanation.extend([f"Matched urgency phrase '{p}'" for p in matched_urgency_phrases])

    if matched_impact_phrases:
        impact = "high"
        explanation.extend([f"Matched impact phrase '{p}'" for p in matched_impact_phrases])

    if matched_systemic_phrases:
        systemic_risk = "detected"
        explanation.extend([f"Matched systemic phrase '{p}'" for p in matched_systemic_phrases])

    # Direct keyword detection with negation handling
    for idx, token in enumerate(tokens):
        if token in urgency_terms and not detect_negation(tokens, idx):
            urgency = "critical"
            explanation.append(f"Detected urgency keyword '{token}'")
        elif token in urgency_terms and detect_negation(tokens, idx):
            explanation.append(f"Negated urgency keyword '{token}' ignored")

        if token in high_impact_terms and not detect_negation(tokens, idx):
            impact = "high"
            explanation.append(f"Detected impact keyword '{token}'")
        elif token in high_impact_terms and detect_negation(tokens, idx):
            explanation.append(f"Negated impact keyword '{token}' ignored")

        if token in systemic_terms and not detect_negation(tokens, idx):
            systemic_risk = "detected"
            explanation.append(f"Detected systemic keyword '{token}'")
        elif token in systemic_terms and detect_negation(tokens, idx):
            explanation.append(f"Negated systemic keyword '{token}' ignored")

    # Context mapping overrides
    for context_key, context_values in context_map.items():
        if context_key in text_lower:
            detected_context = context_key
            explanation.append(f"Detected '{context_key}' → context map applied")
            if "urgency" in context_values:
                urgency = context_values["urgency"]
            if "impact" in context_values:
                impact = context_values["impact"]
            if "systemic_risk" in context_values:
                systemic_risk = context_values["systemic_risk"]
            break

    # Semantic similarity detection
    semantic_urgency = None
    semantic_impact = None
    semantic_systemic = None
    semantic_explanation = ""
    model = get_sentence_transformer_model()
    if model is not None:
        try:
            from sentence_transformers import util

            ref_texts = list(reference_sentences.keys())
            ref_embeddings = model.encode(ref_texts, convert_to_tensor=True)
            text_embedding = model.encode(text_lower, convert_to_tensor=True)

            similarities = util.cos_sim(text_embedding, ref_embeddings)[0]
            most_sim, most_idx = float(similarities.max()), int(similarities.argmax())

            if most_sim > 0.70:  # Threshold for meaningful match
                top_ref = ref_texts[most_idx]
                semantic_signals = reference_sentences[top_ref]
                semantic_urgency = semantic_signals["urgency"]
                semantic_impact = semantic_signals["impact"]
                semantic_systemic = semantic_signals["systemic_risk"]
                semantic_explanation = f"Semantic match: '{top_ref}' (similarity: {most_sim:.2f}) → urgency={semantic_urgency}, impact={semantic_impact}, systemic={semantic_systemic}"
                explanation.append(semantic_explanation)
            else:
                explanation.append("Semantic similarity below threshold; no adjustment")
        except Exception as e:
            explanation.append(f"Semantic processing failed: {str(e)}")
    else:
        explanation.append("Sentence Transformers not available; skipped semantic similarity")

    # Collect signal details
    signals = {
        "systemic_matches": [term for term in systemic_terms if term in text_lower] + matched_systemic_phrases,
        "impact_matches": [term for term in high_impact_terms if term in text_lower] + matched_impact_phrases,
        "urgency_matches": [term for term in urgency_terms if term in text_lower] + matched_urgency_phrases,
    }

    return {
        "systemic_risk": systemic_risk,
        "impact": impact,
        "urgency": urgency,
        "signals": signals,
        "detected_context": detected_context,
        "explanation": "\n".join(explanation) if explanation else "",
        "semantic_urgency": semantic_urgency,
        "semantic_impact": semantic_impact,
        "semantic_systemic": semantic_systemic,
        "semantic_explanation": semantic_explanation,
    }

