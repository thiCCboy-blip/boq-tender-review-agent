from evaluate import evaluate_extraction


def test_evaluate_perfect_extraction():
    expected = [{"description": "Concrete work", "unit": "m3"}]
    extracted = [
        {
            "description": "Supply and place concrete",
            "unit": "cubic metres",
            "source_excerpt": "Concrete measured in cubic metres.",
        }
    ]

    metrics = evaluate_extraction(expected, extracted)

    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["unit_accuracy"] == 1.0
    assert metrics["citation_coverage"] == 1.0


def test_evaluate_missing_item():
    metrics = evaluate_extraction([{"description": "Concrete work", "unit": "m3"}], [])

    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["citation_coverage"] == 0.0


def test_evaluate_reports_unit_mismatch():
    metrics = evaluate_extraction(
        [{"description": "Concrete work", "unit": "m3"}],
        [
            {
                "description": "Supply and place concrete",
                "unit": "tonnes",
                "source_excerpt": "Concrete described in tonnes.",
            }
        ],
    )

    assert metrics["unit_accuracy"] == 0.0
    assert metrics["citation_coverage"] == 1.0
