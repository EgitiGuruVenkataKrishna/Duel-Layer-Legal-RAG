# ⚖️ NyayaRAG

# Internal Team Knowledge Base

### Product · UX · AI · Retrieval · Engineering · Evaluation · Operations

---

# 00 · Document Control

| Field                      | Value                                            |
| -------------------------- | ------------------------------------------------ |
| Product                    | NyayaRAG                                         |
| Repository                 | `Duel-Layer-Legal-RAG`                           |
| Product Type               | Domain-specific Legal RAG                        |
| Current Stage              | Functional Localhost Prototype                   |
| Primary Audience           | Law Students + General Users                     |
| Secondary Audience         | Researchers / Competition Judges / AI Developers |
| Current UI                 | Streamlit                                        |
| Backend                    | FastAPI                                          |
| Orchestration              | LangGraph / LangChain                            |
| Legal Domain               | Indian Law                                       |
| Current Deployment         | Localhost                                        |
| Current G-Eval Measurement | Up to ~80%                                       |
| Direct Query Latency       | ~1–2 sec                                         |
| Scenario Query Latency     | ~4–5 sec                                         |

---

# 01 · Executive Product Definition

NyayaRAG is an Indian Legal RAG system designed to provide accessible, source-grounded legal information.

The product was created in response to a practical user problem:

> People have legal questions.

They may not immediately have access to a lawyer.

They increasingly use general-purpose AI systems for answers.

Those systems can produce fluent answers that may be insufficiently grounded in legal evidence.

Therefore, NyayaRAG introduces a specialized retrieval-and-verification pipeline.

The product should be understood internally as:

> **A legal-information retrieval and explanation system — not an AI lawyer.**

---

# 02 · Product North Star

The product should make the following experience possible:

```text
User has legal doubt
        ↓
User asks naturally
        ↓
System understands question type
        ↓
Relevant legal evidence is retrieved
        ↓
Evidence is verified
        ↓
Answer is generated from retrieved context
        ↓
User sees supporting evidence
```

The desired user perception is:

> "I can understand the answer, and I can see where it came from."

Not:

> "The AI sounds confident, so it must be correct."

---

# 03 · Primary Product Problem

## Core Problem Statement

Users need accessible legal information, but general AI systems can provide convincing answers without sufficiently reliable legal grounding.

This produces a trust mismatch:

```text
AI confidence
      ≠
Legal correctness
```

NyayaRAG attempts to improve this by introducing:

* Domain-specific retrieval.
* Source separation.
* Structured legal parsing.
* Hybrid search.
* Verification.
* Citations.
* Fallback handling.

---

# 04 · Product Goals

## Goal 1 — Accessibility

Allow non-experts to ask legal questions naturally.

## Goal 2 — Grounding

Tie answers to retrieved legal evidence.

## Goal 3 — Transparency

Expose supporting context.

## Goal 4 — Risk Reduction

Reduce unsupported legal generation.

## Goal 5 — Speed

Maintain practical response times.

## Goal 6 — Demonstrability

The architecture should be easy to explain in competitions and technical reviews.

## Goal 7 — Reusability

The architecture should be extensible toward a daily-use legal-information product.

---

# 05 · Non-Goals

The current project is **not**:

* A lawyer.
* A legal representation service.
* A replacement for professional legal consultation.
* A guaranteed legal correctness engine.
* A court outcome prediction engine.
* A complete representation of all Indian law.

This distinction must remain consistent across:

* Code.
* UI.
* README.
* Presentations.
* Demos.
* Social media.
* Competition submissions.

---

# 06 · Users

## 6.1 Law Students

### Needs

* Understand legal provisions.
* Search legal concepts.
* Connect factual scenarios to law.
* Inspect source material.

### Pain Points

* Dense legal language.
* Large documents.
* Time required for manual searching.
* Difficulty connecting natural language with formal provisions.

### Product Response

Provide:

* Simple explanation.
* Relevant law.
* Evidence.
* Precedent where applicable.

---

## 6.2 General Users

### Needs

* Quick legal orientation.
* Simple explanations.
* Relevant provisions.
* Evidence visibility.

### Pain Points

* Legal terminology.
* Search complexity.
* Financial barriers to immediate consultation.
* Overconfidence in general chatbots.

