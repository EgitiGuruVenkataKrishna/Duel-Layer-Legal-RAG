# NyayaSetu — Master Agent Instructions

## 1. Mission

Build NyayaSetu into a tested, documented, evidence-backed v1.0 legal research assistant for Indian criminal law.

**Core purpose:** Help users understand the transition between the Indian Penal Code (IPC), Code of Criminal Procedure (CrPC), Indian Evidence Act (IEA), and their successor laws: Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA).

The system must prioritize:
- Correct legal sources and traceable citations.
- Reliable retrieval and calibrated abstention.
- Date-aware legal applicability.
- Verifiable offence and transition information.
- Reproducible evaluation.
- Low-cost development on available hardware.
- A usable interface and straightforward setup.

This is a legal information and research tool, not a substitute for a qualified lawyer. Never represent unverified outputs as authoritative legal advice.

## 2. Project Context

- Repository: NyayaSetu.
- Local development: Windows and PowerShell.
- Hardware: Intel Core i7, Intel Iris Xe integrated graphics, 16 GB RAM.
- Prioritize CPU-compatible, resource-efficient solutions.
- Prefer free or low-cost services and APIs.
- Use the existing architecture where practical; do not introduce unnecessary frameworks.
- Keep legal source material, evaluation data, generated outputs, and application code clearly separated.

Before implementation, inspect the actual repository. Do not assume a file, dependency, test, command, dataset, or feature exists until verified.

## 3. Operating Rules

### 3.1 Preserve existing work

Before editing:
1. Run `git status --short`.
2. Confirm the current branch and recent commits.
3. Inspect relevant files and existing changes.
4. Read `docs/STATE.md` and identify the next incomplete task.

Never discard user changes, reset the repository, force-push, or automatically overwrite existing work.

Do not commit unrelated changes. Stage only the intended files.

### 3.2 Work incrementally

- Complete one queue task per implementation session; at most two tightly related tasks if genuinely small.
- Prefer minimal, targeted edits.
- Do not rewrite entire files when a small change is sufficient.
- Avoid unrelated refactoring and dependency additions.
- Inspect the diff after every meaningful change.
- Run the narrowest relevant tests first, then broader tests when appropriate.
- Stop and report blockers instead of inventing missing data or silently bypassing failures.

### 3.3 Use tools efficiently

- Inspect only the files needed for the current task.
- Avoid repeatedly reading large files or dumping entire directories.
- Use targeted searches and concise command output.
- Prefer deterministic scripts and tests over manual inspection.
- Use mocks for LLM-dependent tests wherever possible.
- Do not spend API credits on tests that can be completed offline.
- Keep implementation prompts and session reports concise.

### 3.4 Legal accuracy

- Never invent statutory provisions, quotations, citations, case names, legal mappings, commencement dates, or legal conclusions.
- Preserve the exact wording and provenance of source material.
- Distinguish statutory text from interpretation, commentary, and model-generated explanations.
- Account for relevant commencement dates, transitional provisions, and legally applicable dates.
- Do not assume a successor provision is legally equivalent to a predecessor merely because their wording looks similar.
- If authoritative data is missing, record the gap in `HUMAN_TODO.md`.
- Clearly label fixtures, illustrative examples, and unverified mappings.
- Do not publish unreviewed legal cards or mappings as authoritative.

### 3.5 Evidence-backed claims

Any reported benchmark must come from a reproducible evaluation artifact.

Do not fabricate:
- Retrieval recall or precision.
- Citation-validity rates.
- Latency or token usage.
- User counts or production performance.
- Confidence intervals or evaluation sample sizes.

For each metric, preserve the evaluation dataset, method, denominator, and result artifact where practical.

Do not use the held-out test set to tune the system.

### 3.6 Secrets and costs

- Never commit API keys, tokens, credentials, or `.env` files containing secrets.
- Use environment variables and `.env.example`.
- Avoid unnecessary LLM calls.
- Cache deterministic or reusable responses where safe.
- Implement timeouts, bounded retries, and graceful failure.
- Do not make paid API calls without a clear need.
- Tests must run without real API credentials wherever practical.

## 4. Canonical Project State

Use **`docs/STATE.md`** as the single canonical progress tracker.

After each completed task, update it with:
- Task ID and status.
- Files changed.
- Tests and commands executed.
- Actual outcomes, including failures.
- Relevant evaluation artifacts.
- Known limitations.
- The exact next task.

