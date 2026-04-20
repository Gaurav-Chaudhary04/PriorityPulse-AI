import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import spacy
from spacy.lang.en import English
from sqlalchemy.orm import Session
from app.models.complaint import Complaint

# Load spaCy model if available; fallback to simple tokenizer.
try:
    nlp_model = spacy.load("en_core_web_sm")
except Exception:
    nlp_model = English()
    nlp_model.add_pipe("sentencizer")

# Singleton for Sentence Transformer model
_sentence_transformer_model = None

def get_sentence_transformer_model():
    """Lazy load the Sentence Transformer model."""
    global _sentence_transformer_model
    if _sentence_transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Failed to load sentence_transformers: {e}")
            _sentence_transformer_model = None
    return _sentence_transformer_model


def preprocess_text(text: str) -> Dict[str, List[str]]:
    if not text or not text.strip():
        return {"entities": [], "keywords": []}

    if hasattr(nlp_model, "pipe") and nlp_model.meta.get("name") == "en_core_web_sm":
        doc = nlp_model(text)
        entities = [f"{ent.text}:{ent.label_}" for ent in doc.ents]
        keywords = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]
    else:
        entities = re.findall(r"\b[A-Z][a-z]+\b", text)
        tokens = re.findall(r"\w+", text.lower())
        stop_words = {"the", "and", "or", "a", "an", "to", "of", "in", "for", "on", "with", "is", "are"}
        keywords = [tok for tok in tokens if tok not in stop_words and len(tok) > 2]

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


def calculate_systemic_risk_score(current_complaint: Complaint, db: Session, hours_window: int = 24, similarity_threshold: float = 0.55) -> float:
    """Calculate time-decayed systemic risk based on semantic similarity to recent complaints."""
    import math
    model = get_sentence_transformer_model()
    if model is None:
        return 0.0

    target_text = current_complaint.text
    if current_complaint.problem_description:
        target_text += " " + current_complaint.problem_description

    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=hours_window)
    
    # Query recent complaints from DB (exclude current one)
    recent_complaints = db.query(Complaint).filter(Complaint.created_at >= cutoff_time).filter(Complaint.id != current_complaint.id).all()
    
    if not recent_complaints:
        return 0.0

    try:
        from sentence_transformers import util
        
        target_embedding = model.encode(target_text, convert_to_tensor=True)
        texts_to_compare = []
        for c in recent_complaints:
            combo = c.text
            if c.problem_description:
                combo += " " + c.problem_description
            texts_to_compare.append(combo)

        compare_embeddings = model.encode(texts_to_compare, convert_to_tensor=True)
        similarities = util.cos_sim(target_embedding, compare_embeddings)[0]

        weighted_sum = 0.0
        
        cutoff_1hr = now - timedelta(hours=1)
        cutoff_7hr = now - timedelta(hours=7)
        recent_1hr_count = 0
        prev_6hr_count = 0

        for idx, sim in enumerate(similarities):
            sim_val = float(sim)
            if sim_val > similarity_threshold:
                c = recent_complaints[idx]
                hours_ago = (now - c.created_at).total_seconds() / 3600.0
                
                # Exponential decay
                decay_weight = math.exp(-0.1 * hours_ago)
                contribution = sim_val * decay_weight
                weighted_sum += contribution
                
                if c.created_at >= cutoff_1hr:
                    recent_1hr_count += 1
                elif c.created_at >= cutoff_7hr:
                    prev_6hr_count += 1

        risk_score = min(1.0, weighted_sum / 5.0)
        
        # Spike detection
        avg_previous_6hr_count = prev_6hr_count / 6.0
        spike = recent_1hr_count / max(avg_previous_6hr_count, 1.0)
        
        if spike > 2:
            risk_score += 0.2
            
        return min(risk_score, 1.0)
    except Exception as e:
        print(f"Error calculating systemic risk: {e}")
        return 0.0


def calculate_incident_match_score(text: str, problem_description: Optional[str], active_incidents: List[str]) -> float:
    """Calculate max semantic similarity between the complaint and a list of active incidents."""
    if not active_incidents:
        return 0.0
    
    model = get_sentence_transformer_model()
    if model is None:
        return 0.0

    target_text = text
    if problem_description:
        target_text += " " + problem_description

    try:
        from sentence_transformers import util
        target_embedding = model.encode(target_text, convert_to_tensor=True)
        incident_embeddings = model.encode(active_incidents, convert_to_tensor=True)
        
        similarities = util.cos_sim(target_embedding, incident_embeddings)[0]
        max_sim = float(similarities.max())
        
        if max_sim < 0.4:
            return 0.0
            
        if max_sim > 0.8:
            return 1.0
        
        return min(max_sim, 1.0)
    except Exception as e:
        print(f"Error calculating incident match score: {e}")
        return 0.0
