from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_health_endpoint_reports_feature_flags():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "llm_enabled" in body
    assert "db_enabled" in body


def test_analyze_endpoint_returns_grounded_analysis():
    response = client.post(
        "/support/analyze",
        json={"issue": "My Windows laptop cannot connect to Wi-Fi."},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["issue"] == "My Windows laptop cannot connect to Wi-Fi."
    analysis = body["analysis"]
    assert analysis["category"] == "network"
    assert analysis["severity"] == "medium"
    assert analysis["escalation_required"] is False
    assert len(analysis["sources"]) > 0


def test_analyze_endpoint_rejects_too_short_issue():
    response = client.post("/support/analyze", json={"issue": "hi"})
    assert response.status_code == 422


def test_knowledge_base_search_endpoint():
    response = client.get(
        "/knowledge-base/search", params={"q": "printer not printing"}
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert any("hardware" in r["source"] for r in results)
