# NyayaSetu BUILD PROMPT: Phase 1 + Phase 2, then the overview doc

## Context (already decided, do not re-derive)
Repo: Indian criminal-law RAG (formerly Duel-Layer-Legal-RAG; LangGraph, FastAPI, Streamlit, FAISS, BM25+dense with RRF, an LLM 'firewall'). Target product NyayaSetu: a citation-verified bridge between old laws (IPC, CrPC, IEA) and new laws (BNS, BNSS, BSA). Differentiators:
1. Temporal Applicability Engine (pure rules, no LLM)
2. Transition Map (old section -> new section + change type)
3. Offence Cards + Ingredient Matcher
4. Machine-verified citations + calibrated abstention
Scope: Indian criminal law only. Budget: free tiers only (Groq = generator, Gemini = eval judge, Ollama = dev). The BUILD itself must use near-zero LLM calls, so prefer deterministic code.

## Rules (priority order)
R1. NEVER overwrite working code. Before touching a feature, check STATE.md; if DONE, skip it. Extend with new modules or small targeted edits (str_replace), never whole-file rewrites of existing files. Run `git diff --stat` before each commit to confirm no unintended deletions.
R2. NEVER fabricate: no invented eval numbers, no invented legal mappings, no invented section text, no guessed download URLs. Missing data or human work goes to docs/HUMAN_TODO.md, and you continue with what exists.
R3. TOKEN DISCIPLINE (cost matters; I am paying for premium models):
   - Never read the whole repo. Start with `git ls-files`, README, and targeted `grep -n`. Read files over 300 lines only by range (`sed -n`).
   - Do not re-read files you just wrote. Do not re-print files in chat. Do not explain code in chat.
   - Batch shell commands with &&. Always trim output: `pytest -q -x --tb=short 2>&1 | tail -25`, `| head -40`. Write large outputs to a file and print the tail.
   - Short code: minimal comments, no tutorial docstrings, no boilerplate.
   - Config-driven design (YAML) so one script covers many variants.
   - Chat reply after each task: at most 1 line. After each checkpoint: at most 8 lines (DONE / SKIPPED-already-existed / BLOCKED / NEXT).
   - Create only these docs: STATE.md, DECISIONS.md, HUMAN_TODO.md, limitations.md, PROJECT_OVERVIEW.md, plus README edits.
R4. No questions unless truly blocked. Otherwise decide, and log one line in docs/DECISIONS.md.
R5. No secrets in git. Keys only via .env (.env.example lists names). Mock all LLM calls in tests; use recorded fixtures.
R6. Commit after each task (conventional commits, e.g. `feat(temporal): ...`), on branch `phase1` then `phase2`. Do not push.
R7. Network: only fetch URLs the user wrote in data/sources.yaml. If network is unavailable, skip and log in HUMAN_TODO.md.

## Resume protocol
Fresh session: read ONLY this file and docs/STATE.md. Execute only the checkpoint named in the kickoff message. STATE.md format, one line per feature: `feature | DONE/PARTIAL/MISSING | path | evidence`. Update it at the end of every task.

## C0: Audit (cheap, do first, skip if STATE.md exists)
1. `git ls-files | head -100`, read README, grep for: rrf, firewall, langgraph, faiss, parser/ingest, tests, Dockerfile, CI, .env.example.
2. Write docs/STATE.md covering every feature in C1 and C2 below, marking DONE/PARTIAL/MISSING with file path.
3. If tag `v0.0-baseline` does not exist, create it on the current HEAD (before any change).

## C1: Phase 1 (hygiene, data, eval, retrieval). Do only items that are not DONE.
A. Hygiene: rename project strings to NyayaSetu; fix README clone URL; delete list_models.py; remove words 'zero-hallucination' and 'production-grade'; fix the LLM model ID by reading it from config, not hardcoded; add `.env.example`, pinned deps, ruff + pre-commit, Makefile (`ingest`, `index`, `eval-dev`, `eval-test`, `run`, `test`), Dockerfile (python:3.11-slim, works on Win/Mac/Linux), GitHub Actions (lint + unit tests + gitleaks).
B. Data layer: `src/nyayasetu/ingest/` parses official PDFs in data/raw/ to JSONL: `{id:'BNS-303', act, chapter, section_no, title, text, subsections[], illustrations[], explanations[], exceptions[], provisos[], effective_date, status, source_url, page}`. Illustrations, explanations, exceptions and provisos are child fields of the parent section, never separate chunks. Tests assert section counts per Act (BNS 358, BNSS 531, BSA 170, IPC 511 base sections plus lettered ones, CrPC 484, IEA 167; if the PDF disagrees, report it, do not silently force). Add contiguous-numbering and non-empty-body checks. `scripts/make_manifest.py` writes data/MANIFEST.json (source URL from data/sources.yaml, date, SHA-256). Parse the BNSS First Schedule (classification of offences) into SQLite table `offence_classification(section, cognizable, bailable, compoundable, triable_by, punishment_text)`.
C. Golden set `eval/golden/*.jsonl`, each row: `{id, type, question, expected_ids[], expected_points[], answerable, provenance:'auto'|'draft'|'human', needs_review}`.
   - Auto-generate from the corpus where truth is deterministic: ~100 lookup questions (expected id = the section), ~20 unanswerable with nonexistent sections (e.g. 'BNS 999', answerable=false).
   - Draft rows (provenance 'draft', needs_review true) for out-of-scope and harmful-intent cases (max 10) and temporal cases (max 20).
   - Do NOT write scenario questions or expected legal answers; add a template file and list the needed count (50 scenarios) in HUMAN_TODO.md.
   - Deterministic split by hash(id): 40% dev, 60% test. `make eval-test` must require `--confirm` and append to eval/test_run_log.md. Report metrics separately per provenance.
