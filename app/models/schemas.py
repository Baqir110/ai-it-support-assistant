from typing import Literal

from pydantic import BaseModel, Field


class SupportRequest(BaseModel):
    issue: str = Field(
        ...,
        min_length=5,
        description="Description of the IT issue",
        examples=["My Windows laptop cannot connect to Wi-Fi."],
    )


class SourceReference(BaseModel):
    source: str = Field(..., description="Knowledge base document the answer drew on")
    snippet: str = Field(..., description="Short excerpt used for grounding")
    relevance_score: float = Field(..., ge=0, le=1)


class IssueAnalysis(BaseModel):
    category: Literal[
        "network",
        "authentication",
        "performance",
        "hardware",
        "system",
        "general",
    ]

    severity: Literal["low", "medium", "high", "unknown"]

    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence score for the issue classification"
    )

    probable_cause: str
    recommended_steps: list[str]
    relevant_commands: list[str] = Field(
        default_factory=list,
        description="Diagnostic or remediation commands, if any apply",
    )
    escalation_required: bool
    escalation_reason: str | None = Field(
        default=None, description="Why escalation is (or isn't) recommended"
    )
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Knowledge base documents retrieved to ground this analysis",
    )
    generated_by: Literal["llm", "rule_based"] = Field(
        default="rule_based",
        description="Whether the analysis was produced by the LLM+RAG pipeline or the deterministic fallback",
    )


class SupportResponse(BaseModel):
    issue: str
    analysis: IssueAnalysis


class KnowledgeSearchResult(BaseModel):
    source: str
    content: str
    score: float
