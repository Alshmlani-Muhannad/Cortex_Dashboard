"""Tests for the AI analysis service."""
from app.services.ai_service import AIService, get_disclaimer
from app.schemas.analysis import AIAnalysisResult


def test_mock_analysis_structure():
    svc = AIService()
    svc.demo_mode = True
    result, aid, is_demo, cached = svc.analyze("al1", None, {"alert_name": "x"}, language="en")
    AIAnalysisResult(**result.model_dump())  # validates schema
    assert is_demo is True
    assert cached is False
    assert "synthetic" in result.summary.lower() or "demo" in result.summary.lower()


def test_ai_distinguishes_evidence_from_hypothesis():
    svc = AIService()
    svc.demo_mode = True
    result, _, _, _ = svc.analyze("al1", None, {
        "alert_name": "Mimikatz detection",
        "description": "lsass access",
        "severity": "high",
    }, language="en")
    # The structured result must include hypothesis_flags and limitations
    assert isinstance(result.hypothesis_flags, list)
    assert isinstance(result.limitations, list)
    assert result.confidence <= 1.0


def test_disclaimer_both_languages():
    assert "advisory" in get_disclaimer("en").lower()
    assert "استشاري" in get_disclaimer("ar") or "استشاري" in get_disclaimer("ar")


def test_secrets_not_in_prompt(monkeypatch):
    svc = AIService()
    svc.demo_mode = True
    captured = {}
    orig = svc._mock_analysis

    def fake(alert_id, incident_id, evidence, language):
        captured["evidence"] = evidence
        return orig(alert_id, incident_id, evidence, language)

    svc._mock_analysis = fake
    svc.analyze("al1", None, {"alert_name": "x", "api_key": "SECRET123", "password": "pw"}, language="en")
    assert "api_key" not in captured["evidence"]
    assert "password" not in captured["evidence"]
    assert captured["evidence"].get("alert_name") == "x"