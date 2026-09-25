import json

from comparison import canonical_unit, match_score


def evaluate_extraction(expected_items, extracted_items):
    matched_expected = set()
    matched_extracted = set()
    unit_correct = 0

    for expected_index, expected_item in enumerate(expected_items):
        best_index = None
        best_score = 0.0

        for extracted_index, extracted_item in enumerate(extracted_items):
            if extracted_index in matched_extracted:
                continue
            score = match_score(expected_item["description"], extracted_item["description"])
            if score > best_score:
                best_score = score
                best_index = extracted_index

        if best_index is not None and best_score >= 0.5:
            matched_expected.add(expected_index)
            matched_extracted.add(best_index)
            extracted_item = extracted_items[best_index]
            if canonical_unit(expected_item["unit"]) == canonical_unit(extracted_item["unit"]):
                unit_correct += 1

    true_positives = len(matched_expected)
    false_positives = len(extracted_items) - len(matched_extracted)
    false_negatives = len(expected_items) - true_positives
    precision = true_positives / (true_positives + false_positives) if true_positives + false_positives else 0.0
    recall = true_positives / (true_positives + false_negatives) if true_positives + false_negatives else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    unit_accuracy = unit_correct / true_positives if true_positives else 0.0
    citation_coverage = (
        sum(bool(item.get("source_excerpt")) for item in extracted_items) / len(extracted_items)
        if extracted_items
        else 0.0
    )

    return {
        "expected_count": len(expected_items),
        "extracted_count": len(extracted_items),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "unit_accuracy": round(unit_accuracy, 3),
        "citation_coverage": round(citation_coverage, 3),
    }


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    expected_items = load_json("data/expected_items.json")
    report = load_json("data/live_review_report.json")
    extracted_items = report.get("extraction", [])
    metrics = evaluate_extraction(expected_items, extracted_items)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
