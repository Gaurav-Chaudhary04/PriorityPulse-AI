from app.services.llm_engine import analyze_complaint
from app.services.scoring import compute_score

# This file does not require active DB for rule-based classification.
# For a real DB test, pass an actual session with known complaints.

test_cases = [
    {
        "text": "Many users including me are unable to complete payments. The transaction fails every time. This affects multiple users.",
        "expected_systemic": "detected",
        "expected_impact": "high",
        "expected_urgency": "critical",
    },
    {
        "text": "I can't log in to my account and need help ASAP. Something is broken for me.",
        "expected_systemic": "not_detected",
        "expected_impact": "low",
        "expected_urgency": "critical",
    },
    {
        "text": "Small typo on the billing page, not urgent." ,
        "expected_systemic": "not_detected",
        "expected_impact": "low",
        "expected_urgency": "low",
    },
    {
        "text": "Payment failure during checkout, funds are held but purchase does not complete. This is likely a platform issue and affects all users.",
        "expected_systemic": "detected",
        "expected_impact": "high",
        "expected_urgency": "critical",
    },
    {
        "text": "There is a suggestion to improve the UI for selecting payment methods.",
        "expected_systemic": "not_detected",
        "expected_impact": "low",
        "expected_urgency": "low",
    },
]

for case in test_cases:
    analysis = analyze_complaint(case["text"])
    score_data = compute_score(analysis["urgency"], analysis["impact"], analysis["systemic_risk"])

    print("\n=== CASE ===")
    print("Text:", case["text"])
    print("Signals:", analysis)
    print("Score:", score_data)

    if analysis["systemic_risk"] != case["expected_systemic"]:
        print("[FAIL] systemic risk mismatch")
    if analysis["impact"] != case["expected_impact"]:
        print("[FAIL] impact mismatch")
    if analysis["urgency"] != case["expected_urgency"]:
        print("[FAIL] urgency mismatch")

    if analysis["systemic_risk"] == "detected" and not score_data["escalation_flag"]:
        print("[FAIL] systemic risk should force escalation")

    print("----")

print("Done")
