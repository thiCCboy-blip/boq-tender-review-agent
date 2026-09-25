def calculate_amount(quantity, rate):
    return round(float(quantity) * float(rate), 2)


def review_item(item, tender_text):
    calculated_amount = calculate_amount(item["quantity"], item["rate"])
    listed_amount = round(float(item["listed_amount"]), 2)
    amount_status = "OK" if calculated_amount == listed_amount else "CHECK"
    description_status = "FOUND" if item["description"].lower() in tender_text else "NOT_FOUND"
    return {
        "code": item["code"],
        "description": item["description"],
        "calculated_amount": calculated_amount,
        "amount_status": amount_status,
        "description_status": description_status,
    }


def review_boq(boq_items, tender_text):
    return [review_item(item, tender_text) for item in boq_items]
