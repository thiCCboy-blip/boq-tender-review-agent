import csv
import json
import re


def tokenize(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def match_score(left, right):
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))


def canonical_unit(unit):
    aliases = {
        "cubic metres": "m3",
        "cubic meters": "m3",
        "m3": "m3",
        "tonnes": "t",
        "tons": "t",
        "t": "t",
        "square metres": "m2",
        "square meters": "m2",
        "m2": "m2",
        "lot": "lot",
    }
    return aliases.get(unit.strip().lower(), unit.strip().lower())


def compare_items(boq_items, extracted_items):
    comparisons = []

    for boq_item in boq_items:
        best_item = None
        best_score = 0.0

        for extracted_item in extracted_items:
            score = match_score(boq_item["description"], extracted_item["description"])
            if score > best_score:
                best_score = score
                best_item = extracted_item

        matched = best_item is not None and best_score >= 0.5
        unit_ok = matched and canonical_unit(boq_item["unit"]) == canonical_unit(best_item["unit"])
        comparisons.append(
            {
                "code": boq_item["code"],
                "boq_description": boq_item["description"],
                "match_status": "MATCHED" if matched else "UNMATCHED",
                "match_score": round(best_score, 2),
                "unit_status": "OK" if unit_ok else "CHECK",
                "llm_description": best_item["description"] if best_item else None,
                "extracted_unit": best_item["unit"] if best_item else None,
                "source_excerpt": best_item["source_excerpt"] if best_item else None,
            }
        )

    return comparisons


def load_boq(file_path):
    with open(file_path, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_extraction(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)["items"]


def main():
    boq_items = load_boq("data/sample_boq.csv")
    extracted_items = load_extraction("data/sample_extraction.json")
    comparisons = compare_items(boq_items, extracted_items)

    for comparison in comparisons:
        print(
            comparison["code"],
            comparison["match_status"],
            comparison["match_score"],
            comparison["unit_status"],
            comparison["source_excerpt"],
        )

    with open("data/comparison_report.json", "w", encoding="utf-8") as file:
        json.dump(comparisons, file, indent=2)


if __name__ == "__main__":
    main()
