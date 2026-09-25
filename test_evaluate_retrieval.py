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


def test_evaluate_method_without_embedder_is_none():
    assert evaluate_method(load_cases(), "embedding", None) is None


def test_compare_methods_records_skip_reason_without_embedder():
    results, skipped = compare_methods(load_cases(), None)

    assert "token_overlap" in results
    assert set(skipped) == {"embedding", "hybrid"}
    for reason in skipped.values():
        assert reason


def test_compare_methods_survives_backend_failure():
    class BrokenEmbedder:
        def embed(self, texts):
            raise RuntimeError("quota exhausted")

    results, skipped = compare_methods(load_cases(), BrokenEmbedder())

    assert "token_overlap" in results
    assert "quota exhausted" in skipped["embedding"]


def test_format_comparison_lists_skips():
    results, skipped = compare_methods(load_cases(), None)
    output = format_comparison(results, skipped)

    assert "token_overlap" in output
    assert "skipped" in output
