import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dotenv import load_dotenv

from src.nyayasetu.pipeline.dual_tier import DualTierPipeline
from src.nyayasetu.offence.schedule_store import OffenceClassificationStore
from src.nyayasetu.temporal.classifier import TemporalLegalityEngine
from src.nyayasetu.transition.mapper import StatutoryTransitionMapper

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NyayaSetu — AI Legal Research",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for professional look ──────────────────────────────────────

st.markdown(
    """
    <style>
    /* ─── Global ─── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ─── Sidebar ─── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1B2A 0%, #1B2838 100%);
        color: #E0E7EE;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #E0E7EE !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #2A3F55;
    }

    /* ─── Tier badges ─── */
    .tier-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .tier-badge.tier1 {
        background: #E8F5E9;
        color: #2E7D32;
        border: 1px solid #A5D6A7;
    }
    .tier-badge.tier2 {
        background: #E3F2FD;
        color: #1565C0;
        border: 1px solid #90CAF9;
    }

    /* ─── Metrics cards ─── */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E8ECF1;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .metric-card .label {
        font-size: 11px;
        font-weight: 600;
        color: #78909C;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }
    .metric-card .value {
        font-size: 22px;
        font-weight: 700;
        color: #1A237E;
    }
    .metric-card .value.green { color: #2E7D32; }
    .metric-card .value.orange { color: #E65100; }
    .metric-card .value.red { color: #C62828; }
    .metric-card .value.blue { color: #1565C0; }

    /* ─── Answer card ─── */
    .answer-card {
        background: #FFFFFF;
        border: 1px solid #E0E7EE;
        border-left: 4px solid #1E88E5;
        border-radius: 8px;
        padding: 24px 28px;
        margin: 16px 0;
        line-height: 1.7;
    }

    /* ─── Source card ─── */
    .source-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }
    .source-card .source-header {
        font-weight: 600;
        color: #1A237E;
        font-size: 14px;
    }
    .source-card .source-score {
        font-size: 12px;
        font-weight: 500;
        color: #546E7A;
    }

    /* ─── Example question buttons ─── */
    .example-btn {
        background: #F0F4F8;
        border: 1px solid #D2DCE6;
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 13px;
        color: #37474F;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
        width: 100%;
    }
    .example-btn:hover {
        background: #E3ECF4;
        border-color: #1E88E5;
    }

    /* ─── Status indicators ─── */
    .status-verified {
        color: #2E7D32;
        font-weight: 600;
    }
    .status-unverified {
        color: #E65100;
        font-weight: 600;
    }
    .status-abstained {
        color: #C62828;
        font-weight: 600;
    }

    /* ─── Disclaimer ─── */
    .disclaimer {
        background: #FFF8E1;
        border: 1px solid #FFE082;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 13px;
        color: #5D4037;
        margin-top: 16px;
    }

    /* ─── Hide default streamlit branding ─── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* ─── Section header styling ─── */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #1A237E;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #E8ECF1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Cached resources ──────────────────────────────────────────────────────

@st.cache_resource
def load_pipeline():
    return DualTierPipeline()


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


# ── Sidebar ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚖️ NyayaSetu")
    st.markdown("*AI-Powered Indian Legal Research*")
    st.markdown("---")
    st.markdown(
        """
        **How it works**

        🔵 **Tier 1 — Direct Lookup**
        For named sections, definitions, bare-act text.
        Uses SQLite + BM25 — no LLM needed.

        🟢 **Tier 2 — Scenario Analysis**
        For factual scenarios, hypotheticals, FIR narratives.
        Uses hybrid retrieval + reranking + LLM generation.
        """
    )
    st.markdown("---")
    st.markdown(
        f"**Model:** `{os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')}`"
    )
    st.markdown("---")
    st.markdown(
        """
        **Covered Statutes**
        - Bharatiya Nyaya Sanhita (BNS)
        - Bharatiya Nagarik Suraksha Sanhita (BNSS)
        - Bharatiya Sakshya Adhiniyam (BSA)
        - Indian Penal Code (IPC)
        - Code of Criminal Procedure (CrPC)
        - Indian Evidence Act (IEA)
        - Constitution of India
        """
    )
    st.markdown("---")
    st.caption("v1.0.0 · Research tool · Not legal advice")


# ── Main content ──────────────────────────────────────────────────────────

st.markdown(
    """
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h1 style="font-size: 36px; font-weight: 700; color: #1A237E; margin-bottom: 4px;">
            ⚖️ NyayaSetu
        </h1>
        <p style="font-size: 16px; color: #546E7A; margin-top: 0;">
            Verified Indian Criminal-Law Research — Grounded in Statutory Evidence
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🔍  Ask a Question",
        "🔄  Statutory Transition",
        "📋  Offence Classification",
        "⏰  Temporal Engine",
        "📊  Retrieval Evidence",
    ]
)