### Product Response

Provide:

* Natural-language interaction.
* Scenario interpretation.
* Grounded retrieval.
* Transparent limitations.

---

# 07 · User Research

Current research is exploratory.

Observed signals:

### Observation A

Users have genuine legal doubts.

### Observation B

Some users may not have the money or immediate access required to consult a lawyer for every question.

### Observation C

General-purpose chatbot usage is already an intuitive behavior.

### Observation D

Users may have difficulty detecting hallucinated legal answers.

### Observation E

Legal misinformation has higher potential consequences than many ordinary conversational errors.

---

# 08 · Research Limitations

The current user research should **not** be represented internally as statistically representative.

The team still needs:

* Defined participant count.
* Demographic breakdown.
* Research protocol.
* Task taxonomy.
* Structured interviews.
* Usability data.
* Trust measurements.
* Error observations.
* Quantitative task completion.

---

# 09 · Persona Model

## Persona A — Student Researcher

### Behavior

Asks:

* "What does this section mean?"
* "What law applies here?"
* "What did the Supreme Court say?"

### Desired Experience

Fast understanding + source inspection.

---

## Persona B — Everyday User

### Behavior

Describes a real situation:

> "My landlord isn't returning my deposit..."

### Desired Experience

Simple explanation + relevant law + limitations.

---

## Persona C — Technical Reviewer

### Behavior

Evaluates architecture.

### Questions

* Why RAG?
* Why hybrid retrieval?
* Why two tiers?
* Why separate statutes and judgments?
* Why G-Eval?
* What metrics support the approach?

### Desired Experience

Clear architecture + measurable evidence.

---

# 10 · Product Value Proposition

## For Users

> Understand legal information without needing to know exactly how legal documents are written.

## For Technical Reviewers

> A domain-specific Legal RAG architecture with structured parsing, tiered routing, hybrid retrieval, verification, and evidence visibility.

## For Competition Judges

> A practical AI system addressing a real high-risk hallucination problem through an evidence-first architecture.

---

# 11 · End-to-End Architecture

```text
USER
  │
  ▼
QUESTION / SCENARIO
  │
  ▼
QUERY ROUTER
  │
  ├─────────────────────┐
  │                     │
  ▼                     ▼
TIER 1                TIER 2
Direct Lookup         Scenario Deconstruction
  │                     │
  └──────────┬──────────┘
             ▼
     LEGAL RETRIEVAL
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
    FAISS         BM25
   Dense          Sparse
      │             │
      └──────┬──────┘
             ▼
            RRF
             │
             ▼
    RETRIEVED CONTEXT
             │
             ▼
       G-EVAL CHECK
             │
       ┌─────┴─────┐
       │           │
      PASS        FAIL
       │           │
       ▼           ▼
 GENERATION      FALLBACK
       │
       ▼
ANSWER + CITATIONS
```

---

# 12 · Why LangGraph?

The problem is not a single retrieval call.

The system requires conditional execution:

```text
Question
 ↓
Determine query type
 ↓
Choose retrieval path
 ↓
Retrieve
 ↓
Evaluate evidence
 ↓
Route based on evaluation
 ↓
Generate or fallback
```

A state-machine / graph-based orchestration model is therefore useful because the workflow contains:

* Branching.
* Conditional edges.
* Multiple processing stages.
* Verification.
* Controlled fallback.

---

# 13 · Dual-Tier Design

## Tier 1 — Direct Lookup

### Intended Query Class

Queries closely tied to known legal provisions.

Examples:

```text
"What does Section X say?"
"What is Article X?"
"Explain Section Y."
```

### Expected Behavior

1. Identify legal target.
2. Retrieve statutory evidence.
3. Rank evidence.
4. Verify context.
5. Generate concise explanation.
6. Attach supporting evidence.

### Performance Target

Current observed latency:

**~1–2 seconds.**

---

## Tier 2 — Scenario Deconstruction

### Intended Query Class

Narrative / case-like input.

Example:

```text
"My landlord refuses to return my deposit
after I moved out. What legal provisions
could apply?"
```

### Expected Behavior

Extract:

* Entities.
* Actions.
* Relationships.
* Legal concepts.
* Potential legal issues.

