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

## Data and privacy

- Use only non-confidential documents for testing.
- Uploads are limited to 10 MB per file and are written to a temporary directory for processing and removed afterwards.
- The public app allows five AI reviews per browser session; this is a convenience guard, not server-side rate limiting.
- Leave `APP_PASSWORD` blank for public live mode, or set it in Streamlit Secrets to require a password before review.
- Tender text is sent to the configured OpenAI API when the AI step runs.
- The project does not currently implement OCR for scanned or image-only PDFs.
- The matching layer is deliberately explainable and deterministic, but it is not a replacement for professional quantity surveying or procurement review.

## Project structure

```text
app.py                  Streamlit web interface and access gate
llm_review.py           Structured OpenAI extraction and run metadata
run_review.py           End-to-end CLI pipeline
comparison.py           BOQ matching and unit normalization
review.py               Deterministic amount and coverage checks
document_loader.py      TXT, Markdown, and PDF loading
evaluate.py             Single-report extraction quality metrics
evaluate_dataset.py     Multi-case evaluation harness
main.py                 Offline review example
data/                   Sample inputs, fixtures, and expected items
test_*.py               Automated tests
```

## Possible next improvements

- OCR support for scanned PDFs.
- Table-aware BOQ extraction for complex spreadsheets.
- Embedding-based semantic matching in addition to token matching.
- Human review workflow for flagged discrepancies.
- Identity-based access control, rate limiting, and usage monitoring.
- Representative customer-approved evaluation data and reliability targets.
