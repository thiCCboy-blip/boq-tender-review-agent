# Case Study: BOQ / Tender Review Agent

## Problem

Quantity surveying and tender teams often compare a Bill of Quantities against long tender documents manually. The work is repetitive, easy to get wrong, and difficult to audit when a reviewer cannot quickly see the source of an extracted item.

## User workflow

1. A estimator uploads a text-based PDF or text tender document.
2. They upload the BOQ CSV.
3. The application extracts explicit work items with a description, unit, requirement, and source excerpt.
4. Each BOQ row is matched to the closest extracted item.
5. Unit variants are normalized and discrepancies are flagged for human review.
6. The reviewer downloads a JSON report containing matches, evidence, and run metadata.

## Architecture

| Layer | Implementation | Responsibility |
| --- | --- | --- |
| Document ingestion | `document_loader.py` and `pypdf` | Read TXT, Markdown, and text-based PDF documents; label PDF pages |
| Structured extraction | `llm_review.py`, OpenAI Responses API, Pydantic | Return validated JSON-shaped tender items |
| Deterministic review | `comparison.py` and `review.py` | Match descriptions, normalize units, and check amounts/coverage |
| Evaluation | `evaluate.py` and `evaluate_dataset.py` | Measure extraction precision, recall, F1, units, and citations |
| Interface | `app.py` and Streamlit | Provide upload, review, metrics, and report download |
| Operations | Streamlit Community Cloud | Deploy the app from GitHub and store secrets outside the repository |

## Evaluation

The repository includes a labelled, nine-case synthetic fixture covering:

- Clean extraction
- Unit variants such as `tonnes` and `t`
- Lot-based items
- Missing items
- Unexpected extra items
- Missing source excerpts
- Empty documents
- Unit mismatches

Current micro metrics from `evaluate_dataset.py`:

| Metric | Score |
| --- | ---: |
| Precision | 0.889 |
| Recall | 0.889 |
| F1 | 0.889 |
| Unit accuracy | 0.875 |
| Citation coverage | 0.889 |

These are deliberately non-perfect results to demonstrate error analysis. They are not a production benchmark. A production evaluation would use representative, consented tender documents and domain-expert adjudication.

## Reliability and safety decisions

- The model is instructed not to invent quantities, rates, or requirements.
- Pydantic validates the model's structured response before it reaches the comparison layer.
- Source excerpts are retained so a reviewer can verify the result.
- Uploads are limited to 10 MB and processed in a temporary directory.
- An optional `APP_PASSWORD` gate protects the deployed demo.
- API keys and passwords are stored as deployment secrets, never in Git.
- The app reports model latency, token usage, and optional cost estimates.

## Trade-offs and limitations

- Token-overlap matching is explainable but can miss synonyms and complex scope language.
- Scanned PDFs require OCR, which is not implemented yet.
- The current application is a public prototype, not an authenticated enterprise service.
- The evaluation fixture is synthetic and small; it should be replaced with customer-approved data.
- A production system would need audit logs, identity and access management, rate limits, monitoring, and retention policies.

## Business value

The project demonstrates a path from a domain problem to a working AI-enabled workflow: reduce repetitive document review, surface discrepancies earlier, and preserve evidence for human sign-off. The next measurable outcome to validate with users would be reduction in review time and error rate on a representative tender package.

## Links

- Live app: https://amruu-boq-agent.streamlit.app/
- Source code: https://github.com/thiCCboy-blip/boq-tender-review-agent
