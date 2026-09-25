import json

from evaluate_dataset import evaluate_dataset


def test_evaluate_dataset_aggregates_error_cases():
    with open("data/evaluation_cases.json", "r", encoding="utf-8") as file:
        cases = json.load(file)

    report = evaluate_dataset(cases)

    assert report["case_count"] == 9
    assert report["totals"]["expected_items"] == 9
    assert report["totals"]["extracted_items"] == 9
    assert report["totals"]["true_positives"] == 8
    assert report["totals"]["false_positives"] == 1
    assert report["totals"]["false_negatives"] == 1
    assert report["metrics"]["f1"] == 0.889
    assert report["metrics"]["unit_accuracy"] == 0.875
    assert report["metrics"]["citation_coverage"] == 0.889


def test_evaluate_dataset_handles_empty_dataset():
    report = evaluate_dataset([])

    assert report["case_count"] == 0
    assert report["metrics"]["f1"] == 0.0
