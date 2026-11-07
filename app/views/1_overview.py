"""Page 1 · Overview: the big picture and this month's numbers."""
import plotly.graph_objects as go
import streamlit as st

import tl_core as T
import tl_ui as U

lst = T.load_tenders()
s = T.load_settings()
names = s["month_names"]
keys = list(names.keys())
if "month_key" not in st.session_state:
    st.session_state["month_key"] = "2023-01"

top_l, top_r = st.columns([4, 1.3])
with top_l:
    U.header("Overview", "Where should an auditor look first this month?")
with top_r:
    mh = T.load_table("model_health.csv").set_index("month_key")
    stat = mh.loc[st.session_state["month_key"], "status"]
    dot = {"Same as training": U.TEAL, "Some change": U.AMBER, "Check the model": U.DEEP}[stat]
    U.md('<div class="tl-card" style="padding:10px 14px; margin-top:18px; font-size:13px;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'
         + dot + ';margin-right:8px;"></span>Model health: <b>' + U.esc(stat) + "</b></div>")

def _set_month():
    if st.session_state.get("ov_month"):
        st.session_state["month_key"] = st.session_state["ov_month"]


st.session_state["ov_month"] = st.session_state["month_key"]
st.segmented_control("Pick a month", keys, format_func=lambda k: names[k], key="ov_month",
                     label_visibility="collapsed", on_change=_set_month)
mk = st.session_state["month_key"]
g = lst[lst["month_key"] == mk]

# ---- story card (S8 numbers)
U.md("""
<div class="tl-story"><div style="display:flex; flex-wrap:wrap; gap:26px; align-items:center;">
<div style="flex:2 1 420px;"><div class="k">WHY THIS MATTERS</div>
<div class="big"><span style="color:#ffdd7b;">Rs 14,752 crore</span> of Assam tender money went out with only one bidder.</div>
<div class="small">That is 36.5% of the money but only 31% of the tenders, so one-bid works are the bigger ones. Real price discounts only show up with 4 or more bidders.</div></div>
<div style="flex:1 1 280px; display:grid; grid-template-columns:1fr 1fr; gap:10px;">
<div class="tl-mini"><div class="n">36.5%</div><div class="t">of all the money</div></div>
<div class="tl-mini"><div class="n">4+</div><div class="t">bidders for real discounts</div></div>
<div class="tl-mini"><div class="n">101 vs 79</div><div class="t">caught vs random checking (riskiest 20%)</div></div>
<div class="tl-mini"><div class="n">1 in 7</div><div class="t">tenders to check first</div></div>
</div></div></div>
""")
st.write("")

# ---- this month's numbers
c = st.columns(5)
val_cr = g["estimated_value"].sum() / 1e7
c[0].markdown(U.kpi("Tenders in " + names[mk], format(len(g), ","), "Rs " + format(val_cr, ",.0f") + " crore in total"), unsafe_allow_html=True)
c[1].markdown(U.kpi("High risk band", str((g["band"] == "High").sum()), "top 20% of this month", U.AMBER), unsafe_allow_html=True)
c[2].markdown(U.kpi("Unusual tenders", str(int(g["unusual"].sum())), "odd mix of clues", U.DEEP), unsafe_allow_html=True)
c[3].markdown(U.kpi("Check first (P1)", str((g["check"] == "P1").sum()), "High and (unusual or Rs 1 cr+)", U.GOLD, U.GOLD), unsafe_allow_html=True)
c[4].markdown(U.kpi("Real single-bid rate", format(g["single_bid"].mean() * 100, ".1f") + "%", "known after bids opened", U.TEAL), unsafe_allow_html=True)
U.plain("single_bid")

# ---- charts row
a, b = st.columns(2)
with a:
    with st.container(border=False):
        U.md('<h3 style="margin:8px 0 0 0;font-size:20px;">Single-bid tenders kept falling after Sep 2022</h3><div class="tl-sub" style="font-size:13px;">Share of tenders with only one bid · dashed line = training level 36.1% · <b>click a bar</b> to open that month\'s list</div>')
        rate = lst.groupby("month_key")["single_bid"].mean().reindex(keys) * 100
        colours = []
        lines = []
        for k in keys:
            colours.append(U.AMBER if rate[k] > 36.1 else U.GREY)
            lines.append(4 if k == mk else 0)
        fig = go.Figure(go.Bar(x=[names[k] for k in keys], y=rate.values, marker=dict(color=colours, line=dict(color=U.NAVY, width=lines)),
                               text=[format(v, ".1f") for v in rate.values], textposition="outside", customdata=keys,
                               hovertemplate="%{x}<br>%{y:.1f}% single-bid<extra>click to open</extra>"))
        fig.add_hline(y=36.1, line_dash="dash", line_color=U.DEEP, line_width=2)
        U.base_layout(fig, 330)
        fig.update_yaxes(range=[0, 46], title="% single-bid")
        ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="ov_rate")
        if ev and ev.selection and ev.selection.points:
            st.session_state["month_key"] = ev.selection.points[0]["customdata"]
            st.switch_page("views/2_risk_list.py")
