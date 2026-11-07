"""Page 6 · Score new tenders: type one tender (Predict) or upload a CSV of many."""
import hashlib
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import tl_core as T
import tl_ui as U

s = T.load_settings()
rates = T.load_dept_rates()
dept_list = sorted(rates.keys())

U.header("Score new tenders", "Type in a new tender, press Predict, and see its full page",
         "The app builds the 7 clues exactly like my S4 notebook, runs the saved model live, and opens the complete tender page.")

tab_one, tab_many = st.tabs(["Predict one tender", "Upload a CSV of many tenders"])


def open_new(row):
    """Store the predicted tender and jump to the Tender detail page."""
    rec = row.to_dict()
    rec["source"] = "new"
    if not rec.get("tender_id") or pd.isna(rec.get("tender_id")):
        rec["tender_id"] = "NEW-" + hashlib.md5(str(rec["title"]).encode()).hexdigest()[:6].upper()
    rec["month_key"] = None
    st.session_state["new_record"] = rec
    st.switch_page("views/3_tender_detail.py")


EXAMPLES = {
    "Community hall, 2-day window, re-posted": dict(dept="Public Works Building and NH Department",
        title="Construction of Community hall near Maleghar Madrassa, Karimganj under Indo Bangla Border Areas of Karimganj District under BADP for the year 202122. GrII",
        value=8.9, written=True, pub=date(2023, 1, 19), last=date(2023, 1, 21), emd=17804.0, fee=500.0, period=60),
    "Big road work, normal window": dict(dept="Public Works Roads Department",
        title="Improvement of road from Jorhat town to Titabar with RCC bridge", value=850.0, written=True,
        pub=date(2023, 2, 10), last=date(2023, 3, 2), emd=170000.0, fee=5000.0, period=365),
    "Supply tender, no value written": dict(dept="National Health Mission",
        title="Supply of medical equipment for district hospitals", value=0.0, written=False,
        pub=date(2023, 3, 20), last=date(2023, 4, 5), emd=None, fee=1000.0, period=90),
}

with tab_one:
    ex = st.pills("Fill an example", list(EXAMPLES.keys()), key="sn_example")
    e = EXAMPLES.get(ex) if ex else None
    with st.form("one_tender"):
        a, b = st.columns([1.2, 2])
        dsel = a.selectbox("Department", dept_list + ["Other / new department"],
                           index=(dept_list.index(e["dept"]) if e else dept_list.index("Public Works Roads Department")), key="f_dept_" + str(ex))
        title = b.text_input("Tender title", value=(e["title"] if e else ""), placeholder="e.g. Construction of community hall at …", key="f_title_" + str(ex))
        c1, c2, c3 = st.columns(3)
        written = c1.checkbox("Value is written on the tender", value=(e["written"] if e else True), key="f_written_" + str(ex))
        lakh = c2.number_input("Tender value (Rs lakh)", min_value=0.0, value=(float(e["value"]) if e else 25.0), step=1.0, key="f_val_" + str(ex))
        pub = c3.date_input("Published date", value=(e["pub"] if e else date(2023, 1, 16)), key="f_pub_" + str(ex))
        c4, c5, c6, c7 = st.columns(4)
        last = c4.date_input("Last date for bids", value=(e["last"] if e else date(2023, 2, 2)), key="f_last_" + str(ex))
        emd = c5.number_input("EMD (Rs, 0 = not given)", min_value=0.0, value=(float(e["emd"]) if e and e["emd"] else 0.0), step=1000.0, key="f_emd_" + str(ex))
        fee = c6.number_input("Tender fee (Rs, 0 = not given)", min_value=0.0, value=(float(e["fee"]) if e else 0.0), step=100.0, key="f_fee_" + str(ex))
        period = c7.number_input("Work period (days, 0 = not given)", min_value=0, value=(int(e["period"]) if e else 0), step=10, key="f_per_" + str(ex))
        go = st.form_submit_button("Predict", type="primary", width="stretch")
    if go:
        if not title.strip():
            st.error("Please type a tender title.")
        else:
            raw = pd.DataFrame([{
                "department": dsel if dsel != "Other / new department" else "Other",
                "title": title,
                "estimated_value": lakh * 1e5 if written and lakh > 0 else None,
                "published_date": pd.Timestamp(pub) + pd.Timedelta(hours=12),
                "last_date": pd.Timestamp(last) + pd.Timedelta(hours=12),
                "emd_amount": emd if emd > 0 else None,
                "tender_fee": fee if fee > 0 else None,
                "work_period_days": period if period > 0 else None,
            }])
            with st.spinner("Building the 7 clues and running the model…"):
                out = T.predict_new(raw)
            open_new(out.iloc[0])
    U.plain("An unknown department gets the overall training rate (36.1%). Blank EMD, fee or work period are filled with the training medians, like in S5.")

