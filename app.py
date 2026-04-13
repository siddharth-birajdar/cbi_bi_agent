import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
from crewai import Crew, Process

from agent import schema_analyst, dimensional_modeller, sql_writer
from tasks import schema_analysis, dimensional_modelling, sql_writing
from datamodels import PipelineOutput

st.set_page_config(page_title="Conrad BI Modelling Agent", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {
    --bg:#f5f7fa; --border:#dde2ec; --accent:#2563eb; --accent2:#7c3aed;
    --success:#059669; --mono:'Space Mono',monospace; --sans:'DM Sans',sans-serif;
}
html,body,.stApp,.stApp>div,
[data-testid="stAppViewContainer"],[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],.main .block-container {
    background:#f5f7fa !important; color:#111827 !important;
}
[data-testid="block-container"] { padding:0 !important; max-width:100% !important; }
[data-testid="stVerticalBlock"] { background:transparent !important; }
[data-testid="stHorizontalBlock"] { background:#f5f7fa !important; gap:0 !important; }
[data-testid="column"] { background:#f5f7fa !important; }
section[data-testid="stSidebar"] { background:#ffffff !important; }
[data-testid="stForm"] { background:transparent !important; border:none !important; }
[data-testid="stMarkdownContainer"] { background:transparent !important; color:#111827 !important; }
[data-testid="stHorizontalBlock"]>div+div { border-left:1px solid #dde2ec; }
#MainMenu,footer,header,[data-testid="stToolbar"] { visibility:hidden !important; height:0 !important; }
*,*::before,*::after { box-sizing:border-box; }
body { font-family:'DM Sans',sans-serif !important; }

.top-header {
    display:flex; align-items:center; justify-content:space-between;
    background:#ffffff; border-bottom:1px solid #dde2ec;
    padding:0 28px; height:52px; position:sticky; top:0; z-index:100;
    box-shadow:0 1px 4px rgba(0,0,0,0.05);
}
.brand-block { display:flex; align-items:center; gap:10px; }
.brand-icon {
    width:28px; height:28px; background:linear-gradient(135deg,#2563eb,#7c3aed);
    border-radius:6px; display:flex; align-items:center; justify-content:center;
    font-size:14px; color:#fff; font-weight:700; font-family:'Space Mono',monospace;
}
.brand-name { font-family:'DM Sans',sans-serif; font-size:14px; font-weight:600; color:#111827; }
.brand-name span { color:#2563eb; }
.user-block { display:flex; align-items:center; gap:10px; }
.user-greeting { font-size:13px; color:#6b7280; font-family:'DM Sans',sans-serif; }
.user-greeting strong { color:#111827; }
.user-avatar {
    width:34px; height:34px; background:linear-gradient(135deg,#2563eb,#7c3aed);
    border-radius:50%; display:flex; align-items:center; justify-content:center;
    font-size:13px; font-weight:600; color:#fff; border:2px solid #e5e7eb;
    font-family:'DM Sans',sans-serif;
}

div[data-baseweb="input"],div[data-baseweb="base-input"],
[data-testid="stTextInput"]>div,[data-testid="stTextInput"]>div>div { background:#ffffff !important; }
[data-testid="stTextInput"] input {
    background:#ffffff !important; color:#111827 !important;
    border:1px solid #dde2ec !important; border-radius:8px !important;
    font-family:'DM Sans',sans-serif !important; font-size:13px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stTextInput"] input:focus {
    border-color:#2563eb !important; box-shadow:0 0 0 3px rgba(37,99,235,0.1) !important;
}
[data-testid="stTextInput"] input::placeholder { color:#9ca3af !important; }

.stButton>button, [data-testid="stFormSubmitButton"]>button {
    background:#2563eb !important; color:#ffffff !important; border:none !important;
    border-radius:8px !important; font-family:'Space Mono',monospace !important;
    font-size:12px !important; padding:10px 20px !important;
    box-shadow:0 1px 4px rgba(37,99,235,0.25) !important; width:100% !important; cursor:pointer !important;
}
.stButton>button:hover, [data-testid="stFormSubmitButton"]>button:hover { background:#1d4ed8 !important; }
.approve-btn .stButton>button { background:#059669 !important; }
.approve-btn .stButton>button:hover { background:#047857 !important; }
.refine-btn [data-testid="stFormSubmitButton"]>button {
    background:#ffffff !important; color:#374151 !important;
    border:1px solid #dde2ec !important; box-shadow:none !important;
}
.refine-btn [data-testid="stFormSubmitButton"]>button:hover { background:#f3f4f6 !important; }
.sql-btn .stButton>button { background:#7c3aed !important; }
.sql-btn .stButton>button:hover { background:#6d28d9 !important; }
.skip-btn .stButton>button {
    background:#f9fafb !important; color:#6b7280 !important;
    border:1px solid #e5e7eb !important; box-shadow:none !important; font-size:11px !important;
}
[data-testid="stDownloadButton"] button {
    background:#ffffff !important; color:#374151 !important;
    border:1px solid #dde2ec !important; border-radius:8px !important;
    font-family:'Space Mono',monospace !important; font-size:11px !important;
}

.pane-label {
    font-family:var(--mono); font-size:10px; letter-spacing:0.15em;
    text-transform:uppercase; color:#9ca3af; padding:14px 20px 10px;
    border-bottom:1px solid #dde2ec; background:#ffffff;
}
.version-badge {
    font-family:var(--mono); font-size:11px; color:#2563eb;
    background:#eff6ff; border:1px solid #bfdbfe; border-radius:4px;
    padding:3px 10px; display:inline-block; margin:14px 20px 6px;
}
.version-block { padding:0 20px 16px; }
.version-item {
    display:flex; justify-content:space-between; align-items:center;
    padding:8px 0; border-bottom:1px solid #eef1f6; font-size:13px; color:#374151;
}
.version-item span.tag {
    font-family:var(--mono); font-size:10px; background:#f3f4f6;
    border:1px solid #e5e7eb; border-radius:3px; padding:2px 8px; color:#111827;
}
.status-pill {
    display:inline-flex; align-items:center; gap:6px; font-family:var(--mono);
    font-size:11px; padding:4px 12px; border-radius:999px; margin:8px 20px;
}
.status-pill.idle { background:#f3f4f6; color:#6b7280; border:1px solid #e5e7eb; }
.status-pill.run  { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; }
.status-pill.done { background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; flex-shrink:0; }
.dot.idle { background:#d1d5db; }
.dot.run  { background:#2563eb; animation:blink 1s infinite; }
.dot.done { background:#059669; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.25} }

[data-testid="stExpander"] {
    background:#ffffff !important; border:1px solid #dde2ec !important;
    border-radius:10px !important; margin-bottom:12px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.04) !important; overflow:hidden !important;
}
[data-testid="stExpander"] summary {
    font-family:'Space Mono',monospace !important; font-size:11px !important;
    letter-spacing:0.06em !important; color:#111827 !important;
    padding:12px 16px !important; background:#f9fafb !important;
}
[data-testid="stExpander"] summary:hover { background:#f3f4f6 !important; }
[data-testid="stExpander"] > div > div { padding:0 !important; }

.dm-table { width:100%; border-collapse:collapse; font-size:12.5px; font-family:'DM Sans',sans-serif; }
.dm-table th {
    font-family:'Space Mono',monospace; font-size:9px; text-transform:uppercase;
    letter-spacing:0.1em; color:#9ca3af; padding:9px 14px;
    background:#f9fafb; border-bottom:1px solid #e5e7eb; text-align:left; font-weight:400;
}
.dm-table td { padding:8px 14px; border-bottom:1px solid #f3f4f6; color:#111827; vertical-align:middle; }
.dm-table tr:last-child td { border-bottom:none; }
.dm-table tr:hover td { background:#fafbfd; }
.badge-fact { background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;border-radius:4px;font-size:9px;font-family:'Space Mono',monospace;padding:2px 7px;white-space:nowrap; }
.badge-dim  { background:#f5f3ff;color:#7c3aed;border:1px solid #ddd6fe;border-radius:4px;font-size:9px;font-family:'Space Mono',monospace;padding:2px 7px;white-space:nowrap; }
.badge-type { background:#f3f4f6;color:#6b7280;border:1px solid #e5e7eb;border-radius:3px;font-size:10px;font-family:'Space Mono',monospace;padding:2px 6px; }

.sql-block {
    background:#1e2333; border-left:4px solid #059669; padding:16px 18px;
    font-family:'Space Mono',monospace; font-size:12px; line-height:1.8;
    color:#6ee7b7; white-space:pre-wrap; overflow-x:auto; margin:0;
}
.json-block {
    background:#1e2333; border-left:4px solid #2563eb; padding:16px 18px;
    font-family:'Space Mono',monospace; font-size:12px; line-height:1.8;
    color:#93c5fd; white-space:pre-wrap; overflow-x:auto; margin:0;
}

.chat-wrap { padding:12px 14px; display:flex; flex-direction:column; gap:10px; }
.msg-user {
    background:#2563eb; border-radius:14px 14px 2px 14px; padding:10px 14px;
    font-size:13px; color:#ffffff; align-self:flex-end; max-width:88%; line-height:1.55;
}
.msg-agent {
    background:#ffffff; border:1px solid #dde2ec; border-radius:2px 14px 14px 14px;
    padding:10px 14px; font-size:13px; color:#111827; align-self:flex-start;
    max-width:88%; line-height:1.55; box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.msg-system { font-family:'Space Mono',monospace; font-size:10px; color:#9ca3af; text-align:center; padding:4px 0; }
.mid-scroll { max-height:calc(100vh - 104px); overflow-y:auto; padding:16px 16px 48px; background:#f5f7fa; }
.chat-divider { border:none; border-top:1px solid #dde2ec; margin:12px 0; }
[data-testid="InputInstructions"] { display:none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-header">
  <div class="brand-block">
    <div class="brand-icon">C</div>
    <div class="brand-name"><span>Conrad</span> BI Modelling Agent</div>
  </div>
  <div class="user-block">
    <div class="user-greeting">Hello, <strong>John</strong></div>
    <div class="user-avatar">JD</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Session State ──
def ss(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

ss("chat_history", [])
ss("stage", "idle")
ss("entity_map", None)
ss("model", None)
ss("sql_output", None)
ss("df_table", None)
ss("status_msg", "Awaiting input")
ss("pending_schema_content", None)

# ── Helpers ──
def is_valid_input(data):
    return isinstance(data, dict) and "datasets" in data and isinstance(data["datasets"], list)

def load_input(raw):
    content = raw.strip()
    try:
        with open(content, "r") as f:
            parsed = json.load(f)
    except Exception:
        try:
            parsed = json.loads(content)
        except Exception:
            return content, False
    return (json.dumps(parsed), True) if is_valid_input(parsed) else (json.dumps(parsed), False)

def build_df(model):
    rows = []
    for fact in model.fact_tables:
        for col in fact.columns:
            rows.append({
                "Table": fact.name, "Role": "Fact", "Column": col.name,
                "Data Type": col.data_type, "Dim Type": "—"
            })
    for dim in model.dimension_tables:
        for col in dim.columns:
            rows.append({
                "Table": dim.name, "Role": "Dimension", "Column": col.name,
                "Data Type": col.data_type,
                "Dim Type": dim.dimension_type.value if dim.dimension_type else "—"
            })
    return pd.DataFrame(rows)

def run_schema_crew(c):
    return Crew(
        agents=[schema_analyst], tasks=[schema_analysis],
        process=Process.sequential, verbose=False
    ).kickoff(inputs={"raw_input": c}).raw

def run_modelling_crew(em):
    return Crew(
        agents=[dimensional_modeller], tasks=[dimensional_modelling], verbose=False
    ).kickoff(inputs={"raw_input": "", "entity_map": em})

def run_refinement_crew(model, changes):
    return Crew(
        agents=[dimensional_modeller], tasks=[dimensional_modelling],
        process=Process.sequential, verbose=False
    ).kickoff(inputs={
        "raw_input": (
            f"Here is the current dimensional model:\n{model.model_dump_json(indent=2)}\n\n"
            f"The user wants the following changes:\n{changes}\n\nReturn an updated PipelineOutput JSON."
        ),
        "entity_map": ""
    })

def run_sql_crew(bq):
    return Crew(
        agents=[sql_writer], tasks=[sql_writing],
        process=Process.sequential, verbose=False
    ).kickoff(inputs={"business_question": bq}).raw

# ── SVG ──
def build_star_schema_svg(model):
    CARD_W, ROW_H, HEADER_H, PAD, GAP_X, GAP_Y = 190, 22, 32, 16, 80, 20
    facts, dims = model.fact_tables, model.dimension_tables

    def ch(n):
        return HEADER_H + n * ROW_H + PAD

    n_dims = len(dims)
    tdh = sum(ch(len(d.columns)) for d in dims) + GAP_Y * (n_dims - 1) if n_dims else 0
    tfh = sum(ch(len(f.columns)) for f in facts) + GAP_Y * (len(facts) - 1) if facts else 0
    canvas_h = max(tdh, tfh) + 80
    canvas_w = CARD_W * 2 + GAP_X + 120
    FX, DX = 40, 40 + CARD_W + GAP_X
    MY = (canvas_h - max(tdh, tfh)) // 2

    fp, dp = [], []
    fy = MY + (max(tdh, tfh) - tfh) // 2
    for f in facts:
        fp.append((FX, fy, f))
        fy += ch(len(f.columns)) + GAP_Y
    dy = MY + (max(tdh, tfh) - tdh) // 2
    for d in dims:
        dp.append((DX, dy, d))
        dy += ch(len(d.columns)) + GAP_Y

    ls, cs = [], []

    def card(x, y, name, cols, isf):
        h = ch(len(cols))
        hf = "#eff6ff" if isf else "#f5f3ff"
        hs = "#2563eb" if isf else "#7c3aed"
        bc = "#2563eb" if isf else "#7c3aed"
        tc = "#1d4ed8" if isf else "#6d28d9"
        lb = "FACT" if isf else "DIM"
        p = [
            f'<rect x="{x+3}" y="{y+3}" width="{CARD_W}" height="{h}" rx="6" fill="rgba(0,0,0,0.07)"/>',
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{h}" rx="6" fill="#fff" stroke="{bc}" stroke-width="1.5"/>',
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{HEADER_H}" rx="6" fill="{hf}" stroke="{bc}" stroke-width="1.5"/>',
            f'<rect x="{x}" y="{y+HEADER_H-6}" width="{CARD_W}" height="6" fill="{hf}"/>',
            f'<text x="{x+10}" y="{y+21}" font-family="DM Sans,sans-serif" font-size="12" font-weight="600" fill="{tc}">{name}</text>',
        ]
        bx = x + CARD_W - 38
        p += [
            f'<rect x="{bx}" y="{y+8}" width="30" height="14" rx="3" fill="{hs}" fill-opacity="0.18" stroke="{hs}" stroke-width="0.8"/>',
            f'<text x="{bx+15}" y="{y+19}" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="{hs}">{lb}</text>',
            f'<line x1="{x}" y1="{y+HEADER_H}" x2="{x+CARD_W}" y2="{y+HEADER_H}" stroke="{bc}" stroke-width="0.8" stroke-opacity="0.4"/>',
        ]
        for i, col in enumerate(cols):
            ry = y + HEADER_H + i * ROW_H
            if i % 2 == 0:
                p.append(f'<rect x="{x+1}" y="{ry}" width="{CARD_W-2}" height="{ROW_H}" fill="rgba(0,0,0,0.018)"/>')
            if i == 0:
                p.append(f'<text x="{x+8}" y="{ry+15}" font-size="9" fill="#d97706">🔑</text>')
            cn = col.name[:22] + "…" if len(col.name) > 23 else col.name
            p.append(f'<text x="{x+20}" y="{ry+15}" font-family="DM Sans,sans-serif" font-size="11" fill="{"#92400e" if i==0 else "#111827"}">{cn}</text>')
            dt = col.data_type[:10] if hasattr(col, "data_type") else ""
            p.append(f'<text x="{x+CARD_W-8}" y="{ry+15}" text-anchor="end" font-family="Space Mono,monospace" font-size="9" fill="#9ca3af">{dt}</text>')
            if i < len(cols) - 1:
                p.append(f'<line x1="{x+8}" y1="{ry+ROW_H}" x2="{x+CARD_W-8}" y2="{ry+ROW_H}" stroke="#e5e7eb" stroke-width="0.5"/>')
        return "".join(p)

    def conn(fx, fy, fh, dx, dy, dh):
        x1, y1, x2, y2 = fx + CARD_W, fy + fh // 2, dx, dy + dh // 2
        mx = (x1 + x2) // 2
        return (
            f'<path d="M {x1} {y1} C {mx} {y1} {mx} {y2} {x2} {y2}" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,3"/>'
            f'<circle cx="{x1}" cy="{y1}" r="3" fill="#2563eb" fill-opacity="0.7"/>'
            f'<circle cx="{x2}" cy="{y2}" r="3" fill="#7c3aed" fill-opacity="0.7"/>'
        )

    for (fx, fy, f) in fp:
        fh = ch(len(f.columns))
        for (dx, dy, d) in dp:
            ls.append(conn(fx, fy, fh, dx, dy, ch(len(d.columns))))
    for (fx, fy, f) in fp:
        cs.append(card(fx, fy, f.name, f.columns, True))
    for (dx, dy, d) in dp:
        cs.append(card(dx, dy, d.name, d.columns, False))

    return f"""<svg viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;background:#f9fafb;border-radius:8px;display:block;">
  <pattern id="dots" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.8" fill="#e5e7eb"/></pattern>
  <rect width="{canvas_w}" height="{canvas_h}" fill="url(#dots)"/>
  {"".join(ls)}{"".join(cs)}
  <rect x="10" y="{canvas_h-28}" width="10" height="10" rx="2" fill="#eff6ff" stroke="#2563eb" stroke-width="1.2"/>
  <text x="24" y="{canvas_h-19}" font-family="DM Sans,sans-serif" font-size="10" fill="#2563eb">Fact</text>
  <rect x="62" y="{canvas_h-28}" width="10" height="10" rx="2" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.2"/>
  <text x="76" y="{canvas_h-19}" font-family="DM Sans,sans-serif" font-size="10" fill="#7c3aed">Dimension</text>
</svg>"""

# ── Chat helpers ──
def add_chat(role, text):
    st.session_state.chat_history.append({"role": role, "text": text})

def chat_bubble(role, text):
    cls = "msg-user" if role == "user" else ("msg-system" if role == "system" else "msg-agent")
    if role == "user" and len(text) > 300:
        short = text[:300].replace("<", "&lt;").replace(">", "&gt;")
        full = text.replace("<", "&lt;").replace(">", "&gt;").replace("'", "\\'")
        display = (
            f'{short}… <span style="cursor:pointer;font-size:11px;opacity:0.7;text-decoration:underline;" '
            f'onclick="this.parentElement.innerHTML=\'{full}\'">show more</span>'
        )
    else:
        display = text
    return f'<div class="{cls}">{display}</div>'

# ── Handlers ──
def handle_schema_input(msg):
    add_chat("user", msg)
    add_chat("system", "Parsing input…")
    content, is_structured = load_input(msg)
    if is_structured:
        st.session_state.pending_schema_content = content
        add_chat("agent", "✓ Structured dataset detected.<br>What is your <b>business question</b>? (e.g. <i>'Analyse monthly sales revenue by product and region'</i>)")
    else:
        entity_map = run_schema_crew(content)
        st.session_state.pending_schema_content = entity_map
        add_chat("agent", "✓ Schema analysis complete.<br>What is your <b>business question</b>?")
    st.session_state.stage = "biz_question"

def handle_biz_question(msg):
    add_chat("user", msg)
    st.session_state.sql_business_question = msg
    st.session_state.entity_map = st.session_state.pending_schema_content
    st.session_state.pending_schema_content = None
    add_chat("agent", f"Got it — building a dimensional model optimised for: <i>{msg}</i>")
    st.session_state.stage = "modelling"
    result = run_modelling_crew(st.session_state.entity_map)
    st.session_state.model = result.pydantic
    st.session_state.df_table = build_df(result.pydantic)
    st.session_state.stage = "review"
    add_chat("agent", "✓ Dimensional model built. Review the tables in the centre pane.<br>Use <b>Approve</b> to proceed, or type changes below.")

def handle_refinement(msg):
    add_chat("user", msg)
    add_chat("agent", "Applying your changes…")
    result = run_refinement_crew(st.session_state.model, msg)
    st.session_state.model = result.pydantic
    st.session_state.df_table = build_df(result.pydantic)
    add_chat("agent", "✓ Model updated. Click <b>Approve</b> when ready.")

def handle_approve():
    add_chat("system", "Model approved.")
    add_chat("agent", "Model approved! Click <b>Generate SQL</b> or <b>Skip</b>.")
    st.session_state.stage = "sql_prompt"

def handle_generate_sql():
    bq = getattr(st.session_state, "sql_business_question", None) or "Generate CREATE TABLE DDL."
    add_chat("agent", "Generating SQL DDL…")
    st.session_state.sql_output = run_sql_crew(bq)
    st.session_state.stage = "done"
    add_chat("agent", "✓ SQL generated. See the centre pane.")

def handle_skip_sql():
    add_chat("agent", "Done! No SQL generated. Refresh to restart.")
    st.session_state.stage = "done"

# ══════════════════════════════════════════════
# Layout
# ══════════════════════════════════════════════
left, mid, right = st.columns([1.1, 2.6, 1.1], gap="small")

# ══ LEFT ══
with left:
    st.markdown('<div class="pane-label">System</div>', unsafe_allow_html=True)
    st.markdown('<div class="version-badge">v1.1.0</div>', unsafe_allow_html=True)
    status_map = {
        "idle":         ("idle", "Awaiting Input"),
        "biz_question": ("run",  "Awaiting Biz Question"),
        "modelling":    ("run",  "Dimensional Modelling"),
        "review":       ("done", "Awaiting Review"),
        "sql_prompt":   ("done", "SQL Decision"),
        "done":         ("done", "Complete"),
    }
    s_cls, s_label = status_map.get(st.session_state.stage, ("idle", "—"))
    st.markdown(f'<div class="status-pill {s_cls}"><span class="dot {s_cls}"></span>{s_label}</div>', unsafe_allow_html=True)
    st.markdown('<div class="version-block">', unsafe_allow_html=True)
    for lbl, val in [("Agent","CrewAI"),("LLM","GPT-4o"),("Schema","JSONSchema"),("Output","PipelineOutput"),("Stage", st.session_state.stage)]:
        st.markdown(f'<div class="version-item">{lbl}<span class="tag">{val}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="pane-label" style="margin-top:16px;">Pipeline</div>', unsafe_allow_html=True)
    stages_order = ["idle", "biz_question", "modelling", "review", "sql_prompt", "done"]
    stage_labels = {
        "idle":         "① Input",
        "biz_question": "② Business Question",
        "modelling":    "③ Dim Modelling",
        "review":       "④ Human Review",
        "sql_prompt":   "⑤ SQL Generation",
        "done":         "⑥ Complete",
    }
    ci = stages_order.index(st.session_state.stage) if st.session_state.stage in stages_order else 0
    sh = '<div class="version-block">'
    for i, s in enumerate(stages_order):
        color = "var(--success)" if i < ci else ("var(--accent)" if i == ci else "var(--border)")
        icon  = "✓" if i < ci else ("▶" if i == ci else "○")
        sh += (
            f'<div style="display:flex;align-items:center;gap:8px;padding:7px 0;'
            f'border-bottom:1px solid var(--border);font-size:12px;color:{color};">'
            f'<span style="font-family:Space Mono,monospace;font-size:10px;">{icon}</span>{stage_labels[s]}</div>'
        )
    sh += "</div>"
    st.markdown(sh, unsafe_allow_html=True)

# ══ MIDDLE ══
with mid:
    st.markdown('<div class="pane-label">Output Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="mid-scroll">', unsafe_allow_html=True)

    # ── 01 Classification Table ──
    if st.session_state.df_table is not None:
        df = st.session_state.df_table
        facts_u = len(df[df["Role"] == "Fact"]["Table"].unique())
        dims_u  = len(df[df["Role"] == "Dimension"]["Table"].unique())

        with st.expander(f"📋  01 — Fact & Dimension Classification   ·   {facts_u} fact · {dims_u} dim · {len(df)} cols", expanded=True):
            rows_html = ""
            for _, row in df.iterrows():
                badge = '<span class="badge-fact">FACT</span>' if row["Role"] == "Fact" else '<span class="badge-dim">DIM</span>'
                rows_html += (
                    f'<tr><td>{badge}</td>'
                    f'<td style="color:#374151;font-weight:500;">{row["Table"]}</td>'
                    f'<td style="font-family:monospace;font-size:11px;">{row["Column"]}</td>'
                    f'<td><span class="badge-type">{row["Data Type"]}</span></td>'
                    f'<td style="color:#9ca3af;font-size:11px;">{row["Dim Type"]}</td></tr>'
                )
            st.markdown(f"""<table class="dm-table">
<thead><tr><th>Role</th><th>Table</th><th>Column</th><th>Type</th><th>Dim Type</th></tr></thead>
<tbody>{rows_html}</tbody></table>""", unsafe_allow_html=True)
            st.download_button(
                "⬇ Download CSV", data=df.to_csv(index=False),
                file_name="classification.csv", mime="text/csv", key="dl_csv"
            )

    # ── 01b JSON Summary ──
    if st.session_state.model is not None:
        model_dict = {}
        for fact in st.session_state.model.fact_tables:
            model_dict[fact.name] = [col.name for col in fact.columns]
        for dim in st.session_state.model.dimension_tables:
            dim_type = dim.dimension_type.value if dim.dimension_type else "unknown"
            key = f"{dim.name}  ({dim_type})"
            model_dict[key] = [col.name for col in dim.columns]

        json_lines = ["{"]
        items = list(model_dict.items())
        for i, (table, cols) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            json_lines.append(f'  "{table}": {json.dumps(cols)}{comma}')
        json_lines.append("}")
        json_str = "\n".join(json_lines)

        with st.expander(f"🗂️  01b — Model JSON Summary   ·   {len(model_dict)} tables", expanded=False):
            st.markdown(f'<div class="json-block">{json_str}</div>', unsafe_allow_html=True)
            st.download_button(
                "⬇ Download JSON", data=json_str,
                file_name="dimensional_model.json", mime="application/json", key="dl_json"
            )

    # ── 02 SQL DDL ──
    if st.session_state.sql_output:
        sql_lines = st.session_state.sql_output.strip().splitlines()
        with st.expander(f"💾  02 — SQL DDL   ·   {len(sql_lines)} lines", expanded=False):
            sql_escaped = st.session_state.sql_output.replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(f'<div class="sql-block">{sql_escaped}</div>', unsafe_allow_html=True)
            st.download_button(
                "⬇ Download SQL", data=st.session_state.sql_output,
                file_name="dimensional_model.sql", mime="text/plain", key="dl_sql"
            )

    # ── 03 Change Requests ──
    change_msgs = [
        m for m in st.session_state.chat_history
        if m["role"] == "user" and st.session_state.stage in ("review", "sql_prompt", "done")
    ]
    if change_msgs and len(change_msgs) > 1:
        actual = change_msgs[1:]
        with st.expander(f"✏️  03 — Change Requests   ·   {len(actual)} total", expanded=False):
            for m in actual:
                st.markdown(
                    f'<div style="padding:9px 4px;border-bottom:1px solid #f3f4f6;font-size:13px;color:#374151;">'
                    f'<span style="color:#9ca3af;font-family:Space Mono,monospace;font-size:10px;">→ </span>{m["text"]}</div>',
                    unsafe_allow_html=True
                )
            change_text = "\n".join(f"→ {m['text']}" for m in actual)
            st.download_button(
                "⬇ Download Change Log", data=change_text,
                file_name="change_log.txt", mime="text/plain", key="dl_changes"
            )

    # ── 04 Star Schema ──
    if st.session_state.model is not None:
        n_facts = len(st.session_state.model.fact_tables)
        n_dims  = len(st.session_state.model.dimension_tables)
        with st.expander(f"🔷  04 — Star Schema Diagram   ·   {n_facts} fact · {n_dims} dim", expanded=True):
            svg = build_star_schema_svg(st.session_state.model)
            schema_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{background:#f9fafb;overflow:hidden;}}</style>
</head><body>{svg}</body></html>"""
            adc = sum(len(d.columns) for d in st.session_state.model.dimension_tables) / max(n_dims, 1)
            afc = sum(len(f.columns) for f in st.session_state.model.fact_tables) / max(n_facts, 1)
            est_h = max(int(n_dims * (adc * 22 + 32 + 16 + 20)), int(n_facts * (afc * 22 + 32 + 16 + 20))) + 120
            components.html(schema_html, height=max(est_h, 420), scrolling=False)

    # Empty state
    if st.session_state.model is None and st.session_state.df_table is None:
        st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:55vh;text-align:center;">
  <div style="font-size:56px;margin-bottom:16px;color:#2e3448;">◈</div>
  <div style="font-family:Space Mono,monospace;font-size:13px;letter-spacing:0.1em;color:#4a5578;">OUTPUTS APPEAR HERE</div>
  <div style="font-size:12px;color:#3a4468;margin-top:8px;">Paste a schema or file path in the chat →</div>
</div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ══ RIGHT ══
with right:
    st.markdown('<div class="pane-label">Agent Chat</div>', unsafe_allow_html=True)
    chat_html = '<div class="chat-wrap">'
    if not st.session_state.chat_history:
        chat_html += '<div class="msg-system">Send a schema or file path to begin</div>'
    for m in st.session_state.chat_history:
        chat_html += chat_bubble(m["role"], m["text"])
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)
    st.markdown("<hr class='chat-divider'>", unsafe_allow_html=True)

    stage = st.session_state.stage

    if stage == "idle":
        with st.form("schema_form", clear_on_submit=True):
            user_input = st.text_input("", placeholder="Paste schema, DDL, or file path…", label_visibility="collapsed")
            submitted  = st.form_submit_button("Send →")
        if submitted and user_input.strip():
            handle_schema_input(user_input.strip())
            st.rerun()

    elif stage == "biz_question":
        with st.form("biz_form", clear_on_submit=True):
            biz_input = st.text_input("", placeholder="e.g. 'Monthly sales by product and region'…", label_visibility="collapsed")
            submitted = st.form_submit_button("Confirm Question →")
        if submitted and biz_input.strip():
            handle_biz_question(biz_input.strip())
            st.rerun()

    elif stage == "modelling":
        st.markdown('<div style="text-align:center;padding:20px 0;font-family:Space Mono,monospace;font-size:11px;color:#6b7280;">⏳ Building dimensional model…</div>', unsafe_allow_html=True)

    elif stage == "review":
        st.markdown('<div class="approve-btn">', unsafe_allow_html=True)
        if st.button("✓ Approve Model", key="approve_btn"):
            handle_approve()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:Space Mono,monospace;font-size:10px;color:#9ca3af;text-align:center;padding:8px 0;">— or request changes —</div>', unsafe_allow_html=True)
        with st.form("refine_form", clear_on_submit=True):
            refine_input = st.text_input("", placeholder="Describe changes to the model…", label_visibility="collapsed")
            st.markdown('<div class="refine-btn">', unsafe_allow_html=True)
            refine_submitted = st.form_submit_button("Request Changes →")
            st.markdown("</div>", unsafe_allow_html=True)
        if refine_submitted and refine_input.strip():
            handle_refinement(refine_input.strip())
            st.rerun()

    elif stage == "sql_prompt":
        bq = getattr(st.session_state, "sql_business_question", "")
        st.markdown(
            f'<div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:8px;padding:10px 14px;'
            f'font-size:12px;color:#6d28d9;margin-bottom:12px;">'
            f'<span style="font-family:Space Mono,monospace;font-size:9px;letter-spacing:0.1em;'
            f'display:block;margin-bottom:4px;color:#9ca3af;">BUSINESS QUESTION</span>{bq}</div>',
            unsafe_allow_html=True
        )
        st.markdown('<div class="sql-btn">', unsafe_allow_html=True)
        if st.button("⚡ Generate SQL DDL", key="gen_sql_btn"):
            handle_generate_sql()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="skip-btn">', unsafe_allow_html=True)
        if st.button("Skip →", key="skip_sql_btn"):
            handle_skip_sql()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif stage == "done":
        st.markdown('<div style="text-align:center;padding:16px 0;font-family:Space Mono,monospace;font-size:11px;color:#059669;">✓ Pipeline complete. Refresh to restart.</div>', unsafe_allow_html=True)
