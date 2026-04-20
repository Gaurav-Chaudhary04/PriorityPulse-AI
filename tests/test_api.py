#!/usr/bin/env python3
"""
Simple test script to demonstrate the Context-Aware AI API.
Run this after starting the FastAPI server.
"""

import requests

BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Testing Context-Aware Prioritization AI API")
    print("=" * 50)

    print("\n1. Creating a complaint...")
    complaint_data = {
        "text": "My payment via Stripe keeps failing.",
        "product_category": "Payments",
        "problem_description": "Every time I try to complete the transaction, it hangs and then logs me out. My account balance shows missing funds."
    }

    try:
        response = requests.post(f"{BASE_URL}/complaints", json=complaint_data)
        response.raise_for_status()
        complaint_id = response.json()["complaint_id"]
        print(f"✅ Complaint created with ID: {complaint_id}")

        print("\n2. Analyzing complaint...")
        analysis_payload = {
            "complaint_id": complaint_id,
            "active_system_incidents": ["Stripe API Degradation and Timeout Issues"]
        }
        analysis_response = requests.post(f"{BASE_URL}/analyse", json=analysis_payload)
        analysis_response.raise_for_status()
        analysis = analysis_response.json()
        print("✅ Analysis completed:")
        print(f"   - Context Analysis: {analysis['context_analysis'][:80]}...")
        scores = analysis['scores']
        print(f"   - Urgency: {scores['urgency']:.2f} | Impact: {scores['impact']:.2f}")
        print(f"   - Systemic Risk: {scores['systemic_risk']:.2f} | Incident Match: {scores['incident_match']:.2f}")

        print("\n3. Calculating priority score...")
        score_response = requests.post(f"{BASE_URL}/score", json=analysis_payload)
        score_response.raise_for_status()
        score_data = score_response.json()
        print("✅ Scoring completed:")
        print(f"   - Score: {score_data['score']}/100")
        print(f"   - Level: {score_data['level']}")
        print(f"   - Escalation: {score_data['escalation_flag']}")

        print("\n4. Getting explainable reasoning...")
        explanation_response = requests.get(f"{BASE_URL}/explanation/{complaint_id}")
        explanation_response.raise_for_status()
        print("✅ Explanation retrieved successfully!")

        print("\n5. Getting dashboard metrics...")
        dashboard_response = requests.get(f"{BASE_URL}/dashboard")
        dashboard_response.raise_for_status()
        dashboard = dashboard_response.json()
        print("✅ Dashboard data:")
        print(f"   - Total complaints: {dashboard['total_complaints']}")
        print(f"   - High priority: {dashboard['high_priority_count']}")
        print(f"   - Escalated cases: {dashboard['escalated_cases_count']}")

        print("\n🎉 All tests passed! The SRE context framework is running.")

    except requests.exceptions.HTTPError as e:
        print(f"❌ API test failed with HTTP status: {e.response.status_code}")
        print(f"   Response Body: {e.response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    test_api()