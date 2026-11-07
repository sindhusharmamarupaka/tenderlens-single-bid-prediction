"""Page 3 · Tender detail: everything about one tender (from the list, or typed in on page 6)."""
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import tl_core as T
import tl_ui as U

lst = T.load_tenders()
s = T.load_settings()
names = s["month_names"]

# ---------------------------------------------------------------- which tender?
rec = None
if st.session_state.get("new_record") is not None:
    rec = st.session_state["new_record"]
else:
    tid = st.session_state.get("tender_id")
    if tid is None:
        mk = st.session_state.get("month_key", "2023-01")
        tid = lst[(lst["month_key"] == mk)].sort_values("rank").iloc[0]["tender_id"]
        st.session_state["tender_id"] = tid
    rec = T.record_from_list(tid)

nav_l, nav_r = st.columns([1.2, 3])
with nav_l:
    st.page_link("views/2_risk_list.py", label="Back to the risk list", icon=":material/arrow_back:")
with nav_r:
    mk_now = st.session_state.get("month_key", "2023-01")
    pool = lst[lst["month_key"] == mk_now].sort_values("rank").head(200)
    opts = list(pool["tender_id"])
    labels = dict(zip(pool["tender_id"], ["#" + str(r) + " · " + str(t)[:80] for r, t in zip(pool["rank"], pool["title"])]))
    jump = st.selectbox("Jump to another tender in " + names[mk_now], ["—"] + opts, format_func=lambda x: "Pick a tender…" if x == "—" else labels[x],
                        key="td_jump", label_visibility="collapsed")
    if jump != "—" and (rec.get("source") != "list" or jump != rec["tender_id"]):
        st.session_state["td_jump"] = "—"
        U.open_tender(jump)

is_new = rec.get("source") != "list"
tid = rec.get("tender_id") or "NEW"

# ---------------------------------------------------------------- header
head_l, head_r = st.columns([3.2, 1.3])
with head_l:
    where = "NEW TENDER (TYPED IN)" if is_new else "TENDER " + str(tid)
    U.header(where + " · " + str(rec["dept_main"]).upper(), str(rec["title"])[:200])
    tags = ""
    if rec.get("rank") is not None and pd.notna(rec.get("rank")) and rec.get("n_month"):
        tags += U.band_pill(rec["band"], " band · #" + str(int(rec["rank"])) + " of " + format(int(rec["n_month"]), ","))
    else:
        tags += U.band_pill(rec["band"], " band")
    tags += U.check_tag(rec["check"])
    if rec["unusual"] == 1:
        tags += U.unusual_tag()
    if rec.get("dq"):
        tags += U.dq_tag(rec["dq"])
    if rec["retender_60d"] == 1:
        tags += U.re_tag()
    U.md(tags)
with head_r:
    st.write("")
    checked = st.session_state.setdefault("checked", {})
    is_checked = checked.get(tid, False)
    if st.button("Checked ✓" if is_checked else "Mark as checked", key="td_check", width="stretch", type="secondary" if is_checked else "primary"):
        checked[tid] = not is_checked
        st.rerun()
    brief_now = st.session_state.get("brief", {}).get((tid, "en"), (None, None))[0]
    note_now = st.session_state.get("notes", {}).get(tid, "")
    st.download_button("Download 1-page PDF", T.tender_pdf(rec, brief_now, note_now), "TenderLens_" + str(tid) + ".pdf", "application/pdf",
                       width="stretch", key="td_pdf")

# ---------------------------------------------------------------- four cards
row_a = st.columns(2)
row_b = st.columns(2)
c1, c2 = row_a
c3, c4 = row_b
with c1:
    with st.container(border=True):
        lab = "Risk meter (inside " + (names.get(rec.get("month_key"), "its month") if not is_new else "the same month of the year") + ")"
        st.caption(lab)
        pct = rec.get("pct")
        if not is_new and rec.get("rank") is not None:
            pct = rec["rank"] / rec["n_month"]
        st.plotly_chart(U.gauge(pct if pct is not None and pd.notna(pct) else None, rec["band"], ""), width="stretch", key="td_gauge",
                        config={"displayModeBar": False})
        if pct is not None and pd.notna(pct):
            U.md('<div style="text-align:center;"><span class="tl-num" style="font-size:19px;font-weight:700;">Top ' + format(max(pct * 100, 0.1), ".1f") + '% of its month</span><br><span style="font-size:12px;color:#4a5f66;">Low · Medium · High</span></div>')
        else:
            U.md('<div style="text-align:center;font-size:13px;color:#4a5f66;">June–September: band from the S7 fixed cut-offs</div>')
