# NyayaSetu DECISIONS.md
# Format: date | decision | rationale

2026-10-22 | v0.0-baseline tag points to older commit (f61d6f1), not HEAD | Tag pre-existed; rule says create only if absent; leaving it to preserve original baseline
2026-10-22 | Golden set schema upgraded in place (not replaced) | Existing rows have valid questions; add missing fields with defaults to preserve annotator work
2026-10-22 | Makefile eval-dev and eval-test targets added; existing eval target retained as alias | Backward compatibility
2026-10-22 | gitleaks added to CI job (not only pre-commit) | C1.A requires it in GitHub Actions; pre-commit alone is insufficient for CI enforcement
2026-10-22 | configs/ directory created with retrieval.yaml; reranker model set bge-reranker-v2-m3 | C1.E spec; config-driven means model IDs never hardcoded
2026-10-22 | data/sources.yaml created from MANIFEST.json content | R7 requires fetching only URLs listed there; MANIFEST already has source URLs
2026-10-22 | scripts/make_manifest.py writes MANIFEST from sources.yaml + SHA-256 | MANIFEST.json existed without generator; script needed for reproducibility
2026-10-22 | tests/fixtures/ 20-section BM25 fixture extracted from BNS processed JSONL | Avoids network; deterministic; CI-safe
2026-10-22 | eval/results/ directory created; v0_baseline run executed before any retrieval change | C1.D requires baseline first
2026-10-27 | Dual-tier router is rules-based, not an LLM gateway | Lower hallucination and cost on direct lookups; Groq only on scenario tier
2026-10-27 | ChatGPT comparison is a live OpenAI call, never used as NyayaSetu's generator | User-requested contrast; Groq remains the only generation provider for grounded answers