Then retrieve relevant material.

### Performance

Current observed latency:

**~4–5 seconds.**

The additional latency is expected because scenario questions require more processing.

---

# 14 · Structural Legal Parsing

Legal documents contain hierarchy.

Bad chunking can transform:

```text
Section
Subsection
Explanation
Exception
Proviso
```

into unrelated fragments.

NyayaRAG's parser is designed to preserve legal structural boundaries.

Conceptual hierarchy:

```text
Act
 ↓
Chapter
 ↓
Section
 ↓
Subsection
 ↓
Chunk
```

---

# 15 · Why Metadata Matters

Every legal chunk should ideally preserve fields such as:

```text
document_id
source_type
document_name
act_name
chapter
section
subsection
court
case_name
date
chunk_id
source_path
```

Metadata is not optional from a product perspective.

It powers:

* Citations.
* Filtering.
* Source display.
* Debugging.
* Retrieval analysis.
* Future updates.

---

# 16 · Legal Source Isolation

The system conceptually maintains separate source classes.

## Statutes

Examples:

* BNS.
* BNSS.
* BSA.
* Constitution of India.

## Precedents

Examples:

* Supreme Court judgments.

## Why?

Statutory provisions and judgments are not interchangeable evidence.

The product should always preserve the distinction.

---

# 17 · Dense Retrieval

Embedding model:

`all-MiniLM-L6-v2`

Backend:

`FAISS`

### Role

Dense retrieval is useful for semantic similarity.

Example:

**User:**

> "Someone took my property without permission."

The legal document may use substantially different vocabulary.

Semantic retrieval can still identify conceptually similar material.

---

# 18 · Sparse Retrieval

Backend:

`Rank-BM25`

### Role

Useful for:

* Section numbers.
* Exact terms.
* Legal phrases.
* Formal names.
* Case references.

Legal text often contains highly meaningful exact terminology, so sparse retrieval remains valuable.

---

# 19 · Reciprocal Rank Fusion

Concept:

```text
Dense ranking
+
Sparse ranking
↓
RRF
↓
Unified candidate ranking
```

The purpose is to combine:

* Semantic relevance.
* Lexical relevance.

RRF must remain independently measurable so the team can evaluate whether it actually improves retrieval.

---

# 20 · Verification Layer

Current mechanism:

```text
Retrieved Context
       ↓
G-Eval
       ↓
Threshold = 0.80
```

### PASS

Continue to generation.

### FAIL

Abort normal generation and use fallback behavior.

---

# 21 · Important Metric Interpretation

The project has observed G-Eval results up to approximately 80%.

Internally we must describe this as:

> **"Internal G-Eval measurement."**

We must **not** translate this directly to:

> "80% legal accuracy."

Those are different concepts.

Accuracy requires:

* Defined ground truth.
* Evaluation set.
* Methodology.
* Task definition.
* Statistical analysis.

---

# 22 · Generation Layer

The current repository documents Groq API integration with a Qwen model.

The generator should be conceptually constrained to:

```text
Retrieved Evidence
        ↓
Reason over evidence
        ↓
Explain evidence
        ↓
Cite evidence
```

It should **not** do:

```text
Weak evidence
 ↓
Use model memory
 ↓
Invent answer
```

---

# 23 · Citation Principle

Citations are part of the UX, not just backend metadata.

For every meaningful answer, users should ideally be able to inspect:

* Source document.
* Section.
* Retrieved passage.
* Source category.
* Relevance.

---

# 24 · Current UX

Current interface:

```text
Streamlit
```

Backend:

```text
FastAPI
```

Deployment:

```text
Localhost
```

This is sufficient for:

* Development.
* Testing.
* Competition demonstrations.

It is not yet sufficient for production-scale user traffic.

---

# 25 · Current UX Strengths

* Rapid prototyping.
* Easy iteration.
* Easy demonstration.
* Low infrastructure overhead.
* Direct connection to backend.

---

# 26 · Current UX Limitations

Streamlit is not necessarily the long-term product interface.

Potential future limitations include:

* Weaker design-system control.
* Limited polished navigation.
* Less control over highly customized interactions.
* Limited mobile product experience.
* Weaker information architecture for advanced research workflows.

