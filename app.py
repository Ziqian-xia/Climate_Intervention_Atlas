"""
Winnow — Systematic Literature Search, Powered by AI
Multi-agent pipeline: Query Generation → Search → Screening → Full-Text Retrieval
"""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.m1_query_gen import QueryGenerationTeam
from modules.m2_search_exec import SearchExecutor
from modules.m3_screening import ScreeningOrchestrator
from modules.m4_fulltext import FullTextRetriever
from utils.logger import get_logger
from utils.llm_providers import create_llm_provider, AnthropicProvider, BedrockProvider, DummyProvider
from utils.prompt_inspector import (
    get_phase1_agent_prompts,
    get_phase3_screening_prompts,
    get_model_information,
    format_prompt_display
)

# Page config
st.set_page_config(
    page_title="Winnow — Systematic Literature Search, Powered by AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logger
logger = get_logger()

# Initialize session state
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        # Phase tracking
        'phase': 1,

        # Phase 1: Query Generation
        'queries_generated': False,
        'topic': '',
        'pulse_keywords': [],
        'pulse_reasoning': '',
        'elsevier_query': '',
        'pubmed_query': '',
        'openalex_query': '',
        'formulator_reasoning': '',
        'sentinel_validation': '',
        'sentinel_warnings': [],
        'refiner_notes': '',
        'issues_resolved': [],
        'approved': False,
        'agent_logs': [],
        'query_variations': [],  # Store multiple query variations
        'enable_variations': False,  # Disable by default (Advanced feature)
        'num_variations': 5,  # Default to 5 variations
        'auto_search_variations': False,  # Disable by default (Advanced feature)

        # API Settings (Phase 1 LLM Provider)
        'provider_type': 'anthropic',
        'anthropic_api_key': '',
        'anthropic_model_id': 'claude-sonnet-4-6',
        'aws_region': 'us-east-1',
        'aws_model_id': 'us.anthropic.claude-sonnet-4-6',
        'aws_access_key_id': '',
        'aws_secret_access_key': '',

        # Phase 2: Search Execution
        'search_running': False,
        'search_results': {},
        'run_openalex': True,
        'run_pubmed': True,
        'run_scopus': False,

        # Search API credentials
        'openalex_api_key': '',
        'openalex_mailto': '',
        'pubmed_api_key': '',
        'pubmed_email': '',
        'scopus_api_key': '',
        'scopus_insttoken': '',
        'search_results_dir': '',  # Store Phase 2 output directory

        # Phase 3: Abstract Screening
        'screening_mode': 'simple',
        'screening_threads': 4,
        'screening_criteria': '',
        'screening_results': None,
        'screening_complete': False,
        'screening_approved': False,
        'screening_out_dir': '',

        # Phase 4: Full-Text Retrieval
        'fulltext_use_playwright': False,
        'fulltext_max_retries': 3,
        'fulltext_timeout': 60,
        'fulltext_results': None,
        'fulltext_complete': False,
        'fulltext_approved': False,
        'fulltext_out_dir': '',
        'wiley_tdm_token': '',  # Wiley TDM API token

        # Workflow control
        'workflow_started': False,
        'returned_from_phase2': False,  # Flag: user went back from Phase 2 to edit queries
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ==============================================================================
# GLOBAL CSS + UI HELPERS
# ==============================================================================

def inject_css():
    st.markdown("""
    <style>
    /* ── Brand tokens ─────────────────────────────────────────────── */
    :root {
        --w-navy:  #054067;
        --w-teal:  #036380;
        --w-teal2: #068c94;
        --w-light: #e8f4f7;
        --w-text:  #1E293B;
        --w-muted: #64748B;
        --w-faint: #94A3B8;
        --w-border:#E2E8F0;
    }

    /* ── Progress stepper ─────────────────────────────────────────── */
    .sr-steps {
        display: flex; align-items: center; justify-content: center;
        padding: 1.2rem 0.5rem 1.6rem; gap: 0; width: 100%;
    }
    .sr-step {
        display: flex; flex-direction: column; align-items: center; gap: 6px;
        min-width: 90px; position: relative;
    }
    .sr-circle {
        width: 34px; height: 34px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.85em; flex-shrink: 0;
        transition: box-shadow 0.2s;
    }
    .sr-label { font-size: 0.72em; text-align: center; font-weight: 500; line-height: 1.3; }
    .sr-connector { height: 2px; flex: 1; min-width: 32px; margin-bottom: 26px; }

    .sr-step.done  .sr-circle { background: var(--w-teal2); color: #fff; }
    .sr-step.done  .sr-label  { color: var(--w-teal2); }
    .sr-step.active .sr-circle { background: var(--w-navy); color: #fff;
                                  box-shadow: 0 0 0 4px rgba(5,64,103,0.18); }
    .sr-step.active .sr-label  { color: var(--w-navy); font-weight: 700; }
    .sr-step.pending .sr-circle { background: var(--w-border); color: var(--w-faint); }
    .sr-step.pending .sr-label  { color: var(--w-faint); }
    .sr-connector.done    { background: var(--w-teal2); }
    .sr-connector.pending { background: var(--w-border); }

    /* ── Phase header banners ─────────────────────────────────────── */
    .ph-banner {
        padding: 0.75rem 1.2rem; border-radius: 8px; margin-bottom: 0.5rem;
        border-left: 5px solid; display: flex; align-items: baseline; gap: 10px;
    }
    .ph-banner h2 { margin: 0; font-size: 1.3rem; font-weight: 700; }
    .ph-banner p  { margin: 0; font-size: 0.88rem; opacity: 0.72; }
    .ph1 { border-color: var(--w-navy);  background: #eef4f8; }
    .ph2 { border-color: var(--w-teal);  background: #e8f4f6; }
    .ph3 { border-color: var(--w-teal2); background: #e8f5f5; }
    .ph4 { border-color: #4a6fa5;        background: #eef1f8; }

    /* ── Landing hero ─────────────────────────────────────────────── */
    .hero-logo  { display: flex; justify-content: center; align-items: center;
                  padding: 0.5rem 0 0.8rem; }
    .hero-sub   { text-align: center; color: var(--w-muted); font-size: 1.05rem;
                  margin-top: 0.2rem; }
    .hero-byline { text-align: center; color: var(--w-faint); font-size: 0.82rem;
                   margin-top: 0.15rem; }

    /* ── Feature cards ────────────────────────────────────────────── */
    .feature-card {
        border: 1px solid var(--w-border); border-radius: 10px;
        padding: 1.2rem 1rem; text-align: center; height: 100%;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .feature-card:hover {
        border-color: var(--w-teal); box-shadow: 0 2px 12px rgba(3,99,128,0.1);
    }
    .feature-card .icon { font-size: 1.7rem; margin-bottom: 6px; }
    .feature-card h4 { margin: 0 0 4px; font-size: 0.93rem; font-weight: 700;
                       color: var(--w-text); }
    .feature-card p { margin: 0; font-size: 0.81rem; color: var(--w-muted); }

    /* ── Sidebar logo ─────────────────────────────────────────────── */
    .sidebar-logo { display: flex; justify-content: center; padding: 0.4rem 0 0.6rem; }
    .sidebar-logo img { max-width: 140px; }

    /* ── Back button pill ─────────────────────────────────────────── */
    div[data-testid="stButton"] button[kind="secondary"] {
        border-radius: 20px; font-size: 0.85em; padding: 0.25rem 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)


def _logo_img(height: str = "72px") -> str:
    """Return an <img> tag with the Winnow logo embedded as base64."""
    import base64
    logo_path = Path(__file__).parent / "logo" / "SVG" / "Asset 1.svg"
    try:
        data = logo_path.read_bytes()
        b64 = base64.b64encode(data).decode()
        return (
            f'<img src="data:image/svg+xml;base64,{b64}" '
            f'height="{height}" style="display:block;">'
        )
    except Exception:
        return "<span style='font-size:1.6rem;font-weight:800;color:#054067'>Winnow</span>"


def render_progress_steps(current_phase: int):
    steps = [
        (1, "📝", "Query<br>Generation"),
        (2, "🔍", "Metadata<br>Search"),
        (3, "✅", "Abstract<br>Screening"),
        (4, "📄", "Full-Text<br>Retrieval"),
    ]
    html = '<div class="sr-steps">'
    for i, (num, icon, label) in enumerate(steps):
        if num < current_phase:
            cls, sym = "done", "✓"
        elif num == current_phase:
            cls, sym = "active", icon
        else:
            cls, sym = "pending", str(num)
        html += (
            f'<div class="sr-step {cls}">'
            f'  <div class="sr-circle">{sym}</div>'
            f'  <div class="sr-label">{label}</div>'
            f'</div>'
        )
        if i < len(steps) - 1:
            conn = "done" if num < current_phase else "pending"
            html += f'<div class="sr-connector {conn}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def phase_header(num: int, icon: str, title: str, subtitle: str):
    cls = f"ph{num}"
    st.markdown(
        f'<div class="ph-banner {cls}">'
        f'  <h2>{icon} {title}</h2>'
        f'  <p>{subtitle}</p>'
        f'</div>',
        unsafe_allow_html=True
    )


inject_css()

# Model catalogue — display label → API model ID
ANTHROPIC_MODELS = {
    "Claude Sonnet 4.6  ⭐ Recommended":            "claude-sonnet-4-6",
    "Claude Haiku 4.5   ⭐ Best value (large screening)": "claude-haiku-4-5-20251001",
    "Claude Opus 4.7    — Most capable":            "claude-opus-4-7",
    "Claude 3.5 Sonnet  — Previous gen":            "claude-3-5-sonnet-20241022",
    "Claude 3.5 Haiku   — Previous gen":            "claude-3-5-haiku-20241022",
}
_ANTHROPIC_MODEL_IDS = list(ANTHROPIC_MODELS.values())
_ANTHROPIC_MODEL_LABELS = list(ANTHROPIC_MODELS.keys())

BEDROCK_MODELS = {
    "Claude Sonnet 4.6  ⭐ Recommended":            "us.anthropic.claude-sonnet-4-6",
    "Claude Haiku 4.5   ⭐ Best value (large screening)": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "Claude Opus 4.7    — Most capable":            "us.anthropic.claude-opus-4-7",
    "Claude Opus 4.6    — Previous Opus":           "us.anthropic.claude-opus-4-6-v1",
    "Claude Sonnet 4.5  — Previous Sonnet":         "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "Claude 3.5 Sonnet  — Previous gen":            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
}
_BEDROCK_MODEL_IDS = list(BEDROCK_MODELS.values())
_BEDROCK_MODEL_LABELS = list(BEDROCK_MODELS.keys())

# Helper function for merging query variation results
def _merge_database_variations(db_name: str, variations: list, base_out_dir: str) -> dict:
    """
    Merge results from multiple query variations for a single database.
    Deduplicates by DOI (or PMID for PubMed, or EID for Scopus).

    Args:
        db_name: Database name ("openalex", "pubmed", "scopus")
        variations: List of result dicts from each variation
        base_out_dir: Base output directory

    Returns:
        Merged result dict with deduplicated data
    """
    import json

    all_dfs = []
    all_jsonl_data = []
    total_retrieved = 0
    total_meta_count = 0

    id_column = {
        "openalex": "openalex_id",
        "pubmed": "pmid",
        "scopus": "eid"
    }.get(db_name, "doi")

    # Collect all successful variation results
    for var_result in variations:
        if not var_result.get("success"):
            continue

        var_idx = var_result.get("variation_idx", 1)
        output_files = var_result.get("output_files", {})

        # Read CSV if available
        csv_path = output_files.get("summary_csv")
        if csv_path and Path(csv_path).exists():
            try:
                df = pd.read_csv(csv_path)
                df['source_variation'] = var_idx
                all_dfs.append(df)
                total_retrieved += len(df)
            except Exception as e:
                logger.warning(f"Failed to read CSV from variation {var_idx}: {e}")

        # Read JSONL if available
        jsonl_path = output_files.get("full_jsonl")
        if jsonl_path and Path(jsonl_path).exists():
            try:
                with open(jsonl_path, 'r') as f:
                    for line in f:
                        data = json.loads(line)
                        data['source_variation'] = var_idx
                        all_jsonl_data.append(data)
            except Exception as e:
                logger.warning(f"Failed to read JSONL from variation {var_idx}: {e}")

        # Read summary for meta_count
        summary_path = output_files.get("summary_json")
        if summary_path and Path(summary_path).exists():
            try:
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                    total_meta_count = max(total_meta_count, summary.get("meta_count", 0))
            except Exception as e:
                logger.warning(f"Failed to read summary from variation {var_idx}: {e}")

    if not all_dfs:
        return {
            "success": False,
            "status": "no_data",
            "error": "No data collected from any variation",
            "results_count": 0,
            "output_files": {}
        }

    # Merge all DataFrames
    merged_df = pd.concat(all_dfs, ignore_index=True)

    # Deduplicate by ID column
    before_dedup = len(merged_df)

    # Handle missing IDs
    if id_column in merged_df.columns:
        merged_df = merged_df.dropna(subset=[id_column])
        merged_df = merged_df.drop_duplicates(subset=[id_column], keep='first')
    elif 'doi' in merged_df.columns:
        # Fallback to DOI
        merged_df = merged_df.dropna(subset=['doi'])
        merged_df['doi_normalized'] = merged_df['doi'].str.lower().str.strip()
        merged_df = merged_df.drop_duplicates(subset=['doi_normalized'], keep='first')
        merged_df = merged_df.drop(columns=['doi_normalized'])
    else:
        # No ID column - deduplicate by title
        if 'title' in merged_df.columns:
            merged_df = merged_df.drop_duplicates(subset=['title'], keep='first')

    after_dedup = len(merged_df)
    duplicates_removed = before_dedup - after_dedup

    logger.info(f"{db_name}: Merged {before_dedup} records, removed {duplicates_removed} duplicates, final: {after_dedup}")

    # Save merged results
    merged_out_dir = Path(base_out_dir) / db_name
    merged_out_dir.mkdir(parents=True, exist_ok=True)

    # Save merged CSV
    merged_csv_path = merged_out_dir / "works_summary.csv"
    merged_df.to_csv(merged_csv_path, index=False)

    # Save merged JSONL (deduplicated)
    merged_jsonl_path = merged_out_dir / "works_full.jsonl"
    if all_jsonl_data:
        # Deduplicate JSONL by same ID
        seen_ids = set()
        with open(merged_jsonl_path, 'w') as f:
            for item in all_jsonl_data:
                item_id = item.get(id_column) or item.get('doi', '')
                if item_id and item_id not in seen_ids:
                    f.write(json.dumps(item) + '\n')
                    seen_ids.add(item_id)

    # Save merged summary
    merged_summary = {
        "database": db_name,
        "num_variations": len(variations),
        "total_retrieved_before_dedup": before_dedup,
        "duplicates_removed": duplicates_removed,
        "final_unique_count": after_dedup,
        "meta_count": total_meta_count,
        "status": "merged_success",
        "variations_summary": [
            {
                "variation_idx": v.get("variation_idx"),
                "success": v.get("success"),
                "results_count": v.get("results_count", 0)
            }
            for v in variations
        ]
    }

    merged_summary_path = merged_out_dir / "run_summary.json"
    with open(merged_summary_path, 'w') as f:
        json.dump(merged_summary, f, indent=2)

    return {
        "success": True,
        "status": "merged_success",
        "results_count": after_dedup,
        "meta_count": total_meta_count,
        "duplicates_removed": duplicates_removed,
        "total_before_dedup": before_dedup,
        "num_variations": len(variations),
        "error": "",  # Empty on success
        "variations_summary": merged_summary["variations_summary"],  # Include per-variation details
        "output_files": {
            "summary_json": str(merged_summary_path),
            "summary_csv": str(merged_csv_path),
            "full_jsonl": str(merged_jsonl_path)
        }
    }

# Sidebar: API Settings + Phase Tracker
with st.sidebar:
    st.title("⚙️ API Settings")

    st.info("💡 **Required**: Anthropic (or Bedrock) for Phase 1 & 3\n\n**Optional**: OpenAlex, PubMed, Scopus for Phase 2")

    # LLM Provider Selection (for Phase 1)
    st.session_state.provider_type = st.radio(
        "LLM Provider (Phase 1):",
        options=["anthropic", "bedrock", "dummy"],
        index=["anthropic", "bedrock", "dummy"].index(st.session_state.provider_type),
        help="Select API provider for query generation"
    )

    # Provider-specific configuration
    if st.session_state.provider_type == "anthropic":
        st.session_state.anthropic_api_key = st.text_input(
            "Anthropic API Key:",
            type="password",
            value=st.session_state.anthropic_api_key or "",
            help="Get key at console.anthropic.com"
        )
        # Resolve current model ID → label for selectbox default
        _cur_label = next(
            (lbl for lbl, mid in ANTHROPIC_MODELS.items()
             if mid == st.session_state.anthropic_model_id),
            _ANTHROPIC_MODEL_LABELS[0]
        )
        _sel_label = st.selectbox(
            "Model:",
            options=_ANTHROPIC_MODEL_LABELS,
            index=_ANTHROPIC_MODEL_LABELS.index(_cur_label),
            help=(
                "⭐ Sonnet 4.6 — best quality for query generation & screening\n"
                "⭐ Haiku 4.5 — ~10× cheaper, ideal when screening 1000+ abstracts\n"
                "Opus 4.7 — highest capability, slower & most expensive"
            )
        )
        st.session_state.anthropic_model_id = ANTHROPIC_MODELS[_sel_label]
        st.caption(f"Model ID: `{st.session_state.anthropic_model_id}`")

    elif st.session_state.provider_type == "bedrock":
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.aws_region = st.selectbox(
                "AWS Region:",
                options=["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
                index=["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"].index(st.session_state.aws_region)
            )
        with col2:
            _cur_br_label = next(
                (lbl for lbl, mid in BEDROCK_MODELS.items()
                 if mid == st.session_state.aws_model_id),
                _BEDROCK_MODEL_LABELS[0]
            )
            _sel_br_label = st.selectbox(
                "Model:",
                options=_BEDROCK_MODEL_LABELS,
                index=_BEDROCK_MODEL_LABELS.index(_cur_br_label),
                help=(
                    "⭐ Sonnet 4.6 — best quality for query generation & screening\n"
                    "⭐ Haiku 4.5 — ~10× cheaper, ideal when screening 1000+ abstracts\n"
                    "Opus 4.7 — highest capability, slower & most expensive"
                )
            )
            st.session_state.aws_model_id = BEDROCK_MODELS[_sel_br_label]
        st.caption(f"Model ID: `{st.session_state.aws_model_id}`")

        with st.expander("AWS Credentials (optional)"):
            st.info("Leave blank to use IAM role or default credentials")
            st.session_state.aws_access_key_id = st.text_input(
                "AWS Access Key ID:",
                type="password",
                value=st.session_state.aws_access_key_id
            )
            st.session_state.aws_secret_access_key = st.text_input(
                "AWS Secret Access Key:",
                type="password",
                value=st.session_state.aws_secret_access_key
            )

    elif st.session_state.provider_type == "dummy":
        st.info("🧪 Dummy mode: Uses pre-defined test queries")

    # Test connection button
    if st.session_state.provider_type != "dummy":
        if st.button("🔌 Test Connection"):
            with st.spinner("Testing connection..."):
                try:
                    if st.session_state.provider_type == "anthropic":
                        # Check if API key is provided
                        if not st.session_state.anthropic_api_key:
                            st.error("❌ Please enter your Anthropic API key first")
                        else:
                            provider = AnthropicProvider(api_key=st.session_state.anthropic_api_key, model=st.session_state.anthropic_model_id)
                            if provider.is_available():
                                if provider.test_connection():
                                    st.success(f"✅ Connected successfully to {provider.get_model_name()}")
                                else:
                                    st.error("❌ Connection test failed - check API key and model access")
                            else:
                                st.error("❌ Provider not available - check anthropic package installation")
                    else:
                        # Bedrock - check if using explicit credentials or default chain
                        using_explicit = bool(st.session_state.aws_access_key_id and st.session_state.aws_secret_access_key)

                        provider = BedrockProvider(
                            region=st.session_state.aws_region,
                            model_id=st.session_state.aws_model_id,
                            aws_access_key_id=st.session_state.aws_access_key_id or None,
                            aws_secret_access_key=st.session_state.aws_secret_access_key or None
                        )

                        if not provider.is_available():
                            st.error("❌ boto3 not available - install with: pip install boto3")
                        else:
                            # Show which credential method is being used
                            if using_explicit:
                                st.info("🔑 Using explicit AWS credentials from UI")
                            else:
                                st.info("🔑 Using AWS default credential chain (IAM role/environment/~/.aws/credentials)")

                            # Actually test the connection with a call
                            if provider.test_connection():
                                st.success(f"✅ Connected successfully to {provider.get_model_name()}")
                            else:
                                st.error("❌ Connection test failed - check credentials and Bedrock model access")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    logger.error(f"Connection test failed: {e}", exc_info=True)

    st.markdown("---")

    # Phase Tracker
    st.markdown(
        f"<div class='sidebar-logo'>{_logo_img('52px')}</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    phases = [
        ("Phase 1: Query Generation", 1, "✅" if st.session_state.phase >= 1 else "⏸️"),
        ("Phase 2: Metadata Search", 2, "✅" if st.session_state.phase >= 2 else "⏸️"),
        ("Phase 3: Screening", 3, "✅" if st.session_state.phase >= 3 else "⏸️"),
        ("Phase 4: Full-Text Retrieval", 4, "✅" if st.session_state.phase >= 4 else "⏸️"),
    ]

    for name, phase_num, icon in phases:
        status = "[ACTIVE]" if phase_num == st.session_state.phase else "[PENDING]" if phase_num > st.session_state.phase else "[COMPLETE]"
        color = "green" if phase_num <= st.session_state.phase else "gray"

        st.markdown(
            f'<span style="color:{color}">{icon} <strong>{name}</strong> {status}</span>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("**Status:**")
    if st.session_state.approved:
        st.success("Phase 1 Locked ✅")
    elif st.session_state.queries_generated:
        st.info("Queries Generated")
    else:
        st.warning("Awaiting Input")

    # File Import Portal
    st.markdown("---")
    with st.expander("📥 Import Data (Skip Phases)", expanded=False):
        st.markdown("**Already have data? Import and jump to any phase!**")

        uploaded_file = st.file_uploader(
            "Upload CSV file:",
            type=["csv"],
            help="Upload a CSV file with your papers",
            key="import_csv_uploader"
        )

        if uploaded_file:
            try:
                import_df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(import_df)} rows, {len(import_df.columns)} columns")

                # Show preview
                st.markdown("**Preview:**")
                st.dataframe(import_df.head(3), use_container_width=True)

                # Column mapping interface
                st.markdown("---")
                st.markdown("**🔗 Map Your Columns:**")

                col_map1, col_map2 = st.columns(2)

                with col_map1:
                    title_col = st.selectbox(
                        "Title Column:",
                        options=[""] + list(import_df.columns),
                        key="import_title_col"
                    )
                    abstract_col = st.selectbox(
                        "Abstract Column:",
                        options=[""] + list(import_df.columns),
                        key="import_abstract_col"
                    )

                with col_map2:
                    doi_col = st.selectbox(
                        "DOI Column (optional):",
                        options=[""] + list(import_df.columns),
                        key="import_doi_col"
                    )
                    authors_col = st.selectbox(
                        "Authors Column (optional):",
                        options=[""] + list(import_df.columns),
                        key="import_authors_col"
                    )

                # Jump to phase buttons
                if title_col and abstract_col:
                    st.markdown("---")
                    st.markdown("**🚀 Jump to Phase:**")

                    col_p3, col_p4 = st.columns(2)

                    with col_p3:
                        if st.button("→ Phase 3 (Screening)", type="primary", key="jump_to_phase3"):
                            # Map columns
                            mapped_df = pd.DataFrame()
                            mapped_df['title'] = import_df[title_col]
                            mapped_df['abstract'] = import_df[abstract_col]
                            if doi_col:
                                mapped_df['doi'] = import_df[doi_col]
                            if authors_col:
                                mapped_df['authors'] = import_df[authors_col]

                            # Add record IDs
                            mapped_df['record_id'] = range(1, len(mapped_df) + 1)

                            # Save to temp location
                            import tempfile
                            temp_dir = tempfile.mkdtemp(prefix="imported_data_")
                            mapped_df.to_csv(f"{temp_dir}/imported_papers.csv", index=False)

                            # Set session state
                            st.session_state.phase = 3
                            st.session_state.search_results_dir = temp_dir
                            st.session_state.imported_data = mapped_df
                            st.session_state.data_imported = True

                            logger.info(f"Imported {len(mapped_df)} papers, jumping to Phase 3")
                            st.success(f"✅ Imported {len(mapped_df)} papers! Jumping to Phase 3...")
                            st.rerun()

                    with col_p4:
                        if st.button("→ Phase 4 (Download)", key="jump_to_phase4"):
                            # Require DOI for Phase 4
                            if not doi_col:
                                st.error("❌ DOI column required for Phase 4")
                            else:
                                # Map columns
                                mapped_df = pd.DataFrame()
                                mapped_df['title'] = import_df[title_col]
                                mapped_df['abstract'] = import_df[abstract_col]
                                mapped_df['doi'] = import_df[doi_col]
                                mapped_df['judgement'] = True  # All papers marked for download
                                if authors_col:
                                    mapped_df['authors'] = import_df[authors_col]

                                # Set session state
                                st.session_state.phase = 4
                                st.session_state.screening_results = mapped_df
                                st.session_state.screening_approved = True
                                st.session_state.data_imported = True

                                logger.info(f"Imported {len(mapped_df)} papers, jumping to Phase 4")
                                st.success(f"✅ Imported {len(mapped_df)} papers! Jumping to Phase 4...")
                                st.rerun()

                else:
                    st.warning("⚠️ Please map at least Title and Abstract columns")

            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
                logger.error(f"Import error: {e}", exc_info=True)

    # Model & Prompt Information Section
    st.markdown("---")
    with st.expander("🔍 Model & Prompt Information", expanded=False):
        st.markdown("### Active Model Configuration")

        # Show current provider info
        if 'llm_provider' in st.session_state and st.session_state.get('llm_provider'):
            provider = st.session_state.llm_provider
            model_info = get_model_information(provider)

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Provider", model_info["provider_name"])
            with col_m2:
                st.metric("Status", "✅ Available" if model_info["is_available"] else "❌ Unavailable")

            st.markdown(f"**Model**: `{model_info['model_name']}`")
            if "region" in model_info:
                st.markdown(f"**Region**: `{model_info['region']}`")
            if "model_id" in model_info:
                st.markdown(f"**Model ID**: `{model_info['model_id']}`")
        else:
            st.info("No provider configured yet. Configure above and test connection.")

        st.markdown("---")
        st.markdown("### Phase 1: Query Generation Prompts")

        phase1_prompts = get_phase1_agent_prompts()
        for agent_name, prompt_text in phase1_prompts.items():
            with st.expander(f"🤖 {agent_name}", expanded=False):
                st.code(prompt_text, language="text")

        st.markdown("---")
        st.markdown("### Phase 3: Abstract Screening Prompts")

        phase3_prompts = get_phase3_screening_prompts()
        for mode_name, prompt_text in phase3_prompts.items():
            with st.expander(f"✅ {mode_name}", expanded=False):
                # Show with parameter placeholders
                display_text = prompt_text.replace("{k_strictness}", "[k_strictness]").replace("{criteria}", "[inclusion/exclusion criteria]")
                st.code(display_text, language="text")

        st.markdown("---")
        st.caption("ℹ️ All prompts shown are the actual system-level prompts used by the agents. User messages (research topic, queries, etc.) are added dynamically during execution.")


# ==============================================================================
# LANDING PAGE (before workflow starts)
# ==============================================================================

if not st.session_state.workflow_started:
    # ── Hero ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='hero-logo'>{_logo_img('96px')}</div>"
        "<div class='hero-sub'>Find the right papers. Faster.</div>"
        "<div class='hero-byline'>Systematic search methods · Multi-database · Human-in-the-loop</div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Workflow stepper ───────────────────────────────────────────────
    render_progress_steps(1)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Feature cards ──────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("🤖", "AI Query Generation", "4-agent team builds Boolean queries for every database"),
        ("🔍", "Multi-Database Search", "OpenAlex, PubMed, Scopus — merged & deduplicated"),
        ("✅", "AI Abstract Screening", "LLM screens titles/abstracts against your criteria"),
        ("📄", "Full-Text Retrieval", "OA → Publishers → browser fallback, output as Markdown"),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(
                f"<div class='feature-card'>"
                f"  <div class='icon'>{icon}</div>"
                f"  <h4>{title}</h4>"
                f"  <p>{desc}</p>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── What you need ─────────────────────────────────────────────────
    st.markdown("#### 🔑 What you need to get started")
    col_need1, col_need2 = st.columns(2)
    with col_need1:
        st.markdown("""
**Required**
- **Anthropic API key** — for query generation & screening
  → [console.anthropic.com](https://console.anthropic.com/)
- **Email address** — for OpenAlex (free, no registration)
""")
    with col_need2:
        st.markdown("""
**Optional**
- **PubMed API key** — free at [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/)
- **Scopus API key** — institutional, [dev.elsevier.com](https://dev.elsevier.com/)
- **Wiley TDM token** — for full-text PDF download
""")
    st.caption("💡 Enter keys in the sidebar after clicking Start. Only Anthropic + email needed for a first run.")

    st.markdown("---")

    # ── CTA ────────────────────────────────────────────────────────────
    col_btn1, col_btn2, _ = st.columns([1, 1, 1])
    with col_btn1:
        if st.button("🚀 Start", type="primary", use_container_width=True):
            st.session_state.workflow_started = True
            st.rerun()
    with col_btn2:
        if st.button("💡 Try an Example", use_container_width=True):
            st.session_state.workflow_started = True
            st.session_state.topic = (
                "I am interested in research on cooling centers (sometimes called heat relief centers "
                "or cooling shelters) and their effectiveness in reducing heat-related mortality and "
                "morbidity. Focus on studies with causal research designs (experimental or "
                "quasi-experimental) that quantify health impacts."
            )
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#94A3B8; font-size:0.82em;'>"
        "Winnow · Powered by Claude AI"
        "</p>",
        unsafe_allow_html=True
    )

    st.stop()  # Stop here if workflow hasn't started

# ==============================================================================
# MAIN WORKFLOW (Phase 1-5)
# ==============================================================================

# Main content
render_progress_steps(st.session_state.phase)
phase_header(1, "📝", "Phase 1 · Query Generation", "A 4-agent AI team builds optimized Boolean queries for each database")

# Back to landing button
if st.button("← Home", key="back_to_home_phase1"):
    st.session_state.workflow_started = False
    st.rerun()

# Description
with st.expander("ℹ️ How it works", expanded=False):
    st.markdown("""
    **The Four-Agent Team:**

    1. **🔍 Pulse Agent** - Keyword Expander
       - Takes your research topic and expands it with synonyms, related terms, and domain-specific vocabulary
       - Includes methodological terms for causal/systematic review studies
       - Can generate variations with different keyword angles

    2. **⚙️ Formulator Agent** - Query Constructor
       - Creates database-specific Boolean search strings
       - Formats queries for Elsevier/Scopus, PubMed, and OpenAlex
       - Balances precision and recall with proper Boolean logic

    3. **🛡️ Sentinel Agent** - Quality Controller
       - Validates syntax and checks for errors
       - Reviews for overly broad or narrow terms
       - Ensures proper operator precedence and field restrictions
       - Identifies any issues or warnings

    4. **💎 Refiner Agent** - Final Polisher
       - Takes Sentinel's validation report and fixes ALL issues
       - Produces final, execution-ready queries
       - Ensures queries are perfect with zero errors

    **Your role:** Review the final polished queries and edit them if needed before approval.
    """)

st.markdown("---")

# Show edit-mode banner when user returns from Phase 2
if st.session_state.returned_from_phase2 and not st.session_state.approved:
    st.info(
        "✏️ **Edit Mode** — You've returned from Phase 2. "
        "Edit the queries in the **'Final Queries'** section below, then click **Approve & Proceed to Phase 2** again. "
        "You don't need to regenerate queries unless you want to start fresh."
    )

# Input Section
st.subheader("📝 Research Topic")

topic_input = st.text_area(
    "Enter your research topic and requirements:",
    value=st.session_state.topic,
    placeholder="e.g., 'I am interested in research on cooling centers and heat-related mortality. I specifically want studies with causal research designs (experimental or quasi-experimental studies, randomized controlled trials).'",
    disabled=st.session_state.approved,
    height=120,
    key="topic_input",
    help="Be specific! Include your intervention/exposure, outcome, and study design requirements (e.g., causal, experimental, RCT)"
)

# Update topic in session state
if topic_input != st.session_state.topic:
    st.session_state.topic = topic_input

# Variation/Looping Options
with st.expander("🔄 Advanced: Query Variations & Batch Search", expanded=False):
    st.markdown("""
    Generate multiple query variations to explore different keyword combinations and search strategies.
    Optionally run automated searches for all variations.
    """)

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.session_state.enable_variations = st.checkbox(
            "Enable Query Variations",
            value=st.session_state.enable_variations,
            help="Generate multiple alternative query sets",
            disabled=st.session_state.approved
        )
    with col_v2:
        if st.session_state.enable_variations:
            st.session_state.num_variations = st.number_input(
                "Number of Variations:",
                min_value=1,
                max_value=10,
                value=st.session_state.num_variations,
                help="Each variation explores different keyword angles",
                disabled=st.session_state.approved
            )

    if st.session_state.enable_variations:
        st.session_state.auto_search_variations = st.checkbox(
            "Auto-run Phase 2 searches for all variations",
            value=st.session_state.auto_search_variations,
            help="Automatically execute searches after generating all query variations (requires Phase 2 setup)",
            disabled=st.session_state.approved
        )
        if st.session_state.auto_search_variations:
            st.warning("⚠️ This will run searches for each variation. Make sure API credentials are configured in Phase 2.")

col1, col2 = st.columns([1, 3])

with col1:
    generate_button = st.button(
        "🚀 Generate Queries",
        type="primary",
        disabled=st.session_state.approved or not st.session_state.topic,
        help="Run the 4-agent team to generate Boolean queries"
    )

with col2:
    if st.session_state.approved:
        st.info("✅ Phase 1 is locked. Queries cannot be regenerated.")
    elif not st.session_state.topic:
        st.warning("⚠️ Please enter a research topic first.")

# Generate Queries Logic
if generate_button:
    try:
        # Create LLM provider based on sidebar settings
        if st.session_state.provider_type == "anthropic":
            provider = AnthropicProvider(api_key=st.session_state.anthropic_api_key, model=st.session_state.anthropic_model_id)
        elif st.session_state.provider_type == "bedrock":
            provider = BedrockProvider(
                region=st.session_state.aws_region,
                model_id=st.session_state.aws_model_id,
                aws_access_key_id=st.session_state.aws_access_key_id or None,
                aws_secret_access_key=st.session_state.aws_secret_access_key or None
            )
        else:  # dummy
            provider = DummyProvider()

        # Initialize team with provider
        team = QueryGenerationTeam(llm_provider=provider)

        # Handle variations if enabled
        num_runs = st.session_state.num_variations if st.session_state.enable_variations else 1
        all_variations = []

        for variation_idx in range(num_runs):
            variation_seed = variation_idx + 1 if st.session_state.enable_variations else None
            variation_label = f" - Variation #{variation_seed}" if variation_seed else ""

            # Create progress display with status widget
            with st.status(f"🔮 Initiating the Four-Agent Query Generation Ritual{variation_label}...", expanded=True) as status:
                # Show model information
                model_name = provider.get_model_name() if hasattr(provider, 'get_model_name') else "Unknown"
                st.write(f"🤖 **Active Model**: {model_name}")
                st.write(f"💡 _View system prompts: Sidebar → 'Model & Prompt Information'_")
                st.write("")

                # Agent 1: Pulse
                st.write("🔍 **Agent 1: Pulse** - Diving into academic jargon soup...")
                st.write("_Extracting synonyms, related terms, and methodological keywords from the research cosmos..._")
                import time
                start_time = time.time()

                pulse_result = team._agent_pulse(st.session_state.topic, variation_seed=variation_seed)
                pulse_time = time.time() - start_time

                keyword_count = len(pulse_result.get('expanded_keywords', []))
                st.write(f"✅ **Pulse Complete!** Found {keyword_count} keywords in {pulse_time:.1f}s")
                st.write("")

                # Agent 2: Formulator
                st.write("🧙 **Agent 2: Formulator** - Weaving Boolean magic spells...")
                st.write("_Crafting database-specific queries with AND, OR, and wildcards of power..._")
                start_time = time.time()

                formulator_result = team._agent_formulator(pulse_result)
                formulator_time = time.time() - start_time

                st.write(f"✅ **Formulator Complete!** Created 3 database queries in {formulator_time:.1f}s")
                st.write("")

                # Agent 3: Sentinel
                st.write("🛡️ **Agent 3: Sentinel** - Inspecting queries with extreme prejudice...")
                st.write("_Validating syntax, checking parentheses, ensuring systematic review rigor..._")
                start_time = time.time()

                sentinel_result = team._agent_sentinel({
                    "elsevier_query": formulator_result.get('elsevier_query', ''),
                    "pubmed_query": formulator_result.get('pubmed_query', ''),
                    "openalex_query": formulator_result.get('openalex_query', '')
                })
                sentinel_time = time.time() - start_time

                warnings = sentinel_result.get('warnings', [])
                if warnings:
                    st.write(f"⚠️ **Sentinel Complete!** Found {len(warnings)} issues to review in {sentinel_time:.1f}s")
                else:
                    st.write(f"✅ **Sentinel Complete!** All queries validated in {sentinel_time:.1f}s")
                st.write("")

                # Agent 4: Refiner
                st.write("💎 **Agent 4: Refiner** - Polishing queries to perfection...")
                st.write("_Resolving all issues and producing final, execution-ready queries..._")
                start_time = time.time()

                refiner_result = team._agent_refiner(sentinel_result)
                refiner_time = time.time() - start_time

                issues_resolved = refiner_result.get('issues_resolved', [])
                if issues_resolved:
                    st.write(f"✅ **Refiner Complete!** Resolved {len(issues_resolved)} issues in {refiner_time:.1f}s")
                else:
                    st.write(f"✅ **Refiner Complete!** Final polish applied in {refiner_time:.1f}s")

                status.update(label=f"✨ Query Generation Complete{variation_label}!", state="complete", expanded=False)

            # Store this variation
            variation_data = {
                "variation_seed": variation_seed,
                "pulse_keywords": pulse_result.get('expanded_keywords', []),
                "pulse_reasoning": pulse_result.get('reasoning', ''),
                "formulator_reasoning": formulator_result.get('reasoning', ''),
                "sentinel_validation": sentinel_result.get('validation_notes', ''),
                "sentinel_warnings": sentinel_result.get('warnings', []),
                "refiner_notes": refiner_result.get('refinement_notes', ''),
                "issues_resolved": refiner_result.get('issues_resolved', []),
                "queries": {
                    "elsevier_query": refiner_result.get('elsevier_query', ''),
                    "pubmed_query": refiner_result.get('pubmed_query', ''),
                    "openalex_query": refiner_result.get('openalex_query', '')
                }
            }
            all_variations.append(variation_data)

        # Store all variations
        st.session_state.query_variations = all_variations

        # Set the primary query set to the first variation (or only one if not using variations)
        primary = all_variations[0]
        st.session_state.pulse_keywords = primary['pulse_keywords']
        st.session_state.pulse_reasoning = primary['pulse_reasoning']
        st.session_state.elsevier_query = primary['queries']['elsevier_query']
        st.session_state.pubmed_query = primary['queries']['pubmed_query']
        st.session_state.openalex_query = primary['queries']['openalex_query']
        st.session_state.formulator_reasoning = primary['formulator_reasoning']
        st.session_state.sentinel_validation = primary['sentinel_validation']
        st.session_state.sentinel_warnings = primary['sentinel_warnings']
        st.session_state.refiner_notes = primary['refiner_notes']
        st.session_state.issues_resolved = primary['issues_resolved']
        st.session_state.queries_generated = True
        st.session_state.agent_logs = logger.get_ui_logs()

        if st.session_state.enable_variations:
            st.success(f"🎉 Generated {len(all_variations)} query variations! Review them below.")
        else:
            st.success("🎉 All agents completed successfully! Review your queries below.")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error during query generation: {str(e)}")
        logger.error(f"Query generation failed: {e}", exc_info=True)

# Agent Output Section (only show if queries generated)
if st.session_state.queries_generated:
    st.markdown("---")

    # Variation Selector (if multiple variations exist)
    if len(st.session_state.query_variations) > 1:
        st.subheader("🔄 Query Variations")
        st.markdown(f"**Generated {len(st.session_state.query_variations)} different query variations.** Select one to view details:")

        variation_options = [f"Variation #{v['variation_seed']}" for v in st.session_state.query_variations]
        selected_idx = st.selectbox(
            "Select Variation:",
            range(len(variation_options)),
            format_func=lambda i: variation_options[i],
            key="variation_selector"
        )

        # Update displayed data based on selection
        selected_variation = st.session_state.query_variations[selected_idx]
        st.session_state.pulse_keywords = selected_variation['pulse_keywords']
        st.session_state.pulse_reasoning = selected_variation['pulse_reasoning']
        st.session_state.elsevier_query = selected_variation['queries']['elsevier_query']
        st.session_state.pubmed_query = selected_variation['queries']['pubmed_query']
        st.session_state.openalex_query = selected_variation['queries']['openalex_query']
        st.session_state.formulator_reasoning = selected_variation['formulator_reasoning']
        st.session_state.sentinel_validation = selected_variation['sentinel_validation']
        st.session_state.sentinel_warnings = selected_variation['sentinel_warnings']
        st.session_state.refiner_notes = selected_variation['refiner_notes']
        st.session_state.issues_resolved = selected_variation['issues_resolved']

        st.markdown("---")

    # Save/Load Queries Section
    st.subheader("💾 Save & Load Queries")

    col_save, col_load = st.columns(2)

    with col_save:
        if st.button("📥 Save All Queries", help="Save all query variations to a JSON file"):
            import json
            from datetime import datetime

            save_data = {
                "topic": st.session_state.topic,
                "generated_at": datetime.now().isoformat(),
                "num_variations": len(st.session_state.query_variations),
                "variations": st.session_state.query_variations
            }

            save_filename = f"queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_json = json.dumps(save_data, indent=2)

            st.download_button(
                label="💾 Download Queries JSON",
                data=save_json,
                file_name=save_filename,
                mime="application/json",
                help="Download all query variations as JSON file"
            )
            st.success(f"✅ Ready to download {len(st.session_state.query_variations)} query variations!")

    with col_load:
        uploaded_file = st.file_uploader(
            "📤 Load Saved Queries",
            type=["json"],
            help="Upload a previously saved queries JSON file",
            key="load_queries_uploader"
        )

        if uploaded_file is not None:
            try:
                import json

                loaded_data = json.load(uploaded_file)

                # Validate loaded data
                if "variations" in loaded_data and loaded_data["variations"]:
                    st.session_state.query_variations = loaded_data["variations"]
                    st.session_state.topic = loaded_data.get("topic", "")

                    # Set primary query from first variation
                    primary = loaded_data["variations"][0]
                    st.session_state.pulse_keywords = primary['pulse_keywords']
                    st.session_state.pulse_reasoning = primary['pulse_reasoning']
                    st.session_state.elsevier_query = primary['queries']['elsevier_query']
                    st.session_state.pubmed_query = primary['queries']['pubmed_query']
                    st.session_state.openalex_query = primary['queries']['openalex_query']
                    st.session_state.formulator_reasoning = primary['formulator_reasoning']
                    st.session_state.sentinel_validation = primary['sentinel_validation']
                    st.session_state.sentinel_warnings = primary['sentinel_warnings']
                    st.session_state.refiner_notes = primary['refiner_notes']
                    st.session_state.issues_resolved = primary['issues_resolved']
                    st.session_state.queries_generated = True

                    st.success(f"✅ Loaded {len(loaded_data['variations'])} query variations!")
                    st.rerun()
                else:
                    st.error("❌ Invalid queries file format")
            except Exception as e:
                st.error(f"❌ Error loading queries: {str(e)}")

    st.markdown("---")

    st.subheader("🔬 Agent Outputs")
    st.info("💡 **View System Prompts**: Expand '🔍 Model & Prompt Information' in the sidebar to see the complete system-level prompts used by each agent.")

    col_a, col_b = st.columns(2)

    with col_a:
        with st.expander("🔍 Pulse Agent - Keyword Expansion", expanded=True):
            st.markdown("**Expanded Keywords:**")
            for kw in st.session_state.pulse_keywords:
                st.markdown(f"- `{kw}`")

            if st.session_state.pulse_reasoning:
                st.markdown("**Reasoning:**")
                st.info(st.session_state.pulse_reasoning)

    with col_b:
        with st.expander("💎 Refiner Agent - Final Polish", expanded=True):
            if st.session_state.refiner_notes:
                st.markdown("**Refinement Notes:**")
                st.success(st.session_state.refiner_notes)

            if st.session_state.issues_resolved:
                st.markdown("**Issues Resolved:**")
                for issue in st.session_state.issues_resolved:
                    st.markdown(f"✅ {issue}")
            else:
                st.markdown("**Status:**")
                st.success("✅ Queries were already perfect - final polish applied!")

    # Additional agent details
    col_c, col_d = st.columns(2)
    with col_c:
        with st.expander("⚙️ Formulator Agent - Query Strategy", expanded=False):
            if st.session_state.formulator_reasoning:
                st.info(st.session_state.formulator_reasoning)

    with col_d:
        with st.expander("🛡️ Sentinel Agent - Validation Report", expanded=False):
            if st.session_state.sentinel_validation:
                st.markdown("**Validation Notes:**")
                st.success(st.session_state.sentinel_validation)

            if st.session_state.sentinel_warnings:
                st.markdown("**Warnings:**")
                for warning in st.session_state.sentinel_warnings:
                    st.warning(f"⚠️ {warning}")

    st.markdown("---")

    # Editable Queries Section
    st.subheader("📋 Final Queries (from Refiner Agent)")
    st.markdown("*These queries have been refined and polished. You can still edit before approval.*")

    # Elsevier/Scopus Query
    st.markdown("**Elsevier/Scopus Query:**")
    elsevier_query = st.text_area(
        "Elsevier Query",
        value=st.session_state.elsevier_query,
        height=150,
        disabled=st.session_state.approved,
        key="elsevier_text_area",
        label_visibility="collapsed"
    )
    if elsevier_query != st.session_state.elsevier_query:
        st.session_state.elsevier_query = elsevier_query

    # PubMed Query
    st.markdown("**PubMed Query:**")
    pubmed_query = st.text_area(
        "PubMed Query",
        value=st.session_state.pubmed_query,
        height=150,
        disabled=st.session_state.approved,
        key="pubmed_text_area",
        label_visibility="collapsed"
    )
    if pubmed_query != st.session_state.pubmed_query:
        st.session_state.pubmed_query = pubmed_query

    # OpenAlex Query
    st.markdown("**OpenAlex Query:**")
    openalex_query = st.text_area(
        "OpenAlex Query",
        value=st.session_state.openalex_query,
        height=100,
        disabled=st.session_state.approved,
        key="openalex_text_area",
        label_visibility="collapsed"
    )
    if openalex_query != st.session_state.openalex_query:
        st.session_state.openalex_query = openalex_query

    st.markdown("---")

    # Approval Section
    st.subheader("✅ Approve & Lock")

    if not st.session_state.approved:
        st.markdown("Once you approve, **Phase 1 will be locked** and you'll proceed to Phase 2 (Metadata Search).")

        approve_button = st.button(
            "🟢 Approve & Proceed to Phase 2",
            type="primary",
            help="Lock these queries and proceed to metadata search"
        )

        if approve_button:
            st.session_state.approved = True
            st.session_state.phase = 2
            st.session_state.returned_from_phase2 = False
            logger.info("Phase 1 approved and locked by user")
            logger.info(f"Elsevier Query: {st.session_state.elsevier_query}")
            logger.info(f"PubMed Query: {st.session_state.pubmed_query}")
            logger.info(f"OpenAlex Query: {st.session_state.openalex_query}")
            st.success("✅ Phase 1 locked successfully! Ready for Phase 2.")
            st.balloons()
            st.rerun()
    else:
        st.success("✅ Phase 1 is locked. Queries are ready for Phase 2!")

# ==============================================================================
# PHASE 2: METADATA SEARCH EXECUTION
# ==============================================================================

if st.session_state.phase >= 2:
    st.markdown("---")
    render_progress_steps(st.session_state.phase)
    phase_header(2, "🔍", "Phase 2 · Metadata Search", "Execute approved queries across academic databases")

    # Back button
    if st.button("← Back to Phase 1 (Edit Queries)", key="back_to_phase1"):
        st.session_state.phase = 1
        st.session_state.approved = False
        st.session_state.returned_from_phase2 = True
        st.rerun()

    # Show variation info if multiple variations exist
    if len(st.session_state.query_variations) > 1:
        st.info(
            f"📊 **Query Variations Mode**: {len(st.session_state.query_variations)} query variations will be searched for each database. "
            f"Results will be automatically merged and deduplicated by DOI/PMID/EID."
        )

    # Database selection
    st.subheader("📚 Select Databases")

    col1, col2, col3 = st.columns(3)

    with col1:
        run_openalex = st.checkbox(
            "OpenAlex",
            value=st.session_state.run_openalex,
            help="Free, comprehensive coverage",
            key="run_openalex_checkbox"
        )
        if run_openalex:
            openalex_max = st.number_input(
                "Max results (OpenAlex):",
                min_value=10,
                max_value=10000,
                value=1000,
                step=100,
                key="openalex_max"
            )

    with col2:
        run_pubmed = st.checkbox(
            "PubMed",
            value=st.session_state.run_pubmed,
            help="NCBI biomedical literature",
            key="run_pubmed_checkbox"
        )
        if run_pubmed:
            pubmed_max = st.number_input(
                "Max results (PubMed):",
                min_value=10,
                max_value=10000,
                value=1000,
                step=100,
                key="pubmed_max"
            )

    with col3:
        run_scopus = st.checkbox(
            "Scopus",
            value=st.session_state.run_scopus,
            help="Elsevier Scopus (requires API key)",
            key="run_scopus_checkbox"
        )
        if run_scopus:
            scopus_max = st.number_input(
                "Max results (Scopus):",
                min_value=10,
                max_value=5000,
                value=1000,
                step=100,
                key="scopus_max"
            )

    # API credentials section
    with st.expander("🔑 Search API Credentials", expanded=False):
        st.info("💡 **Quick Tip**: OpenAlex only requires an email to get started (free)!")

        st.markdown("**OpenAlex** (Recommended)")
        openalex_mailto = st.text_input(
            "Email (recommended):",
            value=st.session_state.openalex_mailto or "",
            key="openalex_mailto_input",
            placeholder="your@email.com",
            help="Required for polite pool access (better rate limits)"
        )
        openalex_key = st.text_input(
            "API Key (optional):",
            type="password",
            value=st.session_state.openalex_api_key or "",
            key="openalex_api_key_input",
            help="Optional - get it at openalex.org for higher rate limits"
        )

        st.markdown("**PubMed:**")
        pubmed_key = st.text_input(
            "API Key (optional):",
            type="password",
            value=st.session_state.pubmed_api_key or "",
            key="pubmed_api_key_input"
        )
        pubmed_email = st.text_input(
            "Email (optional):",
            value=st.session_state.pubmed_email or "",
            key="pubmed_email_input"
        )

        st.markdown("**Scopus:**")
        scopus_key = st.text_input(
            "API Key (required):",
            type="password",
            value=st.session_state.scopus_api_key or "",
            key="scopus_api_key_input"
        )
        scopus_insttoken = st.text_input(
            "Inst Token (optional):",
            type="password",
            value=st.session_state.scopus_insttoken or "",
            key="scopus_insttoken_input"
        )

    # Advanced settings (optional output directory customization)
    with st.expander("⚙️ Advanced Settings", expanded=False):
        # Auto-generate default output directory
        if 'current_out_dir' not in st.session_state or not st.session_state.search_results_dir:
            st.session_state.current_out_dir = f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        out_dir = st.text_input(
            "Output Directory:",
            value=st.session_state.current_out_dir,
            help="Custom directory name (auto-generated by default)",
            key="out_dir_input"
        )
        st.caption("💡 Leave as default unless you need a custom location")

    # Execute button
    if st.button("🚀 Execute Search", type="primary", key="execute_search_button"):
        # Determine which databases to search
        db_list = []
        if run_openalex:
            db_list.append(("openalex", openalex_max))
        if run_pubmed:
            db_list.append(("pubmed", pubmed_max))
        if run_scopus:
            db_list.append(("scopus", scopus_max))

        if not db_list:
            st.warning("⚠️ Please select at least one database to search.")
        else:
            st.session_state.search_running = True
            st.session_state.search_results = {}

            # Determine how many query variations to search
            num_variations = len(st.session_state.query_variations) if st.session_state.query_variations else 1

            # Progress tracking
            total_tasks = len(db_list) * num_variations
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Store results for each database (will be merged later)
            merged_results = {db[0]: {"variations": [], "success": False} for db in db_list}

            task_idx = 0

            # Search all variations for each database
            for var_idx in range(num_variations):
                variation_label = f" (Variation #{var_idx + 1})" if num_variations > 1 else ""

                # Get queries for this variation
                if st.session_state.query_variations:
                    variation = st.session_state.query_variations[var_idx]
                    openalex_query = variation['queries']['openalex_query']
                    pubmed_query = variation['queries']['pubmed_query']
                    elsevier_query = variation['queries']['elsevier_query']
                else:
                    openalex_query = st.session_state.openalex_query
                    pubmed_query = st.session_state.pubmed_query
                    elsevier_query = st.session_state.elsevier_query

                for db, max_results in db_list:
                    query = openalex_query if db == "openalex" else (pubmed_query if db == "pubmed" else elsevier_query)

                    status_text.text(f"Searching {db.upper()}{variation_label}...")

                    config = {
                        "api_key": openalex_key if db == "openalex" else (pubmed_key if db == "pubmed" else scopus_key),
                        "mailto": openalex_mailto if db == "openalex" else "",
                        "email": pubmed_email if db == "pubmed" else "",
                        "inst_token": scopus_insttoken if db == "scopus" else ""
                    }

                    try:
                        executor = SearchExecutor(db, query, config)
                        var_out_dir = f"{out_dir}/{db}/variation_{var_idx + 1}" if num_variations > 1 else f"{out_dir}/{db}"
                        result = executor.execute_search(max_results=max_results, out_dir=var_out_dir)

                        # Debug logging for Scopus
                        if db == "scopus":
                            logger.info(f"Scopus result dict: {result}")
                            logger.info(f"Scopus success: {result.get('success')}")
                            logger.info(f"Scopus status: {result.get('status')}")
                            logger.info(f"Scopus error: {result.get('error', 'No error key')}")

                        result['variation_idx'] = var_idx + 1
                        merged_results[db]["variations"].append(result)
                        if result.get("success"):
                            merged_results[db]["success"] = True
                    except Exception as e:
                        logger.error(f"Search execution failed for {db} variation {var_idx + 1}: {e}", exc_info=True)
                        merged_results[db]["variations"].append({
                            "success": False,
                            "status": "error",
                            "error": str(e),
                            "results_count": 0,
                            "output_files": {},
                            "variation_idx": var_idx + 1
                        })

                    task_idx += 1
                    progress_bar.progress(task_idx / total_tasks)

            # Merge and deduplicate results for each database
            status_text.text("Merging and deduplicating results...")
            final_results = {}

            for db in db_list:
                db_name = db[0]
                if num_variations > 1 and merged_results[db_name]["success"]:
                    # Merge all variations
                    final_results[db_name] = _merge_database_variations(
                        db_name,
                        merged_results[db_name]["variations"],
                        out_dir
                    )
                else:
                    # Single variation or all failed
                    final_results[db_name] = merged_results[db_name]["variations"][0] if merged_results[db_name]["variations"] else {
                        "success": False,
                        "status": "error",
                        "error": "No results",
                        "results_count": 0,
                        "output_files": {}
                    }

            st.session_state.search_results = final_results
            st.session_state.search_running = False
            st.session_state.search_results_dir = out_dir
            status_text.empty()
            progress_bar.empty()

            if num_variations > 1:
                st.success(f"✅ Search completed for all {num_variations} variations and merged!")
            else:
                st.success("✅ Search execution completed!")
            st.rerun()

    # Display results
    if st.session_state.search_results:
        st.markdown("---")
        st.subheader("📊 Search Results")

        # Show output directory location
        if st.session_state.search_results_dir:
            st.info(f"💾 **Results saved to:** `{st.session_state.search_results_dir}/`")

        for db, result in st.session_state.search_results.items():
            # Debug logging for Scopus
            if db == "scopus":
                logger.info(f"Displaying Scopus results: {result}")

            with st.expander(f"📁 {db.upper()} Results", expanded=True):
                if result["success"]:
                    st.success(f"✅ Status: {result['status']}")

                    # Show merge statistics if multiple variations were used
                    if result.get("num_variations", 0) > 1:
                        col_m1, col_m2, col_m3 = st.columns(3)
                        col_m1.metric("Variations Searched", result["num_variations"])
                        col_m2.metric("Total Retrieved", result["total_before_dedup"])
                        col_m3.metric("Duplicates Removed", result["duplicates_removed"])
                        st.info(f"**Final Unique Results:** {result['results_count']} papers after deduplication")

                        # Show detailed per-variation statistics
                        with st.expander("📊 Detailed Per-Variation Statistics"):
                            var_summary = result.get("variations_summary", [])
                            if var_summary:
                                var_df = pd.DataFrame(var_summary)
                                var_df.columns = ["Variation #", "Success", "Results Retrieved"]
                                var_df["Success"] = var_df["Success"].map({True: "✅", False: "❌"})
                                st.dataframe(var_df, use_container_width=True, hide_index=True)

                                # Show statistics
                                successful = sum(1 for v in var_summary if v.get("success"))
                                failed = len(var_summary) - successful
                                col_s1, col_s2 = st.columns(2)
                                col_s1.metric("Successful Variations", f"{successful}/{len(var_summary)}")
                                col_s2.metric("Failed Variations", failed)
                    else:
                        st.metric("Results Found", result["results_count"])

                    # Show CSV preview
                    if "summary_csv" in result["output_files"]:
                        csv_path = result["output_files"]["summary_csv"]
                        if Path(csv_path).exists():
                            df = pd.read_csv(csv_path)
                            st.dataframe(df.head(10), use_container_width=True)

                            # Download buttons (read files into memory first)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                with open(csv_path, "rb") as f:
                                    csv_data = f.read()
                                st.download_button(
                                    "📥 Download CSV",
                                    data=csv_data,
                                    file_name=f"{db}_summary.csv",
                                    mime="text/csv",
                                    key=f"download_csv_{db}"
                                )
                            with col2:
                                json_path = result["output_files"]["summary_json"]
                                if Path(json_path).exists():
                                    with open(json_path, "rb") as f:
                                        json_data = f.read()
                                    st.download_button(
                                        "📥 Download JSON",
                                        data=json_data,
                                        file_name=f"{db}_summary.json",
                                        mime="application/json",
                                        key=f"download_json_{db}"
                                    )
                            with col3:
                                jsonl_path = result["output_files"]["full_jsonl"]
                                if Path(jsonl_path).exists():
                                    with open(jsonl_path, "rb") as f:
                                        jsonl_data = f.read()
                                    st.download_button(
                                        "📥 Download JSONL",
                                        data=jsonl_data,
                                        file_name=f"{db}_full.jsonl",
                                        mime="application/json",
                                        key=f"download_jsonl_{db}"
                                    )
                        else:
                            st.warning(f"Output file not found: {csv_path}")
                else:
                    error_msg = result.get('error', '')
                    if error_msg:
                        st.error(f"❌ Error: {error_msg}")
                    else:
                        st.error(f"❌ Search failed with status: {result.get('status', 'unknown')}")

        # Approve Phase 2 button
        if st.button("🟢 Approve & Proceed to Phase 3", type="primary", key="approve_phase2_button"):
            st.session_state.phase = 3
            st.session_state.search_results_dir = out_dir  # Save output directory for Phase 3
            logger.info("Phase 2 approved and locked by user")
            st.success("✅ Phase 2 locked. Ready for Phase 3 (Screening)!")
            st.rerun()

# ==============================================================================
# PHASE 3: ABSTRACT SCREENING
# ==============================================================================

if st.session_state.phase >= 3:
    st.markdown("---")
    render_progress_steps(st.session_state.phase)
    phase_header(3, "✅", "Phase 3 · Abstract Screening", "AI screens titles and abstracts against your inclusion criteria")

    # Back button
    if st.button("← Back to Phase 2", key="back_to_phase2"):
        st.session_state.phase = 2
        st.session_state.screening_approved = False
        st.session_state.screening_complete = False
        st.rerun()

    # Configuration Section
    st.subheader("⚙️ Screening Configuration")

    # Display model information
    if 'llm_provider' in st.session_state and st.session_state.get('llm_provider'):
        provider = st.session_state.llm_provider
        model_name = provider.get_model_name() if hasattr(provider, 'get_model_name') else "Unknown"
        st.info(f"🤖 **Active Model**: {model_name} | 💡 View system prompts in sidebar: '🔍 Model & Prompt Information'")
    else:
        st.warning("⚠️ No LLM provider configured. Please configure in Phase 1 first.")

    col_mode, col_threads = st.columns(2)
    with col_mode:
        screening_mode = st.selectbox(
            "Screening Mode:",
            options=["simple", "detailed"],
            index=0 if st.session_state.screening_mode == "simple" else 1,
            format_func=lambda x: {
                "simple": "Simple (Fast, concise)",
                "detailed": "Detailed (Thorough reasoning)"
            }[x],
            help="Simple: Quick decision with brief reason. Detailed: Step-by-step analysis with reasoning.",
            key="screening_mode_select",
            disabled=st.session_state.screening_approved
        )
        st.session_state.screening_mode = screening_mode

    with col_threads:
        thread_count = st.slider(
            "Worker Threads:",
            1, 16, st.session_state.screening_threads,
            help="Number of parallel screening workers. More threads = faster, but higher API usage.",
            key="screening_threads_slider",
            disabled=st.session_state.screening_approved
        )
        st.session_state.screening_threads = thread_count

    # AI-powered criteria generation
    with st.expander("🤖 AI Criteria Assistant", expanded=False):
        st.markdown("**Describe your screening needs in plain language, and AI will generate structured criteria.**")

        user_description = st.text_area(
            "What do you want to screen for?",
            placeholder="e.g., I want to find studies about cooling centers that reduce heat-related deaths, focusing on experimental or quasi-experimental designs...",
            height=100,
            key="criteria_description_input",
            disabled=st.session_state.screening_approved
        )

        col_gen, col_clear = st.columns([3, 1])
        with col_gen:
            generate_criteria_btn = st.button(
                "✨ Generate Criteria",
                type="primary",
                disabled=not user_description or st.session_state.screening_approved,
                key="generate_criteria_button"
            )
        with col_clear:
            if st.button("🔄 Clear", key="clear_criteria_button", disabled=st.session_state.screening_approved):
                st.session_state.generated_criteria = ""
                st.rerun()

        if generate_criteria_btn and user_description:
            with st.spinner("🤖 AI is formulating your criteria..."):
                try:
                    # Use the same LLM provider from Phase 1
                    if st.session_state.provider_type == "anthropic":
                        provider = AnthropicProvider(api_key=st.session_state.anthropic_api_key, model=st.session_state.anthropic_model_id)
                    elif st.session_state.provider_type == "bedrock":
                        provider = BedrockProvider(
                            region=st.session_state.aws_region,
                            model_id=st.session_state.aws_model_id,
                            aws_access_key_id=st.session_state.aws_access_key_id or None,
                            aws_secret_access_key=st.session_state.aws_secret_access_key or None
                        )
                    else:  # dummy
                        provider = DummyProvider()

                    if not provider.is_available():
                        st.error("❌ LLM provider not available. Please configure API settings in the sidebar.")
                    else:
                        system_prompt = """You are an expert in systematic literature reviews and abstract screening criteria formulation.

Your task: Convert the user's plain language description into structured, precise inclusion/exclusion criteria.

Structure your output as follows:
1. INCLUSION CRITERIA (numbered list with specific, measurable criteria)
2. EXCLUSION CRITERIA (numbered list with specific types to exclude)

Be specific about:
- Population/intervention
- Outcomes
- Study designs (e.g., RCT, quasi-experimental, observational)
- Geographic scope (if mentioned)
- Time period (if mentioned)

Use clear, concise language. Each criterion should be unambiguous."""

                        user_message = f"""Convert this description into structured screening criteria:

{user_description}

Provide clear inclusion and exclusion criteria that can be used for abstract screening."""

                        response = provider.call_model(system_prompt, user_message, max_tokens=1500)

                        st.session_state.generated_criteria = response
                        st.success("✅ Criteria generated!")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error generating criteria: {str(e)}")
                    logger.error(f"Criteria generation failed: {e}", exc_info=True)

        # Display generated criteria
        if 'generated_criteria' not in st.session_state:
            st.session_state.generated_criteria = ""

        if st.session_state.generated_criteria:
            st.markdown("---")
            st.markdown("**Generated Criteria:**")
            st.markdown(st.session_state.generated_criteria)

            col_accept, col_edit = st.columns(2)
            with col_accept:
                if st.button("✅ Use This Criteria", key="accept_criteria_button", disabled=st.session_state.screening_approved):
                    st.session_state.screening_criteria = st.session_state.generated_criteria
                    st.success("✅ Criteria copied to main input!")
                    st.rerun()
            with col_edit:
                st.info("💡 You can edit the criteria in the main text area below")

    criteria_text = st.text_area(
        "Inclusion/Exclusion Criteria:",
        value=st.session_state.screening_criteria,
        height=150,
        placeholder="e.g., Include studies that examine cooling centers and heat-related mortality with causal research designs (experimental or quasi-experimental)...",
        key="screening_criteria_input",
        disabled=st.session_state.screening_approved
    )
    st.session_state.screening_criteria = criteria_text

    # Execute Screening Button
    if not st.session_state.screening_approved:
        if st.button("🚀 Run Screening", type="primary", disabled=not criteria_text, key="run_screening_button"):
            # Funny screening messages that change with progress
            funny_messages = [
                "🔍 Reading abstracts like a caffeinated grad student...",
                "🤔 Judging papers harder than peer reviewers...",
                "📚 Channeling inner systematic review guru...",
                "🧐 Separating wheat from chaff (academically speaking)...",
                "🎯 Applying inclusion criteria with surgical precision...",
                "📊 Computing relevance scores faster than you can say 'meta-analysis'...",
                "🤓 Being more picky than journal editors...",
                "🔬 Scrutinizing methods sections with microscopic detail...",
                "📖 Speed-reading like it's a competitive sport...",
                "🎓 Channeling years of systematic review training...",
                "🧠 Neural networks doing the heavy intellectual lifting...",
                "📝 Writing rejection letters (politely) in my head...",
                "✨ Sprinkling AI magic on your literature search...",
                "🚀 Launching papers into 'included' or 'excluded' orbits...",
                "🎪 Performing the great abstract screening circus act...",
                "🏆 Competing for the gold medal in paper judgment...",
                "🔮 Predicting which papers will make the cut...",
                "🎨 Painting your systematic review masterpiece...",
                "🌟 Finding needles in the academic haystack...",
                "🎯 Hitting the inclusion criteria bullseye..."
            ]

            with st.status("📋 Screening Abstracts...", expanded=True) as status:
                # Placeholders for dynamic updates
                progress_bar = st.progress(0)
                message_placeholder = st.empty()
                stats_placeholder = st.empty()

                try:
                    # Create LLM provider instance
                    if st.session_state.provider_type == "anthropic":
                        provider = AnthropicProvider(api_key=st.session_state.anthropic_api_key, model=st.session_state.anthropic_model_id)
                    elif st.session_state.provider_type == "bedrock":
                        provider = BedrockProvider(
                            region=st.session_state.aws_region,
                            model_id=st.session_state.aws_model_id,
                            aws_access_key_id=st.session_state.aws_access_key_id or None,
                            aws_secret_access_key=st.session_state.aws_secret_access_key or None
                        )
                    else:  # dummy
                        provider = DummyProvider()

                    if not provider.is_available():
                        st.error("❌ LLM provider not available. Please configure API settings in the sidebar.")
                        raise RuntimeError("LLM provider not available")

                    orchestrator = ScreeningOrchestrator(config={
                        'mode': screening_mode,
                        'llm_provider': provider,
                        'thread_count': thread_count
                    })

                    # Get Phase 2 output directory or imported data
                    if st.session_state.get('data_imported') and 'imported_data' in st.session_state:
                        st.write("📁 Using imported data...")
                        df_consolidated = st.session_state.imported_data
                    else:
                        phase2_dir = st.session_state.search_results_dir
                        if not phase2_dir:
                            st.error("❌ Phase 2 output directory not found. Please complete Phase 2 first.")
                            raise RuntimeError("No Phase 2 data")
                        st.write("📁 Consolidating Phase 2 results...")
                        df_consolidated = orchestrator.consolidate_phase2_results(phase2_dir)

                    st.write(f"✅ Loaded {len(df_consolidated)} unique records")
                    st.write(f"🤖 Screening with {screening_mode} mode...")

                    # Progress callback for funny messages
                    progress_state = {'last_message_idx': -1}

                    def update_progress(completed, total, included, excluded):
                        # Update progress bar
                        progress = completed / total
                        progress_bar.progress(progress)

                        # Change funny message every ~10% progress
                        message_idx = int(progress * len(funny_messages))
                        if message_idx != progress_state['last_message_idx'] and message_idx < len(funny_messages):
                            message_placeholder.markdown(f"**{funny_messages[message_idx]}**")
                            progress_state['last_message_idx'] = message_idx

                        # Update stats
                        stats_placeholder.markdown(
                            f"**Progress:** {completed}/{total} papers | "
                            f"✅ Included: {included} | "
                            f"❌ Excluded: {excluded}"
                        )

                    # Run screening with progress callback
                    df_screened = orchestrator.run_screening(
                        df_consolidated,
                        criteria_text,
                        progress_callback=update_progress
                    )

                    # Final message
                    message_placeholder.markdown("**🎉 All done! Your papers have been judged!**")
                    status.update(label="✅ Screening Complete!", state="complete", expanded=False)

                    # Save to session state
                    st.session_state.screening_results = df_screened
                    st.session_state.screening_complete = True
                    st.success(f"🎉 Screened {len(df_screened)} papers!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Screening failed: {str(e)}")
                    logger.error(f"Screening error: {e}", exc_info=True)
                    status.update(label="❌ Screening Failed", state="error", expanded=True)

    # HITL Review Interface (Paginated Table)
    if st.session_state.screening_complete:
        st.markdown("---")
        st.subheader("📊 Screening Results & Review")

        df = st.session_state.screening_results

        # Summary stats
        col_inc, col_exc, col_err = st.columns(3)
        col_inc.metric("Included", len(df[df['judgement'] == True]))
        col_exc.metric("Excluded", len(df[df['judgement'] == False]))
        col_err.metric("Errors", len(df[df['error'] != ""]) if 'error' in df.columns else 0)

        # Model information (if available in results)
        if 'model' in df.columns and not df['model'].isna().all():
            model_used = df['model'].iloc[0]
            mode_used = df['mode'].iloc[0] if 'mode' in df.columns else st.session_state.screening_mode
            st.caption(f"🤖 **Model**: {model_used} | **Mode**: {mode_used} | 💡 View prompts: Sidebar → 'Model & Prompt Information'")

        # Filter controls
        filter_option = st.radio(
            "Show:",
            options=["All", "Included Only", "Excluded Only", "Low Confidence (<70%)"],
            horizontal=True,
            key="screening_filter_radio"
        )

        if filter_option == "Included Only":
            df_display = df[df['judgement'] == True].copy()
        elif filter_option == "Excluded Only":
            df_display = df[df['judgement'] == False].copy()
        elif filter_option == "Low Confidence (<70%)":
            if 'confidence' in df.columns:
                df_display = df[df['confidence'] < 70].copy()
            else:
                df_display = df.copy()
                st.warning("No confidence column found")
        else:
            df_display = df.copy()

        # Pagination
        items_per_page = 20
        total_pages = max(1, (len(df_display) - 1) // items_per_page + 1)
        page = st.number_input("Page", 1, total_pages, 1, key="review_page") - 1

        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(df_display))
        df_page = df_display.iloc[start_idx:end_idx]

        # Download buttons (before table for easy access)
        st.markdown("**📥 Export Results:**")
        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            df_included = df[df['judgement'] == True].copy()
            csv_included = df_included.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Included Papers ({len(df_included)})",
                data=csv_included,
                file_name=f"screening_included_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_included_csv"
            )

        with dl_col2:
            csv_all = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 All Results ({len(df)})",
                data=csv_all,
                file_name=f"screening_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_all_csv"
            )

        st.markdown("---")

        # Editable dataframe
        st.markdown(f"**Review and Edit Decisions (showing {start_idx + 1}-{end_idx} of {len(df_display)}):**")

        # Build display columns: screening fields + available metadata
        core_cols = ['judgement', 'title', 'reason']
        metadata_cols = ['doi', 'journal_title', 'authors', 'author', 'publication_year',
                         'publication_date', 'source', 'cited_by_count']
        optional_cols = ['abstract', 'confidence']
        display_cols = (
            core_cols
            + [c for c in metadata_cols if c in df_page.columns]
            + [c for c in optional_cols if c in df_page.columns]
        )

        col_config = {
            "judgement": st.column_config.CheckboxColumn("Include?", help="Toggle to override Claude decision"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "reason": st.column_config.TextColumn("Reason", width="medium"),
            "doi": st.column_config.TextColumn("DOI", width="medium"),
            "journal_title": st.column_config.TextColumn("Journal", width="medium"),
            "authors": st.column_config.TextColumn("Authors", width="medium"),
            "author": st.column_config.TextColumn("Authors", width="medium"),
            "publication_year": st.column_config.NumberColumn("Year", format="%d"),
            "publication_date": st.column_config.TextColumn("Date"),
            "source": st.column_config.TextColumn("Source", width="small"),
            "abstract": st.column_config.TextColumn("Abstract", width="large"),
            "confidence": st.column_config.NumberColumn("Confidence %", format="%.0f"),
            "cited_by_count": st.column_config.NumberColumn("Citations", format="%d"),
        }

        disabled_cols = [c for c in display_cols if c != 'judgement']

        edited_df = st.data_editor(
            df_page[display_cols],
            use_container_width=True,
            column_config=col_config,
            disabled=disabled_cols,
            hide_index=True,
            key="screening_data_editor"
        )

        # Apply edits back to session state
        if st.button("💾 Save Edits", key="save_edits_button"):
            st.session_state.screening_results.loc[df_page.index, 'judgement'] = edited_df['judgement']
            st.success("✅ Edits saved!")
            st.rerun()

        # Approve Phase 3 Button
        st.markdown("---")
        if not st.session_state.screening_approved:
            if st.button("🟢 Approve & Proceed to Phase 4", type="primary", key="approve_phase3_button"):
                # Save final results
                out_dir = f"screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # Create a minimal provider just for saving (not used during save)
                if st.session_state.provider_type == "anthropic":
                    provider = AnthropicProvider(api_key=st.session_state.anthropic_api_key, model=st.session_state.anthropic_model_id)
                elif st.session_state.provider_type == "bedrock":
                    provider = BedrockProvider(
                        region=st.session_state.aws_region,
                        model_id=st.session_state.aws_model_id,
                        aws_access_key_id=st.session_state.aws_access_key_id or None,
                        aws_secret_access_key=st.session_state.aws_secret_access_key or None
                    )
                else:
                    provider = DummyProvider()

                orchestrator = ScreeningOrchestrator(config={
                    'mode': screening_mode,
                    'llm_provider': provider,
                    'thread_count': thread_count
                })
                orchestrator.save_results(st.session_state.screening_results, out_dir)

                st.session_state.phase = 4
                st.session_state.screening_approved = True
                st.session_state.screening_out_dir = out_dir
                logger.info("Phase 3 approved and locked by user")
                st.success(f"✅ Phase 3 locked! Results saved to {out_dir}")
                st.rerun()
        else:
            st.success("✅ Phase 3 is locked. Ready for Phase 4!")

# ==============================================================================
# PHASE 4: FULL-TEXT RETRIEVAL
# ==============================================================================

if st.session_state.phase >= 4:
    st.markdown("---")
    render_progress_steps(st.session_state.phase)
    phase_header(4, "📄", "Phase 4 · Full-Text Retrieval", "Download PDFs/XMLs via OA → publishers → browser fallback")

    # Back button
    if st.button("← Back to Phase 3", key="back_to_phase3"):
        st.session_state.phase = 3
        st.session_state.fulltext_approved = False
        st.session_state.fulltext_complete = False
        st.rerun()

    # Configuration Section
    st.subheader("⚙️ Retrieval Configuration")

    col_pw, col_retry = st.columns(2)
    with col_pw:
        use_playwright = st.checkbox(
            "Enable Playwright Fallback",
            value=st.session_state.fulltext_use_playwright,
            help="Use browser automation as last resort (slower but higher success rate)",
            key="fulltext_playwright_checkbox",
            disabled=st.session_state.fulltext_approved
        )
        st.session_state.fulltext_use_playwright = use_playwright

    with col_retry:
        max_retries = st.number_input(
            "Max Retries:",
            1, 10, st.session_state.fulltext_max_retries,
            key="fulltext_retries_input",
            disabled=st.session_state.fulltext_approved
        )
        st.session_state.fulltext_max_retries = max_retries

    timeout = st.slider(
        "Timeout (seconds):",
        30, 300, st.session_state.fulltext_timeout, 30,
        key="fulltext_timeout_slider",
        disabled=st.session_state.fulltext_approved
    )
    st.session_state.fulltext_timeout = timeout

    # API credentials section
    with st.expander("🔑 Full-Text API Credentials & Setup Guide"):
        st.markdown("""
        Full-text retrieval uses three sources in priority order:
        **OpenAlex (free OA)** → **Elsevier/Wiley (institutional)** → **Playwright browser fallback**
        """)

        # OpenAlex
        st.markdown("---")
        st.markdown("#### 🟢 OpenAlex — Free & No Registration Required")
        st.info(
            "OpenAlex is **free** and works without an API key. "
            "Providing your **email address** gives you the 'polite pool' (faster rate limit). "
            "No registration needed — just enter any valid email."
        )
        col_oa1, col_oa2 = st.columns(2)
        with col_oa1:
            fulltext_openalex_key = st.text_input(
                "API Key (optional):",
                type="password",
                value=st.session_state.openalex_api_key or "",
                key="fulltext_openalex_key",
                help="Uses Phase 2 credentials if already entered"
            )
        with col_oa2:
            fulltext_openalex_mailto = st.text_input(
                "Email (recommended):",
                value=st.session_state.openalex_mailto or "",
                key="fulltext_openalex_mailto",
                help="Any valid email — enables faster 'polite pool' rate limits"
            )

        # Elsevier
        st.markdown("---")
        st.markdown("#### 🔵 Elsevier — Institutional Access")
        st.info(
            "Requires an **Elsevier API key** from your institution. "
            "Register at [dev.elsevier.com](https://dev.elsevier.com/) with your institutional email. "
            "An institutional token may also be required — contact your library if unsure."
        )
        col_els1, col_els2 = st.columns(2)
        with col_els1:
            fulltext_elsevier_key = st.text_input(
                "API Key:",
                type="password",
                value=st.session_state.scopus_api_key or "",
                key="fulltext_elsevier_key",
                help="Uses Scopus API key from Phase 2 if already entered"
            )
        with col_els2:
            fulltext_elsevier_token = st.text_input(
                "Inst Token (optional):",
                type="password",
                value=st.session_state.scopus_insttoken or "",
                key="fulltext_elsevier_token",
                help="Institutional token for entitled access — ask your library"
            )

        # Wiley
        st.markdown("---")
        st.markdown("#### 🟠 Wiley TDM — Text and Data Mining")
        st.info(
            "Wiley requires a **TDM (Text and Data Mining) token** for full-text access. "
            "Apply at the [Wiley TDM portal](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining) — "
            "you need to log in with an institutional account and request access. "
            "Approval is usually granted within a few days. "
            "Without this token, Wiley papers will fall back to browser download (Playwright)."
        )
        fulltext_wiley_token = st.text_input(
            "TDM Client Token:",
            type="password",
            value=st.session_state.wiley_tdm_token or "",
            key="fulltext_wiley_token",
            help="Apply at onlinelibrary.wiley.com/library-info/resources/text-and-datamining"
        )

        st.session_state.wiley_tdm_token = fulltext_wiley_token

    # DOI Preview & Execute Button
    if st.session_state.screening_results is not None:
        df_screening = st.session_state.screening_results
        doi_count = len(df_screening[df_screening['judgement'] == True])
        st.metric("Papers to Retrieve", doi_count)

        # Performance warning for large downloads
        if doi_count > 100:
            st.error(f"""
            ⚠️ **Large Download Warning**: {doi_count} papers

            **Streamlit Cloud Limitations:**
            - RAM: 1 GB (may crash with >100 PDFs)
            - Processing: Sequential (no parallel downloads)

            **Recommendations:**
            1. 🔄 Download in batches of 50 papers
            2. 💻 Consider local installation for large-scale retrieval
            3. ⏱️ Estimated time: ~{doi_count // 2}-{doi_count} minutes

            **To proceed safely:**
            - Go back to Phase 3 and reduce selection
            - Or use local installation (see README.md)
            """)
        elif doi_count > 50:
            st.warning(f"""
            🟡 **Medium Download Warning**: {doi_count} papers

            For optimal stability on Streamlit Cloud:
            - ✅ Recommended batch size: ≤50 papers
            - ⏱️ Estimated time: ~{doi_count // 3}-{doi_count // 2} minutes
            - 💡 Consider splitting into smaller batches

            You can proceed, but larger batches may experience:
            - Slower processing
            - Potential timeout or memory issues
            """)
        else:
            st.info(f"✅ Good batch size ({doi_count} papers). Estimated time: ~{doi_count // 5}-{doi_count // 3} minutes")
    else:
        st.warning("⚠️ No screening results found. Please complete Phase 3 first.")
        doi_count = 0

    if not st.session_state.fulltext_approved and doi_count > 0:
        if st.button("🚀 Start Full-Text Retrieval", type="primary", key="start_fulltext_button"):
            with st.status("📥 Retrieving Full-Text...", expanded=True) as status:
                st.write("📋 Preparing DOI list...")

                try:
                    retriever = FullTextRetriever(
                        config={
                            'out_dir': f"fulltext_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            'convert_to_md': True,  # Always convert per user decision
                            'use_playwright': use_playwright,
                            'max_retries': max_retries,
                            'timeout': timeout
                        },
                        api_credentials={
                            'openalex_api_key': fulltext_openalex_key,
                            'openalex_mailto': fulltext_openalex_mailto,
                            'elsevier_api_key': fulltext_elsevier_key,
                            'elsevier_inst_token': fulltext_elsevier_token,
                            'wiley_tdm_token': fulltext_wiley_token
                        }
                    )

                    doi_list = retriever.prepare_doi_list(df_screening)
                    st.write(f"✅ Prepared {len(doi_list)} DOIs")

                    st.write("🔄 Running fulltext chain (OA → Publishers → Playwright)...")

                    result_summary = retriever.run_fulltext_chain(doi_list)

                    if result_summary.get('status') == 'error':
                        st.error(f"❌ Retrieval failed: {result_summary.get('message')}")
                        status.update(label="❌ Retrieval Failed", state="error", expanded=True)
                    else:
                        success_count = result_summary.get('success', 0)
                        total_count = result_summary.get('total', len(doi_list))
                        st.write(f"✅ Retrieved {success_count} / {total_count} files")
                        status.update(label="✅ Retrieval Complete!", state="complete", expanded=False)

                        # Save to session state
                        st.session_state.fulltext_results = retriever.parse_results(retriever.config['out_dir'])
                        st.session_state.fulltext_complete = True
                        st.session_state.fulltext_out_dir = retriever.config['out_dir']
                        st.success("🎉 Full-text retrieval complete!")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Retrieval failed: {str(e)}")
                    logger.error(f"Full-text retrieval error: {e}", exc_info=True)
                    status.update(label="❌ Retrieval Failed", state="error", expanded=True)

    # Results Display
    if st.session_state.fulltext_complete and st.session_state.fulltext_results is not None:
        st.markdown("---")
        st.subheader("📊 Retrieval Results")

        df_results = st.session_state.fulltext_results

        if len(df_results) > 0:
            # Summary stats
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Total", len(df_results))

            if 'success' in df_results.columns:
                col_s2.metric("Success", len(df_results[df_results['success'] == True]))

            if 'download_type' in df_results.columns:
                col_s3.metric("PDFs", len(df_results[df_results['download_type'] == 'pdf']))
                col_s4.metric("XMLs", len(df_results[df_results['download_type'] == 'xml']))

            # Preview table
            st.markdown("**Retrieved Files:**")
            preview_cols = [col for col in ['doi', 'title', 'success', 'final_source', 'download_type', 'md_status'] if col in df_results.columns]
            if preview_cols:
                st.dataframe(df_results[preview_cols], use_container_width=True)
            else:
                st.dataframe(df_results, use_container_width=True)

            # Download button for results CSV
            st.markdown(f"**Output Directory:** `{st.session_state.fulltext_out_dir}/`")
        else:
            st.info("No results data available")

        # Complete Phase 4 Button
        st.markdown("---")
        if not st.session_state.fulltext_approved:
            if st.button("🟢 Mark as Complete & Lock", type="primary", key="approve_phase4_button"):
                st.session_state.fulltext_approved = True
                logger.info("Phase 4 approved and locked by user")
                st.success("✅ Phase 4 complete! Full-text retrieval is locked.")
                st.rerun()
        else:
            st.success("✅ Phase 4 is complete. Download your results above.")

# Bottom: Live Agent Log
st.markdown("---")
st.subheader("📋 Live Agent Log")

log_container = st.container()
with log_container:
    if st.session_state.agent_logs:
        # Display logs in a code block for better formatting
        logs_text = "\n".join(st.session_state.agent_logs)
        st.code(logs_text, language="log")
    else:
        st.info("No agent activity yet. Generate queries to see logs.")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#94A3B8; font-size:0.8em; padding:0.5rem 0;">'
    'Winnow · Systematic Literature Search · Powered by Claude AI'
    '</div>',
    unsafe_allow_html=True
)
