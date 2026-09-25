import os

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


def extract_items(tender_text, api_key=None, model=None):
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "replace_with_your_key":
        raise RuntimeError("Set OPENAI_API_KEY in the environment before running the AI step.")

    client = OpenAI(api_key=api_key)
    response = client.responses.parse(
        model=model or os.getenv("OPENAI_MODEL", "gpt-6-luna"),
        input=[
            {
                "role": "system",
                "content": "You are a construction tender analyst. Extract only explicit BOQ work items from the supplied tender text. Do not invent quantities, rates, or requirements. For each item, return a concise description, measurement unit, requirement summary, and a short exact source excerpt. If no BOQ items are present, return an empty items list.",
            },
            {"role": "user", "content": tender_text},
        ],
        text_format=TenderExtraction,
    )

    if response.output_parsed is None:
        raise RuntimeError("The model did not return a structured result.")

    return response.output_parsed


def main():
    with open("data/sample_tender.txt", "r", encoding="utf-8") as file:
        tender_text = file.read()

    result = extract_items(tender_text)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
