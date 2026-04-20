import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.services.nlp import calculate_systemic_risk_score, calculate_incident_match_score, preprocess_text


@dataclass
class AnalysisResult:
    priority: str
    urgency_score: float
    impact_score: float
    systemic_risk_score: float
    incident_match_score: float
    context_analysis: str
    explanation: str
    entities: List[str]
    keywords: List[str]


def _rule_based_analysis(complaint: Complaint, systemic_risk_score: float, incident_match_score: float) -> AnalysisResult:
    """Fallback if LLM fails: estimate urgency and impact via basic keywords."""
    text_lower = (complaint.text + " " + (complaint.problem_description or "")).lower()

    # Very naive rule based urgency and impact for fallback
    high_impact_terms = ["payment failure", "transaction failed", "fraud", "breach", "security", "data loss", "down", "outage"]
    urgency_terms = ["urgent", "immediately", "critical", "asap", "emergency", "broken", "now"]

    urgency_score = 0.0
    impact_score = 0.0

    if any(t in text_lower for t in urgency_terms):
        urgency_score = 0.8
    if any(t in text_lower for t in high_impact_terms):
        impact_score = 0.8
        
    if "cosmetic" in text_lower or "color" in text_lower:
        impact_score = 0.1
        urgency_score = 0.1

    nlp_data = preprocess_text(complaint.text)

    # Basic fallback priority estimation
    base_score = 0.5 * ((urgency_score + impact_score) / 2) + 0.5 * ((systemic_risk_score + incident_match_score) / 2)
    priority = "LOW"
    if base_score > 0.4:
        priority = "MEDIUM"
    if base_score > 0.65:
        priority = "HIGH"
    if base_score > 0.85:
        priority = "CRITICAL"

    return AnalysisResult(
        priority=priority,
        urgency_score=urgency_score,
        impact_score=impact_score,
        systemic_risk_score=systemic_risk_score,
        incident_match_score=incident_match_score,
        context_analysis="Rule-based fallback engaged due to LLM failure.",
        explanation=f"Fallback rules detected urgency={urgency_score}, impact={impact_score}.",
        entities=nlp_data["entities"],
        keywords=nlp_data["keywords"],
    )


def analyze_complaint(complaint: Complaint, active_system_incidents: List[str], db: Session = None) -> AnalysisResult:
    """Main analyze entrypoint for LLM-based context-aware analysis."""
    
    # Deterministic calculation step
    systemic_risk_score = 0.0
    if db:
        systemic_risk_score = calculate_systemic_risk_score(complaint, db, hours_window=24, similarity_threshold=0.55)
        
    incident_match_score = calculate_incident_match_score(complaint.text, complaint.problem_description, active_system_incidents)
    
    nlp_data = preprocess_text(complaint.text)
    
    from app.config import settings
    
    # Ask LLM safely using getattr in case attributes are deleted from config
    openai_key = getattr(settings, "OPENAI_API_KEY", None)
    groq_key = getattr(settings, "GROQ_API_KEY", None)
    
    if groq_key or openai_key:
        if groq_key:
            from groq import Groq
            client = Groq(api_key=groq_key)
            model_name = "llama-3.1-8b-instant"
        else:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            model_name = "gpt-4"
        
        system_prompt = (
            "You are an intelligent complaint prioritization engine designed for a large-scale software system. "
            "Your goal is to assess the priority of a complaint based ONLY on system-level risk and operational impact. "
            "You must NOT consider customer identity, customer tier, or any user-based importance. "
            "You must NOT estimate systemic risk or incident correlation. These are provided as factual inputs. "
            "Be strict. Do not overestimate priority unless there is strong evidence of system-wide impact."
        )
        
        user_prompt = {
            "task": "Analyze the complaint and return pure json.",
            "instructions": [
                "Focus ONLY on system-level factors.",
                "Do NOT use customer tier or user identity in any way.",
                "Base your decision on the following dimensions:"
            ],
            "priority_factors": {
                "urgency": "Does the language indicate immediate failure, blockage, or critical disruption?",
                "impact": "How critical is the affected feature (e.g., payments > login > UI)?"
            },
            "scoring_guidelines": {
                "CRITICAL": "System-wide failure or high-volume similar complaints affecting core functionality",
                "HIGH": "Major feature broken with strong urgency signals or multiple similar complaints",
                "MEDIUM": "Moderate issue with limited scope or fewer similar complaints",
                "LOW": "Minor issue, cosmetic problem, or isolated case"
            },
            "input": {
                "complaint_text": complaint.text,
                "problem_description": complaint.problem_description or "None provided",
                "context": {
                    "product_category": complaint.product_category or "Unknown",
                    "deterministic_systemic_risk_score": round(systemic_risk_score, 2),
                    "deterministic_incident_match_score": round(incident_match_score, 2),
                }
            },
            "output_format": {
                "context_analysis": "Short structured understanding of the issue and affected system",
                "scores": {
                    "urgency": "0-1 float",
                    "impact": "0-1 float"
                },
                "priority": "LOW | MEDIUM | HIGH | CRITICAL",
                "reasoning": "Clear explanation focusing on system impact, NOT user importance"
            }
        }

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_prompt)}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            raw = response.choices[0].message.content.strip()
            
            parsed = json.loads(raw)
            
            # Map LLM results
            urgency_score = float(parsed["scores"]["urgency"])
            impact_score = float(parsed["scores"]["impact"])
            priority = str(parsed["priority"]).upper()
            
            if priority not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                priority = "LOW"
                
            return AnalysisResult(
                priority=priority,
                urgency_score=urgency_score,
                impact_score=impact_score,
                systemic_risk_score=systemic_risk_score,
                incident_match_score=incident_match_score,
                context_analysis=str(parsed.get("context_analysis") or ""),
                explanation=str(parsed.get("reasoning") or ""),
                entities=nlp_data["entities"],
                keywords=nlp_data["keywords"],
            )
        except Exception as e:
            print("LLM analysis failed, fallback to rule-based:", e)
            return _rule_based_analysis(complaint, systemic_risk_score, incident_match_score)
    else:
        return _rule_based_analysis(complaint, systemic_risk_score, incident_match_score)
