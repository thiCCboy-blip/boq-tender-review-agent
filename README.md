# BOQ / Tender Review Agent

An AI-assisted application that reviews a Bill of Quantities (BOQ) against a tender specification, highlights matching work items and unit discrepancies, and preserves source excerpts for review.

This is a portfolio project built to demonstrate document extraction, structured LLM outputs, deterministic validation, evaluation, and a working web interface.

## Live demo

[Open the deployed Streamlit app](https://amruu-boq-agent.streamlit.app/)

Project documentation: [case study](CASE_STUDY.md) · [demo script](DEMO_SCRIPT.md)

## Features

- Loads text, Markdown, and text-based PDF tender documents.
- Extracts explicit BOQ work items with descriptions, units, requirements, and source excerpts.
- Uses OpenAI Structured Outputs with Pydantic schemas.
- Matches BOQ rows to extracted tender items using token-overlap scoring.
- Normalizes common unit variants such as `cubic metres` → `m3` and `tonnes` → `t`.
- Compares token-overlap, TF-IDF, embedding, and hybrid retrieval strategies against a labelled set of synonym and hard-negative cases.
- Runs deterministic quantity and amount checks.
- Reports latency, token usage, and optional cost estimates for each AI run.
- Reports precision, recall, F1, unit accuracy, and citation coverage on labelled sample data.
- Provides a Streamlit interface with JSON report download, optional password protection, and a five-review browser-session guard.
- Includes automated tests for review logic, document loading, comparison, extraction configuration, and evaluation.

## Tech stack

- Python
- OpenAI Responses API with Structured Outputs
- Pydantic
- pypdf
- Streamlit
- pytest

## Getting started

### 1. Clone and install

```powershell
git clone https://github.com/thiCCboy-blip/boq-tender-review-agent.git
cd boq-tender-review-agent
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### 2. Configure the API

Edit `.env` and add your OpenAI API key:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-6-luna
APP_PASSWORD=
OPENAI_INPUT_COST_PER_MILLION=
OPENAI_OUTPUT_COST_PER_MILLION=
```

`APP_PASSWORD` enables a simple password gate for the web app. The two cost variables are optional; set them to the model's current per-million-token prices if you want cost estimates in reports.

The `.env` file is ignored by Git and must not be committed.

### 3. Run the web application

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

Open `http://localhost:8501` if the browser does not open automatically. Upload a tender document and a BOQ CSV, then select **Run review**.

## Deploy to Streamlit Community Cloud

1. Push the project to GitHub; this repository already contains the required `app.py` and `requirements.txt`.
2. Open `https://share.streamlit.io` and sign in with GitHub.
3. Select **New app**, then choose `thiCCboy-blip/boq-tender-review-agent`, branch `main`, and main file `app.py`.
4. Select **Deploy** and wait for the build to finish.
5. Open the deployed app's **Settings → Secrets**.
6. Add these secrets using TOML syntax, then save and redeploy/restart the app:

   ```toml
   OPENAI_API_KEY = "your_openai_api_key"
   OPENAI_MODEL = "gpt-6-luna"
   APP_PASSWORD = "use_a_private_password_for_the_demo"
   ```

7. Copy the generated `*.streamlit.app` URL for your README, resume, and portfolio.

For public live mode, omit `APP_PASSWORD` or set it to an empty string. In that mode, anyone with the URL can run reviews, so configure a strict budget and usage limit at the API provider. Never put an API key or app password in `app.py`, `README.md`, or a committed file.

## Command-line usage

Review the bundled text sample:

```powershell
.\.venv\Scripts\python.exe .\run_review.py
```

Review a text-based PDF:

```powershell
.\.venv\Scripts\python.exe .\run_review.py --tender data\sample_tender.pdf --boq data\sample_boq.csv --output data\pdf_review_report.json
```

The runner prints each BOQ match and writes a JSON report containing the extracted items, match scores, unit status, source excerpts, model latency, and token usage.

## Tests and evaluation

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Evaluate a generated review report against the labelled sample expectations:

```powershell
.\.venv\Scripts\python.exe .\evaluate.py
```

Run the multi-case evaluation set, including missing items, extra items, unit mismatches, and missing citations:

```powershell
.\.venv\Scripts\python.exe .\evaluate_dataset.py
```

The multi-case fixture currently reports micro precision `0.889`, recall `0.889`, F1 `0.889`, unit accuracy `0.875`, and citation coverage `0.889`. It is a controlled synthetic fixture, not a production benchmark; replace it with representative, consented documents before using the numbers in a business claim.

### Retrieval strategy comparison

The matching layer was originally token-overlap only, on the assumption that it was explainable and sufficient. A labelled 20-case fixture was built to test that assumption, using the two cases that break a lexical matcher: synonym pairs where the same work is described in different words, and hard negatives where distractors are near-identical to the query.

```powershell
.\.venv\Scripts\python.exe .\evaluate_retrieval.py
```

| Strategy | hit@1 | hit@3 | MRR | Backend |
| --- | ---: | ---: | ---: | --- |
| `token_overlap` | 0.200 | 1.000 | 0.575 | in-process |
| `tfidf` | 0.200 | 0.900 | 0.558 | in-process |

The lexical matcher places the correct item in the top three candidates for every case, but ranks it first in only one in five. Every failure is a synonym or paraphrase case: `syn-rebar` puts `Reinforcement steel` second to `Rebar fabrication and fixing` because the two share almost no tokens, while the two are the same work item to anyone who reads construction descriptions. That is a real failure mode, not a metric artifact.

TF-IDF scores identically on hit@1. That is the useful part of the result: inverse document frequency weighting cannot close the gap, because the problem is missing vocabulary rather than poorly weighted vocabulary. The synonym is absent from the description entirely, so no amount of term reweighting will surface it. This is the evidence for why the fix needs semantics rather than a better lexical scorer.

The `embedding` and `hybrid` rows are reported as skipped when no API key or warm cache is available, so the free strategies remain reproducible on a clean machine with no dependencies. Adding credit and re-running populates `data/embedding_cache.json`, after which the comparison is reproducible offline.

The harness reports a skip reason rather than silently presenting fewer strategies, and names the backend behind every row.

As with the extraction fixture, these 20 cases are synthetic and were written by the author. They demonstrate a failure mode and a method for measuring it; they are not a benchmark of production retrieval quality.

## Data and privacy

- Use only non-confidential documents for testing.
- Uploads are limited to 10 MB per file and are written to a temporary directory for processing and removed afterwards.
- The public app allows five AI reviews per browser session; this is a convenience guard, not server-side rate limiting.
- Leave `APP_PASSWORD` blank for public live mode, or set it in Streamlit Secrets to require a password before review.
- Tender text is sent to the configured OpenAI API when the AI step runs.
- The project does not currently implement OCR for scanned or image-only PDFs.
- The matching layer is deliberately explainable and deterministic, but token-overlap scoring measurably underperforms on synonym and paraphrase pairs. See the retrieval strategy comparison for measured results.
- The retrieval comparison covers 20 synthetic cases written by the author. TF-IDF is a lexical baseline, not a semantic model; the semantic arms (`embedding`, `hybrid`) were not run because the API account had no remaining credit, so the implemented fix is unverified.
- The application is an assistive tool, not a replacement for professional quantity surveying or procurement review.

## Project structure

```text
app.py                  Streamlit web interface and access gate
llm_review.py           Structured OpenAI extraction and run metadata
run_review.py           End-to-end CLI pipeline
comparison.py           BOQ matching and unit normalization
retrieval.py            Pluggable retrieval strategies and reciprocal rank fusion
review.py               Deterministic amount and coverage checks
document_loader.py      TXT, Markdown, and PDF loading
evaluate.py             Single-report extraction quality metrics
evaluate_dataset.py     Multi-case evaluation harness
evaluate_retrieval.py   Retrieval strategy comparison harness
main.py                 Offline review example
data/                   Sample inputs, fixtures, and expected items
test_*.py               Automated tests
```

## Possible next improvements

- OCR support for scanned PDFs.
- Table-aware BOQ extraction for complex spreadsheets.
- Enable the hybrid retrieval strategy and re-measure the extraction fixture, since the current matching layer is lexical only and measurably weaker on synonyms. TF-IDF was measured and did not close the gap, so a semantic model is the required next step.
- Expand the retrieval fixture with real, consented tender descriptions.
- Human review workflow for flagged discrepancies.
- Identity-based access control, rate limiting, and usage monitoring.
- Representative customer-approved evaluation data and reliability targets.