Therefore:

```text
Current Streamlit
=
Functional prototype

Future dedicated frontend
=
Productization path
```

---

# 27 · Future UX Information Architecture

```text
NYAYARAG
│
├── Ask
│   ├── Ask about a Law
│   └── Describe a Situation
│
├── Results
│   ├── Explanation
│   ├── Relevant Law
│   ├── Precedents
│   └── Evidence
│
├── Research
│   ├── Statutes
│   ├── Judgments
│   └── Search
│
└── About
    ├── How it works
    ├── Limitations
    └── Disclaimer
```

---

# 28 · Future Answer Design

Recommended hierarchy:

```text
1. Direct answer
2. Simple explanation
3. Relevant law
4. Relevant precedent
5. Evidence
6. Limitations
7. Disclaimer
```

The user should never have to dig through five technical sections before seeing the actual answer.

---

# 29 · Future Trust UI

Recommended:

```text
✓ Evidence found
3 supporting sources
```

Avoid arbitrary "confidence percentages" unless their meaning is experimentally validated.

The UI should emphasize:

> **Evidence available**

rather than:

> **AI confidence = 93%**

---

# 30 · Future Source Panel

Each source could contain:

```text
SOURCE
Bharatiya Nyaya Sanhita

SECTION
Section X

RELEVANT PASSAGE
...

SOURCE TYPE
Statute

WHY THIS MATTERS
...
```

---

# 31 · Fallback Experience

Fallback is a product state.

It must not look like a system error.

### Bad

```text
Error 500
```

### Better

```text
I couldn't find sufficient legal evidence
to answer this reliably.

Try:
• adding the relevant Act
• adding the location/jurisdiction
• describing the situation more specifically
```

---

# 32 · Empty State

Recommended first-screen experience:

```text
What legal question do you have?

Examples:

• Explain Section X in simple language
• What law applies to this situation?
• What does the Constitution say about...?
```

---

# 33 · Loading State

Do not show unexplained spinning.

Future UX should communicate:

```text
Understanding question...
Finding legal sources...
Checking evidence...
Preparing grounded answer...
```

This also helps users understand that the system is doing retrieval rather than simply generating text.

---

# 34 · Design System

Future versions should define:

## Typography

* Display.
* H1.
* H2.
* Body.
* Caption.
* Citation.
* Legal metadata.

## Spacing

Use a tokenized spacing scale.

## Colors

Potential conceptual groups:

* Neutral / legal text.
* Primary brand.
* Evidence.
* Warning.
* Fallback.
* Success.

## Components

* Search box.
* Query mode.
* Answer card.
* Section card.
* Source card.
* Citation.
* Status badge.
* Fallback.
* Error.
* Loading.
* Disclaimer.

---

# 35 · Accessibility

Future UI should include:

* Sufficient contrast.
* Keyboard navigation.
* Visible focus states.
* Semantic labels.
* Text alternatives.
* Non-color-only status indication.

---

# 36 · Performance Baseline

Current internal baseline:

| Scenario          |    Latency |
| ----------------- | ---------: |
| Direct question   |   ~1–2 sec |
| Scenario question |   ~4–5 sec |
| G-Eval            | Up to ~80% |

When benchmarking in the future, record:

* Machine.
* API provider.
* Model.
* Corpus version.
* Number of retrieved chunks.
* Query type.
* Cold/warm state.

---

# 37 · KPI Framework

## Primary KPI Group 1 — Grounding

### Metric

Evidence-supported claim rate.

### Question

> How many substantive claims in the answer are supported by retrieved evidence?

---

## Primary KPI Group 2 — Retrieval

Track:

* Recall@K.
* Precision@K.
* MRR.
* NDCG.
* Hit rate.

---

## Primary KPI Group 3 — Verification

Track:

* True accept.
* False accept.
* True reject.
* False reject.

The most dangerous error is:

```text
Weak / irrelevant evidence
        ↓
Accepted
        ↓
Confident legal answer
```

---

## Primary KPI Group 4 — UX

Track:

* Question completion.
* Task completion.
* Time to useful answer.
* Source-open rate.
* Citation comprehension.
* User-rated understanding.

---

## Primary KPI Group 5 — Performance