Maintain `HUMAN_TODO.md` for decisions requiring a human, especially legal review, unavailable authoritative data, and unresolved release gates.

Do not claim that a human review occurred unless it actually did.

## 5. Preflight Checklist

Before starting a task, inspect:

1. `git status --short`
2. Current branch and recent commit history.
3. The first 50 lines of `docs/STATE.md`, plus the relevant task entry.
4. Relevant specifications, implementation files, and tests.

Use PowerShell-compatible commands. If a suggested command is unavailable, use an equivalent already installed in the environment.

If the working tree contains changes, preserve them and determine whether they affect the task before editing.

Do not start implementation until the current task and its acceptance criteria are clear.

## 6. Required Task Workflow

For every task:

1. **Inspect:** Read the relevant code, tests, specifications, and current state.
2. **Plan:** Identify the smallest viable change and its acceptance criteria.
3. **Implement:** Make targeted changes that preserve unrelated behavior.
4. **Test:** Run relevant unit, integration, regression, or lint checks.
5. **Review:** Inspect the diff for accidental changes, unsupported claims, secrets, and regressions.
6. **Document:** Update `docs/STATE.md` and `HUMAN_TODO.md` when necessary.
7. **Report:** State what changed, what passed, what failed, and what remains.

Never claim a test passed unless the command actually completed successfully.

If a task is blocked by missing data, credentials, dependencies, or legal decisions, document the blocker and continue only with safe, independent work.

## 7. Development Queue

Follow this order unless repository evidence establishes a concrete dependency or blocker. If the existing code differs from these assumptions, inspect it and adapt the task rather than blindly recreating functionality.

### Q1 — Repository and evaluation audit

- Inspect the repository structure, evaluation pipeline, datasets, retrieval implementation, and existing tests.
- Verify the C1 evaluation files and data split.
- Verify that unanswerable or draft rows are excluded from recall calculations when appropriate.
- Verify that citations and provenance are represented consistently.
- Confirm the evaluation runner's actual interface, including `eval/run.py --help` if it exists.
- Record the current state and blockers.

**Acceptance:** Reproducible audit findings, verified file paths, and a clear next step.

### Q2 — Reproduce the retrieval baseline

- Reproduce the existing MiniLM + BM25 + Reciprocal Rank Fusion (RRF) baseline if supported by the repository.
- Do not silently introduce a reranker or parent-child retrieval into the baseline.
- Save results to `eval/results/v0_baseline.json`, adapting the path only if the repository's existing evaluation conventions require it.
- Record dataset version, configuration, metrics, sample size, and any applicable confidence intervals.
- If reproduction is impossible, document the exact reason.

**Acceptance:** A reproducible baseline or a clearly documented blocker.

### Q3 — Retrieval improvements and ablation

- Evaluate suitable embedding, reranking, and parent-child retrieval options.
- Consider BGE-M3 only if its resource requirements, compatibility, and measured benefits justify it.
- Keep components configurable.
- Measure the contribution of each component independently.
- Preserve the baseline for comparison.
- Avoid adding complexity without measurable improvement.

**Acceptance:** Comparable baseline and ablation artifacts with documented configurations.

### Q4 — BNSS offence classification

- Inspect available authoritative BNSS First Schedule data.
- Implement a structured offence-classification representation and SQLite integration if consistent with the existing architecture.
- Add tests for representative records and missing-data behavior.
- Verify the legal source and data provenance.

**Acceptance:** Tested lookups using traceable source data. Fixtures must be labelled as fixtures.

### Q5 — Temporal applicability engine

- Implement a deterministic, testable function for date-aware legal applicability.
- Separate legal rules from LLM-generated language.
- Cover commencement, relevant transition periods, and applicable exceptions supported by verified sources.
- Add truth-table tests for supported cases.
- Create a legal-review section in `docs/legal_review.md`.

**Acceptance:** Deterministic tests pass, and unsupported legal scenarios are explicitly identified.

### Q6 — Citation verifier

- Define a structured output schema using the project's existing validation approach, such as Pydantic where appropriate.
- Validate statutory identifiers against the available authoritative corpus.
- Check quoted text against source text.
- Reject nonexistent provisions and materially altered quotations.
- Test valid citations, fake identifiers, altered quotations, and near-miss cases.
- Implement the project's supported abstention or confidence rule, including the 30% threshold only if it is already an agreed requirement.

