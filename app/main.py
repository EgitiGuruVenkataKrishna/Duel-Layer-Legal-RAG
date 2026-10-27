import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.nyayasetu.compare.chatgpt import ChatGPTBaseline
from src.nyayasetu.pipeline.dual_tier import DualTierPipeline
from src.nyayasetu.offence.schedule_store import OffenceClassificationStore
from src.nyayasetu.temporal.classifier import TemporalLegalityEngine
from src.nyayasetu.transition.mapper import StatutoryTransitionMapper

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

st.set_page_config(
    page_title="NyayaSetu",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def load_pipeline():
    return DualTierPipeline()


@st.cache_resource
def load_compare_client():
    return ChatGPTBaseline()


@st.cache_data
def load_ablation_table():
    path = ROOT / "eval" / "results" / "ablation.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "No ablation.md found. Run `python eval/run.py --split dev --ablation`."


@st.cache_data
def load_baseline_metrics():
    path = ROOT / "eval" / "results" / "v0_baseline.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


pipeline = load_pipeline()
chatgpt = load_compare_client()

with st.sidebar:
    st.title("⚖️ NyayaSetu")
    st.caption("Dual-tier verified Indian criminal-law research")
    st.markdown("---")
    st.markdown("**Tier 1** — named section / short lookup (SQLite + BM25, no Groq)")
    st.markdown("**Tier 2** — scenario (hybrid + rerank + generate + verify)")
    st.markdown("---")
    st.markdown(f"**Groq model:** `{os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')}`")
    st.markdown(f"**ChatGPT compare:** `{'ready' if chatgpt.available() else 'OPENAI_API_KEY missing'}`")
    st.caption("v0.6.0 • Not legal advice")

st.title("NyayaSetu")
st.markdown(
    "Answers are grounded in the local statute database (BNS, BNSS, BSA, and mapped legacy provisions). "
    "Every response includes citation metrics. This is research information, not legal advice."
)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Legal Q&A",
        "vs ChatGPT",
        "Statutory transition",
        "Offence / bail",
        "Temporal engine",
        "Retrieval evidence",
    ]
)


def render_metrics(metrics: dict, verification: dict):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tier", metrics.get("tier", ""))
    c2.metric("Citation validity", f"{(metrics.get('citation_validity') or 0) * 100:.1f}%")
    c3.metric("Groundedness", f"{(metrics.get('groundedness') or 0) * 100:.1f}%")
    c4.metric("Latency", f"{metrics.get('latency_ms', 0):.0f} ms")
    c5.metric("Status", verification.get("status", ""))
    st.caption(
        f"Route: `{metrics.get('route_type')}` · compute: `{metrics.get('computation')}` · "
        f"LLM used: `{metrics.get('llm_used')}` · abstained: `{metrics.get('abstained')}` · "
        f"reason: {metrics.get('tier_reason')}"
    )


def render_sources(docs):
    st.markdown("### Retrieved statutory sources")
    if not docs:
        st.warning("No sections retrieved.")
        return
    for doc in docs:
        label = f"[{doc.get('act_code')}] Section {doc.get('section_no')}: {doc.get('title')}"
        with st.expander(label):
            st.markdown(
                f"ID `{doc.get('id')}` · score `{doc.get('retrieval_score')}` ({doc.get('score_type')})"
            )
            st.text(doc.get("text") or "")


with tab1:
    query_input = st.text_area(
        "Question",
        placeholder="Tier 1: What is BNS 103?  /  what is the thief related section\n"
        "Tier 2: Yesterday police registered an FIR after a phone was snatched from a parked scooter. What provisions may be attracted?",
        height=110,
    )
    if st.button("Answer and verify", type="primary") and query_input.strip():
        with st.spinner("Running dual-tier pipeline..."):
            result = pipeline.run(query_input.strip())
        render_metrics(result["metrics"], result["verification"])
        st.markdown("### Answer")
        st.markdown(result["answer"])
        render_sources(result["retrieved_sections"])
        with st.expander("Raw metrics JSON"):
            st.json(result["metrics"])
        st.info(result.get("disclaimer") or "Informational research output only. Not legal advice.")

