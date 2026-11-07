"""Page 8 · About & behind the model: how it works, the fair test, honest limits, data credits."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import tl_core as T
import tl_ui as U

U.header("About & behind the model", "How TenderLens works, and why I trust it only as much as the tests allow")

t1, t2, t3, t4 = st.tabs(["How it works", "Behind the model", "Honest limits", "Data & credits"])

with t1:
    steps = [
        ("1", "Read the tender", "On the day a tender is published, I take only what is known that day: department, value, dates, title."),
        ("2", "Build 7 clues", "Department's past single-bid rate, value, value not written, days to bid, months left in the financial year, same-day lot, re-tender within 60 days."),
        ("3", "Score and rank", "A Logistic Regression gives a risk score. Tenders are ranked inside their own month: top 20% High, next 30% Medium, rest Low."),
        ("4", "Explain", "SHAP shows which clues pushed the score up or down for this one tender."),
        ("5", "Flag odd ones", "An Isolation Forest flags the 5% of tenders whose clues look most unlike normal, and names the odd clues."),
        ("6", "Check first", "P1 = High and (unusual or Rs 1 crore+). An AI writes a short brief using only the real facts."),
    ]
    cols = st.columns(3)
    for i, (n, t, d) in enumerate(steps):
        cols[i % 3].markdown('<div class="tl-card" style="margin-bottom:14px;min-height:150px;"><div class="tl-num" style="font-size:30px;font-weight:700;color:#e0a000;">'
                             + n + '</div><div style="font-weight:700;font-size:16px;margin:2px 0 6px 0;">' + t + '</div><div style="font-size:14px;color:#4a5f66;line-height:1.5;">' + d + "</div></div>",
                             unsafe_allow_html=True)
    U.md('<div class="tl-story" style="margin-top:6px;"><div class="k">WHAT IT IS FOR</div><div class="big" style="font-size:22px;">Screening support, not fraud detection.</div><div class="small">A single bid can have honest reasons: a far-away site, a very special job, a short season. TenderLens only says where an auditor may look first. A person always decides.</div></div>')

with t2:
    test = T.load_table("s7_test_results.csv")
    keep = ["Random checking", "Rule B: re-tender then dept", "LogReg 7 clues, monthly", "Embeddings alone"]
    tt = test[test["method"].isin(keep)].copy()
    U.md('<h3 style="margin:8px 0 0 0;font-size:20px;">The one fair test (Jan–May 2023, used once)</h3><div class="tl-sub" style="font-size:13px;">Single-bid tenders caught in the riskiest 20% (353 checks, 421 single-bid in total)</div>')
    av = T.load_table("s7_auditor_view.csv")
    colours = []
    for m in av["method"]:
        colours.append(U.TEAL if "LogReg" in m else (U.DEEP if "Rule" in m else U.GREY))
    fig = go.Figure(go.Bar(x=av["caught"], y=av["method"], orientation="h", marker_color=colours, text=av["caught"], textposition="outside",
                           hovertemplate="%{y}: %{x} caught<extra></extra>"))
    U.base_layout(fig, 260)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    st.plotly_chart(fig, width="stretch", key="ab_caught")
    a, b = st.columns(2)
    with a:
        bs = T.load_table("s7_bootstrap.csv")
        U.md('<div class="tl-card"><b>Bootstrap (500 re-draws of the test)</b><br><br>' +
             "".join(["<div style='font-size:14px;margin-bottom:6px;'>" + U.esc(r["comparison"]) + ": wins in <b>" + format(r["A wins (% of draws)"], ".1f") + "%</b></div>" for _, r in bs.iterrows()])
             + "<div style='font-size:13px;color:#4a5f66;margin-top:8px;'>Beats random in 95.8% → a small but real win. The simple Rule B is a strong baseline and I say that openly.</div></div>")
    with b:
        U.md('<div class="tl-card"><b>Why the ANN is not in the app (S9)</b><br><br><div style="font-size:14px;line-height:1.6;">'
             "On validation the ANN only tied random checking (PR-AUC 0.286 vs 0.288).<br>It beat random in only 43% of re-draws, and only 2 of 6 seeds were above random.<br>"
             "On test it equalled random (0.232).<br><br><b>So I kept the simpler model.</b> Complexity must earn its place.</div></div>")
    with st.expander("See the full test table"):
        st.dataframe(test, hide_index=True, width="stretch")
    with st.expander("See the S9 validation comparison (ANN and friends)"):
        st.dataframe(T.load_table("s9_val_results.csv"), hide_index=True, width="stretch")

with t3:
    lim = [
        ("Drift", "Single-bid tenders fell from 36.1% (train) to 27.8% (validation) to 23.8% (test), and many clues changed direction after Sep 2022."),
        ("Weak publish-day clues", "On the day of publishing very little is known, and the portal cuts descriptions at 250 letters. So the win over random is small."),
        ("Label timing", "A tender's answer is known only after its bid opening date (about 19 days later), so retraining may only use tenders already opened."),
        ("Scores are not %", "The score is a ranking, not a real chance. That is why the app shows bands, ranked inside each month."),
        ("Saving is a sign", "The possible saving uses the S8 award-price gap (one bid vs 4+ bids). It is a rough sign, not proof that more bidders would bid lower."),
        ("Past months in the list", "The app model learned from all 6,790 labelled tenders, so the list for past months is a demo. The fair numbers are the S7 test and the fair replay pages."),
    ]
    for t, d in lim:
        U.md('<div class="tl-card" style="margin-bottom:10px;"><b>' + U.esc(t) + '</b><div style="font-size:14px;color:#4a5f66;margin-top:4px;">' + U.esc(d) + "</div></div>")

with t4:
    U.md('<div class="tl-card" style="font-size:14px;line-height:1.7;">'
         "<b>Data:</b> Assam e-tenders portal, collected by CivicDataLab (github.com/CivicDataLab/assam-tenders-data), Apr 2016 – May 2023.<br>"
         "39,411 tenders · 6,790 with a verified bidder list · 2,044 single-bid in the labelled set (30.1%).<br>"
         "<b>Time split:</b> train to Sep 2022 (2,753), validation Oct–Dec 2022 (2,270), test Jan–May 2023 (1,767).<br>"
         "<b>Models:</b> Logistic Regression (7 clues, class weights), Isolation Forest (10 clues, top 5%), SHAP for reasons, TF-IDF for similar titles.<br>"
         "<b>Suppliers</b> are anonymised (S1, S2, …). <b>Never</b> use this to blame a department or a company.<br><br>"
         "Built by <b>Sindhu Marupaka</b> · Imarticus PGA56 · Capstone Project 2 · TenderLens: Single-Bid Risk in Assam Government Tenders</div>")
