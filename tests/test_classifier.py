from app.services.classifier import classify


def test_wifi_issue_classified_as_network():
    result = classify("My Windows laptop cannot connect to Wi-Fi.")
    assert result.category == "network"
    assert result.severity == "medium"
    assert result.confidence == 0.90
    assert result.escalation_required is False
    assert "ipconfig /all" in result.relevant_commands


def test_login_issue_classified_as_authentication():
    result = classify(
        "I cannot login to my account because my password is not working."
    )
    assert result.category == "authentication"
    assert result.severity == "medium"
    assert result.escalation_required is False


def test_performance_issue_classified_correctly():
    result = classify("My laptop is very slow and has poor performance.")
    assert result.category == "performance"
    assert result.severity == "medium"
    assert result.escalation_required is False


def test_printer_issue_classified_as_hardware():
    result = classify("My printer is not printing documents.")
    assert result.category == "hardware"
    assert result.severity == "low"
    assert result.confidence == 0.85
    assert result.escalation_required is False


def test_system_crash_requires_escalation():
    result = classify("My laptop keeps crashing with a blue screen.")
    assert result.category == "system"
    assert result.severity == "high"
    assert result.confidence == 0.80
    assert result.escalation_required is True
    assert result.escalation_reason is not None


def test_unclassified_issue_falls_back_to_general_and_escalates():
    result = classify("Something strange is happening with my system.")
    assert result.category == "general"
    assert result.severity == "unknown"
    assert result.escalation_required is True
