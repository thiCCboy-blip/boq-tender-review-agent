"""Compare retrieval strategies on labelled cases and report the trade-off.

Run:
    .\\.venv\\Scripts\\python.exe .\\evaluate_retrieval.py

Token overlap always runs and needs no API key. Embedding and hybrid strategies
run when an API key is set or a warm cache exists, and are reported as skipped
otherwise so the comparison still produces a result on a clean machine.
"""

import json
from pathlib import Path

from retrieval import build_embedder, get_ranker

CASES_PATH = Path("data/retrieval_cases.json")
REPORT_PATH = Path("data/retrieval_report.json")
METHODS = ("token_overlap", "tfidf", "embedding", "hybrid")

def load_cases(path=CASES_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def rank_of_expected(ranking, expected):
    """1-based position of the expected description, or None if unranked."""
    for position, (description, _score) in enumerate(ranking, start=1):
        if description == expected:
            return position
    return None


def evaluate_method(cases, method, embedder):
    ranker = get_ranker(method, embedder)
    if ranker is None:
        return None

    results = []
    for case in cases:
        ranking = ranker(case["query"], case["candidates"])
        rank = rank_of_expected(ranking, case["expected"])
        top = ranking[0][0] if ranking else None
        results.append(
            {
                "case_id": case["case_id"],
                "name": case["name"],
                "expected_rank": rank,
                "top_match": top,
                "correct_at_1": rank == 1,
                "correct_at_3": rank is not None and rank <= 3,
                "top_score": round(ranking[0][1], 4) if ranking else 0.0,
            }
        )

    total = len(results)
    hit_at_1 = sum(item["correct_at_1"] for item in results)
    hit_at_3 = sum(item["correct_at_3"] for item in results)
    reciprocal_sum = sum(
        1.0 / item["expected_rank"] for item in results if item["expected_rank"]
    )

    return {
        "method": method,
        "backend": embedder.model if embedder is not None else "token_overlap",
        "case_count": total,
        "metrics": {
            "hit_rate_at_1": round(hit_at_1 / total, 3) if total else 0.0,
            "hit_rate_at_3": round(hit_at_3 / total, 3) if total else 0.0,
            "mrr": round(reciprocal_sum / total, 3) if total else 0.0,
        },
        "cases": results,
    }


def compare_methods(cases, methods=METHODS, api_key=None):
    """Run every strategy, tolerating an unavailable vector backend.

    A quota, network, or missing-credential failure must not abort the
    comparison, because the strategies that did run are still valid results
    and the reader needs to know which were skipped and why.
    """
    results = {}
    skipped = {}
    for method in methods:
        try:
            embedder = build_embedder(method, cases, api_key=api_key)
            outcome = evaluate_method(cases, method, embedder)
        except Exception as error:  # noqa: BLE001 - reported, not swallowed
            skipped[method] = f"{type(error).__name__}: {error}"
            continue
        if outcome is None:
            skipped[method] = "vector backend unavailable"
        else:
            results[method] = outcome
    return results, skipped


def format_comparison(results, skipped):
    lines = [
        f"{'method':<16}{'hit@1':>8}{'hit@3':>8}{'MRR':>8}  backend",
        "-" * 62,
    ]
    for method, outcome in results.items():
        metrics = outcome["metrics"]
        lines.append(
            f"{method:<16}{metrics['hit_rate_at_1']:>8.3f}"
            f"{metrics['hit_rate_at_3']:>8.3f}{metrics['mrr']:>8.3f}  {outcome['backend']}"
        )
    if skipped:
        lines.append("")
        for method, reason in skipped.items():
            lines.append(f"skipped {method}: {reason}")
    return "\n".join(lines)


def main():
    cases = load_cases()
    results, skipped = compare_methods(cases)

    report = {
        "case_count": len(cases),
        "methods_run": {method: outcome["backend"] for method, outcome in results.items()},
        "skipped_methods": skipped,
        "methods": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(format_comparison(results, skipped))
    print()
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
