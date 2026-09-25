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


def load_styles():
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: #0b1220;
            border-right: 1px solid #1f2a3d;
        }

        [data-testid="stSidebar"] * {
            color: #e2e8f0;
        }

        [data-testid="stSidebar"] hr {
            border-color: #263449;
        }

        .hero {
            background: linear-gradient(135deg, #0b1220 0%, #142b52 55%, #0f766e 130%);
            border-radius: 26px;
            padding: 2.6rem 2.8rem;
            margin-bottom: 1.4rem;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.22);
        }

        .hero .eyebrow {
            color: #5eead4;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }

        .hero h1 {
            color: #f8fafc;
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(2.1rem, 5vw, 4.1rem);
            letter-spacing: -0.06em;
            line-height: 1;
            margin: 0.7rem 0 1rem;
            max-width: 760px;
        }

        .hero p {
            color: #cbd5e1;
            font-family: 'DM Sans', sans-serif;
            font-size: 1.08rem;
            line-height: 1.65;
            margin: 0;
            max-width: 690px;
        }

        .pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1.5rem;
        }

        .pill {
            background: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 999px;
            color: #e2e8f0;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.78rem;
            padding: 0.42rem 0.8rem;
        }

        .feature-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
            min-height: 148px;
            padding: 1.15rem 1.2rem;
        }

        .feature-card .number {
            color: #0f766e;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.12em;
        }

        .feature-card h3 {
            color: #0f172a;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.15rem;
            margin: 0.55rem 0 0.35rem;
        }

        .feature-card p {
            color: #64748b;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 0;
        }

        .section-label {
            color: #0f766e;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.15em;
            text-transform: uppercase;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background: #f8fafc;
            border: 1px dashed #94a3b8;
            border-radius: 16px;
            min-height: 132px;
        }

        div[data-testid="stFileUploaderDropzone"]:hover {
            background: #f0fdfa;
            border-color: #0f766e;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0f766e, #0f5f5b);
            border: 0;
            border-radius: 12px;
            box-shadow: 0 8px 18px rgba(15, 118, 110, 0.22);
            font-family: 'DM Sans', sans-serif;
            font-weight: 700;
            min-height: 3rem;
        }

        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #115e59, #134e4a);
            box-shadow: 0 10px 22px rgba(15, 118, 110, 0.30);
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 0.9rem 1rem;
        }

        .footer-note {
            color: #94a3b8;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.78rem;
            padding-top: 2rem;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="BOQ Tender Review Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_styles()

with st.sidebar:
    st.markdown("### BOQ Review")
    st.caption("AI-assisted construction document intelligence")
    st.divider()
    st.markdown("**Workflow**")
    st.markdown("1. Upload a tender document\n2. Upload a BOQ CSV\n3. Review matches and units")
    st.divider()
    st.caption("Use only non-confidential documents. Content is sent to the configured OpenAI API for the AI extraction step.")

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Construction document intelligence</div>
        <h1>Review the BOQ.<br>Understand the tender.</h1>
        <p>Turn unstructured tender documents into an explainable BOQ review with structured extraction, unit checks, and source-level traceability.</p>
        <div class="pills">
            <span class="pill">PDF ingestion</span>
            <span class="pill">Structured outputs</span>
            <span class="pill">Unit normalization</span>
            <span class="pill">Explainable matching</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

feature_one, feature_two, feature_three = st.columns(3)
with feature_one:
    st.markdown(
        '<div class="feature-card"><div class="number">01 / EXTRACT</div><h3>Read the document</h3><p>Parse text-based PDFs and text files into explicit tender work items.</p></div>',
        unsafe_allow_html=True,
    )
with feature_two:
    st.markdown(
        '<div class="feature-card"><div class="number">02 / COMPARE</div><h3>Match the BOQ</h3><p>Compare BOQ rows with extracted items and normalize unit variants.</p></div>',
        unsafe_allow_html=True,
    )
with feature_three:
    st.markdown(
        '<div class="feature-card"><div class="number">03 / REVIEW</div><h3>Trace every result</h3><p>Keep source excerpts beside each match for human review and auditability.</p></div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-label">Start a review</div>', unsafe_allow_html=True)
st.markdown("### Upload your documents")

with st.container(border=True):
    tender_column, boq_column = st.columns(2)
    with tender_column:
        tender_file = st.file_uploader(
            "Tender document",
            type=["pdf", "txt", "md"],
            help="Upload a text-based PDF, TXT, or Markdown file.",
        )
    with boq_column:
        boq_file = st.file_uploader(
            "BOQ CSV",
            type=["csv"],
            help="CSV columns: code, description, unit, quantity, rate, amount.",
        )

    run_review = st.button(
        "Run review",
        type="primary",
        use_container_width=True,
        disabled=tender_file is None or boq_file is None,
    )

if run_review:
    st.session_state.pop("review_report", None)
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
    match_rate = matched_count / len(comparisons) if comparisons else 0

    st.markdown('<div class="section-label">Review output</div>', unsafe_allow_html=True)
    st.markdown("### Results")
    item_column, matched_column, rate_column = st.columns(3)
    item_column.metric("BOQ items", len(comparisons))
    matched_column.metric("Matched items", matched_count)
    rate_column.metric("Match rate", f"{match_rate:.0%}")
    st.dataframe(comparisons, use_container_width=True, hide_index=True)
    st.download_button(
        "Download JSON report",
        data=json.dumps(report, indent=2).encode("utf-8"),
        file_name="review_report.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("View extracted items"):
        st.json(report["extraction"])

st.markdown(
    '<div class="footer-note">Built for explainable tender review · Sample and evaluation data included in the repository</div>',
    unsafe_allow_html=True,
)
