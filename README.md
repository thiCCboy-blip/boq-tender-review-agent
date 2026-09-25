# BOQ / Tender Review Agent

An AI-assisted application that reviews a Bill of Quantities (BOQ) against a tender specification, highlights matching work items and unit discrepancies, and preserves source excerpts for review.

This is a portfolio project built to demonstrate document extraction, structured LLM outputs, deterministic validation, evaluation, and a working web interface.

## Live demo

[Open the deployed Streamlit app](https://amruu-boq-agent.streamlit.app/)

## Features

- Loads text, Markdown, and text-based PDF tender documents.
- Extracts explicit BOQ work items with descriptions, units, requirements, and source excerpts.
- Uses OpenAI Structured Outputs with Pydantic schemas.
- Matches BOQ rows to extracted tender items using token-overlap scoring.
- Normalizes common unit variants such as `cubic metres` → `m3` and `tonnes` → `t`.
- Runs deterministic quantity and amount checks.
- Reports precision, recall, F1, unit accuracy, and citation coverage on labelled sample data.
- Provides a Streamlit interface with JSON report download.
- Includes automated tests for review logic, document loading, comparison, and evaluation.

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
```

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
6. Add these secrets, then save and redeploy/restart the app:

   ```text
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-6-luna
   ```

7. Copy the generated `*.streamlit.app` URL for your README, resume, and portfolio.

Never put an API key in `app.py`, `README.md`, or a committed file. Anyone with the deployed app URL can run the AI step against the configured account, so add authentication and usage limits before sharing it publicly.

## Command-line usage

Review the bundled text sample:

```powershell
.\.venv\Scripts\python.exe .\run_review.py
```

Review a text-based PDF:

```powershell
.\.venv\Scripts\python.exe .\run_review.py --tender data\sample_tender.pdf --boq data\sample_boq.csv --output data\pdf_review_report.json
```

The runner prints each BOQ match and writes a JSON report containing the extracted items, match scores, unit status, and source excerpts.

## Tests and evaluation

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Evaluate a generated review report against the labelled sample expectations:

```powershell
.\.venv\Scripts\python.exe .\evaluate.py
```

`evaluate.py` currently evaluates the bundled `data/live_review_report.json`. The sample dataset produces perfect scores, which reflects a small controlled fixture rather than a production benchmark.

## Data and privacy

- Use only non-confidential documents for testing.
- Uploaded documents are written to a temporary directory for processing and removed afterwards.
- Tender text is sent to the configured OpenAI API when the AI step runs.
- The project does not currently implement OCR for scanned or image-only PDFs.
- The matching layer is deliberately explainable and deterministic, but it is not a replacement for professional quantity surveying or procurement review.

## Project structure

```text
app.py                  Streamlit web interface
llm_review.py           Structured OpenAI extraction
run_review.py           End-to-end CLI pipeline
comparison.py           BOQ matching and unit normalization
review.py               Deterministic amount and coverage checks
document_loader.py      TXT, Markdown, and PDF loading
evaluate.py             Extraction quality metrics
main.py                 Offline review example
data/                   Sample inputs, fixtures, and expected items
test_*.py               Automated tests
```

## Possible next improvements

- OCR support for scanned PDFs.
- Table-aware BOQ extraction for complex spreadsheets.
- Embedding-based semantic matching in addition to token matching.
- Human review workflow for flagged discrepancies.
- Authentication, rate limiting, and deployment for shared use.