with c2:
    with st.container(border=True):
        st.caption("Key facts (publish day)")
        facts = [("Value", T.money(rec.get("estimated_value"))), ("Published", T.nice_date(rec.get("published_date"))),
                 ("Last date for bids", T.nice_date(rec.get("last_date"))),
                 ("Days to bid", str(int(rec["bid_window_days"])) + " (usual " + str(int(s["bid_window_median"])) + ")"),
                 ("Work period", (format(rec["work_period_days"], ",.0f") + " days") if pd.notna(rec.get("work_period_days")) else "Not given"),
                 ("EMD", ("Rs " + format(rec["emd_amount"], ",.0f")) if pd.notna(rec.get("emd_amount")) else "Not given")]
        if not is_new:
            nb = rec.get("number_of_bids")
            facts.append(("Bids (known later)", ("1 bid" if nb == 1 else str(int(nb)) + " bids") if pd.notna(nb) else "-"))
        h = '<div class="tl-facts">'
        for k_, v_ in facts:
            h += '<span class="l">' + U.esc(k_) + '</span><span class="v">' + U.esc(v_) + "</span>"
        U.md(h + "</div>")
with c3:
    ps = T.possible_saving(rec.get("estimated_value"))
    if ps:
        amt, gap = ps
        U.md('<div class="tl-dark"><div class="k">POSSIBLE SAVING</div><div class="n">≈ ' + U.esc(T.money(amt)) + '</div><div class="t">With 4 or more bidders, works were usually won about 10% below the estimate, against about 4% below with one bidder. The '
             + format(gap * 100, ".0f") + "% gap on " + U.esc(T.money(rec.get("estimated_value"))) + " is a rough sign, not a promise.</div></div>")
    else:
        U.md('<div class="tl-dark"><div class="k">POSSIBLE SAVING</div><div class="n">-</div><div class="t">The value is not written, so no saving can be shown. Tenders with no value written got fewer single bids in every period (S8).</div></div>')
with c4:
    with st.container(border=True):
        st.caption("Re-tender history (same title)")
        hist = T.retender_history(rec.get("title_key") or T.title_key(rec["title"]), rec.get("published_date"))
        if not is_new:
            hist = hist[hist["tender_id"] != tid]
        if len(hist) == 0:
            U.md('<div style="font-size:13px;color:#4a5f66;">No earlier tender with exactly the same title. This is a first try.</div>')
        else:
            h = '<div class="tl-time">'
            for _, r in hist.tail(4).iterrows():
                if r["cancelled"]:
                    what = "cancelled"
                elif pd.notna(r["number_of_bids"]):
                    what = "1 bid" if r["number_of_bids"] == 1 else str(int(r["number_of_bids"])) + " bids"
                else:
                    what = "bids not known"
                h += '<div class="e"><div class="d">' + T.nice_date(r["published_date"]) + '</div><div class="s">' + U.esc(r["tender_id"]) + " · " + what + "</div></div>"
            h += '<div class="e"><div class="d" style="color:#05556b;">' + T.nice_date(rec.get("published_date")) + ' · this tender</div><div class="s">'
            h += ("posted again after " + str(int(rec["days_since_same"])) + " days") if pd.notna(rec.get("days_since_same")) else ""
            U.md(h + "</div></div></div>")

# ---------------------------------------------------------------- tabs
tab_why, tab_odd, tab_sim, tab_what, tab_brief = st.tabs(["Why", "Unusual", "Similar", "What-if", "Review brief"])

