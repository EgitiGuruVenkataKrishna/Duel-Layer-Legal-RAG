# Legal RAG System: Comprehensive Test Cases

This document contains a suite of test queries designed to stress-test the Dual-Tier architecture, the hybrid retriever (BM25 vs FAISS), and the G-Eval anti-hallucination firewall. 

Copy and paste the queries into the Streamlit UI and verify the system's behavior against the Expected Output.

---

## ⚖️ 1. Tier 1: Exact Statutory Lookup (Tests Sparse BM25 Retrieval)
**Purpose:** Tests if the system can accurately fetch a specific, named concept or section without getting confused.

* **Query 1:** `"What is the definition of 'document' under the Bharatiya Sakshya Adhiniyam (BSA), 2023?"`
  * **Expected Routing:** 🟢 Tier 1
  * **Expected Output:** The exact definition of a document as per the BSA, with strict citation (e.g., `[BSA, Chapter X, Section Y, Page Z]`). It should not hallucinate the old Indian Evidence Act definition.

* **Query 2:** `"What is the punishment for murder under Section 103 of the Bharatiya Nyaya Sanhita (BNS)?"`
  * **Expected Routing:** 🟢 Tier 1
  * **Expected Output:** Should pull the exact text of Section 103 of BNS (which replaces IPC 302). It must explicitly cite Section 103.

---

## 🕵️‍♂️ 2. Tier 2: Complex Situational Narrative (Tests FAISS Semantic Matching & Decomposer)
**Purpose:** Tests the `scenario_decomposer` node to see if it can break down a human story into legal facts, and test FAISS for semantic matching rather than exact keyword matching.

* **Query 3:** `"A person was driving his SUV recklessly at 120 km/hr on a busy market street, resulting in a severe crash where one pedestrian died and another was grievously hurt. The driver claims it was a mechanical failure, but CCTV shows he was speeding. What charges under the new criminal laws apply here?"`
  * **Expected Routing:** 🟣 Tier 2
  * **Expected Output:** The UI should show it went to Tier 2. The response should synthesize statutes relating to causing death by negligence, rash driving, and grievous hurt under the **BNS**. It should cite the specific sections retrieved.

* **Query 4:** `"My neighbor has been continuously harassing me by throwing garbage into my compound every night. When I confronted him, he verbally abused me and threatened to harm my family. What legal remedies do I have under the BNSS and what sections of BNS apply?"`
  * **Expected Routing:** 🟣 Tier 2
  * **Expected Output:** Should retrieve BNS sections for criminal intimidation, nuisance, and verbal abuse, alongside BNSS procedures for filing complaints.

---

## 🏛️ 3. Tier 2: Precedential Grounding (Tests Isolated Dual Retrieval)
**Purpose:** Tests if the system correctly queries both the Statutes DB and the Supreme Court Judgments DB and merges them.

* **Query 5:** `"If a police officer refuses to register an FIR for a cognizable offense reported by a woman, what remedies are available under BNSS, and are there any Supreme Court guidelines on mandatory FIR registration?"`
  * **Expected Routing:** 🟣 Tier 2
  * **Expected Output:** The answer MUST synthesize procedural remedies from BNSS (e.g., complaint to Magistrate/SP) AND cite retrieved Supreme Court judgments (e.g., *Lalita Kumari v. Govt of UP* if it exists in your judgments PDF). 

---

## 🛑 4. Edge Cases: Hallucination Traps (Tests the G-Eval Firewall)
**Purpose:** Tests if the system will bravely refuse to answer when the legal context does not exist, proving that the G-Eval Score threshold (< 0.8) works.

* **Query 6:** `"What is the maximum penalty for illegally modifying a flying car's anti-gravity engine under the Bharatiya Nyaya Sanhita?"`
  * **Expected Routing:** 🟢 Tier 1 or 🟣 Tier 2
  * **Expected Output:** The FAISS/BM25 retrievers will fail to find anything relevant. The `G-Eval Score` in the UI should drop below `0.8` (likely closer to 0.0). The system MUST output the fallback: *"Insufficient legal precedent or statutory clarity to ground an accurate answer."* It should **not** invent a fake law.

* **Query 7:** `"Under the BNSS, what is the procedure to legally adopt a pet dinosaur?"`
  * **Expected Routing:** 🟢 Tier 1 or 🟣 Tier 2
  * **Expected Output:** `G-Eval Score` < 0.8. Fallback response triggered.

---

## 🌫️ 5. Edge Cases: Extremely Vague Queries
**Purpose:** Tests how the system handles overly broad or poorly constructed prompts.

* **Query 8:** `"He hit me with a stick."`
  * **Expected Routing:** 🟣 Tier 2
  * **Expected Output:** The decomposer extracts "hit with a stick". The retriever should pull general provisions for "hurt" or "assault" from the BNS. The assistant should provide a generalized answer about assault/battery charges under BNS, with citations.

* **Query 9:** `"Right to privacy."`
  * **Expected Routing:** 🟢 Tier 1
  * **Expected Output:** Should pull Article 21 from the Constitution of India and provide foundational context with exact citations.