# ── Helper functions ──────────────────────────────────────────────────────

def render_tier_badge(tier: str):
    """Render a styled tier badge."""
    if tier == "tier1":
        st.markdown(
            '<span class="tier-badge tier1">⚡ Tier 1 — Direct Lookup</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="tier-badge tier2">🔬 Tier 2 — Scenario Analysis</span>',
            unsafe_allow_html=True,
        )


def render_metrics_dashboard(metrics: dict, verification: dict):
    """Render a professional metrics dashboard."""
    st.markdown('<div class="section-header">📊 Response Metrics</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # Citation validity color
    cv = (metrics.get("citation_validity") or 0)
    cv_color = "green" if cv >= 0.7 else ("orange" if cv >= 0.3 else "red")

    # Groundedness color
    gnd = metrics.get("groundedness", 0)
    gnd_color = "green" if gnd >= 0.7 else ("orange" if gnd >= 0.3 else "red")

    # Verification status
    v_status = verification.get("status", "")
    status_class = (
        "status-verified" if v_status == "verified"
        else ("status-abstained" if v_status == "abstained" else "status-unverified")
    )

    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="label">Citation Validity</div>'
            f'<div class="value {cv_color}">{cv * 100:.0f}%</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="label">Groundedness</div>'
            f'<div class="value {gnd_color}">{gnd * 100:.0f}%</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="metric-card"><div class="label">Latency</div>'
            f'<div class="value blue">{metrics.get("latency_ms", 0):.0f}ms</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="metric-card"><div class="label">Chunks Used</div>'
            f'<div class="value blue">{metrics.get("n_chunks_used", 0)}</div></div>',
            unsafe_allow_html=True,
        )
    with col5:
        top_score = metrics.get("top_retrieval_score", 0) or 0
        st.markdown(
            f'<div class="metric-card"><div class="label">Top Similarity</div>'
            f'<div class="value blue">{top_score:.4f}</div></div>',
            unsafe_allow_html=True,
        )
    with col6:
        st.markdown(
            f'<div class="metric-card"><div class="label">Status</div>'
            f'<div class="value"><span class="{status_class}">{v_status.title()}</span></div></div>',
            unsafe_allow_html=True,
        )

    # Route details (collapsed)
    with st.expander("🔧 Routing Details", expanded=False):
        rc1, rc2, rc3 = st.columns(3)
        rc1.markdown(f"**Route:** `{metrics.get('route_type')}`")
        rc2.markdown(f"**LLM Used:** `{metrics.get('llm_used')}`")
        rc3.markdown(f"**Computation:** `{metrics.get('computation')}`")
        st.markdown(f"**Tier Reason:** `{metrics.get('tier_reason')}`")
        st.markdown(f"**Signals:** `{', '.join(metrics.get('tier_signals', []))}`")
        if metrics.get("model"):
            st.markdown(f"**Model:** `{metrics.get('model')}`")
        st.markdown(
            f"**Avg Similarity:** `{metrics.get('avg_retrieval_score', 0):.4f}` · "
            f"**Min:** `{metrics.get('min_retrieval_score', 0):.4f}` · "
            f"**Max:** `{metrics.get('top_retrieval_score', 0):.4f}`"
        )


def render_answer(answer: str):
    """Render the answer in a styled card."""
    st.markdown('<div class="section-header">💡 Answer</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="answer-card">{answer}</div>',
        unsafe_allow_html=True,
    )


