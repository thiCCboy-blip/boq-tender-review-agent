from llm_review import estimate_cost


def test_estimate_cost_uses_per_million_rates():
    cost = estimate_cost(1_000_000, 500_000, 2.0, 4.0)

    assert cost == 4.0


def test_estimate_cost_returns_none_without_rates():
    assert estimate_cost(100, 50, None, None) is None


def test_estimate_cost_returns_none_for_invalid_rates():
    assert estimate_cost(100, 50, "invalid", 1.0) is None
