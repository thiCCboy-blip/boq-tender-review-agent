# Demo Script: BOQ / Tender Review Agent

Target length: 3 minutes.

## 0:00 - Problem

> Tender documents are long, and checking a BOQ against them manually is slow and error-prone. I wanted a workflow that extracts the important work items, shows the evidence, and leaves the final decision with a human reviewer.

## 0:20 - Open the app

Open the live app: https://amruu-boq-agent.streamlit.app/

> The app accepts a text-based PDF, TXT, or Markdown tender document and a BOQ CSV.

## 0:40 - Upload the sample documents

Upload:

- `data/sample_tender.pdf`
- `data/sample_boq.csv`

> I am using synthetic sample documents. Real tender documents should only be uploaded when they are approved for the relevant data and API policies.

## 1:00 - Run the review

Click **Run review**.

> The model returns validated structured output rather than free-form text. Each item includes a description, unit, requirement, and source excerpt.

## 1:25 - Explain the results

Point to the metrics and table.

> The system matches BOQ rows to extracted items, normalizes unit variants such as tonnes and t, and flags rows for review. The source excerpt is retained so a reviewer can verify the result.

## 1:50 - Show the JSON report

Click **Download JSON report**.

> The report is portable and can be attached to an audit or review workflow. It also includes model latency and token usage so I can monitor the operational cost of an AI step.

## 2:10 - Show the engineering

Open the repository and point to:

- `llm_review.py` for Structured Outputs
- `comparison.py` for deterministic matching
- `evaluate_dataset.py` for the nine-case evaluation
- `CASE_STUDY.md` for trade-offs and limitations

> The current evaluation fixture deliberately includes missing items, extra items, unit mismatches, and missing citations. It is a small controlled evaluation, not a claim of production accuracy.

## 2:40 - Close

> The next production steps are OCR for scanned documents, representative customer-approved evaluation data, authentication, rate limiting, and monitoring. The goal is to accelerate the review while keeping a human accountable for the final decision.
