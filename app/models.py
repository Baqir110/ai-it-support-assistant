from typing import Literal

from pydantic import BaseModel, Field


class SupportRequest(BaseModel):
    issue: str = Field(
        ...,
        min_length=5,
        description="Description of the IT issue",
        examples=["My Windows laptop cannot connect to Wi-Fi."],
    )


class IssueAnalysis(BaseModel):
    category: Literal[
        "network",
        "authentication",
        "performance",
        "hardware",
        "system",
        "general",
    ]

    severity: Literal[
        "low",
        "medium",
        "high",
        "unknown",
    ]

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence score for the issue classification",
    )

    probable_cause: str
    recommended_steps: list[str]
    escalation_required: bool


class SupportResponse(BaseModel):
    issue: str
    analysis: IssueAnalysis
