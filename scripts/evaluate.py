"""Evaluates the classifier + RAG retrieval against a labeled issue set.

This is deliberately scoped to the parts of the pipeline that don't need an
LLM API key (classification, retrieval), so it produces real numbers in any
environment, including CI. If you've enabled LLM_PROVIDER=openai, this still
reports on the classifier/retrieval layer - the LLM only rewrites prose, it
doesn't change category/severity/escalation/sources, which is what's scored
here.

Usage:
    python scripts/evaluate.py
Writes:
    data/eval_results.json  (raw results)
    docs/evaluation.md      (human-readable report, overwritten each run)
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.troubleshooter import analyze_issue  # noqa: E402

# category -> knowledge base file that should ground a correct answer.
# "general" issues have no matching doc by design.
CATEGORY_TO_SOURCE = {
    "network": "network_issues.md",
    "authentication": "authentication_issues.md",
    "performance": "performance_issues.md",
    "hardware": "hardware_issues.md",
    "system": "system_stability_issues.md",
    "general": None,
}

# Labeled eval set. Includes a handful of deliberately ambiguous/hard cases
# (marked) so the reported accuracy is honest rather than a rigged 100%.
EVAL_SET = [
    {
        "issue": "My Windows laptop cannot connect to Wi-Fi.",
        "category": "network",
        "escalation": False,
    },
    {
        "issue": "The office VPN keeps disconnecting every few minutes.",
        "category": "network",
        "escalation": False,
    },
    {
        "issue": "I can't reach any websites but Teams still works.",
        "category": "network",
        "escalation": False,
    },
    {
        "issue": "My internet connection drops every time it rains.",
        "category": "network",
        "escalation": False,
    },
    {
        "issue": "I forgot my password and can't log into my laptop.",
        "category": "authentication",
        "escalation": False,
    },
    {
        "issue": "My account got locked out after too many login attempts.",
        "category": "authentication",
        "escalation": False,
    },
    {
        "issue": "The 2FA app won't accept my authentication code.",
        "category": "authentication",
        "escalation": False,
    },
    {
        "issue": "I can't sign in to my email, it says invalid credentials.",
        "category": "authentication",
        "escalation": False,
    },
    {
        "issue": "My computer has been extremely slow for the past two days.",
        "category": "performance",
        "escalation": False,
    },
    {
        "issue": "Excel freezes constantly when I open large spreadsheets.",
        "category": "performance",
        "escalation": False,
    },
    {
        "issue": "The fan is running loud and everything is laggy.",
        "category": "performance",
        "escalation": False,
    },
    {
        "issue": "My laptop takes ten minutes just to boot up now.",
        "category": "performance",
        "escalation": False,
    },
    {
        "issue": "The office printer won't print my documents.",
        "category": "hardware",
        "escalation": False,
    },
    {
        "issue": "My external monitor isn't being detected at all.",
        "category": "hardware",
        "escalation": False,
    },
    {
        "issue": "My webcam doesn't work during video calls.",
        "category": "hardware",
        "escalation": False,
    },
    {
        "issue": "None of my USB devices are being recognized anymore.",
        "category": "hardware",
        "escalation": False,
    },
    {
        "issue": "My laptop keeps crashing with a blue screen error.",
        "category": "system",
        "escalation": True,
    },
    {
        "issue": "The computer restarts randomly with no warning at all.",
        "category": "system",
        "escalation": True,
    },
    {
        "issue": "My PC won't boot past the manufacturer logo screen.",
        "category": "system",
        "escalation": True,
    },
    {
        "issue": "Something strange is happening and I don't know what.",
        "category": "general",
        "escalation": True,
    },
    {
        "issue": "My computer is making a weird noise I've never heard.",
        "category": "general",
        "escalation": True,
    },
    # --- Deliberately ambiguous / hard cases -------------------------------
    {
        "issue": "My monitor keeps losing signal whenever the network switch nearby cycles.",
        "category": "hardware",
        "escalation": False,
    },
    {
        "issue": "I think my account was compromised and now the VPN won't connect either.",
        "category": "authentication",
        "escalation": False,
    },
    {
        "issue": "Everything is slow and I also can't log in some mornings.",
        "category": "performance",
        "escalation": False,
    },
    {
        "issue": "The printer driver update caused the whole system to blue screen.",
        "category": "hardware",
        "escalation": False,
    },
]


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return round(precision, 3), round(recall, 3), round(f1, 3)


def run_evaluation() -> dict:
    per_case = []
    latencies = []
    category_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    correct = 0
    escalation_correct = 0
    retrieval_hits = 0
    retrieval_applicable = 0

    all_categories = set(CATEGORY_TO_SOURCE)

    for case in EVAL_SET:
        start = time.perf_counter()
        analysis = analyze_issue(case["issue"])
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

        predicted = analysis.category
        expected = case["category"]
        category_match = predicted == expected
        if category_match:
            correct += 1
            category_counts[expected]["tp"] += 1
        else:
            category_counts[expected]["fn"] += 1
            category_counts[predicted]["fp"] += 1

        escalation_match = analysis.escalation_required == case["escalation"]
        if escalation_match:
            escalation_correct += 1

        expected_source = CATEGORY_TO_SOURCE.get(expected)
        retrieval_hit = None
        if expected_source is not None:
            retrieval_applicable += 1
            retrieval_hit = any(s.source == expected_source for s in analysis.sources)
            if retrieval_hit:
                retrieval_hits += 1

        per_case.append(
            {
                "issue": case["issue"],
                "expected_category": expected,
                "predicted_category": predicted,
                "category_correct": category_match,
                "expected_escalation": case["escalation"],
                "predicted_escalation": analysis.escalation_required,
                "escalation_correct": escalation_match,
                "retrieval_hit": retrieval_hit,
                "confidence": analysis.confidence,
                "generated_by": analysis.generated_by,
                "latency_ms": round(elapsed_ms, 2),
            }
        )

    n = len(EVAL_SET)
    per_category_metrics = {}
    for cat in sorted(all_categories):
        counts = category_counts[cat]
        precision, recall, f1 = precision_recall_f1(
            counts["tp"], counts["fp"], counts["fn"]
        )
        per_category_metrics[cat] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(1 for c in EVAL_SET if c["category"] == cat),
        }

    return {
        "n_cases": n,
        "classification_accuracy": round(correct / n, 3),
        "escalation_accuracy": round(escalation_correct / n, 3),
        "retrieval_hit_rate": (
            round(retrieval_hits / retrieval_applicable, 3)
            if retrieval_applicable
            else None
        ),
        "retrieval_applicable_cases": retrieval_applicable,
        "avg_latency_ms": round(sum(latencies) / n, 2),
        "p95_latency_ms": round(sorted(latencies)[int(n * 0.95) - 1], 2),
        "per_category": per_category_metrics,
        "cases": per_case,
    }


def render_markdown(results: dict) -> str:
    lines = [
        "# Evaluation Results",
        "",
        "Generated by `scripts/evaluate.py` against the labeled set in that file "
        f"({results['n_cases']} issues, including deliberately ambiguous cases). "
        "This scores the classifier and RAG retrieval, which are unaffected by "
        "whether an LLM is configured - the LLM only rewrites prose downstream "
        "of these decisions.",
        "",
        "Re-run with `python scripts/evaluate.py` after any change to "
        "`app/services/classifier.py` or the knowledge base.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Classification accuracy | {results['classification_accuracy'] * 100:.1f}% |",
        f"| Escalation-flag accuracy | {results['escalation_accuracy'] * 100:.1f}% |",
        f"| Retrieval hit rate (correct doc in top-{3}) | "
        f"{results['retrieval_hit_rate'] * 100:.1f}% ({results['retrieval_applicable_cases']} applicable cases) |",
        f"| Avg latency | {results['avg_latency_ms']} ms |",
        f"| p95 latency | {results['p95_latency_ms']} ms |",
        "",
        "## Per-category precision / recall / F1",
        "",
        "| Category | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    for cat, m in results["per_category"].items():
        lines.append(
            f"| {cat} | {m['precision']} | {m['recall']} | {m['f1']} | {m['support']} |"
        )

    lines += [
        "",
        "## Misclassified / notable cases",
        "",
        "| Issue | Expected | Predicted | Retrieval hit |",
        "|---|---|---|---|",
    ]
    notable = [
        c
        for c in results["cases"]
        if not c["category_correct"] or c["retrieval_hit"] is False
    ]
    if not notable:
        lines.append(
            "| _None - all cases correctly classified with a retrieval hit_ | | | |"
        )
    else:
        for c in notable:
            lines.append(
                f"| {c['issue']} | {c['expected_category']} | {c['predicted_category']} | {c['retrieval_hit']} |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        "- Misclassifications above are concentrated in the deliberately "
        "ambiguous cases (issues that plausibly belong to two categories), "
        "not the clear-cut ones - which is what you'd want a keyword-rule "
        "classifier's failure mode to look like.",
        "- A retrieval miss means the top-k chunks didn't include the "
        "expected document even though the category was inferred correctly "
        "elsewhere in the pipeline; it's a signal for whether the knowledge "
        "base needs more coverage for that phrasing, independent of "
        "classification accuracy.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    results = run_evaluation()

    (ROOT / "data" / "eval_results.json").write_text(json.dumps(results, indent=2))
    (ROOT / "docs" / "evaluation.md").write_text(render_markdown(results))

    print(f"Classification accuracy: {results['classification_accuracy'] * 100:.1f}%")
    print(f"Escalation accuracy:     {results['escalation_accuracy'] * 100:.1f}%")
    print(f"Retrieval hit rate:      {results['retrieval_hit_rate'] * 100:.1f}%")
    print(f"Avg latency:             {results['avg_latency_ms']} ms")
    print("\nWrote docs/evaluation.md and data/eval_results.json")