Track:

* p50 latency.
* p95 latency.
* Timeout rate.
* API error rate.
* Retrieval time.
* Generation time.

---

# 38 · Evaluation Dataset

The team should create a permanent benchmark.

## Category A — Direct Lookup

Examples:

* Section lookup.
* Article lookup.
* Legal definition.
* Punishment / provision query.

## Category B — Scenario

Examples:

* Landlord dispute.
* Property dispute.
* Criminal scenario.
* Evidence issue.
* Procedural question.

## Category C — Ambiguous

Questions missing important context.

## Category D — Negative

Questions outside current corpus.

## Category E — Adversarial

Questions designed to expose hallucination or unsupported assumptions.

---

# 39 · Error Taxonomy

Every failed answer should be categorized.

## 1. Retrieval Failure

Relevant document exists but is not retrieved.

## 2. Ranking Failure

Relevant document is retrieved but ranked too low.

## 3. Parsing Failure

Document hierarchy was incorrectly extracted.

## 4. Verification Failure

Good context is incorrectly rejected.

## 5. False Acceptance

Weak context incorrectly passes verification.

## 6. Generation Failure

Model misinterprets supporting context.

## 7. Citation Failure

Answer does not correctly connect to evidence.

## 8. Corpus Gap

Required legal source is absent.

## 9. User Input Gap

Question lacks enough information.

---

# 40 · Edge Cases

## Ambiguous

**User:**

> "Is this illegal?"

**Required:**

Clarification.

---

## No Evidence

**Required:**

Fallback.

Never guess.

---

## Multiple Laws

**Required:**

Separate the provisions.

---

## Conflicting Cases

**Required:**

Show source attribution and explain the conflict.

---

## Outdated Legal Material

**Future requirement:**

Version/date metadata.

---

## Very Long Prompt

**Future requirement:**

Summarize / structure the scenario before retrieval.

---

## Unsupported Topic

**Required:**

Clear coverage limitation.

---

# 41 · Corpus Governance

A future production corpus needs:

* Source provenance.
* Document version.
* Acquisition date.
* Update date.
* Validation status.
* Metadata.
* Source URL/reference where applicable.

No document should be silently inserted into the production corpus.

---

# 42 · Corpus Update Workflow

```text
Source identified
      ↓
Authenticity verified
      ↓
Document extracted
      ↓
Structure parsed
      ↓
Metadata validated
      ↓
Chunking
      ↓
Embedding
      ↓
Index generation
      ↓
Retrieval tests
      ↓
Generation tests
      ↓
Publish corpus version
```

---

# 43 · Prompt Governance

Every major prompt change should record:

```text
Prompt version
Date
Owner
Reason
Expected impact
Evaluation result
Regression result
```

Do not modify a legal generation prompt casually.

A prompt can materially change:

* Hallucination behavior.
* Citation behavior.
* Answer style.
* Refusal behavior.
* Legal interpretation.

---

# 44 · Model Governance

Any model change requires comparison against:

* Grounding.
* Retrieval compatibility.
* Latency.
* Citation behavior.
* Answer quality.
* Hallucination rate.

Example:

```text
Model A
vs
Model B
```

should be evaluated on the same benchmark.

---

# 45 · Retrieval Governance

Changes to:

* Embeddings.
* Chunk size.
* Overlap.
* BM25 parameters.
* FAISS configuration.
* RRF.
* Top-k.

must be evaluated against the benchmark.

---

# 46 · Regression Testing

Every meaningful architectural change should test:

```text
Question
 ↓
Routing
 ↓
Retrieval
 ↓
Verification
 ↓
Generation
 ↓
Citation
```

A feature is not complete merely because it works on one happy-path question.

---

# 47 · Testing Pyramid

## Unit

Test individual:

* Parser.
* Chunker.
* Metadata.
* Retriever.
* Ranker.
* Threshold logic.

## Integration

Test the whole RAG chain.

## UX

Test:

* Discoverability.
* Comprehension.
* Evidence inspection.
* Fallback clarity.

## Evaluation

Run benchmark set after significant changes.

---

# 48 · Security

Current localhost prototype is not equivalent to production security.

Future deployment must consider:

* API key protection.
* Authentication.
* Authorization.
* Rate limiting.
* Request validation.
* Prompt injection.
* Malicious documents.
* Logging.
* Privacy.
* Secret rotation.
* Dependency vulnerabilities.

Never expose API keys in:

* GitHub.
* Screenshots.
* Frontend source.
* README examples.

---

# 49 · Prompt Injection

Future RAG versions should assume retrieved or uploaded text may contain malicious instructions.

The system must distinguish:

```text
Legal content
```

from:

```text
Instructions contained inside legal content
```

Retrieved documents should be treated as evidence, not as system instructions.

---

# 50 · Data Privacy

Users may eventually enter sensitive facts.

Future productization therefore requires careful consideration of:

* Storage.
* Retention.
* Logs.
* PII.
* Legal confidentiality expectations.
* Data deletion.

The team should avoid storing user legal scenarios by default until a defined privacy model exists.

---

# 51 · Stakeholder Requirements

## User

Needs:

* Clear answer.
* Evidence.
* Understandable language.
* Low waiting time.

## Design

Needs:

* Consistent information hierarchy.
* Clear trust cues.
* Robust error states.

## Engineering

Needs:

* Modular components.
* Reproducibility.
* Tests.
* Clear interfaces.

## AI/ML

Needs:

* Measurable retrieval.
* Controlled generation.
* Benchmark data.
* Evaluation methodology.

## Competition

Needs:

* Clear problem.
* Technical novelty.
* Measurable results.
* Real user relevance.
* Visually understandable demonstration.

---

# 52 · Competition Demo Flow

Recommended live demonstration:

## Step 1 — Show the Problem

```text
General AI
↓
Legal question
↓
Confident answer
↓
Where did it come from?
```

## Step 2 — Show NyayaRAG

```text
Same question
↓
Legal routing
↓
Retrieval
↓
Verification
↓
Answer
↓
Sources
```

## Step 3 — Show Scenario Input

Demonstrate Tier 2.

## Step 4 — Show Evidence

Open the retrieved chunks.

## Step 5 — Demonstrate Failure Behavior

Ask a question for which the system does not have enough evidence.

This demonstrates that the system is not designed to answer everything at any cost.

---

# 53 · What the Judge Should Understand

After a good demo, a reviewer should understand five things:

1. **The problem is real.**
2. **Legal AI requires stronger grounding than a generic chatbot.**
3. **NyayaRAG changes the architecture, not just the prompt.**
4. **The evidence is visible.**
5. **The system is still a prototype with measurable limitations.**

---

# 54 · Current Project Strengths

The most defensible strengths today are:

* Legal domain specialization.
* Structural parsing.
* Dual-tier query routing.
* Scenario deconstruction.
* Dense retrieval.
* Sparse retrieval.
* RRF fusion.
* Source isolation.
* Verification gate.
* Grounded citations.
* FastAPI backend.
* Streamlit UI.
* Measured prototype latency.

---

# 55 · Current Project Gaps

Do not hide these internally.

Current gaps include:

* Localhost-only deployment.
* Limited formal user research.
* Limited benchmark scale.
* Need for standardized evaluation.
* Need for broader source governance.
* No mature design system.
* Production security not yet implemented.
* Monitoring not yet mature.
* Corpus versioning not yet mature.

---

# 56 · Future Roadmap

## Phase 1 — Competition Ready

Priority:

* UI polish.
* Stronger demo.
* Benchmark dataset.
* Reproducible evaluation.
* Citation presentation.
* Architecture documentation.

---

## Phase 2 — Retrieval Quality

* Reranking.
* Better chunking.
* Better metadata.
* Query rewriting.
* Benchmark comparisons.
* Retrieval error analysis.

---

## Phase 3 — UX Productization

* Dedicated frontend.
* Responsive design.
* Design system.
* Source explorer.
* Research history.
* Advanced search.

---

## Phase 4 — Reliability

* Corpus versioning.
* Automated regression.
* Model versioning.
* Prompt versioning.
* Evaluation dashboard.
* Monitoring.

---

## Phase 5 — Product

Potential future capabilities:

* User accounts.
* Saved research.
* Personal documents.
* Multilingual support.
* Advanced citation navigation.
* Expert workflows.

