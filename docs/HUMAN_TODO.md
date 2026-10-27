# NyayaSetu HUMAN_TODO.md
# Tasks that require human work (law student, legal reviewer, or developer)
# Format: [ ] owner: task

## Law Student / Legal Reviewer
- [ ] reviewer: Review and sign off docs/legal_review.md temporal rules table (leave sign-off block empty until reviewed)
- [ ] reviewer: Verify transition_map entries — see eval/review/transition_priority60.csv (60 priority sections; verification_status='unverified')
- [ ] reviewer: Review offence_cards review CSV in eval/review/ for accuracy of elements and source_spans
- [ ] law-student: Write 50 scenario questions for eval/golden/scenarios.jsonl using template eval/golden/scenario_template.jsonl
- [ ] law-student: Review 20 draft temporal golden rows in eval/golden/temporal_draft.jsonl (provenance='draft', needs_review=true)
- [ ] law-student: Review 10 draft out-of-scope / harmful-intent rows in eval/golden/edge_draft.jsonl

## Developer
- [ ] developer: Download IPC and CrPC official PDFs and place in data/raw/statutes/ (IPC, CrPC not currently in data/raw/statutes/)
- [ ] developer: Download official concordance tables (BNS<->IPC, BNSS<->CrPC, BSA<->IEA) to data/raw/concordance/
- [ ] developer: Run `make eval-test --confirm` after human review of golden sets and record results in eval/results/
- [ ] developer: Hand-label 50 claims for NLI check — save to eval/nli_check.jsonl (needed before NLI entailment can be enabled)
- [ ] developer: Run Gemini judge-based faithfulness script on 50-item sample (separate from main eval)
- [ ] developer: Verify section counts if parser reports mismatch — do not silently force the target counts