**Acceptance:** Invalid references cannot silently pass verification.

### Q7 — Legal transition mapping

- Define a schema for predecessor-to-successor legal mappings.
- Prefer authoritative concordance tables and verified legal sources.
- Do not infer legal mappings from an LLM.
- If authoritative data is unavailable, use `data/transition_input.csv` only as a clearly labelled input or fixture, with a small illustrative test dataset.
- Add tests for lookup, missing mappings, and ambiguous relationships.
- Record unverified mappings in `HUMAN_TODO.md`.
- Generate a priority CSV for human review if useful.

**Acceptance:** Every published mapping has provenance and an explicit verification status.

### Q8 — LLM provider layer

- Inspect existing provider abstractions before adding another.
- Support the configured providers, such as Groq and Gemini, only where required by the current project.
- Provide timeouts, bounded retries, caching, and graceful degradation.
- Track token usage and latency when the provider exposes those values.
- Use mocks in tests.
- Confirm the application still behaves safely when API keys are absent.

**Acceptance:** Provider failures do not crash unrelated application functionality or fabricate legal answers.

### Q9 — Workflow orchestration

- Integrate retrieval, routing, sufficiency checks, citation verification, and response rendering.
- Use the project's existing orchestration framework; introduce LangGraph only if it provides a concrete benefit.
- Add mocked end-to-end tests for supported routes.
- Ensure that low-confidence or insufficiently supported questions can be refused safely.

**Acceptance:** Each supported route has a test demonstrating the expected behavior.

### Q10 — Evaluation and calibration

- Evaluate retrieval quality, citation validity, abstention, false refusals, latency, and token usage where measurable.
- Store thresholds in a configuration file such as `thresholds.yaml` if appropriate.
- Generate a development evaluation artifact such as `eval/results/gen_dev.json`.
- Include the evaluation method, denominator, and dataset details.
- Create risk-coverage or calibration artifacts only where the available data supports them.
- Never tune against the held-out test set.

**Acceptance:** Reproducible development metrics with clearly defined calculations.

### Q11 — Continuous integration and security

- Add or repair GitHub Actions for linting, unit tests, regression tests, and secret scanning.
- Use existing project tooling where possible.
- Fix issues caused by the changes made in this project.
- Check the actual workflow result if GitHub CLI access is available.
- Do not claim remote CI passed when it was not run or its result could not be inspected.

**Acceptance:** Required checks run reproducibly, with unavailable checks documented.

### Q12 — Release candidate preparation

- Review the complete diff and repository status.
- Confirm that required tests and security checks pass.
- Resolve unintended generated files and data artifacts.
- Prepare a release candidate only when its stated gates are satisfied.
- Merge, push, or tag only after confirming the target branch and remote.
- Never force-push.

**Acceptance:** A release candidate whose actual status is accurately documented.

### Q13 — Documentation and reproducibility

Update the README and relevant documentation to cover:
- Problem and intended users.
- Architecture and data flow.
- Installation and quickstart.
- Configuration and API setup.
- Tests and evaluation commands.
- Actual benchmark results and limitations.
- Legal-data provenance and review status.
- Known failure modes.

Create or update `docs/limitations.md` and `HUMAN_TODO.md` as appropriate.

Keep the overview concise. All numerical claims must be supported by actual evidence.

**Acceptance:** Another developer can understand the project, run it, and reproduce supported results.

### Q14 — Application interface

- Inspect the existing UI before modifying it.
- Implement a clean interface for supported features, such as:
  - Ask a legal question with visible sources.
  - Inspect why a response was given or refused.
  - Check date-dependent applicability.
  - Look up an offence or verified legal transition.
- Make missing data and provider errors explicit.
- Include an appropriate legal-information disclaimer.
- Add a health endpoint if the existing backend architecture supports one.
- Verify the actual Docker build or document why it cannot run.

**Acceptance:** The interface handles normal, unsupported, and failure scenarios safely.

### Q15 — Offence cards and ingredient matching

- Build structured offence cards only from verified source material.
- Implement ingredient matching with traceable source spans.
- Preserve verbatim source text where required.
- Generate a review CSV for human validation.
- Enforce a maximum of 60 total LLM calls for this task, including retries; prefer caching and mocks.
- If credentials are unavailable, skip live generation and document the result.
- Never publish unreviewed cards as authoritative legal content.

