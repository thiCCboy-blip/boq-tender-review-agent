from review import calculate_amount, review_item


def make_item():
    return {
        "code": "C-01",
        "description": "Concrete work",
        "quantity": 120,
        "unit": "m3",
        "rate": 850,
        "listed_amount": 102000,
    }


def test_calculate_amount():
    assert calculate_amount(120, 850) == 102000


def test_review_item_flags_amount_mismatch():
    item = make_item()
    item["listed_amount"] = 100000
    result = review_item(item, "concrete work")
    assert result["amount_status"] == "CHECK"


def test_review_item_finds_description():
    result = review_item(make_item(), "concrete work")
    assert result["description_status"] == "FOUND"


def test_review_item_reports_missing_description():
    result = review_item(make_item(), "unrelated text")
    assert result["description_status"] == "NOT_FOUND"