with tab_many:
    st.markdown("**Step 1.** Download the template (empty) or my sample file (40 real Assam tenders from April–May 2023 whose bids are not known).")
    d1, d2 = st.columns(2)
    d1.download_button("Download blank template", open(T.DATA + "/upload_template.csv", "rb").read(), "tenderlens_upload_template.csv", "text/csv", width="stretch")
    d2.download_button("Download sample file (40 tenders)", open(T.DATA + "/sample_new_tenders.csv", "rb").read(), "tenderlens_sample_new_tenders.csv", "text/csv", width="stretch")
    st.markdown("**Step 2.** Upload the filled file, or use the sample straight away.")
    up = st.file_uploader("Upload a CSV", type=["csv"], key="sn_up")
    use_sample = st.toggle("Use the sample file", key="sn_sample")
    raw = None
    if up is not None:
        raw = pd.read_csv(up)
    elif use_sample:
        raw = pd.read_csv(T.DATA + "/sample_new_tenders.csv")
    if raw is not None:
        need = ["department", "title", "estimated_value", "published_date", "last_date"]
        miss = [c for c in need if c not in raw.columns]
        if miss:
            st.error("These columns are missing: " + ", ".join(miss) + ". Please use the template.")
        else:
            for c in ["tender_id", "emd_amount", "tender_fee", "work_period_days"]:
                if c not in raw.columns:
                    raw[c] = None
            bad = pd.to_datetime(raw["published_date"], errors="coerce").isna().sum()
            if bad:
                st.warning(str(bad) + " rows have no readable published date; they are left out.")
                raw = raw[pd.to_datetime(raw["published_date"], errors="coerce").notna()]
            with st.spinner("Scoring " + str(len(raw)) + " tenders…"):
                out = T.predict_new(raw)
            st.session_state["sn_out"] = out
            k = st.columns(4)
            k[0].markdown(U.kpi("Tenders scored", str(len(out))), unsafe_allow_html=True)
            k[1].markdown(U.kpi("High band", str((out["band"] == "High").sum()), "", U.AMBER), unsafe_allow_html=True)
            k[2].markdown(U.kpi("Unusual", str(int(out["unusual"].sum())), "", U.DEEP), unsafe_allow_html=True)
            k[3].markdown(U.kpi("Check first (P1)", str((out["check"] == "P1").sum()), "", U.GOLD, U.GOLD), unsafe_allow_html=True)
            show = out.sort_values("risk", ascending=False).reset_index(drop=True)
            view = pd.DataFrame({
                "Tender": show["title"].str.slice(0, 110), "Department": show["dept_main"],
                "Value": [T.money(x) for x in show["estimated_value"]], "Band": show["band"], "Check": show["check"],
                "Unusual": ["◆" if u == 1 else "" for u in show["unusual"]], "Data alert": show["dq"],
                "Re-tender": ["↻" if r == 1 else "" for r in show["retender_60d"]],
            })
            st.caption("Click a row to open its full tender page.")
            ev = st.dataframe(view, width="stretch", hide_index=True, on_select="rerun", selection_mode="single-row", key="sn_table", height=420)
            if ev and ev.selection and ev.selection.rows:
                open_new(show.iloc[ev.selection.rows[0]])
            cols = ["tender_id", "title", "dept_main", "estimated_value", "published_date", "last_date", "band", "check", "unusual", "dq", "retender_60d", "risk"]
            st.download_button("Download scored file", show[[c for c in cols if c in show.columns]].to_csv(index=False).encode(),
                               "tenderlens_scored.csv", "text/csv", type="primary")
    U.plain("Each new tender is compared with list tenders from the same month of the year, because the month clue moves whole months up or down.")