D. Eval harness `eval/run.py` (config-driven, no LLM): Recall@5, Recall@10, MRR, nDCG@10, with 95% bootstrap CI (1000 resamples), results to eval/results/<run_id>.json, and an auto-generated markdown table. Run the CURRENT retrieval first as the baseline result named `v0_baseline` BEFORE any retrieval change.
E. Retrieval upgrade (config switchable, `configs/retrieval.yaml`):
   - bge-m3 embeddings (index script runnable on CPU and as a Colab-friendly script; checkpoint embeddings to disk so they are never recomputed)
   - bge-reranker-v2-m3 on the top 20
   - parent-child retrieval (match the subsection, return the full section with illustrations and provisos)
   - exact-match router: queries such as 'BNS 103' or 'Section 302 IPC' go to a SQLite lookup, not vectors.
   Ablation rows via one command: bm25 | dense-MiniLM(v0) | dense-bge-m3 | hybrid-RRF | hybrid+rerank | hybrid+rerank+parent-child, on dev. Write eval/results/ablation.md.
F. Tests: parser, router, metrics. CI also runs a tiny BM25-only retrieval regression on a 20-section fixture (tests/fixtures) and fails if Recall@5 drops more than 2 points. The full eval runs locally only.
STOP after C1: update STATE.md, commit, print the 8-line report, and tell me to `/clear` and send the kickoff for C2.

## C2: Phase 2 (the unique core). Do only items that are not DONE. Reuse existing LangGraph nodes, RRF and firewall code; insert new nodes rather than rebuild.
A. Provider layer `src/nyayasetu/llm/`: Groq -> Gemini -> degraded mode (no LLM: return verbatim sections + offence card + transition row). SQLite cache keyed by sha256(normalized prompt + model). Exponential backoff with jitter. Model IDs come from config. Token/latency counters logged per call.
B. Transition Map: SQLite `transition_map(old_act, old_section, new_act, new_section, relation, change_summary, old_punishment, new_punishment, source_url, verification_status)`; relation in {identical, reworded, punishment_changed, merged, split, new, omitted, moved}. Write a parser for the official concordance tables the user places in data/raw/concordance/ (BNS<->IPC full; BNSS<->CrPC and BSA<->IEA the same way). Set verification_status='unverified' for all. Never infer mappings with an LLM. Export the 60 priority sections to eval/review/transition_priority60.csv for human verification and list it in HUMAN_TODO.md. Auto-generate ~60 transition golden questions from the table (provenance 'auto').
C. Temporal Applicability Engine `src/nyayasetu/temporal/rules.py`: a pure function, no LLM. CUTOVER = 2024-07-01. Inputs: offence_date, proceeding_start_date (or None), proceedings_pending_at_cutover (bool or None). Implement EXACTLY these rules and mark every rule `status='draft_pending_review'`:
   - offence_date >= CUTOVER -> BNS (substance), BNSS (procedure), BSA (evidence).
   - offence_date < CUTOVER -> IPC (substance; cite Article 20(1) and the BNS repeal-and-savings section).
   - Procedure: proceeding started on/after CUTOVER and none pending -> BNSS. Pending at CUTOVER -> CrPC continues (cite the BNSS repeal-and-savings section).
   - Evidence: no pending proceeding at CUTOVER -> BSA; pending at CUTOVER -> NEEDS_LAWYER.
   - Pre-cutover offence where the mapped punishment relation is `punishment_changed` -> NEEDS_LAWYER (beneficial-punishment question).
   - Missing inputs -> NEEDS_INPUT listing the missing fields.
   Output: dataclass {substantive, procedural, evidence, reasons[], citations[] (section ids looked up from the corpus, not hardcoded text), needs_lawyer, status}. Truth-table unit tests cover every branch. Create docs/legal_review.md with the rule table and a sign-off block left EMPTY for a human reviewer. Do not claim it is reviewed.
