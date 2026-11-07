"""Page 5 · Model health: is the model still working? Monthly catch rate (fair replay) and drift score."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import tl_core as T
import tl_ui as U

mh = T.load_table("model_health.csv")
s = T.load_settings()

U.header("Model health", "Is the model still working, month by month?",
         "Two checks every month: how many single-bid tenders the riskiest 20% caught (fair replay), and how different the new tenders look from training (drift).")

last = mh.iloc[-1]
tot_c = int(mh["caught"].sum())
tot_s = int(mh["single_total"].sum())
k = st.columns(4)
k[0].markdown(U.kpi("Caught in riskiest 20%", format(tot_c / tot_s * 100, ".1f") + "%", str(tot_c) + " of " + str(tot_s) + " single-bid, Oct 2022 – May 2023", U.AMBER), unsafe_allow_html=True)
k[1].markdown(U.kpi("Random checking", "20.0%", "expected catch with 20% of checks", U.GREY), unsafe_allow_html=True)
k[2].markdown(U.kpi("Months above random", str(int((mh["catch_pct"] > 20).sum())) + " of " + str(len(mh)), "fair replay", U.TEAL), unsafe_allow_html=True)
k[3].markdown(U.kpi("Latest drift", last["status"], last["month"] + " · score " + format(last["psi"], ".2f"), U.DEEP), unsafe_allow_html=True)
U.plain("fair")

a, b = st.columns(2)
with a:
    U.md('<h3 style="margin:10px 0 0 0;font-size:20px;">Catch rate beat random in 4 of 7 months</h3><div class="tl-sub" style="font-size:13px;">Share of the month\'s single-bid tenders found in the riskiest 20% · dashed = random 20% · <b>click a bar</b> to open that month\'s list</div>')
    cols = [U.AMBER if v > 20 else U.GREY for v in mh["catch_pct"]]
    fig = go.Figure(go.Bar(x=mh["month"], y=mh["catch_pct"], marker_color=cols, customdata=mh["month_key"],
                           text=[format(v, ".1f") for v in mh["catch_pct"]], textposition="outside",
                           hovertext=[str(c) + " of " + str(t) + " single-bid caught" for c, t in zip(mh["caught"], mh["single_total"])],
                           hovertemplate="%{x}<br>%{y:.1f}% caught<br>%{hovertext}<extra>click to open</extra>"))
    fig.add_hline(y=20, line_dash="dash", line_color=U.DEEP, line_width=2)
    U.base_layout(fig, 330)
    fig.update_yaxes(range=[0, 34], title="% of single-bid caught")
    ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="mh_catch")
    if ev and ev.selection and ev.selection.points:
        st.session_state["month_key"] = ev.selection.points[0]["customdata"]
        st.switch_page("views/2_risk_list.py")
with b:
    U.md('<h3 style="margin:10px 0 0 0;font-size:20px;">Drift was strongest in Nov–Dec 2022 and Apr–May 2023</h3><div class="tl-sub" style="font-size:13px;">Drift score (PSI) vs training · below 0.1 same, 0.1–0.25 some change, above 0.25 check the model</div>')
    colmap = {"Same as training": U.TEAL, "Some change": U.AMBER, "Check the model": U.DEEP}
    fig = go.Figure(go.Bar(x=mh["month"], y=mh["psi"], marker_color=[colmap[x] for x in mh["status"]],
                           text=[format(v, ".2f") for v in mh["psi"]], textposition="outside", hovertext=mh["status"],
                           customdata=[T.CLUE_NAMES[c] for c in mh["psi_worst_clue"]],
                           hovertemplate="%{x}<br>drift %{y:.2f} · %{hovertext}<br>most changed: %{customdata}<extra></extra>"))
    fig.add_hline(y=0.1, line_dash="dot", line_color=U.NAVY)
    fig.add_hline(y=0.25, line_dash="dash", line_color=U.NAVY)
    U.base_layout(fig, 330)
    fig.update_yaxes(range=[0, max(0.6, mh["psi"].max() * 1.2)], title="drift score")
    st.plotly_chart(fig, width="stretch", key="mh_psi")

U.md('<h3 style="margin:10px 0 0 0;font-size:20px;">Which clue changed, and when</h3><div class="tl-sub" style="font-size:13px;">Darker = that clue looks more different from training in that month. Hover a square for the number.</div>')
clues = ["log_value", "value_missing", "bid_window_days", "same_day_lot", "retender_60d"]
z = mh[["psi_" + c for c in clues]].T.values
fig = go.Figure(go.Heatmap(z=z, x=mh["month"], y=[T.CLUE_NAMES[c] for c in clues],
                           colorscale=[[0, "#fdf6e3"], [0.25, "#ffdd7b"], [0.5, "#0aa6a6"], [1, "#02151f"]], zmin=0, zmax=1,
                           text=[[format(v, ".2f") for v in row] for row in z], texttemplate="%{text}",
                           hovertemplate="%{y}<br>%{x}: drift %{z:.2f}<extra></extra>", colorbar=dict(title="drift")))
U.base_layout(fig, 300)
st.plotly_chart(fig, width="stretch", key="mh_heat")
st.caption("Months left in the financial year is left out (it is the same for every tender in a month by design). Department rate is left out too: for training tenders it was built from earlier tenders only, so comparing it would show fake drift.")
U.plain("drift")

with st.expander("See the monthly table"):
    t = mh[["month", "tenders", "single_rate", "single_total", "caught", "catch_pct", "high_rate", "psi", "status"]].copy()
    t.columns = ["Month", "Tenders", "Single-bid %", "Single-bid tenders", "Caught in top 20%", "Catch %", "Single-bid % in top 20%", "Drift score", "Drift status"]
    st.dataframe(t.round(2), hide_index=True, width="stretch")
U.md('<div class="tl-card" style="margin-top:8px;font-size:14px;line-height:1.55;"><b>What I would do in real use:</b> retrain at the start of every month, learning only from tenders whose bids are already opened (my S6 label timing rule). When the drift status says "Check the model", look at the most changed clue before trusting the list.</div>')