These are future concepts and must not be represented as current features.

---

# 57 · Definition of Done

A feature is complete only when:

```text
Implementation
    +
Happy-path test
    +
Edge-case handling
    +
Failure state
    +
Evaluation
    +
Documentation
    +
Regression check
```

---

# 58 · Product Language Rules

## Preferred

* Grounded.
* Source-backed.
* Evidence-based.
* Legal information.
* Domain-specific.
* Retrieval.
* Verification.
* Prototype.

## Avoid Without Evidence

* Zero hallucination.
* 100% accurate.
* Lawyer replacement.
* Production-grade.
* Guaranteed.
* Legally correct in every case.

---

# 59 · Critical Positioning Rule

The project should **not** be positioned as:

> "AI Lawyer"

Preferred:

> **"Grounded Legal Information Assistant"**

or:

> **"Source-Grounded Legal RAG for Indian Law"**

or:

> **"An evidence-first Legal RAG system for Indian law."**

---

# 60 · Product Principles

## Principle 1

Evidence before confidence.

## Principle 2

A fallback can be a successful answer.

## Principle 3

Source visibility builds trust.

## Principle 4

Legal source types should remain distinguishable.

## Principle 5

Every major technical change should be measurable.

## Principle 6

The UI should simplify legal complexity, not expose system complexity.

## Principle 7

Never confuse an evaluation score with legal truth.

---

# 61 · Source-of-Truth Rule

When documentation and implementation disagree:

```text
IMPLEMENTED CODE
      ↓
CURRENT TESTED BEHAVIOR
      ↓
DOCUMENTATION
      ↓
ROADMAP
```

Roadmap items must never be presented as implemented.

Experimental features must be clearly labeled.

---

# 62 · Status Labels

Use:

### CURRENT

Implemented and tested.

### EXPERIMENTAL

Implemented but still under evaluation.

### PLANNED

Designed but not implemented.

### DEPRECATED

Previously supported but no longer recommended.

---

# 63 · Internal One-Line Definition

> NyayaRAG is a domain-specific Indian Legal RAG system that routes direct and scenario-based questions through structured legal retrieval, hybrid ranking, context verification, and evidence-grounded generation.

---

# 64 · Internal Success Criteria

The project should eventually be able to demonstrate:

```text
Higher retrieval relevance
        +
Lower unsupported claim rate
        +
Transparent citations
        +
Acceptable latency
        +
Clear user comprehension
```

The final objective is not simply:

> "Generate a legal answer."

The objective is:

> **"Generate a useful legal explanation that users can trace back to evidence and understand the limitations of."**

---

# 65 · Team Checklist Before Release

## Engineering

* [ ] Tests pass.
* [ ] No API keys committed.
* [ ] Retrieval works.
* [ ] Verification gate works.
* [ ] Fallback works.
* [ ] API responds correctly.

## AI/ML

* [ ] Benchmark evaluated.
* [ ] Retrieval quality measured.
* [ ] Grounding checked.
* [ ] Model version documented.
* [ ] Prompt version documented.

## UX

* [ ] Empty state works.
* [ ] Loading state works.
* [ ] Answer hierarchy is clear.
* [ ] Sources are visible.
* [ ] Fallback is understandable.
* [ ] Disclaimer is visible.

## Documentation

* [ ] README updated.
* [ ] Current features separated from roadmap.
* [ ] Metrics have methodology.
* [ ] Architecture diagram current.
* [ ] Setup instructions tested.

---

# 66 · Final Internal Standard

NyayaRAG should always be optimized toward:

```text
MORE EVIDENCE
LESS GUESSING

MORE TRANSPARENCY
LESS BLACK-BOX BEHAVIOR

MORE MEASUREMENT
LESS MARKETING CLAIM

MORE ACCESSIBILITY
LESS LEGAL COMPLEXITY

MORE SAFE FALLBACKS
LESS UNSUPPORTED CONFIDENCE
```

---

# 67 · Final Product Definition

NyayaRAG is not trying to win by being the chatbot that answers every question.

It is trying to win by being the system that can say:

> **"Here is what the available legal evidence supports, here is where it came from, and here is when the evidence is not strong enough to give you a reliable answer."**

That is the core product philosophy.
