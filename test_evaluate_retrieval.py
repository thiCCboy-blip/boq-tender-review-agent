from evaluate_retrieval import (
    compare_methods,
    evaluate_method,
    format_comparison,
    load_cases,
    rank_of_expected,
)


def test_load_cases_returns_labelled_cases():
    cases = load_cases()

    assert cases
    for case in cases:
        assert "query" in case
        assert "expected" in case
        assert case["expected"] in [item["description"] for item in case["candidates"]]


def test_load_cases_includes_synonym_and_hard_negative_coverage():
    cases = load_cases()
    names = " ".join(case["name"] for case in cases)

    assert "Synonym" in names
    assert "Hard negative" in names


def test_rank_of_expected_finds_position():
    ranking = [("a", 0.9), ("b", 0.8), ("c", 0.7)]

    assert rank_of_expected(ranking, "b") == 2


def test_rank_of_expected_returns_none_when_absent():
    assert rank_of_expected([("a", 0.9)], "missing") is None


def test_evaluate_method_token_overlap_produces_metrics():
    cases = load_cases()
    outcome = evaluate_method(cases, "token_overlap", None)

    assert outcome["case_count"] == len(cases)
    assert "hit_rate_at_1" in outcome["metrics"]
    assert len(outcome["cases"]) == len(cases)


def test_evaluate_method_records_backend():
    outcome = evaluate_method(load_cases(), "token_overlap", None)

    assert outcome["backend"] == "token_overlap"


def test_compare_methods_runs_free_strategies_and_reports_paid_skips():
    results, skipped = compare_methods(load_cases(), api_key="")

    assert "token_overlap" in results
    assert "tfidf" in results
    assert "embedding" in skipped


def test_compare_methods_survives_backend_failure(monkeypatch):
    def broken_embedder(method, cases, api_key=None):
        raise RuntimeError("quota exhausted")

    monkeypatch.setattr("evaluate_retrieval.build_embedder", broken_embedder)
    results, skipped = compare_methods(load_cases())

    assert results == {}
    assert "quota exhausted" in skipped["token_overlap"]


def test_format_comparison_lists_skips():
    results, skipped = compare_methods(load_cases(), api_key="")
    output = format_comparison(results, skipped)

    assert "token_overlap" in output
    assert "backend" in output
    assert "skipped" in output


def test_format_comparison_reports_backend_per_row():
    results, skipped = compare_methods(load_cases(), api_key="")
    output = format_comparison(results, skipped)

    assert "tfidf" in output
