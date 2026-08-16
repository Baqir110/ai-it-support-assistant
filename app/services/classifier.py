"""Deterministic issue classifier.

This stays rule-based (rather than delegated to the LLM) on purpose: category,
severity, and escalation policy are business rules a support team wants to
control precisely and test with plain unit tests, not something that should
silently drift because a model's phrasing changed. The LLM (when enabled) is
used downstream only to write the natural-language explanation and steps,
grounded in retrieved documentation - it never picks the category or severity.
"""

from dataclasses import dataclass, field


@dataclass
class ClassificationRule:
    category: str
    severity: str
    confidence: float
    keywords: list[str]
    probable_cause: str
    recommended_steps: list[str]
    escalation_required: bool
    escalation_reason: str | None = None
    relevant_commands: list[str] = field(default_factory=list)


RULES: list[ClassificationRule] = [
    ClassificationRule(
        category="network",
        severity="medium",
        confidence=0.90,
        keywords=["wifi", "wi-fi", "internet", "network", "connection", "vpn", "dns"],
        probable_cause="Network connectivity or configuration issue.",
        recommended_steps=[
            "Check whether Airplane Mode is disabled.",
            "Restart the Wi-Fi adapter.",
            "Forget and reconnect to the Wi-Fi network.",
            "Run the Windows network troubleshooter.",
            "Restart the router if other devices are also affected.",
        ],
        relevant_commands=["ipconfig /all", "ipconfig /release", "ipconfig /renew", "ipconfig /flushdns"],
        escalation_required=False,
    ),
    ClassificationRule(
        category="authentication",
        severity="medium",
        confidence=0.90,
        keywords=["password", "login", "log in", "sign in", "account", "credentials", "locked out", "2fa", "mfa"],
        probable_cause="Authentication or credential-related issue.",
        recommended_steps=[
            "Verify the username and password.",
            "Check whether Caps Lock is enabled.",
            "Try resetting the password.",
            "Check whether the account is locked.",
        ],
        relevant_commands=[],
        escalation_required=False,
    ),
    ClassificationRule(
        category="performance",
        severity="medium",
        confidence=0.85,
        keywords=[
            "slow", "performance", "freezing", "freezes", "lag", "lagging",
            "high cpu", "high memory", "takes forever", "takes long", "boot up",
        ],
        probable_cause="System resource or performance issue.",
        recommended_steps=[
            "Check CPU and memory usage.",
            "Close unnecessary applications.",
            "Restart the system.",
            "Check available disk space.",
        ],
        relevant_commands=["tasklist /v", "wmic cpu get loadpercentage", "wmic logicaldisk get size,freespace,caption"],
        escalation_required=False,
    ),
    ClassificationRule(
        category="hardware",
        severity="low",
        confidence=0.85,
        keywords=["printer", "printing", "print", "monitor", "keyboard", "mouse", "webcam", "usb"],
        probable_cause="Peripheral connectivity, driver, or hardware issue.",
        recommended_steps=[
            "Check that the device is powered on.",
            "Verify the device connection or cable.",
            "Check for driver or firmware updates.",
            "Restart the device.",
            "Reinstall the device driver if the issue persists.",
        ],
        relevant_commands=[],
        escalation_required=False,
    ),
    ClassificationRule(
        category="system",
        severity="high",
        confidence=0.80,
        keywords=[
            "blue screen", "bsod", "crash", "crashing", "won't start", "wont start",
            "kernel panic", "freeze on boot", "won't boot", "wont boot", "restarts randomly",
            "reboots randomly", "restarting on its own", "reboots on its own",
        ],
        probable_cause="Operating system, driver, or hardware stability issue.",
        recommended_steps=[
            "Restart the system.",
            "Record any error codes or messages.",
            "Check for recent driver or software changes.",
            "Run system diagnostics.",
            "Escalate to IT support if the issue persists.",
        ],
        relevant_commands=["sfc /scannow", "DISM /Online /Cleanup-Image /RestoreHealth"],
        escalation_required=True,
        escalation_reason="System instability (crashes/BSOD) can indicate hardware failure and risks data loss.",
    ),
]

DEFAULT_RULE = ClassificationRule(
    category="general",
    severity="unknown",
    confidence=0.30,
    keywords=[],
    probable_cause="The issue could not be automatically categorized.",
    recommended_steps=[
        "Collect additional information about the problem.",
        "Check system logs and error messages.",
        "Escalate to IT support if the problem persists.",
    ],
    relevant_commands=[],
    escalation_required=True,
    escalation_reason="Issue does not match a known category and needs human triage.",
)


def classify(issue_text: str) -> ClassificationRule:
    issue_lower = issue_text.lower()
    for rule in RULES:
        if any(keyword in issue_lower for keyword in rule.keywords):
            return rule
    return DEFAULT_RULE