with tab2:
    st.subheader("Same question: NyayaSetu vs general ChatGPT")
    st.caption("NyayaSetu uses the statute database and citation verifier. ChatGPT is an ungrounded OpenAI call.")
    cmp_q = st.text_area("Question to compare", key="cmp_q", height=90)
    if st.button("Run comparison", type="primary") and cmp_q.strip():
        with st.spinner("NyayaSetu + ChatGPT..."):
            ours = pipeline.run(cmp_q.strip())
            gpt = chatgpt.ask(cmp_q.strip())
        left, right = st.columns(2)
        with left:
            st.markdown("#### NyayaSetu (grounded)")
            render_metrics(ours["metrics"], ours["verification"])
            st.markdown(ours["answer"])
        with right:
            st.markdown("#### ChatGPT (ungrounded)")
            if gpt.get("error"):
                st.error(gpt["error"])
            else:
                st.caption(f"Model: {gpt.get('model')}")
                st.markdown(gpt.get("answer") or "")
            cites = chatgpt.extract_loose_citations(gpt.get("answer") or "")
            if cites:
                st.markdown("**Sections ChatGPT named (checked against our database):**")
                for act, sec in cites:
                    exists = pipeline.verifier.verify_section_exists(act, sec)
                    st.write(f"- {act} {sec}: {'in corpus' if exists else 'NOT in corpus (possible hallucination)'}")
        render_sources(ours["retrieved_sections"])

with tab3:
    st.subheader("Statutory transition navigator")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        sel_code = st.selectbox("Select statute", ["IPC (Penal)", "CRPC (Procedure)", "IEA (Evidence)"])
    with col_t2:
        code_key = sel_code.split()[0]
        sample_sections = {
            "IPC": ["302 (Murder)", "307 (Attempt to murder)", "420 (Cheating)", "376 (Rape)", "378 (Theft)"],
            "CRPC": ["154 (FIR)", "161 (Police exam)", "167 (Custody)", "173 (Chargesheet)", "438 (Anticipatory bail)"],
            "IEA": ["65B (Electronic records)", "32(1) (Dying declaration)"],
        }
        sel_sec_str = st.selectbox("Select section", sample_sections[code_key])
        sel_sec_no = sel_sec_str.split()[0]
    trans = StatutoryTransitionMapper.lookup_transition(code_key, sel_sec_no)
    if trans:
        st.info(f"{trans['title']} — {trans['change_type']}")
        c1, c2 = st.columns(2)
        c1.metric("Old provision", f"{trans['old_code']} {trans['old_sec']}")
        c2.metric("New provision", f"{trans['new_code']} {trans['new_sec']}")
        st.write(trans["key_differences"])
        st.caption("Mappings are unverified pending legal review (see docs/HUMAN_TODO.md).")

with tab4:
    st.subheader("BNSS First Schedule lookup")
    off_sec = st.text_input("BNS section number", value="103(1)")
    store = OffenceClassificationStore()
    if off_sec:
        data = store.get_offence(off_sec)
        if data:
            st.markdown(store.format_summary(data))
        else:
            st.warning(f"No First Schedule row for Section {off_sec}.")

with tab5:
    st.subheader("Temporal applicability")
    c_d1, c_d2 = st.columns(2)
    with c_d1:
        off_date = st.date_input("Date of offence", value=None)
    with c_d2:
        fir_date = st.date_input("Date of FIR / proceedings", value=None)
    if st.button("Evaluate applicable law") and off_date:
        res = TemporalLegalityEngine.evaluate(off_date, fir_date or off_date)
        st.write(f"- Substantive: `{res['substantive_law']}`")
        st.info(res["substantive_reason"])
        st.write(f"- Procedural: `{res['procedural_law']}`")
        st.info(res["procedural_reason"])
        st.write(f"- Evidence: `{res['evidence_law']}`")
        st.caption(res["constitutional_basis"])
        st.caption("Rules are draft_pending_review until docs/legal_review.md is signed.")

with tab6:
    st.subheader("Measured retrieval metrics (from eval/results, not estimates)")
    baseline = load_baseline_metrics()
    if baseline:
        m = baseline["metrics"]
        st.markdown(
            f"v0 baseline `{baseline['mode']}` on `{baseline['split']}` "
            f"(n={m['n_evaluated']}): Recall@5 **{m['recall_at_5']['mean']}** "
            f"[{m['recall_at_5']['ci95_lo']}, {m['recall_at_5']['ci95_hi']}], "
            f"MRR **{m['mrr']['mean']}**"
        )
    st.markdown(load_ablation_table())
    st.caption("Copied from eval/results/*.json and ablation.md. Do not treat UI tables as new measurements.")
