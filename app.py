import streamlit as st
import json
import pandas as pd
from crewai import Crew, Process

from agent import schema_analyst, dimensional_modeller, sql_writer
from tasks import schema_analysis, dimensional_modelling, sql_writing
from datamodels import PipelineOutput

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Dimensional Modelling Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# Custom CSS — Dark Industrial / Refined Utility
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:         #f5f7fa;
    --surface:    #ffffff;
    --surface2:   #eef1f6;
    --border:     #dde2ec;
    --accent:     #2563eb;
    --accent2:    #7c3aed;
    --success:    #059669;
    --warn:       #d97706;
    --danger:     #dc2626;
    --text:       #111827;
    --muted:      #6b7280;
    --fact-color: #2563eb;
    --dim-color:  #7c3aed;
    --mono:       'Space Mono', monospace;
    --sans:       'DM Sans', sans-serif;
}

/* ══ FORCE LIGHT BACKGROUND EVERYWHERE ══ */
html, body                                        { background: #f5f7fa !important; color: #111827 !important; }
.stApp                                            { background: #f5f7fa !important; }
.stApp > div                                      { background: #f5f7fa !important; }
[data-testid="stAppViewContainer"]                { background: #f5f7fa !important; }
[data-testid="stAppViewBlockContainer"]           { background: #f5f7fa !important; }
[data-testid="block-container"]                   { background: #f5f7fa !important; padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"]                   { background: transparent !important; }
[data-testid="stHorizontalBlock"]                 { background: #f5f7fa !important; gap: 0 !important; }
[data-testid="column"]                            { background: #f5f7fa !important; }
section[data-testid="stSidebar"]                  { background: #ffffff !important; }
.main .block-container                            { background: #f5f7fa !important; padding: 0 !important; max-width: 100% !important; }
[data-testid="stForm"]                            { background: transparent !important; border: none !important; }
[data-testid="stMarkdownContainer"]               { background: transparent !important; color: #111827 !important; }
[data-testid="stHorizontalBlock"] > div + div     { border-left: 1px solid #dde2ec; }
#MainMenu, footer, header, [data-testid="stToolbar"] { visibility: hidden !important; height: 0 !important; }
*, *::before, *::after                            { box-sizing: border-box; }
body                                              { font-family: 'DM Sans', sans-serif !important; }

/* ══ INPUTS ══ */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] > div > div           { background: #ffffff !important; }

[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #dde2ec !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #9ca3af !important; }

/* ══ BUTTONS ══ */
.stButton > button {
    background: #2563eb !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
    padding: 10px 20px !important;
    transition: background 0.2s !important;
    box-shadow: 0 1px 4px rgba(37,99,235,0.25) !important;
}
.stButton > button:hover { background: #1d4ed8 !important; }

[data-testid="stDownloadButton"] button {
    background: #ffffff !important;
    color: #374151 !important;
    border: 1px solid #dde2ec !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}

/* ══ PANE LABEL ══ */
.pane-label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #9ca3af;
    padding: 14px 20px 10px;
    border-bottom: 1px solid #dde2ec;
    background: #ffffff;
}

/* ══ VERSION BADGE ══ */
.version-badge {
    font-family: var(--mono);
    font-size: 11px;
    color: #2563eb;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    padding: 3px 10px;
    display: inline-block;
    margin: 14px 20px 6px;
}

.version-block { padding: 0 20px 16px; }

.version-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #eef1f6;
    font-size: 13px;
    color: #374151;
}

.version-item span.tag {
    font-family: var(--mono);
    font-size: 10px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 3px;
    padding: 2px 8px;
    color: #111827;
}

/* ══ STATUS PILL ══ */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--mono);
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 999px;
    margin: 8px 20px;
}
.status-pill.idle { background: #f3f4f6;              color: #6b7280; border: 1px solid #e5e7eb; }
.status-pill.run  { background: #eff6ff;              color: #2563eb; border: 1px solid #bfdbfe; }
.status-pill.done { background: #ecfdf5;              color: #059669; border: 1px solid #a7f3d0; }

.dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.dot.idle { background: #d1d5db; }
.dot.run  { background: #2563eb; animation: blink 1s infinite; }
.dot.done { background: #059669; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.25} }

/* ══ PIPELINE STEPS ══ */
.step-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid #eef1f6;
    font-size: 12px;
    color: #374151;
}

/* ══ SECTION HEADER ══ */
.section-header {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #2563eb;
    border-left: 3px solid #2563eb;
    padding: 5px 10px;
    margin: 28px 0 14px;
    background: #eff6ff;
    border-radius: 0 4px 4px 0;
}

/* ══ CLASSIFICATION TABLE ══ */
.tbl-container {
    background: #ffffff;
    border: 1px solid #dde2ec;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.dm-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    font-family: var(--sans);
}

.dm-table th {
    font-family: var(--mono);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #9ca3af;
    padding: 10px 14px;
    background: #f9fafb;
    border-bottom: 1px solid #dde2ec;
    text-align: left;
    font-weight: 400;
}

.dm-table td {
    padding: 9px 14px;
    border-bottom: 1px solid #f3f4f6;
    color: #111827;
    vertical-align: middle;
}

.dm-table tr:last-child td { border-bottom: none; }
.dm-table tr:hover td { background: #f9fafb; }

.badge-fact {
    background: #eff6ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    font-size: 9px;
    font-family: var(--mono);
    padding: 2px 8px;
    white-space: nowrap;
    letter-spacing: 0.05em;
}

.badge-dim {
    background: #f5f3ff;
    color: #7c3aed;
    border: 1px solid #ddd6fe;
    border-radius: 4px;
    font-size: 9px;
    font-family: var(--mono);
    padding: 2px 8px;
    white-space: nowrap;
    letter-spacing: 0.05em;
}

.badge-type {
    background: #f3f4f6;
    color: #6b7280;
    border: 1px solid #e5e7eb;
    border-radius: 3px;
    font-size: 10px;
    font-family: var(--mono);
    padding: 2px 7px;
}

/* ══ SQL BLOCK ══ */
.sql-block {
    background: #1e2333;
    border: 1px solid #2e3a52;
    border-left: 4px solid #059669;
    border-radius: 8px;
    padding: 18px 20px;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.8;
    color: #6ee7b7;
    white-space: pre-wrap;
    overflow-x: auto;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

/* ══ SCHEMA WRAP ══ */
.schema-wrap {
    background: #ffffff;
    border: 1px solid #dde2ec;
    border-radius: 10px;
    padding: 16px;
    overflow-x: auto;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* ══ CHAT ══ */
.chat-wrap {
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.msg-user {
    background: #2563eb;
    border-radius: 14px 14px 2px 14px;
    padding: 10px 14px;
    font-size: 13px;
    color: #ffffff;
    align-self: flex-end;
    max-width: 88%;
    line-height: 1.55;
}

.msg-agent {
    background: #ffffff;
    border: 1px solid #dde2ec;
    border-radius: 2px 14px 14px 14px;
    padding: 10px 14px;
    font-size: 13px;
    color: #111827;
    align-self: flex-start;
    max-width: 88%;
    line-height: 1.55;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.msg-system {
    font-family: var(--mono);
    font-size: 10px;
    color: #9ca3af;
    text-align: center;
    padding: 4px 0;
    letter-spacing: 0.05em;
}

/* ══ MIDDLE PANE SCROLL ══ */
.mid-scroll {
    max-height: calc(100vh - 52px);
    overflow-y: auto;
    padding: 0 22px 48px;
    background: #f5f7fa;
}
.mid-scroll::-webkit-scrollbar       { width: 4px; }
.mid-scroll::-webkit-scrollbar-track { background: #f5f7fa; }
.mid-scroll::-webkit-scrollbar-thumb { background: #dde2ec; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────

def ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

ss("chat_history", [])          # list of {role, text}
ss("stage", "idle")             # idle | schema | modelling | review | sql | done
ss("entity_map", None)
ss("model", None)               # PipelineOutput
ss("sql_output", None)
ss("df_table", None)
ss("status_msg", "Awaiting input")

# ─────────────────────────────────────────────
# Helper: re-used logic from main.py (unchanged)
# ─────────────────────────────────────────────

DATASET_SCHEMA = {
    "type": "object",
    "properties": {
        "datasets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["table_name", "columns", "primary_key"],
                "properties": {
                    "table_name": {"type": "string"},
                    "description": {"type": "string"},
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "type"],
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                            },
                        },
                    },
                    "primary_key": {"type": "array", "items": {"type": "string"}},
                    "foreign_keys": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["column", "references"],
                            "properties": {
                                "column": {"type": "string"},
                                "references": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }
    },
    "required": ["datasets"],
}


def is_valid_input(data: dict) -> bool:
    return isinstance(data, dict) and "datasets" in data and isinstance(data["datasets"], list)


def load_input(raw: str):
    content = raw.strip()
    try:
        with open(content, "r") as f:
            parsed = json.load(f)
    except Exception:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return content, False
    if is_valid_input(parsed):
        return json.dumps(parsed), True
    return json.dumps(parsed), False


def build_df(model: PipelineOutput) -> pd.DataFrame:
    rows = []
    for fact in model.fact_tables:
        for col in fact.columns:
            rows.append({
                "Table": fact.name,
                "Role": "Fact",
                "Column": col.name,
                "Data Type": col.data_type,
                "Dim Type": "—",
            })
    for dim in model.dimension_tables:
        for col in dim.columns:
            rows.append({
                "Table": dim.name,
                "Role": "Dimension",
                "Column": col.name,
                "Data Type": col.data_type,
                "Dim Type": dim.dimension_type.value if dim.dimension_type else "—",
            })
    return pd.DataFrame(rows)


def run_schema_crew(content: str) -> str:
    crew = Crew(agents=[schema_analyst], tasks=[schema_analysis],
                process=Process.sequential, verbose=False)
    result = crew.kickoff(inputs={"raw_input": content})
    return result.raw


def run_modelling_crew(entity_map: str) -> object:
    crew = Crew(agents=[dimensional_modeller], tasks=[dimensional_modelling], verbose=False)
    result = crew.kickoff(inputs={"raw_input": "", "entity_map": entity_map})
    return result


def run_refinement_crew(model: PipelineOutput, changes: str) -> object:
    crew = Crew(agents=[dimensional_modeller], tasks=[dimensional_modelling],
                process=Process.sequential, verbose=False)
    result = crew.kickoff(inputs={
        "raw_input": (
            f"Here is the current dimensional model:\n{model.model_dump_json(indent=2)}\n\n"
            f"The user wants the following changes:\n{changes}\n\nReturn an updated PipelineOutput JSON."
        ),
        "entity_map": ""
    })
    return result


def run_sql_crew(business_question: str) -> str:
    crew = Crew(agents=[sql_writer], tasks=[sql_writing],
                process=Process.sequential, verbose=False)
    result = crew.kickoff(inputs={"business_question": business_question})
    return result.raw


# ─────────────────────────────────────────────
# Star Schema SVG renderer
# ─────────────────────────────────────────────

def build_star_schema_svg(model: PipelineOutput) -> str:
    import math

    # ── Card dimensions ──
    CARD_W      = 190
    ROW_H       = 22
    HEADER_H    = 32
    PAD         = 16          # padding inside card
    GAP_X       = 80          # horizontal gap between fact and dims
    GAP_Y       = 20          # vertical gap between dim cards

    # ── Collect fact columns ──
    facts = model.fact_tables
    dims  = model.dimension_tables

    def card_height(n_cols: int) -> int:
        return HEADER_H + n_cols * ROW_H + PAD

    # ── Layout: fact(s) centred left, dims stacked right ──
    n_dims = len(dims)

    # Compute total height needed for dims column
    dim_heights = [card_height(len(d.columns)) for d in dims]
    total_dim_h = sum(dim_heights) + GAP_Y * (n_dims - 1) if n_dims else 0

    # Compute max fact height
    fact_heights = [card_height(len(f.columns)) for f in facts]
    total_fact_h = sum(fact_heights) + GAP_Y * (len(facts) - 1) if facts else 0

    canvas_h = max(total_dim_h, total_fact_h) + 80
    canvas_w = CARD_W * 2 + GAP_X + 120   # left margin + fact + gap + dim + right margin

    FACT_X   = 40
    DIM_X    = FACT_X + CARD_W + GAP_X
    MARGIN_Y = (canvas_h - max(total_dim_h, total_fact_h)) // 2

    # Fact card positions
    fact_positions = []
    fy = MARGIN_Y + (max(total_dim_h, total_fact_h) - total_fact_h) // 2
    for f in facts:
        h = card_height(len(f.columns))
        fact_positions.append((FACT_X, fy, f))
        fy += h + GAP_Y

    # Dim card positions
    dim_positions = []
    dy = MARGIN_Y + (max(total_dim_h, total_fact_h) - total_dim_h) // 2
    for d in dims:
        h = card_height(len(d.columns))
        dim_positions.append((DIM_X, dy, d))
        dy += h + GAP_Y

    # ── SVG parts ──
    lines_svg   = []
    cards_svg   = []

    def make_card(x, y, name, columns, is_fact):
        h        = card_height(len(columns))
        hdr_fill = "#eff6ff" if is_fact else "#f5f3ff"
        hdr_str  = "#2563eb" if is_fact else "#7c3aed"
        brd_col  = "#2563eb" if is_fact else "#7c3aed"
        txt_col  = "#1d4ed8" if is_fact else "#6d28d9"
        label    = "FACT" if is_fact else "DIM"
        parts    = []

        # Card shadow
        parts.append(
            f'<rect x="{x+3}" y="{y+3}" width="{CARD_W}" height="{h}" rx="6" '
            f'fill="rgba(0,0,0,0.07)"/>'
        )
        # Card body
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{h}" rx="6" '
            f'fill="#ffffff" stroke="{brd_col}" stroke-width="1.5"/>'
        )
        # Header band
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{HEADER_H}" rx="6" '
            f'fill="{hdr_fill}" stroke="{brd_col}" stroke-width="1.5"/>'
        )
        # Clip bottom corners of header
        parts.append(
            f'<rect x="{x}" y="{y + HEADER_H - 6}" width="{CARD_W}" height="6" '
            f'fill="{hdr_fill}"/>'
        )
        # Table name
        parts.append(
            f'<text x="{x + 10}" y="{y + 21}" font-family="DM Sans,sans-serif" '
            f'font-size="12" font-weight="600" fill="{txt_col}">{name}</text>'
        )
        # Role badge
        badge_x = x + CARD_W - 38
        parts.append(
            f'<rect x="{badge_x}" y="{y + 8}" width="30" height="14" rx="3" '
            f'fill="{hdr_str}" fill-opacity="0.18" stroke="{hdr_str}" stroke-width="0.8"/>'
        )
        parts.append(
            f'<text x="{badge_x + 15}" y="{y + 19}" text-anchor="middle" '
            f'font-family="Space Mono,monospace" font-size="8" fill="{hdr_str}">{label}</text>'
        )
        # Divider
        parts.append(
            f'<line x1="{x}" y1="{y + HEADER_H}" x2="{x + CARD_W}" y2="{y + HEADER_H}" '
            f'stroke="{brd_col}" stroke-width="0.8" stroke-opacity="0.4"/>'
        )
        # Column rows
        for i, col in enumerate(columns):
            row_y    = y + HEADER_H + i * ROW_H
            # Alternating row bg
            if i % 2 == 0:
                parts.append(
                    f'<rect x="{x+1}" y="{row_y}" width="{CARD_W-2}" height="{ROW_H}" '
                    f'fill="rgba(0,0,0,0.018)"/>'
                )
            # Key icon for first col (assume PK)
            icon = "🔑" if i == 0 else "·"
            if i == 0:
                parts.append(
                    f'<text x="{x + 8}" y="{row_y + 15}" font-size="9" fill="#d97706">{icon}</text>'
                )
            # Column name
            col_name = col.name[:22] + "…" if len(col.name) > 23 else col.name
            col_color = "#111827" if i > 0 else "#92400e"
            parts.append(
                f'<text x="{x + 20}" y="{row_y + 15}" font-family="DM Sans,sans-serif" '
                f'font-size="11" fill="{col_color}">{col_name}</text>'
            )
            # Data type (right aligned)
            dt = col.data_type[:10] if hasattr(col, "data_type") else ""
            parts.append(
                f'<text x="{x + CARD_W - 8}" y="{row_y + 15}" text-anchor="end" '
                f'font-family="Space Mono,monospace" font-size="9" fill="#9ca3af">{dt}</text>'
            )
            # Row divider
            if i < len(columns) - 1:
                parts.append(
                    f'<line x1="{x+8}" y1="{row_y + ROW_H}" x2="{x + CARD_W - 8}" '
                    f'y2="{row_y + ROW_H}" stroke="#e5e7eb" stroke-width="0.5"/>'
                )

        return "".join(parts)

    def connector(fx, fy, fh, dx, dy, dh):
        """Draw an elbow connector from the right edge of fact to left edge of dim."""
        # Fact right-mid → dim left-mid
        x1 = fx + CARD_W
        y1 = fy + fh // 2
        x2 = dx
        y2 = dy + dh // 2
        mx = (x1 + x2) // 2
        # Curved path
        path = f"M {x1} {y1} C {mx} {y1} {mx} {y2} {x2} {y2}"
        return (
            f'<path d="{path}" fill="none" stroke="#cbd5e1" stroke-width="1.5" '
            f'stroke-dasharray="5,3"/>'
            f'<circle cx="{x1}" cy="{y1}" r="3" fill="#2563eb" fill-opacity="0.7"/>'
            f'<circle cx="{x2}" cy="{y2}" r="3" fill="#7c3aed" fill-opacity="0.7"/>'
        )

    # Draw connectors (each fact → each dim)
    for (fx, fy, f) in fact_positions:
        fh = card_height(len(f.columns))
        for (dx, dy, d) in dim_positions:
            dh = card_height(len(d.columns))
            lines_svg.append(connector(fx, fy, fh, dx, dy, dh))

    # Draw cards
    for (fx, fy, f) in fact_positions:
        cards_svg.append(make_card(fx, fy, f.name, f.columns, is_fact=True))
    for (dx, dy, d) in dim_positions:
        cards_svg.append(make_card(dx, dy, d.name, d.columns, is_fact=False))

    svg = f"""<svg viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;height:auto;background:#f9fafb;border-radius:8px;display:block;">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <!-- Grid dots -->
  <pattern id="dots" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="0.8" fill="#e5e7eb"/>
  </pattern>
  <rect width="{canvas_w}" height="{canvas_h}" fill="url(#dots)"/>

  <!-- Connectors -->
  {"".join(lines_svg)}

  <!-- Cards -->
  {"".join(cards_svg)}

  <!-- Legend -->
  <rect x="10" y="{canvas_h - 28}" width="10" height="10" rx="2" fill="#eff6ff" stroke="#2563eb" stroke-width="1.2"/>
  <text x="24" y="{canvas_h - 19}" font-family="DM Sans,sans-serif" font-size="10" fill="#2563eb">Fact</text>
  <rect x="62" y="{canvas_h - 28}" width="10" height="10" rx="2" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.2"/>
  <text x="76" y="{canvas_h - 19}" font-family="DM Sans,sans-serif" font-size="10" fill="#7c3aed">Dimension</text>
</svg>"""
    return svg


# ─────────────────────────────────────────────
# Chat helpers
# ─────────────────────────────────────────────

def add_chat(role: str, text: str):
    st.session_state.chat_history.append({"role": role, "text": text})


def chat_bubble(role: str, text: str) -> str:
    cls = "msg-user" if role == "user" else ("msg-system" if role == "system" else "msg-agent")
    return f'<div class="{cls}">{text}</div>'


# ─────────────────────────────────────────────
# Process user message
# ─────────────────────────────────────────────

def handle_user_message(msg: str):
    add_chat("user", msg)
    stage = st.session_state.stage

    # ── IDLE: accept schema / file path ──
    if stage == "idle":
        add_chat("system", "Analysing input…")
        content, is_structured = load_input(msg)
        st.session_state.status_msg = "Running schema analysis…"

        if is_structured:
            st.session_state.entity_map = content
            add_chat("agent", "✓ Structured dataset detected — skipping schema analysis.")
        else:
            st.session_state.status_msg = "Schema analyst running…"
            entity_map = run_schema_crew(content)
            st.session_state.entity_map = entity_map
            add_chat("agent", "✓ Schema analysis complete. Building dimensional model…")

        st.session_state.stage = "modelling"
        st.session_state.status_msg = "Dimensional modelling in progress…"
        result = run_modelling_crew(st.session_state.entity_map)
        st.session_state.model = result.pydantic
        st.session_state.df_table = build_df(result.pydantic)
        st.session_state.stage = "review"
        st.session_state.status_msg = "Model ready — awaiting review"
        add_chat("agent",
                 "✓ Dimensional model built. Review the tables in the centre pane.<br>"
                 "Type <b>approve</b> to proceed to SQL, or describe changes you'd like.")

    # ── REVIEW: approve or refine ──
    elif stage == "review":
        if msg.strip().lower() in ("approve", "yes", "y", "looks good", "ok", "proceed"):
            st.session_state.stage = "sql_prompt"
            add_chat("agent", "Great! Type <b>generate sql</b> to produce DDL, or <b>skip</b> to finish.")
        else:
            add_chat("agent", "Applying your changes — refining the model…")
            st.session_state.status_msg = "Refining model…"
            result = run_refinement_crew(st.session_state.model, msg)
            st.session_state.model = result.pydantic
            st.session_state.df_table = build_df(result.pydantic)
            st.session_state.status_msg = "Model updated — awaiting review"
            add_chat("agent", "✓ Model updated. Review the centre pane. Type <b>approve</b> when ready.")

    # ── SQL PROMPT ──
    elif stage == "sql_prompt":
        if msg.strip().lower() in ("skip", "no", "n", "done"):
            st.session_state.stage = "done"
            st.session_state.status_msg = "Complete"
            add_chat("agent", "Done! No SQL generated.")
        else:
            business_q = msg if len(msg) > 10 else "Analyse the dimensional model and generate CREATE TABLE DDL."
            add_chat("agent", "Generating SQL DDL…")
            st.session_state.status_msg = "SQL writer running…"
            sql = run_sql_crew(business_q)
            st.session_state.sql_output = sql
            st.session_state.stage = "done"
            st.session_state.status_msg = "Complete"
            add_chat("agent", "✓ SQL generated. See the centre pane.")

    # ── DONE: allow further refinement ──
    elif stage == "done":
        add_chat("agent", "The model is finalised. Refresh the page to start over, or describe any last changes.")


# ─────────────────────────────────────────────
# Layout — 3 columns
# ─────────────────────────────────────────────

left, mid, right = st.columns([1.1, 2.6, 1.1], gap="small")

# ══════════════════════════════════════════════
# LEFT — Version / info pane
# ══════════════════════════════════════════════

with left:
    st.markdown('<div class="pane-label">System</div>', unsafe_allow_html=True)
    st.markdown('<div class="version-badge">v1.0.0</div>', unsafe_allow_html=True)

    status_map = {
        "idle":       ("idle", "Awaiting Input"),
        "schema":     ("run",  "Schema Analysis"),
        "modelling":  ("run",  "Dimensional Modelling"),
        "review":     ("done", "Awaiting Review"),
        "sql_prompt": ("done", "SQL Prompt"),
        "done":       ("done", "Complete"),
    }
    s_cls, s_label = status_map.get(st.session_state.stage, ("idle", "—"))
    st.markdown(
        f'<div class="status-pill {s_cls}"><span class="dot {s_cls}"></span>{s_label}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="version-block">', unsafe_allow_html=True)
    items = [
        ("Agent",   "CrewAI"),
        ("LLM",     "GPT-4o"),
        ("Schema",  "JSONSchema"),
        ("Output",  "PipelineOutput"),
        ("Stage",   st.session_state.stage),
    ]
    for label, val in items:
        st.markdown(
            f'<div class="version-item">{label}<span class="tag">{val}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Pipeline steps
    st.markdown('<div class="pane-label" style="margin-top:16px;">Pipeline</div>', unsafe_allow_html=True)
    stages_order = ["idle", "schema", "modelling", "review", "sql_prompt", "done"]
    stage_labels = {
        "idle":       "① Input",
        "schema":     "② Schema Analysis",
        "modelling":  "③ Dim Modelling",
        "review":     "④ Human Review",
        "sql_prompt": "⑤ SQL Generation",
        "done":       "⑥ Complete",
    }
    current_idx = stages_order.index(st.session_state.stage) if st.session_state.stage in stages_order else 0
    step_html = '<div class="version-block">'
    for i, s in enumerate(stages_order):
        if i < current_idx:
            color = "var(--success)"; icon = "✓"
        elif i == current_idx:
            color = "var(--accent)"; icon = "▶"
        else:
            color = "var(--border)"; icon = "○"
        step_html += (
            f'<div style="display:flex;align-items:center;gap:8px;padding:7px 0;'
            f'border-bottom:1px solid var(--border);font-size:12px;color:{color};">'
            f'<span style="font-family:Space Mono,monospace;font-size:10px;">{icon}</span>'
            f'{stage_labels[s]}</div>'
        )
    step_html += "</div>"
    st.markdown(step_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# MIDDLE — Outputs pane
# ══════════════════════════════════════════════

with mid:
    st.markdown('<div class="pane-label">Output Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="mid-scroll">', unsafe_allow_html=True)

    # ── 1. Classification Table ──
    if st.session_state.df_table is not None:
        df = st.session_state.df_table
        st.markdown('<div class="section-header">01 — Fact & Dimension Classification</div>', unsafe_allow_html=True)

        rows_html = ""
        for _, row in df.iterrows():
            badge = (f'<span class="badge-fact">FACT</span>' if row["Role"] == "Fact"
                     else f'<span class="badge-dim">DIM</span>')
            rows_html += (
                f"<tr><td>{badge}</td><td>{row['Table']}</td>"
                f"<td>{row['Column']}</td>"
                f"<td><span class='badge-type'>{row['Data Type']}</span></td>"
                f"<td>{row['Dim Type']}</td></tr>"
            )

        table_html = f"""
<div class="tbl-container">
<table class="dm-table">
  <thead><tr>
    <th>Role</th><th>Table</th><th>Column</th><th>Type</th><th>Dim Type</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>
</div>"""
        st.markdown(table_html, unsafe_allow_html=True)

    # ── 2. SQL DDL ──
    if st.session_state.sql_output:
        st.markdown('<div class="section-header">02 — SQL DDL</div>', unsafe_allow_html=True)
        sql_escaped = st.session_state.sql_output.replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f'<div class="sql-block">{sql_escaped}</div>', unsafe_allow_html=True)
        st.download_button(
            "⬇ Download SQL",
            data=st.session_state.sql_output,
            file_name="dimensional_model.sql",
            mime="text/plain",
        )

    # ── 3. Change history ──
    change_msgs = [m for m in st.session_state.chat_history
                   if m["role"] == "user" and st.session_state.stage in ("review", "done")]
    if change_msgs and len(change_msgs) > 1:
        st.markdown('<div class="section-header">03 — Change Requests</div>', unsafe_allow_html=True)
        for m in change_msgs:
            st.markdown(f'<div style="background:#f3f4f6;border:1px solid #dde2ec;color:#374151;'
                        f'border-radius:6px;padding:10px 14px;font-size:13px;margin-bottom:6px;">'
                        f'→ {m["text"]}</div>', unsafe_allow_html=True)

    # ── 4. Star Schema ──
    if st.session_state.model is not None:
        import streamlit.components.v1 as components
        st.markdown('<div class="section-header">04 — Star Schema Diagram</div>', unsafe_allow_html=True)
        svg = build_star_schema_svg(st.session_state.model)
        schema_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #f9fafb; font-family: 'DM Sans', sans-serif; overflow: hidden; }}
</style>
</head>
<body>{svg}</body>
</html>"""
        n_dims  = len(st.session_state.model.dimension_tables)
        n_facts = len(st.session_state.model.fact_tables)
        avg_dim_cols  = sum(len(d.columns) for d in st.session_state.model.dimension_tables) / max(n_dims, 1)
        avg_fact_cols = sum(len(f.columns) for f in st.session_state.model.fact_tables)      / max(n_facts, 1)
        est_h = max(
            int(n_dims  * (avg_dim_cols  * 22 + 32 + 16 + 20)),
            int(n_facts * (avg_fact_cols * 22 + 32 + 16 + 20)),
        ) + 120
        components.html(schema_html, height=max(est_h, 420), scrolling=False)

    # Empty state
    if st.session_state.model is None and st.session_state.df_table is None:
        st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            height:55vh;text-align:center;">
  <div style="font-size:56px;margin-bottom:16px;color:#2e3448;">◈</div>
  <div style="font-family:Space Mono,monospace;font-size:13px;letter-spacing:0.1em;
              color:#4a5578;">OUTPUTS APPEAR HERE</div>
  <div style="font-size:12px;color:#3a4468;margin-top:8px;">
    Paste a schema or file path in the chat →
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# RIGHT — Chat pane
# ══════════════════════════════════════════════

with right:
    st.markdown('<div class="pane-label">Agent Chat</div>', unsafe_allow_html=True)

    # Chat history display
    chat_html = '<div class="chat-wrap">'
    if not st.session_state.chat_history:
        chat_html += '<div class="msg-system">Send a schema or file path to begin</div>'
    for m in st.session_state.chat_history:
        chat_html += chat_bubble(m["role"], m["text"])
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    # ── Input ──
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Context-aware placeholder
    placeholder_map = {
        "idle":       "Paste schema, DDL, or file path…",
        "review":     "Type 'approve' or describe changes…",
        "sql_prompt": "Describe your business question, or 'skip'…",
        "done":       "Model complete. Refresh to restart.",
    }
    ph = placeholder_map.get(st.session_state.stage, "Type a message…")

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder=ph, label_visibility="collapsed")
        submitted = st.form_submit_button("Send →")

    if submitted and user_input.strip():
        handle_user_message(user_input.strip())
        st.rerun()