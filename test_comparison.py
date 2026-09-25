from comparison import canonical_unit, compare_items, match_score


def test_match_score():
    assert match_score("Concrete work", "Supply and place concrete") == 0.5


def test_canonical_unit():
    assert canonical_unit("cubic metres") == "m3"
    assert canonical_unit("tonnes") == "t"
    assert canonical_unit("square metres") == "m2"


def test_compare_items_returns_match_and_source():
    boq_items = [
        {
            "code": "C-01",
            "description": "Concrete work",
            "unit": "m3",
        }
    ]
    extracted_items = [
        {
            "description": "Supply and place concrete",
            "unit": "cubic metres",
            "source_excerpt": "Concrete measured in cubic metres.",
        }
    ]

    result = compare_items(boq_items, extracted_items)[0]

    assert result["match_status"] == "MATCHED"
    assert result["unit_status"] == "OK"
    assert result["source_excerpt"] == "Concrete measured in cubic metres."


def test_compare_items_reports_unmatched_item():
    result = compare_items(
        [{"code": "X-01", "description": "Roof waterproofing", "unit": "m2"}],
        [],
    )[0]

    assert result["match_status"] == "UNMATCHED"
    assert result["unit_status"] == "CHECK"
