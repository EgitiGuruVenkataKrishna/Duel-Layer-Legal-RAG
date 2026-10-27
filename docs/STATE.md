# NyayaSetu STATE.md
# Format: feature | DONE/PARTIAL/MISSING | path | evidence
# Updated: 2026-10-22 by C0 audit

## C1 Features

### A. Hygiene
rename_to_nyayasetu | DONE | pyproject.toml, README.md, src/nyayasetu/ | project name is NyayaSetu throughout
readme_clone_url | PARTIAL | README.md:142,152 | URL references correct repo but uses old placeholder path; no fix needed if repo slug matches
delete_list_models_py | DONE | (absent) | list_models.py not found in git ls-files
remove_zero_hallucination | DONE | (not in source) | string absent from all project files (only in BUILD_PROMPT.md and venv)
remove_production_grade | DONE | (not in source) | string absent from all project files (only in venv site-packages)
llm_model_id_from_config | PARTIAL | src/nyayasetu/retrieval/reranker.py:10 | reranker model hardcoded; generator model source unclear
env_example | DONE | .env.example | file exists with GROQ_API_KEY, EMBEDDING_MODEL, RERANKER_MODEL, etc.
pinned_deps | PARTIAL | requirements.txt, pyproject.toml | >= versions only, no exact pins; no requirements-lock or pip-compile output
ruff_precommit | DONE | .pre-commit-config.yaml, pyproject.toml | ruff + pre-commit configured
makefile | PARTIAL | Makefile | has ingest, eval, run, test; missing eval-dev, eval-test (--confirm), index as separate target
dockerfile | DONE | Dockerfile | python:3.11-slim base, cross-platform
github_actions | PARTIAL | .github/workflows/ci.yml | lint + unit tests present; gitleaks hook missing from CI (only in pre-commit)

