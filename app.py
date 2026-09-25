import json
import os
import tempfile
from pathlib import Path

import streamlit as st

from comparison import compare_items, load_boq
from document_loader import load_document
from llm_review import extract_items


def get_secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)


st.set_page_config(page_title="BOQ Tender Review Agent", layout="wide")
st.title("BOQ/Tender Review Agent")
st.write("Upload a tender document and BOQ CSV, then review the extracted items, matches, and units.")
st.warning("Use only non-confidential documents. Uploaded content is sent to the configured OpenAI API.")

tender_file = st.file_uploader("Tender document", type=["pdf", "txt", "md"])
boq_file = st.file_uploader("BOQ CSV", type=["csv"])

if st.button(
    "Run review",
    type="primary",
    disabled=tender_file is None or boq_file is None,
):
    with tempfile.TemporaryDirectory() as directory:
        tender_path = Path(directory) / tender_file.name
        boq_path = Path(directory) / boq_file.name
        tender_path.write_bytes(tender_file.getvalue())
        boq_path.write_bytes(boq_file.getvalue())

        try:
            tender_text = load_document(tender_path)
            extraction = extract_items(
                tender_text,
                api_key=get_secret("OPENAI_API_KEY"),
                model=get_secret("OPENAI_MODEL", "gpt-6-luna"),
            )
            extracted_items = extraction.model_dump()["items"]
            boq_items = load_boq(boq_path)
            comparisons = compare_items(boq_items, extracted_items)
            st.session_state["review_report"] = {
                "extraction": extracted_items,
                "comparisons": comparisons,
            }
        except Exception as error:
            st.error(f"Review failed: {error}")

if "review_report" in st.session_state:
    report = st.session_state["review_report"]
    comparisons = report["comparisons"]
    matched_count = sum(item["match_status"] == "MATCHED" for item in comparisons)

    st.subheader("Results")
    column_one, column_two = st.columns(2)
    column_one.metric("BOQ items", len(comparisons))
    column_two.metric("Matched items", matched_count)
    st.dataframe(comparisons, use_container_width=True, hide_index=True)
    st.download_button(
        "Download JSON report",
        data=json.dumps(report, indent=2).encode("utf-8"),
        file_name="review_report.json",
        mime="application/json",
    )

    with st.expander("View extracted items"):
        st.json(report["extraction"])
