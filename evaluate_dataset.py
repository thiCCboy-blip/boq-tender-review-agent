import json

from evaluate import evaluate_extraction, load_json


def ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def evaluate_dataset(cases):
    case_results = []
    for case in cases:
        metrics = evaluate_extraction(case["expected_items"], case["extracted_items"])
        case_results.append(
            {
                "case_id": case["case_id"],
                "name": case["name"],
                **metrics,
            }
        )

    total_expected = sum(item["expected_count"] for item in case_results)
    total_extracted = sum(item["extracted_count"] for item in case_results)
    total_true_positives = sum(item["true_positives"] for item in case_results)
    total_false_positives = sum(item["false_positives"] for item in case_results)
    total_false_negatives = sum(item["false_negatives"] for item in case_results)
    total_unit_correct = sum(item["unit_correct"] for item in case_results)
    total_cited_items = sum(item["cited_items"] for item in case_results)

    precision = ratio(total_true_positives, total_true_positives + total_false_positives)
    recall = ratio(total_true_positives, total_true_positives + total_false_negatives)
    f1 = ratio(2 * precision * recall, precision + recall)
    unit_accuracy = ratio(total_unit_correct, total_true_positives)
    citation_coverage = ratio(total_cited_items, total_extracted)

    return {
        "case_count": len(case_results),
        "totals": {
            "expected_items": total_expected,
            "extracted_items": total_extracted,
            "true_positives": total_true_positives,
            "false_positives": total_false_positives,
            "false_negatives": total_false_negatives,
            "unit_correct": total_unit_correct,
            "cited_items": total_cited_items,
        },
        "metrics": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "unit_accuracy": round(unit_accuracy, 3),
            "citation_coverage": round(citation_coverage, 3),
        },
        "macro_metrics": {
            "precision": round(sum(item["precision"] for item in case_results) / len(case_results), 3)
            if case_results
            else 0.0,
            "recall": round(sum(item["recall"] for item in case_results) / len(case_results), 3)
            if case_results
            else 0.0,
            "f1": round(sum(item["f1"] for item in case_results) / len(case_results), 3)
            if case_results
            else 0.0,
        },
        "cases": case_results,
    }


def main():
    cases = load_json("data/evaluation_cases.json")
    report = evaluate_dataset(cases)
    with open("data/evaluation_report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
