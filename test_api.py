#!/usr/bin/env python3
"""
Simple test script to demonstrate the Complaint Prioritization AI API.
Run this after starting the FastAPI server.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Testing Complaint Prioritization AI API")
    print("=" * 50)

    # Test 1: Create a complaint
    print("\n1. Creating a complaint...")
    complaint_data = {
        "text": "Urgent: My account was hacked and money was stolen. Security breach detected immediately!"
    }

    try:
        response = requests.post(f"{BASE_URL}/complaints", json=complaint_data)
        response.raise_for_status()
        result = response.json()
        complaint_id = result["complaint_id"]
        print(f"✅ Complaint created with ID: {complaint_id}")

        # Test 2: Analyze the complaint
        print("\n2. Analyzing complaint...")
        analysis_response = requests.post(f"{BASE_URL}/analyse", json={"complaint_id": complaint_id})
        analysis_response.raise_for_status()
        analysis = analysis_response.json()
        print("✅ Analysis completed:")
        print(f"   - Urgency: {analysis['urgency']}")
        print(f"   - Impact: {analysis['impact']}")
        print(f"   - Systemic Risk: {analysis['systemic_risk']}")
        print(f"   - Confidence: {analysis['confidence']:.2f}")
        print(f"   - Keywords: {', '.join(analysis['keywords'][:5])}")

        # Test 3: Score the complaint
        print("\n3. Calculating priority score...")
        score_response = requests.post(f"{BASE_URL}/score", json={"complaint_id": complaint_id})
        score_response.raise_for_status()
        score_data = score_response.json()
        print("✅ Scoring completed:")
        print(f"   - Score: {score_data['score']}/100")
        print(f"   - Level: {score_data['level']}")
        print(f"   - Escalation: {score_data['escalation_flag']}")

        # Test 4: Get explanation
        print("\n4. Getting explainable reasoning...")
        explanation_response = requests.get(f"{BASE_URL}/explanation/{complaint_id}")
        explanation_response.raise_for_status()
        explanation = explanation_response.json()
        print("✅ Explanation retrieved:")
        print(f"   - Urgency reason: {explanation['urgency_reason'][:60]}...")
        print(f"   - Impact reason: {explanation['impact_reason'][:60]}...")
        print(f"   - Systemic risk reason: {explanation['systemic_risk_reason'][:60]}...")

        # Test 5: Get dashboard metrics
        print("\n5. Getting dashboard metrics...")
        dashboard_response = requests.get(f"{BASE_URL}/dashboard")
        dashboard_response.raise_for_status()
        dashboard = dashboard_response.json()
        print("✅ Dashboard data:")
        print(f"   - Total complaints: {dashboard['total_complaints']}")
        print(f"   - High priority: {dashboard['high_priority_count']}")
        print(f"   - Escalated cases: {dashboard['escalated_cases_count']}")

        print("\n🎉 All tests passed! The system is working correctly.")
        print("\n📊 Open dashboard at: http://localhost:8000/dashboard-page")
        print("📚 API docs at: http://localhost:8000/docs")

    except requests.exceptions.RequestException as e:
        print(f"❌ API test failed: {e}")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        return False

    return True

if __name__ == "__main__":
    success = test_api()
    if not success:
        exit(1)