D. Offence Cards: `data/priority_sections.yaml`: 60 BNS sections chosen by title keywords (theft, robbery, extortion, cheating, criminal breach of trust, mischief, hurt, grievous hurt, murder, culpable homicide, kidnapping, sexual offences, cruelty by husband, defamation, criminal intimidation, forgery, stolen property, trespass, house-breaking, rioting, unlawful assembly, abetment, criminal conspiracy, negligence, plus BNS-only: snatching, organised crime, mob lynching). Offline script produces `data/offence_cards/<id>.json`: elements[{type, description, source_span}], punishment, classification (joined from offence_classification), old_ipc_equivalent (joined from transition_map). Each element's source_span must be a verbatim normalized substring of the section text (reject and retry once, otherwise drop). Skip cards that already exist. Export a review CSV and list it in HUMAN_TODO.md.
E. Ingredient Matcher: scenario -> facts -> per-element PRESENT/MISSING/UNCLEAR with the supporting fact and the quote. The output wording is 'provisions potentially attracted', never a guilt verdict.
F. Verified generation graph (LangGraph), nodes: guard (rules first; LLM only if ambiguous; refuse evasion, evidence-destruction and harm requests) -> router (SQLite lookup | transition | temporal | ingredient | hybrid retrieval) -> retrieve -> sufficiency check (reranker score vs threshold; LLM judge only in the borderline band) -> generate (Pydantic JSON: claims[{text, cites[{id, quote<=40 words}]}], one retry on schema failure) -> verify -> render.
   verify = deterministic: the id exists in the corpus AND the normalized quote (casefold, collapsed whitespace, normalized quotes) is a substring of that section. Failing claims are dropped. If more than 30% fail, regenerate once, then abstain. Optional NLI claim entailment only if it scores at least 80% on a 50-claim hand-labelled file (eval/nli_check.jsonl, listed in HUMAN_TODO.md); until that exists, leave it disabled. Render with numbered citations and a source panel.
G. Calibration `eval/calibrate.py`: choose thresholds on dev, write configs/thresholds.yaml and a risk-coverage CSV. Test-set metrics only through `make eval-test --confirm`. Generation metrics: citation validity (deterministic), abstention precision/recall, false-refusal rate, latency p50/p95, tokens/query. Judge-based faithfulness is a separate script using Gemini, run on a 50-item sample only.
H. Tests: temporal truth table, verifier (valid, invalid id, altered quote, near-miss), router, provider fallback with mocks, degraded mode, cache hit.
STOP after C2: update STATE.md, commit, tag `v1.0` ONLY if every exit gate below is met; otherwise tag `v1.0-rc` and list the unmet gates in HUMAN_TODO.md. Print the 8-line report.

## C3: Final doc (no new features)
Write docs/PROJECT_OVERVIEW.md (max 1,800 words), sections:
1. The pain: who suffers and why (old/new law transition confusion; generic chatbots invent sections and cite wrongly; no way to verify; no temporal logic; free-tier constraints for students).
2. The solution in one paragraph.
3. Feature table: feature | what it does | how it works | status (implemented / partial / planned for Phase 3) | file path. Take status from STATE.md only.
4. How it works: one ASCII pipeline diagram plus one real example query traced step by step (use a real run from the code).
5. Operations: setup, make commands, config files, free-tier fallback chain and degraded mode, how to update data when laws are amended, what is logged.
6. Evidence: copy numbers ONLY from eval/results/*.json; mark anything absent 'pending'. Include CIs and the baseline vs current comparison.
7. Limitations and safety: not legal advice, partial verification, bounded scope, anything unreviewed (temporal rules, mappings, cards).
8. Next (Phase 3): precedent bridge, UI tabs, Hindi, deployment, user study.
Also: add a README section linking this file, write docs/limitations.md (10 lines), finalize HUMAN_TODO.md as a checklist grouped by owner (you / law student / reviewer). Commit.

## Exit gates for v1.0 (all must be true; report the actual values)
- Fresh clone -> `make test` green; `docker compose up` works.
- Parser tests green; baseline + ablation results exist in eval/results/.
- Temporal truth-table tests green; a verifier test proves a fabricated section id or altered quote never reaches the output.
- Citation validity is 100% on the dev run (any failure is a bug to fix).
- Degraded mode works with LLM keys unset.
- No README or doc number lacks a result file. No 'zero-hallucination' wording anywhere.