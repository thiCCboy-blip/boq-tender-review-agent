import argparse
import json

from comparison import compare_items, load_boq
from document_loader import load_document
from llm_review import extract_items


def parse_args():
    parser = argparse.ArgumentParser(description="Review a BOQ against a tender document")
    parser.add_argument("--tender", default="data/sample_tender.txt")
    parser.add_argument("--boq", default="data/sample_boq.csv")
    parser.add_argument("--output", default="data/live_review_report.json")
    return parser.parse_args()


def main():
    args = parse_args()
    tender_text = load_document(args.tender)

    extraction = extract_items(tender_text)
    extracted_items = extraction.model_dump()["items"]
    boq_items = load_boq(args.boq)
    comparisons = compare_items(boq_items, extracted_items)

    for comparison in comparisons:
        print(
            comparison["code"],
            comparison["match_status"],
            comparison["match_score"],
            comparison["unit_status"],
            comparison["source_excerpt"],
        )

    report = {
        "extraction": extracted_items,
        "comparisons": comparisons,
    }
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


if __name__ == "__main__":
    main()