with b:
    U.md('<h3 style="margin:8px 0 0 0;font-size:20px;">The bands work in the right order</h3><div class="tl-sub" style="font-size:13px;">Real single-bid rate in each band · fair test on Jan–May 2023 (1,767 tenders)</div>')
    bands = T.load_table("s7_risk_bands.csv")
    fig = go.Figure(go.Bar(x=bands["single-bid %"], y=bands["band"], orientation="h",
                           marker_color=[T.BAND_COLOURS[x] for x in bands["band"]], text=[str(v) + "%" for v in bands["single-bid %"]],
                           textposition="outside", customdata=bands["tenders"],
                           hovertemplate="%{y}: %{x}% single-bid<br>%{customdata} tenders<extra></extra>"))
    U.base_layout(fig, 250)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(range=[0, 34], showgrid=True, gridcolor="#eee6cf")
    st.plotly_chart(fig, width="stretch", key="ov_bands")
    U.md('<div class="tl-card" style="display:flex;gap:12px;align-items:center;padding:12px 16px;"><span class="tl-num" style="font-size:24px;font-weight:700;color:#05556b;">95.8%</span><span style="font-size:13px;">of 500 re-draws: my model beat random checking. A small but real win.</span></div>')
U.plain("band")

# ---- departments money
U.md('<h3 style="margin:18px 0 0 0;font-size:20px;">Three departments hold 75% of the single-bid money</h3><div class="tl-sub" style="font-size:13px;">Single-bid money by department, Rs crore (all labelled tenders) · <b>click a bar</b> to open its report card</div>')
dep = T.load_table("departments.csv").sort_values("single_cr", ascending=False).head(8).iloc[::-1]
cols = [U.AMBER if i >= len(dep) - 3 else U.GREY for i in range(len(dep))]
fig = go.Figure(go.Bar(x=dep["single_cr"], y=dep["dept_main"], orientation="h", marker_color=cols, customdata=dep["dept_main"],
                       text=[format(v, ",.0f") for v in dep["single_cr"]], textposition="outside",
                       hovertemplate="%{y}<br>Rs %{x:,.0f} crore with one bidder<extra>click to open</extra>"))
U.base_layout(fig, 360)
fig.update_yaxes(showgrid=False)
fig.update_layout(margin=dict(l=10, r=60, t=10, b=10))
ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="ov_dept")
if ev and ev.selection and ev.selection.points:
    st.session_state["dept"] = ev.selection.points[0]["customdata"]
    st.switch_page("views/4_department.py")

# ---- top check-first tenders this month
U.md('<h3 style="margin:10px 0 6px 0;font-size:20px;">Check first this month</h3>')
top = g[g["check"] == "P1"].sort_values("rank").head(5)
if len(top) == 0:
    st.info("No P1 tenders this month.")
for _, r in top.iterrows():
    x1, x2, x3 = st.columns([0.6, 5, 1.2])
    x1.markdown('<div class="tl-num" style="font-size:20px;font-weight:700;color:#4a5f66;padding-top:6px;">#' + str(r["rank"]) + "</div>", unsafe_allow_html=True)
    tags = U.band_pill(r["band"]) + (U.unusual_tag() if r["unusual"] == 1 else "") + (U.dq_tag(r["dq"]) if r["dq"] else "")
    x2.markdown("<b>" + U.esc(str(r["title"])[:110]) + "</b><br><span style='font-size:13px;color:#4a5f66;'>" + U.esc(r["dept_main"]) + " · " + T.money(r["estimated_value"]) + "</span><br>" + tags, unsafe_allow_html=True)
    if x3.button("Open", key="ov_open_" + r["tender_id"], width="stretch"):
        U.open_tender(r["tender_id"])