**Acceptance:** Output is traceable, bounded in cost, and clearly marked for review where necessary.

### Q16 — Final held-out evaluation

This is a protected final evaluation step.

- Inspect the evaluation command and test-split safeguards before running.
- Run `make eval-test --confirm` exactly once, only if that command exists and the repository's safeguards are understood.
- Do not tune, alter thresholds, or select features based on held-out test results.
- Record the run in `eval/test_run_log.md`, adapting only to established repository conventions.
- Run any supported result-injection script, such as `inject_results.py`, only after inspecting its behavior and confirming it does not modify the test data or silently alter results.
- Verify all release gates against actual evidence.

Check at least:
- Fresh-clone setup and documented test commands.
- Relevant unit, integration, and regression tests.
- Reproducible retrieval baseline and ablations.
- Temporal applicability truth-table tests.
- Rejection of fabricated statutory identifiers.
- Citation validity with its denominator and calculation method.
- Safe behavior when providers or credentials are unavailable.
- No unsupported benchmark claims in documentation.
- CI status, or a precise explanation of why it could not be checked.
- Legal-review and data-provenance gaps.

If a required gate fails, do not claim a production-ready v1.0. Document the failure and keep the release candidate status accurate.

**Acceptance:** A one-time held-out result, a transparent release-gate report, and no test-set leakage.

### Q17 — Optional Precedent Bridge

Attempt only if usable, legally appropriate judgment data already exists under a path such as `data/raw/judgments/`.

- Preserve source provenance and verbatim judgment paragraphs.
- Link legal transitions only where the relationship has been verified.
- Distinguish precedent retrieval from statutory interpretation.
- Do not invent judgments, quotations, or transferability conclusions.
- Avoid this stretch task if it threatens completion of core release requirements.

**Acceptance:** A narrowly scoped, traceable prototype or a documented reason to defer it.

## 8. Git and Release Safety

Before any commit:
1. Inspect `git status --short`.
2. Inspect the complete diff, including staged and unstaged changes.
3. Confirm that only intended files are staged.
4. Check for secrets and accidental deletion of important files.
5. Check for unexpectedly large staged files. A file over 5 MB requires explicit justification; block it by default.
6. Run the relevant tests.

Use explicit file paths when staging. Do not blindly stage the entire repository.

Run secret scanning with an available tool such as Gitleaks if installed. A custom regex is not a substitute for a reliable secret scanner.

Before pushing:
- Confirm the branch.
- Confirm the remote.
- Inspect the commits to be pushed.
- Never force-push.
- Never claim that a push or remote release succeeded without verifying the command result.

Do not create a tag merely to make progress appear complete. Tags must reflect the actual release state.

## 9. Definition of Done

NyayaSetu v1.0 is complete only when:

- The documented setup works from a clean checkout.
- Required tests pass, or remaining failures are explicitly accepted and documented.
- Retrieval quality is measured against a reproducible baseline.
- Citation verification and abstention behavior are tested.
- Temporal applicability follows verified rules.
- Legal mappings and data have traceable provenance.
- The held-out evaluation was performed under the stated safeguards.
- Documentation reports only evidence-backed results.
- Secrets and unintended files are not committed.
- Release gates and unresolved human decisions are clearly recorded.
- Git, remote, and tag status are verified rather than assumed.

A working demo alone does not establish legal accuracy or production readiness.

## 10. Session Report

At the end of each implementation session, provide:

- **Task:** ID and objective.
- **Changed:** Important files and behavior.
- **Tests:** Commands run and actual outcomes.
- **Evidence:** Evaluation artifacts or logs produced.
- **Blockers:** Unresolved issues and human decisions.
- **Next:** Exact next task and its acceptance criteria.

Keep this report concise and update `docs/STATE.md` before finishing.

## 11. Kickoff Instruction

At the start of a new session:

1. Read `docs/AGENT.md`.
2. Read the first 50 lines of `docs/STATE.md`, then inspect the current task entry.
3. Inspect Git status and the current branch.
4. Identify the next incomplete task.
5. Inspect only the relevant files and tests.
6. State the task and acceptance criteria briefly.
7. Implement the smallest safe change.
8. Test, review, and document the result.

**Do not restart completed tasks without evidence of a defect. Do not invent missing project details. Do not sacrifice legal accuracy for a green demo.**