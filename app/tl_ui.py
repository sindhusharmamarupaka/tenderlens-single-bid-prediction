"""TenderLens look: colours, fonts, cards, badges and charts shared by every page."""
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import tl_core as T

NAVY = "#02151f"
AMBER = "#e0a000"
TEAL = "#0aa6a6"
DEEP = "#05556b"
GOLD = "#ffdd7b"
GREY = "#b8c7cc"
CREAM = "#fdf6e3"
INK2 = "#4a5f66"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select { font-family: 'Inter', system-ui, sans-serif; }
.stApp { background: #fdf6e3; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }
h1, h2, h3, .tl-num { font-family: 'Space Grotesk', 'Inter', sans-serif !important; color: #02151f; letter-spacing: -0.3px; }
[data-testid="stSidebar"] { background: #02151f; }
[data-testid="stSidebar"] * { color: #e8eef0; }
[data-testid="stSidebarNav"] a, [data-testid="stSidebarNavLink"] { border-radius: 10px; }
[data-testid="stSidebarNavLink"][aria-current="page"], [data-testid="stSidebarNav"] a[aria-current="page"] { background: #ffdd7b !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] *, [data-testid="stSidebarNav"] a[aria-current="page"] * { color: #02151f !important; font-weight: 700; }
[data-testid="stSidebarNavLink"]:hover { background: #0b2a36; }
[data-testid="stSidebarHeader"] img, [data-testid="stLogo"] { height: 40px !important; max-width: 220px; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: #9fb4ba; }
[data-testid="stSidebar"] .stDownloadButton button { background: transparent; border: 1px solid #1d3a45; }
.tl-kicker { font-size: 12px; letter-spacing: 1.6px; color: #05556b; font-weight: 700; text-transform: uppercase; margin-bottom: 2px; }
.tl-title { font-family: 'Space Grotesk', sans-serif; font-size: 34px; line-height: 1.15; font-weight: 700; color: #02151f; margin: 0 0 4px 0; letter-spacing: -0.5px; }
.tl-sub { font-size: 15px; color: #4a5f66; margin-bottom: 10px; }
.tl-card { background: #ffffff; border-radius: 18px; padding: 18px 20px; box-shadow: 0 4px 18px rgba(2,21,31,0.07); height: 100%; }
.tl-kpi { background: #ffffff; border-radius: 16px; padding: 16px 18px; box-shadow: 0 4px 18px rgba(2,21,31,0.07); border-top: 6px solid transparent; min-height: 118px; }
.tl-kpi .lab { font-size: 12px; color: #4a5f66; font-weight: 600; }
.tl-kpi .num { font-family: 'Space Grotesk', sans-serif; font-size: clamp(20px, 1.9vw, 27px); white-space: normal; overflow-wrap: anywhere; font-weight: 700; color: #02151f; line-height: 1.2; }
.tl-kpi .foot { font-size: 12px; color: #4a5f66; }
.tl-story { background: #02151f; border-radius: 20px; padding: 26px 30px; color: #ffffff; }
.tl-story .k { font-size: 12px; letter-spacing: 1.6px; color: #ffdd7b; font-weight: 700; }
.tl-story .big { font-family: 'Space Grotesk', sans-serif; font-size: 27px; line-height: 1.25; font-weight: 600; margin: 8px 0; }
.tl-story .small { font-size: 14px; color: #c9d6da; line-height: 1.55; }
.tl-mini { background: #0b2a36; border-radius: 14px; padding: 12px 14px; margin-bottom: 10px; }
.tl-mini .n { font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 700; color: #ffdd7b; }
.tl-mini .t { font-size: 12px; color: #c9d6da; }
.tl-pill { display: inline-block; border-radius: 999px; padding: 3px 12px; font-size: 13px; font-weight: 700; color: #02151f; margin: 0 6px 6px 0; }
.tl-tag { display: inline-block; border-radius: 8px; padding: 3px 10px; font-size: 13px; font-weight: 700; margin: 0 6px 6px 0; }
.tl-plain { display: flex; gap: 12px; background: #e6f6f6; border-radius: 14px; padding: 12px 16px; font-size: 14px; line-height: 1.5; color: #02151f; margin: 6px 0 12px 0; }
.tl-plain .i { flex: 0 0 auto; width: 22px; height: 22px; border-radius: 50%; background: #05556b; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; }
.tl-dark { background: #02151f; color: #fff; border-radius: 18px; padding: 18px 20px; height: 100%; }
.tl-dark .k { font-size: 12px; color: #ffdd7b; font-weight: 700; }
.tl-dark .n { font-family: 'Space Grotesk', sans-serif; font-size: 30px; font-weight: 700; color: #ffdd7b; }
.tl-dark .t { font-size: 13px; color: #c9d6da; line-height: 1.5; }
.tl-facts { display: grid; grid-template-columns: auto 1fr; gap: 6px 14px; font-size: 14px; }
.tl-facts .l { color: #4a5f66; }
.tl-facts .v { font-weight: 700; color: #02151f; }
.tl-time { border-left: 3px solid #b8c7cc; padding-left: 14px; }
.tl-time .e { margin-bottom: 10px; }
.tl-time .d { font-size: 13px; font-weight: 700; color: #02151f; }
.tl-time .s { font-size: 12px; color: #4a5f66; }
.tl-odd { border: 2px solid #05556b; border-radius: 14px; padding: 14px 16px; background: #ffffff; height: 100%; }
.tl-odd .k { font-size: 12px; color: #05556b; font-weight: 700; }
.tl-odd .n { font-size: 16px; font-weight: 700; color: #02151f; margin: 4px 0; }
.tl-brief { background: #fdf6e3; border: 1px solid #eee2bd; border-radius: 14px; padding: 16px 20px; font-size: 15px; line-height: 1.65; color: #02151f; }
.tl-foot { font-size: 11px; line-height: 1.6; color: #9fb4ba; }
.tl-logo { display: flex; align-items: center; gap: 12px; margin: 4px 0 6px 2px; }
.tl-logo .n { font-family: 'Space Grotesk', sans-serif; font-size: 22px; font-weight: 700; color: #ffffff; }
.tl-logo .s { font-size: 10px; color: #9fb4ba; letter-spacing: 1.2px; }
div[data-testid="stTabs"] button[role="tab"] { min-height: 46px; padding: 0 18px; }
div[data-testid="stTabs"] button[role="tab"] p, button[data-baseweb="tab"] p, [data-testid="stTab"] p { font-size: 16px !important; font-weight: 600; }
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { font-weight: 700; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { border-radius: 12px; min-height: 44px; font-weight: 600; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background: #02151f; color: #ffdd7b; border: none; }
.stButton > button[kind="primary"]:hover { background: #05556b; color: #ffffff; }
[data-testid="stMetric"] { background: #ffffff; border-radius: 14px; padding: 12px 16px; box-shadow: 0 4px 18px rgba(2,21,31,0.07); }
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }
.tl-game { background: #ffffff; border-radius: 14px; padding: 10px 12px; box-shadow: 0 2px 10px rgba(2,21,31,0.06); height: 178px; overflow: hidden; font-size: 13px; }
.tl-game .t { font-weight: 600; color: #02151f; font-size: 13px; line-height: 1.35; }
.tl-game .m { color: #4a5f66; font-size: 12px; margin-top: 4px; }
</style>
"""

LOGO = """
<div class="tl-logo">
<svg width="36" height="36" viewBox="0 0 38 38" aria-hidden="true"><circle cx="16" cy="16" r="11" fill="none" stroke="#ffdd7b" stroke-width="3"></circle><circle cx="16" cy="16" r="5" fill="#e0a000"></circle><line x1="24" y1="24" x2="34" y2="34" stroke="#ffdd7b" stroke-width="4" stroke-linecap="round"></line></svg>
<div><div class="n">TenderLens</div><div class="s">SINGLE-BID RISK · ASSAM</div></div>
</div>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(t):
    return html.escape(str(t))


def md(h):
    st.markdown(h, unsafe_allow_html=True)


def header(kicker, title, sub=None):
    h = '<div class="tl-kicker">' + esc(kicker) + '</div><div class="tl-title">' + esc(title) + "</div>"
    if sub:
        h += '<div class="tl-sub">' + esc(sub) + "</div>"
    md(h)


def plain(key_or_text):
    """Show a simple explanation, only when plain-words mode is on."""
    if not st.session_state.get("plain", True):
        return
    text = T.PLAIN.get(key_or_text, key_or_text)
    md('<div class="tl-plain"><span class="i">i</span><span><b>Plain words:</b> ' + esc(text) + "</span></div>")


def kpi(label, number, foot="", edge="transparent", fill="#ffffff"):
    return ('<div class="tl-kpi" style="border-top-color:' + edge + "; background:" + fill + ';"><div class="lab">' + esc(label)
            + '</div><div class="num">' + esc(number) + '</div><div class="foot">' + esc(foot) + "</div></div>")


def band_pill(band, extra=""):
    return '<span class="tl-pill" style="background:' + T.BAND_COLOURS[band] + ';">' + esc(band + extra) + "</span>"


def check_tag(level):
    if level == "P1":
        return '<span class="tl-tag" style="background:#02151f; color:#ffdd7b;">P1 · Check first</span>'
    if level == "P2":
        return '<span class="tl-tag" style="border:2px solid #02151f; color:#02151f; padding:1px 8px;">P2 · Check next</span>'
    return '<span class="tl-tag" style="background:#ffffff; color:#4a5f66; border:1px solid #d7cfb6;">P3 · Routine</span>'


def unusual_tag():
    return '<span class="tl-tag" style="background:#05556b; color:#ffffff;">Unusual</span>'


def dq_tag(text):
    return '<span class="tl-tag" style="background:#ffdd7b; color:#02151f;">Data alert: ' + esc(text) + "</span>"


def re_tag():
    return '<span class="tl-tag" style="border:2px solid #05556b; color:#05556b; padding:1px 8px;">Re-tender</span>'


def sidebar():
    """Logo, plain-words switch, checked list download and footer in the navy side menu."""
    with st.sidebar:
        md('<div style="font-size:10px;color:#9fb4ba;letter-spacing:1.2px;margin:-6px 0 8px 2px;">SINGLE-BID RISK · ASSAM GOVERNMENT TENDERS</div>')
        st.toggle("Plain-words mode", key="plain", help="Shows a one-line simple explanation next to each idea.")
        checked = st.session_state.get("checked", {})
        notes = st.session_state.get("notes", {})
        if checked or notes:
            ids = sorted(set(list(checked.keys()) + list(notes.keys())))
            rows = []
            for i in ids:
                rows.append({"tender_id": i, "checked": checked.get(i, False), "note": notes.get(i, "")})
            st.download_button("Download my checks + notes", pd.DataFrame(rows).to_csv(index=False).encode(),
                               "tenderlens_my_checks.csv", "text/csv", width="stretch")
        md('<div class="tl-foot">Data: Assam e-tenders via CivicDataLab · Apr 2016 – May 2023<br>Screening support, not fraud detection. A person always decides.</div>')


def base_layout(fig, height=320):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color=NAVY, size=13),
                      hoverlabel=dict(bgcolor=NAVY, font_color="#ffffff", font_family="Inter"), showlegend=False)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eee6cf", zeroline=False)
    fig.update_traces(cliponaxis=False, selector=dict(type="bar"))
    return fig


def gauge(pct, band, label):
    """Risk meter: a half circle with Low / Medium / High parts and a needle at the tender's position."""
    pos = 100 - pct * 100 if pct is not None else {"High": 90, "Medium": 65, "Low": 25}[band]
    fig = go.Figure(go.Indicator(
        mode="gauge", value=pos,
        gauge=dict(axis=dict(range=[0, 100], visible=False), bar=dict(color=NAVY, thickness=0.18),
                   steps=[dict(range=[0, 50], color=GREY), dict(range=[50, 80], color=TEAL), dict(range=[80, 100], color=AMBER)],
                   borderwidth=0, threshold=dict(line=dict(color=NAVY, width=6), thickness=0.9, value=pos)),
        domain=dict(x=[0, 1], y=[0, 1])))
    fig.update_layout(height=210, margin=dict(l=10, r=10, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def shap_chart(table):
    t = table.sort_values("push")
    colours = [AMBER if p > 0 else TEAL for p in t["push"]]
    labels = [n + "  (" + v + ")" for n, v in zip(t["name"], t["value"])]
    fig = go.Figure(go.Bar(x=t["push"], y=labels, orientation="h", marker_color=colours,
                           text=[format(p, "+.3f") for p in t["push"]], textposition="outside",
                           hovertemplate="%{y}<br>push %{x:+.3f}<extra></extra>"))
    base_layout(fig, 330)
    lo = min(float(t["push"].min()), 0.0)
    hi = max(float(t["push"].max()), 0.0)
    span = max(hi - lo, 0.1)
    fig.update_layout(margin=dict(l=10, r=30, t=10, b=10))
    fig.update_xaxes(range=[lo - 0.22 * span, hi + 0.22 * span], showgrid=True, gridcolor="#eee6cf", zeroline=True, zerolinecolor=NAVY, zerolinewidth=2, title="← lowers risk     raises risk →")
    fig.update_yaxes(showgrid=False)
    return fig


def open_tender(tender_id):
    """Remember which tender to show, then jump to the Tender detail page."""
    st.session_state["tender_id"] = tender_id
    st.session_state.pop("new_record", None)
    st.switch_page("views/3_tender_detail.py")


def month_picker(widget_key, label="Month"):
    """A month box that stays in step with the month chosen on other pages."""
    s = T.load_settings()
    names = s["month_names"]
    keys = list(names.keys())
    if "month_key" not in st.session_state:
        st.session_state["month_key"] = "2023-01"

    def _sync():
        st.session_state["month_key"] = st.session_state[widget_key]

    st.session_state[widget_key] = st.session_state["month_key"]
    st.selectbox(label, keys, format_func=lambda k: names[k], key=widget_key, on_change=_sync)
    return st.session_state["month_key"]