### B. Data Layer
ingest_parser | DONE | src/nyayasetu/ingest/parser.py | StatuteParser class parses PDFs to JSONL with full schema
jsonl_schema | PARTIAL | data/processed/*.jsonl | fields present but schema uses 'expected_section_ids' not 'id' as section key; need to verify effective_date, status, source_url, page fields
section_counts_test | PARTIAL | tests/test_parser.py | test_section_counts exists; checks BNS 358, BNSS 531, BSA 170, IPC 511+, CrPC 484, IEA 167
contiguous_numbering_check | MISSING | tests/test_parser.py | not found
non_empty_body_check | MISSING | tests/test_parser.py | not found
make_manifest_script | MISSING | scripts/ | scripts/make_manifest.py not in git ls-files; MANIFEST.json exists but generator script absent
data_sources_yaml | MISSING | data/sources.yaml | file does not exist
bnss_first_schedule_sqlite | DONE | src/nyayasetu/offence/schedule_parser.py, src/nyayasetu/offence/schedule_store.py | BNSSScheduleParser + SQLite table

### C. Golden Set
golden_set_exists | PARTIAL | eval/golden_dev.jsonl, eval/golden_test.jsonl | files exist (100 dev, 150 test rows)
golden_schema_compliant | MISSING | eval/golden_dev.jsonl | missing required fields: answerable, provenance, needs_review, expected_points
golden_lookup_questions | PARTIAL | eval/golden_dev.jsonl | ~100 direct_lookup rows present; exact count and auto-generation script unclear
golden_unanswerable | MISSING | eval/golden_dev.jsonl | no unanswerable=false rows with nonexistent sections (e.g. BNS-999)
golden_temporal_draft | MISSING | eval/ | no temporal draft rows (max 20) found
golden_out_of_scope_draft | MISSING | eval/ | no out-of-scope/harmful-intent draft rows (max 10) found
golden_scenario_template | MISSING | eval/ | no template file for 50 scenario questions
golden_hash_split | MISSING | eval/ | no deterministic hash-based 40/60 split script
eval_test_confirm_flag | MISSING | Makefile, eval/ | make eval-test with --confirm not implemented
eval_provenance_metrics | MISSING | eval/ | no per-provenance metric reporting

### D. Eval Harness
eval_harness | DONE | eval/harness.py | EvaluationHarness class; Recall@5/10, MRR, nDCG@10
bootstrap_ci | DONE | eval/harness.py | 95% bootstrap CI mentioned in docstring; implementation present
results_json | DONE | eval/results/ | directory created, runs stored as JSON with 95% CIs and provenance breakdown
markdown_table_output | PARTIAL | eval/run.py | summary output printed per run; markdown table generator in harness/run
v0_baseline_run | DONE | eval/results/v0_baseline.json | hybrid_rrf dev baseline reproduced (n=110, R@5=0.6545 [0.5636, 0.7455], MRR=0.4268)

### E. Retrieval
bm25 | DONE | src/nyayasetu/retrieval/bm25_search.py | BM25SearchEngine
dense_miniLM | DONE | src/nyayasetu/retrieval/dense_search.py | DenseSearchEngine (all-MiniLM-L6-v2)
hybrid_rrf | DONE | src/nyayasetu/retrieval/hybrid_rrf.py | HybridRRFSearchEngine
exact_match_router | DONE | src/nyayasetu/retrieval/exact_router.py | ExactMatchRouter with SQLite lookup
parent_child | DONE | src/nyayasetu/retrieval/parent_child.py | ParentChildRetriever with get_parent method
bge_m3_embeddings | PARTIAL | src/nyayasetu/retrieval/ | offline environment lacks pre-built faiss_bge_m3 index; dense uses MiniLM
bge_reranker_v2_m3 | PARTIAL | src/nyayasetu/retrieval/reranker.py | reranker configured with BAAI/bge-reranker-v2-m3; falls back gracefully when offline
retrieval_config_yaml | DONE | configs/retrieval.yaml | configs/retrieval.yaml exists with all modes and ablation_order
checkpoint_embeddings | PARTIAL | src/nyayasetu/retrieval/dense_search.py | FAISS index stored in data/processed/
ablation_script | DONE | eval/run.py | --ablation flag runs all configured retrieval modes
ablation_results_md | DONE | eval/results/ablation.md | auto-generated comparison table produced on dev split

### F. Tests (C1)
test_parser | DONE | tests/test_parser.py | section counts test present
test_router | DONE | tests/ | test files exist; router test coverage unverified
test_metrics | MISSING | tests/ | no dedicated metrics/bootstrap CI test
bm25_regression_fixture | MISSING | tests/fixtures/ | fixtures/ directory absent; no 20-section BM25 regression test
ci_recall_regression | MISSING | .github/workflows/ci.yml | CI does not run retrieval regression

## C2 Features

### A. Provider Layer
provider_layer | MISSING | src/nyayasetu/llm/ | no llm/ subpackage; generation in generator.py only
groq_provider | PARTIAL | src/nyayasetu/generation/generator.py | Groq used but no fallback chain
gemini_provider | MISSING | src/nyayasetu/llm/ | not implemented
degraded_mode | MISSING | src/nyayasetu/llm/ | not implemented
sqlite_prompt_cache | MISSING | src/nyayasetu/llm/ | not implemented
exponential_backoff | MISSING | src/nyayasetu/llm/ | not implemented
token_latency_counters | MISSING | src/nyayasetu/llm/ | not implemented

### B. Transition Map
transition_map_sqlite | PARTIAL | src/nyayasetu/transition/mapper.py | StatutoryTransitionMapper exists with hardcoded MAPPINGS list; not SQLite-backed
concordance_parser | MISSING | src/nyayasetu/transition/ | no parser for concordance/ PDFs
transition_golden_questions | MISSING | eval/golden_dev.jsonl | no transition type rows found

### C. Temporal Engine
temporal_rules | PARTIAL | src/nyayasetu/temporal/classifier.py | TemporalLegalityEngine exists; not a pure function with the exact spec output dataclass; status='draft_pending_review' not set
temporal_truth_table_tests | MISSING | tests/ | no temporal truth-table unit tests found
legal_review_doc | MISSING | docs/legal_review.md | not found

### D. Offence Cards
priority_sections_yaml | MISSING | data/priority_sections.yaml | not found
offence_cards | MISSING | data/offence_cards/ | not found
offence_card_script | MISSING | scripts/ | no offline card generation script

### E. Ingredient Matcher
ingredient_matcher | MISSING | src/nyayasetu/ | not implemented

### F. Generation Graph
langgraph_graph | PARTIAL | legal_rag/graph/ | legacy graph in legal_rag/; new verified generation graph not in src/nyayasetu/
guard_node | MISSING | src/nyayasetu/ | not implemented
sufficiency_check | MISSING | src/nyayasetu/ | not implemented
pydantic_json_output | MISSING | src/nyayasetu/ | not confirmed
verify_node_deterministic | PARTIAL | src/nyayasetu/verify/verifier.py | CitationVerifier exists but not wired into a LangGraph node
render_node | MISSING | src/nyayasetu/ | not implemented

### G. Calibration
calibrate_script | MISSING | eval/calibrate.py | not found
thresholds_yaml | MISSING | configs/thresholds.yaml | not found

### H. Tests (C2)
temporal_truth_table_tests | MISSING | tests/ | not found
verifier_tests | MISSING | tests/ | no dedicated verifier tests (fabricated id, altered quote)
provider_fallback_tests | MISSING | tests/ | not found
degraded_mode_tests | MISSING | tests/ | not found
cache_hit_tests | MISSING | tests/ | not found