def render_sources(docs):
    """Render retrieved statutory sources with similarity scores."""
    st.markdown('<div class="section-header">📚 Retrieved Statutory Sources</div>', unsafe_allow_html=True)
    if not docs:
        st.warning("No sections retrieved.")
        return

    for i, doc in enumerate(docs, 1):
        act = doc.get("act_code", "")
        sec = doc.get("section_no", "")
        title = doc.get("title", "")
        score = doc.get("retrieval_score", 0)
        score_type = doc.get("score_type", "")
        text = doc.get("text", "")

        # Score color
        if score >= 0.8:
            score_emoji = "🟢"
        elif score >= 0.3:
            score_emoji = "🟡"
        else:
            score_emoji = "🔴"

        label = f"{score_emoji} [{act}] Section {sec}: {title}  —  Similarity: {score:.4f}"
        with st.expander(label, expanded=(i <= 2)):
            st.markdown(
                f'<div class="source-card">'
                f'<div class="source-header">[{act}] Section {sec} — {title}</div>'
                f'<div class="source-score">Similarity: {score:.4f} · Method: {score_type} · ID: {doc.get("id", "")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.text(text or "")


def render_disclaimer():
    """Render the legal disclaimer."""
    st.markdown(
        '<div class="disclaimer">'
        "⚠️ <strong>Disclaimer:</strong> This is an informational research tool, not legal advice. "
        "Always consult a qualified legal professional for specific legal matters."
        "</div>",
        unsafe_allow_html=True,
    )


# ── Tab 1: Ask a Question ────────────────────────────────────────────────

with tab1:
    st.markdown("")

    # Example questions
    st.markdown("**Try an example question:**")
    ex_col1, ex_col2 = st.columns(2)
    with ex_col1:
        st.markdown(
            '<div style="background: #EDE7F6; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">'
            '<span style="font-weight: 600; color: #4527A0;">⚡ Tier 1 examples</span></div>',
            unsafe_allow_html=True,
        )
        t1_examples = [
            "What is BNS Section 103?",
            "What is the thief related section?",
            "Punishment for murder under BNS",
            "Explain Article 21",
        ]
        for ex in t1_examples:
            if st.button(ex, key=f"t1_{ex}", use_container_width=True):
                st.session_state["query_input"] = ex

    with ex_col2:
        st.markdown(
            '<div style="background: #E3F2FD; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">'
            '<span style="font-weight: 600; color: #1565C0;">🔬 Tier 2 examples</span></div>',
            unsafe_allow_html=True,
        )
        t2_examples = [
            "Yesterday police registered an FIR after a phone was snatched from a parked scooter. What provisions may be attracted?",
            "A man threatened his neighbour with a knife during a property dispute. What offences are made out?",
            "Suppose someone cheated an elderly person of their pension money through a fake scheme. What sections apply?",
            "My friend was beaten by a group of people at night. What legal action can he take?",
        ]
        for ex in t2_examples:
            short = ex[:80] + "..." if len(ex) > 80 else ex
            if st.button(short, key=f"t2_{ex}", use_container_width=True):
                st.session_state["query_input"] = ex

    st.markdown("---")

    # Main query input
    default_query = st.session_state.get("query_input", "")
    query_input = st.text_area(
        "Your Legal Question",
        value=default_query,
        placeholder="Type your question here...\n\n"
        "• Tier 1 (Direct): 'What is BNS 103?' or 'punishment for theft'\n"
        "• Tier 2 (Scenario): 'A person snatched a phone from someone walking on the road. What offences apply?'",
        height=120,
    )

    col_btn, col_clear = st.columns([3, 1])
    with col_btn:
        submit = st.button("🔍  Get Answer", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️  Clear", use_container_width=True):
            st.session_state["query_input"] = ""
            st.rerun()

    if submit and query_input.strip():
        # Clear the saved query to avoid repeat
        if "query_input" in st.session_state:
            del st.session_state["query_input"]

        with st.spinner("⏳ Running pipeline... Retrieving chunks, analyzing, and generating answer..."):
            result = pipeline.run(query_input.strip())

        # Tier badge
        render_tier_badge(result["tier"])

        # Metrics dashboard
        render_metrics_dashboard(result["metrics"], result["verification"])

        # Answer
        render_answer(result["answer"])

        # Sources
        render_sources(result["retrieved_sections"])

        # Raw JSON (collapsed)
        with st.expander("🔧 Raw Response JSON", expanded=False):
            st.json(result["metrics"])

        # Disclaimer
        render_disclaimer()


# ── Tab 2: Statutory Transition ───────────────────────────────────────────

with tab2:
    st.markdown(
        """
        <div style="background: #F3E5F5; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 6px 0; color: #4A148C;">🔄 Statutory Transition Navigator</h3>
            <p style="margin: 0; color: #6A1B9A; font-size: 14px;">
                Map between old laws (IPC, CrPC, IEA) and new laws (BNS, BNSS, BSA)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        sel_code = st.selectbox(
            "Select statute",
            ["IPC (Penal)", "CRPC (Procedure)", "IEA (Evidence)"],
        )
    with col_t2:
        code_key = sel_code.split()[0]
        sample_sections = {
            "IPC": [
                "302 (Murder)",
                "307 (Attempt to murder)",
                "420 (Cheating)",
                "376 (Rape)",
                "378 (Theft)",
            ],
            "CRPC": [
                "154 (FIR)",
                "161 (Police exam)",
                "167 (Custody)",
                "173 (Chargesheet)",
                "438 (Anticipatory bail)",
            ],
            "IEA": [
                "65B (Electronic records)",
                "32(1) (Dying declaration)",
            ],
        }
        sel_sec_str = st.selectbox("Select section", sample_sections[code_key])
        sel_sec_no = sel_sec_str.split()[0]

    trans = StatutoryTransitionMapper.lookup_transition(code_key, sel_sec_no)
    if trans:
        st.markdown("---")
        st.markdown(f"### {trans['title']}")
        st.markdown(
            f'<span style="background: #E8F5E9; padding: 4px 12px; border-radius: 12px; '
            f'font-size: 13px; font-weight: 500; color: #2E7D32;">{trans["change_type"]}</span>',
            unsafe_allow_html=True,
        )

        col_old, col_arrow, col_new = st.columns([5, 1, 5])
        with col_old:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">Old Provision</div>'
                f'<div class="value" style="font-size: 18px;">{trans["old_code"]} Section {trans["old_sec"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_arrow:
            st.markdown(
                '<div style="text-align: center; padding-top: 20px; font-size: 28px;">→</div>',
                unsafe_allow_html=True,
            )
        with col_new:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">New Provision</div>'
                f'<div class="value green" style="font-size: 18px;">{trans["new_code"]} Section {trans["new_sec"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("#### Key Differences")
        st.write(trans["key_differences"])
        st.caption("⚠️ Mappings are unverified pending legal review (see docs/HUMAN_TODO.md).")
    else:
        st.info("Select a section above to see the transition mapping.")


# ── Tab 3: Offence Classification ─────────────────────────────────────────

with tab3:
    st.markdown(
        """
        <div style="background: #FFF3E0; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 6px 0; color: #E65100;">📋 BNSS First Schedule Lookup</h3>
            <p style="margin: 0; color: #BF360C; font-size: 14px;">
                Check if an offence is cognizable, bailable, or compoundable
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    off_sec = st.text_input("BNS Section Number", value="103(1)", placeholder="e.g., 103(1), 303, 318")
    store = OffenceClassificationStore()
    if off_sec:
        data = store.get_offence(off_sec)
        if data:
            st.markdown("---")
            st.markdown(store.format_summary(data))
        else:
            st.warning(f"No First Schedule row for Section {off_sec}.")


# ── Tab 4: Temporal Engine ────────────────────────────────────────────────

with tab4:
    st.markdown(
        """
        <div style="background: #E0F7FA; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 6px 0; color: #00695C;">⏰ Temporal Applicability Engine</h3>
            <p style="margin: 0; color: #00796B; font-size: 14px;">
                Determine which law applies based on the date of the offence and FIR
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_d1, c_d2 = st.columns(2)
    with c_d1:
        off_date = st.date_input("Date of offence", value=None)
    with c_d2:
        fir_date = st.date_input("Date of FIR / proceedings", value=None)

    if st.button("⚡ Evaluate Applicable Law", type="primary") and off_date:
        res = TemporalLegalityEngine.evaluate(off_date, fir_date or off_date)
        st.markdown("---")

        col_sub, col_proc, col_evi = st.columns(3)
        with col_sub:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">Substantive Law</div>'
                f'<div class="value blue" style="font-size: 16px;">{res["substantive_law"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.caption(res["substantive_reason"])
        with col_proc:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">Procedural Law</div>'
                f'<div class="value blue" style="font-size: 16px;">{res["procedural_law"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.caption(res["procedural_reason"])
        with col_evi:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">Evidence Law</div>'
                f'<div class="value blue" style="font-size: 16px;">{res["evidence_law"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.info(f"**Constitutional Basis:** {res['constitutional_basis']}")
        st.caption("⚠️ Rules are draft_pending_review until docs/legal_review.md is signed.")


# ── Tab 5: Retrieval Evidence ─────────────────────────────────────────────

with tab5:
    st.markdown(
        """
        <div style="background: #ECEFF1; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 6px 0; color: #37474F;">📊 Retrieval Performance Metrics</h3>
            <p style="margin: 0; color: #546E7A; font-size: 14px;">
                Measured retrieval metrics from eval/results — not estimates
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    baseline = load_baseline_metrics()
    if baseline:
        m = baseline["metrics"]
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">Recall@5 (Mean)</div>'
                f'<div class="value green">{m["recall_at_5"]["mean"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_r2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">MRR (Mean)</div>'
                f'<div class="value blue">{m["mrr"]["mean"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_r3:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">Evaluated</div>'
                f'<div class="value">{m["n_evaluated"]} queries</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        st.caption(
            f"v0 baseline `{baseline['mode']}` on `{baseline['split']}` — "
            f"Recall@5 95% CI: [{m['recall_at_5']['ci95_lo']}, {m['recall_at_5']['ci95_hi']}]"
        )
    else:
        st.info("No baseline metrics found. Run `python eval/run.py --split dev` to generate.")

    st.markdown("---")
    st.markdown("### Ablation Study")
    st.markdown(load_ablation_table())
    st.caption("Copied from eval/results/*.json and ablation.md. Do not treat UI tables as new measurements.")
