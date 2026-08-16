from app.services.troubleshooter import analyze_issue


def test_analysis_falls_back_to_rule_based_without_llm_configured():
    analysis = analyze_issue("My Windows laptop cannot connect to Wi-Fi.")

    assert analysis.category == "network"
    assert analysis.generated_by == "rule_based"
    assert analysis.escalation_required is False
    assert len(analysis.recommended_steps) > 0


def test_analysis_grounds_response_with_knowledge_base_sources():
    analysis = analyze_issue("My Windows laptop cannot connect to Wi-Fi.")

    assert len(analysis.sources) > 0
    assert any("network" in s.source for s in analysis.sources)
    assert all(0 <= s.relevance_score <= 1 for s in analysis.sources)


def test_system_crash_analysis_includes_commands_and_escalation():
    analysis = analyze_issue("My laptop keeps crashing with a blue screen.")

    assert analysis.category == "system"
    assert analysis.escalation_required is True
    assert "sfc /scannow" in analysis.relevant_commands


def test_llm_augmented_path_used_when_configured(monkeypatch):
    """When an LLM is configured, its output should override the rule-based text."""
    from app.services import troubleshooter

    def fake_generate(**kwargs):
        return {
            "probable_cause": "LLM-generated cause.",
            "recommended_steps": ["LLM step one.", "LLM step two."],
        }

    monkeypatch.setattr(troubleshooter, "generate_grounded_analysis", fake_generate)

    analysis = analyze_issue("My Windows laptop cannot connect to Wi-Fi.")

    assert analysis.generated_by == "llm"
    assert analysis.probable_cause == "LLM-generated cause."
    assert analysis.recommended_steps == ["LLM step one.", "LLM step two."]