with tab_why:
    t = T.shap_table(rec)
    t_nomonth = t[t["clue"] != "months_to_fy_end"]
    top = t_nomonth.iloc[0]
    head = top["name"] + (" pushes it up the most" if top["push"] > 0 else " pulls it down the most")
    U.md('<h3 style="margin:6px 0 0 0;font-size:21px;">' + U.esc(head) + '</h3><div class="tl-sub" style="font-size:13px;">Each bar is one clue (SHAP). Amber pushes the risk up, teal pushes it down. Hover for details.</div>')
    st.plotly_chart(U.shap_chart(t), width="stretch", key="td_shap")
    U.plain("\"Months left in the financial year\" is the same for every tender in a month, so it moves the whole month, not this tender's rank inside the month. Look at the other bars to see what makes this tender different.")
    U.plain("shap")

with tab_odd:
    if rec["unusual"] == 1:
        U.md('<h3 style="margin:6px 0 8px 0;font-size:21px;">Unusual: its clues are far from normal</h3>')
    else:
        U.md('<h3 style="margin:6px 0 8px 0;font-size:21px;">Not unusual. These are its clues furthest from normal</h3>')
    oc = T.odd_clues(rec, 3)
    cc = st.columns(3)
    for i, o in enumerate(oc):
        lab = "ODD CLUE " + str(i + 1) if (rec["unusual"] == 1 and i < 2) else "ALSO DIFFERENT"
        border = "2px solid #05556b" if (rec["unusual"] == 1 and i < 2) else "2px dashed #05556b"
        cc[i].markdown('<div class="tl-odd" style="border:' + border + ';"><div class="k">' + lab + '</div><div class="n">' + U.esc(o["name"]) + '</div><div style="font-size:14px;">This tender: <b>'
                       + U.esc(o["this"]) + "</b><br>Normal: " + U.esc(o["normal"]) + "</div></div>", unsafe_allow_html=True)
    sc_ = rec["anomaly_score"]
    cut = s["iforest_cutoff"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[sc_], y=["score"], orientation="h", marker_color=U.DEEP if rec["unusual"] == 1 else U.GREY,
                         hovertemplate="Oddness score %{x:.3f}<extra></extra>"))
    fig.add_vline(x=cut, line_dash="dash", line_color=U.NAVY, annotation_text="unusual line " + format(cut, ".3f"), annotation_position="top")
    U.base_layout(fig, 120)
    fig.update_xaxes(range=[0.3, 0.72])
    fig.update_yaxes(visible=False)
    st.plotly_chart(fig, width="stretch", key="td_oddbar", config={"displayModeBar": False})
    st.caption("Oddness score from the Isolation Forest. The top 5% of training tenders sit right of the dashed line.")
    U.plain("unusual")

with tab_sim:
    sim = T.similar_tenders(rec["title"], rec.get("published_date"), 5)
    if len(sim) == 0:
        st.info("No earlier tender has a similar title.")
    else:
        ones = int((sim["single_bid"] == 1).sum())
        U.md('<h3 style="margin:6px 0 0 0;font-size:21px;">' + str(len(sim)) + " similar earlier tenders: " + str(ones) + ' got only one bid</h3><div class="tl-sub" style="font-size:13px;">Matched on title words (TF-IDF). Only tenders published before this one, so nothing from the future.</div>')
        for _, r in sim.iterrows():
            a_, b_, c_, d_ = st.columns([5, 1.2, 1.1, 1])
            a_.markdown("<b>" + U.esc(str(r["title"])[:120]) + "</b><br><span style='font-size:12px;color:#4a5f66;'>" + U.esc(r["dept_main"]) + " · " + T.money(r["estimated_value"]) + "</span>", unsafe_allow_html=True)
            b_.markdown("<span style='font-size:13px;'>" + T.nice_date(r["published_date"]) + "<br>" + format(r["match"] * 100, ".0f") + "% match</span>", unsafe_allow_html=True)
            nb = r["number_of_bids"]
            col = U.AMBER if nb == 1 else U.GREY
            c_.markdown('<span class="tl-pill" style="background:' + col + ';">' + ("1 bid" if nb == 1 else str(int(nb)) + " bids") + "</span>", unsafe_allow_html=True)
            if r["tender_id"] in set(lst["tender_id"]):
                if d_.button("Open", key="sim_" + r["tender_id"]):
                    U.open_tender(r["tender_id"])

