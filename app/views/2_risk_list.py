"""Page 2 · Tender risk list: every tender of the month, ranked inside the month, plus the audit budget slider."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import tl_core as T
import tl_ui as U

lst = T.load_tenders()
s = T.load_settings()
names = s["month_names"]

top_l, top_r = st.columns([3.2, 1])
with top_r:
    st.write("")
    mk = U.month_picker("rl_month")
g = lst[lst["month_key"] == mk].sort_values("rank")
with top_l:
    U.header("Tender risk list · " + names[mk], format(len(g), ",") + " tenders, ranked inside the month",
             "The riskiest 20% are High, the next 30% Medium, the rest Low. Bands, not percentages.")
U.plain("band")

# ---------------------------------------------------------------- audit budget
with st.container(border=True):
    U.md('<h3 style="margin:0;font-size:20px;">Audit budget: how many tenders can you check this month?</h3>'
         '<div class="tl-sub" style="font-size:13px;">Move the slider. Everything below updates live. Fair replay: the scores the model gave at that time, before the bids were opened.</div>')
    n_max = len(g)
    default_n = max(1, int(round(n_max * 0.2)))
    n = st.slider("I can check", 1, n_max, default_n, key="budget_" + mk, format="%d tenders")
    rate = g["single_bid"].mean()
    order = g.sort_values("fair_rank")
    found = int(order.head(n)["single_bid"].sum())
    rand = n * rate
    total_single = int(g["single_bid"].sum())
    money = order.head(n)["estimated_value"].sum() / 1e7
    k = st.columns(4)
    k[0].markdown(U.kpi("Single-bid tenders my list finds", str(found), "out of " + str(total_single) + " this month", U.AMBER), unsafe_allow_html=True)
    k[1].markdown(U.kpi("Random checking would find", format(rand, ".0f"), "on average, same number of checks", U.GREY), unsafe_allow_html=True)
    diff = found - rand
    k[2].markdown(U.kpi("Extra found vs random", format(diff, "+.0f"), "positive = model helps", U.TEAL), unsafe_allow_html=True)
    k[3].markdown(U.kpi("Money covered", "Rs " + format(money, ",.0f") + " cr", "value of the tenders you check", U.DEEP), unsafe_allow_html=True)
    cum = order["single_bid"].cumsum().values
    xs = np.arange(1, len(order) + 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=xs * rate, mode="lines", line=dict(color=U.GREY, width=3, dash="dash"), name="Random checking",
                             hovertemplate="Random: %{y:.0f} found after %{x} checks<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=cum, mode="lines", line=dict(color=U.AMBER, width=4), name="TenderLens order",
                             hovertemplate="TenderLens: %{y} found after %{x} checks<extra></extra>"))
    fig.add_trace(go.Scatter(x=[n], y=[found], mode="markers", name="Your budget", marker=dict(size=16, color=U.NAVY, line=dict(color=U.GOLD, width=3)),
                             hovertemplate="Your budget: %{x} checks, %{y} found<extra></extra>"))
    fig.add_vline(x=n, line_color=U.NAVY, line_width=1)
    U.base_layout(fig, 260)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.12, x=0))
    fig.update_xaxes(title="tenders checked (in TenderLens order)")
    fig.update_yaxes(title="single-bid found")
    st.plotly_chart(fig, width="stretch", key="budget_curve")
    if abs(diff) < 0.5:
        st.caption("With " + str(n) + " checks this month, TenderLens finds " + str(found) + " single-bid tenders, about the same as random checking. Some months the model does not help (see Model health). I show this honestly.")
    elif diff > 0:
        st.caption("With " + str(n) + " checks, following TenderLens finds " + str(found) + " single-bid tenders, about " + format(diff, ".0f") + " more than random checking.")
    else:
        st.caption("With " + str(n) + " checks this month, TenderLens finds " + str(found) + ", about " + format(-diff, ".0f") + " fewer than random. Some months the model misses (see Model health). I show this honestly.")

# ---------------------------------------------------------------- filters
f1, f2, f3 = st.columns([2.2, 2.2, 2])
with f1:
    q = st.text_input("Search title or department", placeholder="e.g. road, hall, PWD", key="rl_q")
with f2:
    bands = st.pills("Band", ["High", "Medium", "Low"], selection_mode="multi", default=["High", "Medium", "Low"], key="rl_bands")
with f3:
    depts = ["All departments"] + sorted(g["dept_main"].dropna().unique().tolist())
    dsel = st.selectbox("Department", depts, key="rl_dept")
t1, t2, t3, t4 = st.columns(4)
only_p1 = t1.toggle("Check first (P1) only", key="rl_p1")
only_odd = t2.toggle("Unusual only", key="rl_odd")
only_dq = t3.toggle("Data alerts only", key="rl_dq")
only_re = t4.toggle("Re-tenders only", key="rl_re")

v = g.copy()
if q:
    hit = v["title"].fillna("").str.contains(q, case=False, regex=False) | v["dept_main"].fillna("").str.contains(q, case=False, regex=False)
    v = v[hit]
if bands:
    v = v[v["band"].isin(bands)]
if dsel != "All departments":
    v = v[v["dept_main"] == dsel]
if only_p1:
    v = v[v["check"] == "P1"]
if only_odd:
    v = v[v["unusual"] == 1]
if only_dq:
    v = v[v["dq"] != ""]
if only_re:
    v = v[v["retender_60d"] == 1]

checked = st.session_state.get("checked", {})
signals = []
for _, r in v.iterrows():
    sg = []
    if r["unusual"] == 1:
        sg.append("◆ Unusual")
    if r["dq"]:
        sg.append("⚠ Data")
    if r["retender_60d"] == 1:
        sg.append("↻ Re-tender")
    signals.append("  ".join(sg))
view = pd.DataFrame({
    "Rank": v["rank"].values,
    "Band": v["band"].values,
    "Check": v["check"].values,
    "Tender": v["title"].fillna("").str.slice(0, 120).values,
    "Signals": signals,
    "Value": [T.money(x) for x in v["estimated_value"]],
    "Department": v["dept_main"].values,
    "Risk position": (1 - v["rank"] / v["n_month"]).values,
    "Bids (known later)": [("1 bid" if b == 1 else str(int(b)) + " bids") if pd.notna(b) else "" for b in v["number_of_bids"]],
    "Checked": ["✓" if checked.get(i) else "" for i in v["tender_id"]],
})


def band_style(col):
    out = []
    for b in col:
        out.append("background-color: " + T.BAND_COLOURS.get(b, "#fff") + "; color: #02151f; font-weight: 700;")
    return out


def check_style(col):
    out = []
    for c in col:
        if c == "P1":
            out.append("background-color: #02151f; color: #ffdd7b; font-weight: 700;")
        elif c == "P2":
            out.append("font-weight: 700;")
        else:
            out.append("color: #4a5f66;")
    return out


styled = view.style.apply(band_style, subset=["Band"]).apply(check_style, subset=["Check"])
U.md('<div style="display:flex;justify-content:space-between;align-items:end;margin-top:8px;"><h3 style="margin:0;font-size:20px;">'
     + format(len(view), ",") + " tenders shown</h3><span style='font-size:13px;color:#4a5f66;'>Click a row to open the full tender page</span></div>")
ev = st.dataframe(styled, width="stretch", hide_index=True, height=520, on_select="rerun", selection_mode="single-row", key="rl_table",
                  column_config={
                      "Rank": st.column_config.NumberColumn("Rank", format="#%d", width="small"),
                      "Tender": st.column_config.TextColumn("Tender", width="large"),
                      "Band": st.column_config.TextColumn("Band", width="small"),
                      "Check": st.column_config.TextColumn("Check", width="small"),
                      "Department": st.column_config.TextColumn("Department", width="medium"),
                      "Risk position": st.column_config.ProgressColumn("Risk position", min_value=0, max_value=1, format=" "),
                      "Checked": st.column_config.TextColumn("✓", width="small"),
                  })
if ev and ev.selection and ev.selection.rows:
    U.open_tender(v.iloc[ev.selection.rows[0]]["tender_id"])

d1, d2 = st.columns(2)
out_cols = ["rank", "tender_id", "title", "dept_main", "estimated_value", "published_date", "last_date", "band", "check", "unusual", "dq", "retender_60d"]
d1.download_button("Download this list (CSV)", v[out_cols].to_csv(index=False).encode(), "tenderlens_list_" + mk + ".csv", "text/csv", width="stretch")
p1 = g[g["check"] == "P1"]
d2.download_button("Download check-first P1 list (" + str(len(p1)) + ")", p1[out_cols].to_csv(index=False).encode(), "tenderlens_check_first_" + mk + ".csv",
                   "text/csv", width="stretch", type="primary")
U.plain("check")
