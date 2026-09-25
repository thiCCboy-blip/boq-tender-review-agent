import os
import time

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()


class ExtractedItem(BaseModel):
    description: str
    unit: str
    requirement: str
    source_excerpt: str


class TenderExtraction(BaseModel):
    items: list[ExtractedItem]


def estimate_cost(input_tokens, output_tokens, input_rate, output_rate):
    if input_tokens is None or output_tokens is None or input_rate is None or output_rate is None:
        return None

    try:
        cost = (input_tokens / 1_000_000) * float(input_rate)
        cost += (output_tokens / 1_000_000) * float(output_rate)
    except (TypeError, ValueError):
        return None

    return round(cost, 6)


def get_usage_value(usage, name):
    value = getattr(usage, name, None)
    if isinstance(value, (int, float)):
        return int(value)
    return None


def extract_items_with_metadata(
    tender_text,
    api_key=None,
    model=None,
    input_cost_per_million=None,
    output_cost_per_million=None,
):
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "replace_with_your_key":
        raise RuntimeError("Set OPENAI_API_KEY in the environment before running the AI step.")

    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-6-luna")
    client = OpenAI(api_key=api_key)
    started_at = time.perf_counter()
    response = client.responses.parse(
        model=resolved_model,
        input=[
            {
                "role": "system",
                "content": "You are a construction tender analyst. Extract only explicit BOQ work items from the supplied tender text. Do not invent quantities, rates, or requirements. For each item, return a concise description, measurement unit, requirement summary, and a short exact source excerpt. If no BOQ items are present, return an empty items list.",
            },
            {"role": "user", "content": tender_text},
        ],
        text_format=TenderExtraction,
    )
    latency_ms = round((time.perf_counter() - started_at) * 1000)
    usage = getattr(response, "usage", None)
    input_tokens = get_usage_value(usage, "input_tokens")
    output_tokens = get_usage_value(usage, "output_tokens")
    total_tokens = get_usage_value(usage, "total_tokens")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    metadata = {
        "model": resolved_model,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimate_cost(
            input_tokens,
            output_tokens,
            input_cost_per_million or os.getenv("OPENAI_INPUT_COST_PER_MILLION"),
            output_cost_per_million or os.getenv("OPENAI_OUTPUT_COST_PER_MILLION"),
        ),
    }

    if response.output_parsed is None:
        raise RuntimeError("The model did not return a structured result.")

    return response.output_parsed, metadata


def extract_items(tender_text, api_key=None, model=None):
    result, _ = extract_items_with_metadata(
        tender_text,
        api_key=api_key,
        model=model,
    )
    return result


def main():
    with open("data/sample_tender.txt", "r", encoding="utf-8") as file:
        tender_text = file.read()

    result = extract_items(tender_text)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