with tab_what:
    U.md('<h3 style="margin:6px 0 0 0;font-size:21px;">What if the tender was posted differently?</h3><div class="tl-sub" style="font-size:13px;">Change the boxes. The model scores the tender again, live. Department and re-tender stay fixed: they are facts about the past.</div>')
    w1, w2, w3 = st.columns(3)
    days0 = int(rec["bid_window_days"])
    new_days = w1.slider("Days to submit bids", 1, 90, min(max(days0, 1), 90), key="wi_days_" + str(tid))
    val0 = rec.get("estimated_value")
    written = w2.toggle("Value written on the tender", value=pd.notna(val0), key="wi_written_" + str(tid))
    lakh0 = float(val0 / 1e5) if pd.notna(val0) else 50.0
    new_lakh = w3.number_input("Tender value (Rs lakh)", min_value=0.1, max_value=50000.0, value=round(lakh0, 1), step=5.0, disabled=not written,
                               key="wi_val_" + str(tid))
    base = T.what_if(rec, {})
    ch = {"bid_window_days": new_days}
    if written:
        v = new_lakh * 1e5
        ch["log_value"] = math.log1p(v)
        ch["value_missing"] = 0
        if pd.notna(rec.get("emd_amount")):
            ch["emd_ratio"] = rec["emd_amount"] / v
    else:
        ch["log_value"] = s["log_value_median"]
        ch["value_missing"] = 1
    after = T.what_if(rec, ch)
    m1, m2, m3 = st.columns(3)
    m1.metric("Model score now", format(base["risk"], ".3f"))
    m2.metric("Model score after change", format(after["risk"], ".3f"), format(after["risk"] - base["risk"], "+.3f"), delta_color="inverse")
    with m3:
        U.md('<div class="tl-card"><div style="font-size:13px;color:#4a5f66;font-weight:600;">Band</div><div style="margin-top:6px;">' + U.band_pill(base["band"]) + " → " + U.band_pill(after["band"]) + "</div></div>")
    ta = T.shap_table(after)
    st.plotly_chart(U.shap_chart(ta), width="stretch", key="wi_shap")
    st.caption("How the model sees it, not proof that the change brings more bidders.")

with tab_brief:
    briefs = st.session_state.setdefault("brief", {})
    bl, br = st.columns([2.2, 1])
    with bl:
        x1, x2 = st.columns([1.4, 1])
        lang = x2.segmented_control("Language", ["English", "हिन्दी"], default="English", key="td_lang", label_visibility="collapsed")
        code = "hi" if lang == "हिन्दी" else "en"
        if x1.button("Write brief with AI", type="primary", key="td_ai", width="stretch"):
            with st.spinner("Writing the brief from the facts only…"):
                briefs[(tid, code)] = T.ai_brief(rec, hindi=(code == "hi"))
        if (tid, code) not in briefs:
            briefs[(tid, code)] = (T.template_brief(rec, hindi=(code == "hi")), "Template")
        text, source = briefs[(tid, code)]
        U.md('<div class="tl-brief">' + U.esc(text) + "</div>")
        found, total, missing = T.fact_check(text, rec)
        ok = len(missing) == 0
        badge = ("✓ Fact check: all " + str(total) + " numbers are in the facts") if ok else ("⚠ Fact check: " + str(found) + " of " + str(total) + " numbers found. Not in facts: " + ", ".join(missing))
        st.caption("Written by: " + source + "  ·  " + badge)
        if not T.ai_available():
            st.caption("No AI key is set yet, so the rule-based template writes the brief. Add a free Gemini or Groq key to switch on the AI.")
    with br:
        facts = T.brief_facts(rec)
        h = '<div class="tl-card" style="background:#f7f2e2;"><div style="font-size:12px;color:#05556b;font-weight:700;margin-bottom:6px;">FACTS GIVEN TO THE AI</div><div style="font-size:13px;line-height:1.55;">'
        for k_, v_ in facts.items():
            h += "<b>" + U.esc(k_) + ":</b> " + U.esc(v_) + "<br>"
        U.md(h + "</div></div>")

# ---------------------------------------------------------------- note
notes = st.session_state.setdefault("notes", {})
note = st.text_area("My note (stays in this visit, download it from the side menu)", value=notes.get(tid, ""),
                    placeholder="e.g. Asked the office why bidders got only a few days.", key="note_" + str(tid))
if note != notes.get(tid, ""):
    notes[tid] = note
