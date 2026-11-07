"""Page 4 · Department report card: one department's story before and after Sep 2022."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import tl_core as T
import tl_ui as U

dep = T.load_table("departments.csv")
lab = T.load_labelled()
lst = T.load_tenders()
dep = dep[dep["tenders"] >= 15].sort_values("single_cr", ascending=False)
options = list(dep["dept_main"])
if st.session_state.get("dept") not in options:
    st.session_state["dept"] = options[0]


def _sync():
    st.session_state["dept"] = st.session_state["dp_pick"]


st.session_state["dp_pick"] = st.session_state["dept"]
l, r = st.columns([3, 1.6])
with r:
    st.write("")
    st.selectbox("Department", options, key="dp_pick", on_change=_sync)
d = st.session_state["dept"]
row = dep[dep["dept_main"] == d].iloc[0]
with l:
    U.header("Department report card", d, "All " + format(int(row["tenders"]), ",") + " labelled tenders from this department, Apr 2016 – May 2023.")

k = st.columns(5)
k[0].markdown(U.kpi("Single-bid rate", format(row["single_rate"], ".1f") + "%", "all years (overall 31.3%)", U.AMBER), unsafe_allow_html=True)
k[1].markdown(U.kpi("Single-bid money", "Rs " + format(row["single_cr"], ",.0f") + " cr", format(row["share_of_single_money"], ".1f") + "% of all single-bid money", U.AMBER), unsafe_allow_html=True)
rb, ra = row["rate_before"], row["rate_after"]
if pd.notna(rb) and pd.notna(ra):
    arrow = "better" if ra < rb else "worse"
    k[2].markdown(U.kpi("Before → after Sep 2022", format(rb, ".0f") + "% → " + format(ra, ".0f") + "%", "got " + arrow, U.TEAL), unsafe_allow_html=True)
else:
    k[2].markdown(U.kpi("Before → after Sep 2022", "-", "not enough tenders in one period", U.TEAL), unsafe_allow_html=True)
rep = row.get("repeat_share")
k[3].markdown(U.kpi("Won by repeat winners", (format(rep, ".0f") + "%") if pd.notna(rep) else "-", "awards to firms with 3+ wins here", U.DEEP), unsafe_allow_html=True)
tf = row.get("top_firm_share")
k[4].markdown(U.kpi("Top firm's share", (format(tf, ".0f") + "%") if pd.notna(tf) else "-",
                    ("firm " + str(row["top_firm"]) + " · " + str(int(row["awards"])) + " awards") if pd.notna(tf) else "no award data", U.GREY), unsafe_allow_html=True)
U.plain("Firm names are hidden and replaced by codes (S1, S2, …) so the app never blames a company. Repeat winners are firms that won 3 or more times in this department.")

a, b = st.columns([1.1, 1])
with a:
    U.md('<h3 style="margin:10px 0 0 0;font-size:20px;">How its single-bid rate moved, quarter by quarter</h3><div class="tl-sub" style="font-size:13px;">Quarters with at least 10 labelled tenders · dashed line = Sep 2022</div>')
    g = lab[lab["dept_main"] == d].copy()
    g["q"] = g["published_date"].dt.to_period("Q").astype(str)
    qq = g.groupby("q").agg(n=("single_bid", "size"), rate=("single_bid", "mean")).reset_index()
    qq = qq[qq["n"] >= 10]
    fig = go.Figure(go.Scatter(x=qq["q"], y=qq["rate"] * 100, mode="lines+markers+text", line=dict(color=U.DEEP, width=3),
                               marker=dict(size=[min(28, 6 + n / 15) for n in qq["n"]], color=U.AMBER, line=dict(color=U.NAVY, width=1)),
                               text=[format(v * 100, ".0f") for v in qq["rate"]], textposition="top center", customdata=qq["n"],
                               hovertemplate="%{x}<br>%{y:.1f}% single-bid<br>%{customdata} tenders<extra></extra>"))
    if "2022Q3" in list(qq["q"]):
        fig.add_vline(x="2022Q3", line_dash="dash", line_color=U.NAVY)
    U.base_layout(fig, 320)
    fig.update_yaxes(title="% single-bid", rangemode="tozero")
    st.plotly_chart(fig, width="stretch", key="dp_trend")
with b:
    U.md('<h3 style="margin:10px 0 0 0;font-size:20px;">Every department: before vs after Sep 2022</h3><div class="tl-sub" style="font-size:13px;">Departments with 30+ tenders in both periods · <b>click a dot</b> to switch department</div>')
    both = dep[(dep["n_before"] >= 30) & (dep["n_after"] >= 30)].copy()
    both["change"] = both["rate_after"] - both["rate_before"]
    both = both.sort_values("change")
    short = [x[:34] + ("…" if len(x) > 34 else "") for x in both["dept_main"]]
    fig = go.Figure()
    for y, b0, a0, full in zip(short, both["rate_before"], both["rate_after"], both["dept_main"]):
        col = U.NAVY if full == d else "#c9c2aa"
        fig.add_trace(go.Scatter(x=[b0, a0], y=[y, y], mode="lines", line=dict(color=col, width=4 if full == d else 2), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=both["rate_before"], y=short, mode="markers", marker=dict(size=11, color=U.GREY, line=dict(color=U.NAVY, width=1)),
                             customdata=both["dept_main"], hovertemplate="%{customdata}<br>before %{x:.1f}%<extra>click</extra>"))
    fig.add_trace(go.Scatter(x=both["rate_after"], y=short, mode="markers",
                             marker=dict(size=13, color=[U.AMBER if c > 0 else U.TEAL for c in both["change"]], line=dict(color=U.NAVY, width=1)),
                             customdata=both["dept_main"], hovertemplate="%{customdata}<br>after %{x:.1f}%<extra>click</extra>"))
    U.base_layout(fig, 420)
    fig.update_xaxes(title="% single-bid · grey before, colour after", showgrid=True, gridcolor="#eee6cf")
    fig.update_yaxes(showgrid=False, tickfont=dict(size=11))
    ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="dp_dumb")
    if ev and ev.selection and ev.selection.points:
        cd = ev.selection.points[0].get("customdata")
        if cd and cd != d:
            st.session_state["dept"] = cd
            st.rerun()

U.md('<h3 style="margin:14px 0 6px 0;font-size:20px;">Its riskiest tenders right now (Oct 2022 – May 2023)</h3>')
cur = lst[(lst["dept_main"] == d) & (lst["band"] == "High")].copy()
cur["position"] = cur["rank"] / cur["n_month"]
cur = cur.sort_values("position").head(6)
if len(cur) == 0:
    st.info("No High-band tenders from this department in the list months.")
for _, r in cur.iterrows():
    x1, x2, x3 = st.columns([1.1, 5, 1.1])
    x1.markdown(U.band_pill(r["band"]) + "<br><span style='font-size:12px;color:#4a5f66;'>" + r["month"] + " #" + str(r["rank"]) + "</span>", unsafe_allow_html=True)
    tags = U.check_tag(r["check"]) + (U.unusual_tag() if r["unusual"] == 1 else "") + (U.dq_tag(r["dq"]) if r["dq"] else "")
    x2.markdown("<b>" + U.esc(str(r["title"])[:120]) + "</b> · <span style='font-size:13px;color:#4a5f66;'>" + T.money(r["estimated_value"]) + "</span><br>" + tags, unsafe_allow_html=True)
    if x3.button("Open", key="dp_open_" + r["tender_id"], width="stretch"):
        U.open_tender(r["tender_id"])
