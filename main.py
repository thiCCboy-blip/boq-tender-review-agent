import csv

from review import review_boq


def load_boq(file_path):
    with open(file_path, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read().lower()


def main():
    boq_items = load_boq("data/sample_boq.csv")
    tender_text = load_text("data/sample_tender.txt")
    results = review_boq(boq_items, tender_text)

    for result in results:
        print(
            result["code"],
            result["description"],
            result["calculated_amount"],
            result["amount_status"],
            result["description_status"],
        )


if __name__ == "__main__":
    main()
