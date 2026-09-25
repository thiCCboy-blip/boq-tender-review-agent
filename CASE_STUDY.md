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
| Matching and retrieval | `comparison.py`, `retrieval.py` | Rank candidates by token overlap, embedding similarity, or fused ranks; normalize units |
| Deterministic review | `review.py` | Check amounts and coverage |
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

## Retrieval strategy comparison

The matching layer uses token-overlap scoring, chosen for explainability rather than accuracy. To find out how much accuracy that costs, a 20-case labelled fixture was built from the two situations that break a lexical matcher:

- **Synonym and paraphrase pairs** where the same work item is named differently (`Reinforcement steel` / `Rebar fabrication and fixing`).
- **Hard negatives** where distractors differ from the query by one distinguishing attribute (`Tiling to wet area walls` / `Tiling to wet area floors`).

| Strategy | hit@1 | hit@3 | MRR | Backend |
| --- | ---: | ---: | ---: | --- |
| `token_overlap` | 0.200 | 1.000 | 0.575 | in-process |
| `tfidf` | 0.200 | 0.900 | 0.558 | in-process |

The correct item is in the top three for all 20 cases but first in only four. The 16 failures split into 11 synonym or paraphrase cases and 5 hard negatives, and the two groups fail for opposite reasons. The synonym cases have no lexical bridge at all: "Reinforcement steel" and "Rebar fabrication and fixing" share no content token, so the correct item scores near zero. The hard negatives have too much: "Tiling to wet area walls" and "Tiling to wet area floors" differ by one token against a query of "Tiling to wet areas", so the shared tokens outweigh the distinguishing one and the matcher prefers the wrong item with high confidence. A correct ranking in both groups needs something a term-overlap score cannot provide.

The observable effect is that the matcher retrieves the right *neighbourhood* and then orders it incorrectly, which is the specific failure a domain user would report as "it found the section but picked the wrong line."

A second lexical strategy, TF-IDF with inverse document frequency weighting, was added to separate two explanations for that result. It scores the same 0.200 on hit@1, which rules out the cheaper explanation. The failure is not poorly weighted vocabulary; it is absent vocabulary. "Reinforcement" and "rebar" never co-occur in a candidate list, so no reweighting of the terms that are present can surface the match. This is the argument for a semantic model rather than a better lexical scorer, and it is the reason the fixture was designed with a third strategy in mind rather than an improved second one.

Both reported strategies run with no API key and no third-party dependency, so the table above is reproducible by a reviewer on a clean checkout. `embedding` and `hybrid` strategies are implemented in `retrieval.py`; hybrid uses reciprocal rank fusion, which combines the two rankings by position rather than by score, avoiding a tuned weight between an incomparable token-overlap score and a cosine similarity. Both were skipped in the recorded run because the API account had no remaining credit, and the harness reports the skip reason and names the backend behind each row rather than silently presenting fewer strategies. A populated embedding cache makes the comparison reproducible offline.

An earlier hypothesis that the embedding path would be available was not confirmed by this run. Closing it requires adding credit and re-running; the honest current state is that the lexical weakness is measured, the negative lexical result is confirmed, and the semantic fix is implemented but unverified.

## Reliability and safety decisions

- The model is instructed not to invent quantities, rates, or requirements.
- Pydantic validates the model's structured response before it reaches the comparison layer.
- Source excerpts are retained so a reviewer can verify the result.
- Uploads are limited to 10 MB and processed in a temporary directory.
- An optional `APP_PASSWORD` gate protects the deployed demo.
- API keys and passwords are stored as deployment secrets, never in Git.
- The app reports model latency, token usage, and optional cost estimates.

## Trade-offs and limitations

- Token-overlap matching is explainable but measurably weaker on synonyms and paraphrase; `syn-rebar` and `syn-excavation` rank the correct item third.
- Reciprocal rank fusion promotes candidates that both rankers agree on, but cannot break a tie where the two rankers merely swapped two items, because it scores by position and mirrored orderings are symmetric. This is a property of the method, not a defect, and is pinned by a test.
- Scanned PDFs require OCR, which is not implemented yet.
- The current application is a public prototype, not an authenticated enterprise service.
- The evaluation fixture is synthetic and small; it should be replaced with customer-approved data.
- A production system would need audit logs, identity and access management, rate limits, monitoring, and retention policies.

## Business value

The project demonstrates a path from a domain problem to a working AI-enabled workflow: reduce repetitive document review, surface discrepancies earlier, and preserve evidence for human sign-off. The next measurable outcome to validate with users would be reduction in review time and error rate on a representative tender package.

## Links

- Live app: https://amruu-boq-agent.streamlit.app/
- Source code: https://github.com/thiCCboy-blip/boq-tender-review-agent
