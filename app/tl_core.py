"""TenderLens core: loads the saved data and models, and does every calculation the pages need.

Pages never do heavy maths themselves; they call the small functions in this file.
"""
import json
import math
import os
import re
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "app_data")
MODELS = os.path.join(HERE, "models")

# Plain names for every clue (used everywhere on screen)
CLUE_NAMES = {
    "dept_rate": "Department's past single-bid rate",
    "log_value": "Tender value",
    "value_missing": "Value not written",
    "bid_window_days": "Days to submit bids",
    "months_to_fy_end": "Months left in the financial year",
    "same_day_lot": "Lot posted the same day",
    "retender_60d": "Re-tender within 60 days",
    "emd_ratio": "EMD as a share of value",
    "log_fee": "Tender fee",
    "work_period_days": "Work period (days)",
}

# One simple sentence per idea, shown in plain-words mode
PLAIN = {
    "single_bid": "A single-bid tender is a job where only one company applied, so nobody competed on price.",
    "band": "Each month's tenders are lined up from most to least risky. The top 20% are High, the next 30% Medium, the rest Low.",
    "unusual": "Unusual means this tender's mix of clues looks very different from normal tenders (found by an Isolation Forest).",
    "check": "Check first (P1) = High band and either unusual or worth Rs 1 crore or more. P2 = High only or unusual only. P3 = the rest.",
    "shap": "SHAP splits the model's decision into one push per clue. Amber bars push the risk up, teal bars push it down.",
    "dq": "A data quality alert means something in the tender looks wrong or strange, like a 2-day bid window or a tiny value.",
    "drift": "Drift means new tenders look different from the ones the model learned from, so it may be less reliable.",
    "fair": "Fair replay uses the scores the model gave at that time, before anyone knew how many bids came in.",
    "emd": "EMD is the deposit a company pays to show it is serious about bidding.",
}

CLUE_HI = {
    "dept_rate": "विभाग की पिछली सिंगल-बिड दर",
    "log_value": "टेंडर का मूल्य",
    "value_missing": "मूल्य नहीं लिखा",
    "bid_window_days": "बोली के दिन",
    "months_to_fy_end": "वित्त वर्ष के बचे महीने",
    "same_day_lot": "उसी दिन का लॉट",
    "retender_60d": "60 दिन में दोबारा टेंडर",
    "emd_ratio": "EMD का हिस्सा",
    "log_fee": "टेंडर फीस",
    "work_period_days": "काम की अवधि (दिन)",
}

BAND_COLOURS = {"High": "#e0a000", "Medium": "#0aa6a6", "Low": "#b8c7cc"}


# ---------------------------------------------------------------- loading
@st.cache_resource(show_spinner=False)
def load_models():
    """Load the S7 LogReg + scaler and the S8 Isolation Forest once."""
    lr = joblib.load(os.path.join(MODELS, "tenderlens_logreg.joblib"))
    sc = joblib.load(os.path.join(MODELS, "tenderlens_scaler.joblib"))
    iso = joblib.load(os.path.join(MODELS, "tenderlens_iforest.joblib"))
    return lr, sc, iso


@st.cache_data(show_spinner=False)
def load_settings():
    with open(os.path.join(DATA, "settings.json")) as fh:
        return json.load(fh)


@st.cache_data(show_spinner=False)
def load_tenders():
    dates = ["published_date", "last_date", "bid_opening_date"]
    df = pd.read_csv(os.path.join(DATA, "tenders.csv"), parse_dates=dates)
    df["dq"] = df["dq"].fillna("")
    return df


@st.cache_data(show_spinner=False)
def load_labelled():
    return pd.read_csv(os.path.join(DATA, "labelled.csv"), parse_dates=["published_date"])


@st.cache_data(show_spinner=False)
def load_history():
    h = pd.read_csv(os.path.join(DATA, "history.csv"), parse_dates=["published_date"])
    h["title_key"] = h["title_key"].fillna("")
    return h


@st.cache_data(show_spinner=False)
def load_table(name):
    return pd.read_csv(os.path.join(DATA, name))


@st.cache_data(show_spinner=False)
def load_dept_rates():
    d = pd.read_csv(os.path.join(DATA, "dept_rate_train.csv"))
    return dict(zip(d["dept_main"], d["dept_rate"]))


@st.cache_resource(show_spinner=False)
def title_index():
    """TF-IDF on the titles of all 6,790 labelled tenders (for 'similar earlier tenders')."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    lab = load_labelled()
    vec = TfidfVectorizer(stop_words="english", min_df=2, ngram_range=(1, 2))
    mat = vec.fit_transform(lab["title"].fillna(""))
    return vec, mat


# ---------------------------------------------------------------- formatting
def money(v):
    """Rs amount in lakh / crore, the way Indian offices write it."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "Not written"
    if v >= 1e7:
        return "Rs " + format(v / 1e7, ",.2f") + " crore"
    if v >= 1e5:
        return "Rs " + format(v / 1e5, ",.1f") + " lakh"
    return "Rs " + format(v, ",.0f")


def nice_date(d):
    if d is None or pd.isna(d):
        return "Not given"
    return pd.Timestamp(d).strftime("%d %b %Y")


def title_key(title):
    return " ".join(str(title).lower().split())


def clue_display(clue, value):
    """Show a clue's value in everyday units."""
    if value is None or pd.isna(value):
        return "-"
    if clue == "log_value":
        return money(math.expm1(value))
    if clue == "log_fee":
        return "Rs " + format(math.expm1(value), ",.0f")
    if clue == "dept_rate":
        return format(value * 100, ".1f") + "%"
    if clue == "emd_ratio":
        return format(value * 100, ".1f") + "%"
    if clue in ("value_missing", "same_day_lot", "retender_60d"):
        return "Yes" if value >= 0.5 else "No"
    return format(value, ",.0f")


# ---------------------------------------------------------------- scoring new tenders
def months_to_fy_end(month):
    """Months left until the financial year ends in March (Jan = 2, Mar = 0, Apr = 11)."""
    return (3 - month) % 12


def build_clues(new, history=None):
    """Turn raw tender facts into the 7 model clues + 3 Isolation Forest clues, exactly like S4/S5.

    new: DataFrame with department, title, estimated_value, published_date, last_date,
         emd_amount, tender_fee, work_period_days (blanks allowed).
    """
    s = load_settings()
    rates = load_dept_rates()
    if history is None:
        history = load_history()
    df = new.copy()
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
    df["last_date"] = pd.to_datetime(df["last_date"], errors="coerce")
    for c in ["estimated_value", "emd_amount", "tender_fee", "work_period_days"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["dept_main"] = df["department"].fillna("").astype(str).str.strip()
    df["title"] = df["title"].fillna("").astype(str)

    # 1 department's past single-bid rate (unknown department -> overall training rate)
    df["dept_rate"] = df["dept_main"].map(rates).fillna(s["overall_train_rate"])
    # 2-3 value and value missing
    df["value_missing"] = df["estimated_value"].isna().astype(int)
    df["log_value"] = np.log1p(df["estimated_value"]).fillna(s["log_value_median"])
    # 4 days to submit bids
    df["bid_window_days"] = (df["last_date"] - df["published_date"]).dt.days
    df["bid_window_days"] = df["bid_window_days"].fillna(s["bid_window_median"])
    # 5 months left in the financial year
    df["months_to_fy_end"] = df["published_date"].dt.month.map(months_to_fy_end).fillna(6).astype(int)
    # 6-7 same-day lot and re-tender: days since an earlier tender with the same title
    df["title_key"] = df["title"].map(title_key)
    past = history[["tender_id", "title_key", "published_date"]]
    has_id = "tender_id" in df.columns
    days = []
    for i, row in df.iterrows():
        earlier = past[(past["title_key"] == row["title_key"]) & (past["published_date"] <= row["published_date"])]
        if has_id:
            earlier = earlier[earlier["tender_id"] != row["tender_id"]]
        same_batch = df[(df["title_key"] == row["title_key"]) & (df["published_date"] < row["published_date"])]
        dates = pd.concat([earlier["published_date"], same_batch["published_date"]])
        if len(dates) == 0 or pd.isna(row["published_date"]):
            days.append(np.nan)
        else:
            days.append((row["published_date"] - dates.max()).days)
    df["days_since_same"] = days
    df["same_day_lot"] = (df["days_since_same"] == 0).astype(int)
    df["retender_60d"] = df["days_since_same"].between(1, 60).astype(int)
    # Isolation Forest extra clues
    fill = s["fill"]
    df["emd_ratio"] = (df["emd_amount"] / df["estimated_value"]).replace([np.inf, -np.inf], np.nan).fillna(fill["emd_ratio"])
    df["log_fee"] = np.log1p(df["tender_fee"]).fillna(fill["log_fee"])
    df["work_period_days"] = df["work_period_days"].fillna(fill["work_period_days"])
    return df


def score(df):
    """Add risk score, SHAP pushes, unusual flag and the odd clues to a table that already has the clues."""
    s = load_settings()
    lr, sc, iso = load_models()
    clues = s["clues"]
    X = sc.transform(df[clues])
    out = df.copy()
    out["risk"] = lr.predict_proba(X)[:, 1]
    shap = lr.coef_[0] * (X - np.array(s["X_mean"]))
    for i, c in enumerate(clues):
        out["shap_" + c] = shap[:, i]
    ic = s["iforest_clues"]
    out["anomaly_score"] = -iso.score_samples(out[ic])
    out["unusual"] = (out["anomaly_score"] >= s["iforest_cutoff"]).astype(int)
    med = pd.Series(s["iforest_median"])
    sd = pd.Series(s["iforest_std"])
    z = ((out[ic] - med[ic]) / sd[ic]).abs()
    order = np.argsort(-z.values, axis=1)
    out["odd_1"] = [ic[o[0]] for o in order]
    out["odd_2"] = [ic[o[1]] for o in order]
    out["odd_3"] = [ic[o[2]] for o in order]
    return out


def band_new(df):
    """Give new tenders a band by comparing them with list tenders from the same month of the year.

    The 'months left in the financial year' clue moves whole months, so a January tender is
    compared with January tenders. For June-September (not in the list) the S7 fixed cut-offs are used.
    """
    s = load_settings()
    lst = load_tenders()
    bands, ranks, groups, pcts = [], [], [], []
    for _, r in df.iterrows():
        comp = lst[lst["months_to_fy_end"] == r["months_to_fy_end"]]
        if len(comp) >= 30:
            higher = int((comp["risk"] > r["risk"]).sum())
            pct = (higher + 1) / (len(comp) + 1)
            band = "High" if pct <= 0.2 else ("Medium" if pct <= 0.5 else "Low")
            ranks.append(higher + 1)
            groups.append(len(comp))
            pcts.append(pct)
        else:
            cut = s["band_cutoffs"]
            band = "High" if r["risk"] >= cut["High"] else ("Medium" if r["risk"] >= cut["Medium"] else "Low")
            ranks.append(None)
            groups.append(None)
            pcts.append(None)
        bands.append(band)
    out = df.copy()
    out["band"] = bands
    out["rank"] = ranks
    out["n_month"] = groups
    out["pct"] = pcts
    big = out["estimated_value"].fillna(0) >= 1e7
    high = out["band"] == "High"
    odd = out["unusual"] == 1
    out["check"] = np.where(high & (odd | big), "P1", np.where(high | odd, "P2", "P3"))
    out["dq"] = out.apply(dq_alerts, axis=1)
    return out


def dq_alerts(r):
    """The 5 data quality rules (S10 decision 4). 'Value not written' is info, not an error."""
    out = []
    v = r.get("estimated_value")
    w = r.get("bid_window_days")
    e = r.get("emd_amount")
    if pd.notna(v) and v < 10000:
        out.append("Value below Rs 10,000")
    if pd.notna(w) and w < 3:
        out.append("Only " + str(int(w)) + " days to bid")
    if pd.notna(w) and w > 180:
        out.append("Bid window over 180 days")
    if pd.notna(e) and pd.notna(v) and e > v:
        out.append("EMD bigger than the value")
    if pd.notna(r.get("last_date")) and pd.notna(r.get("published_date")) and r["last_date"] < r["published_date"]:
        out.append("Last date before published date")
    return "; ".join(out)


def predict_new(raw):
    """Full pipeline for typed-in or uploaded tenders: clues -> score -> band -> alerts."""
    return band_new(score(build_clues(raw)))


def what_if(record, changes):
    """Re-score one tender after changing some clues (live model call)."""
    s = load_settings()
    row = {c: record[c] for c in s["clues"] + s["iforest_clues"]}
    row.update(changes)
    row["estimated_value"] = record.get("estimated_value")
    df = pd.DataFrame([row])
    out = score(df)
    out["months_to_fy_end"] = record["months_to_fy_end"]
    out["published_date"] = record.get("published_date")
    out["last_date"] = record.get("last_date")
    out["emd_amount"] = record.get("emd_amount")
    return band_new(out).iloc[0]


# ---------------------------------------------------------------- tender extras
def similar_tenders(title, before, k=5):
    """5 earlier labelled tenders with the most similar title words (TF-IDF), with their bid counts."""
    from sklearn.metrics.pairwise import cosine_similarity
    vec, mat = title_index()
    lab = load_labelled()
    q = vec.transform([str(title)])
    sim = cosine_similarity(q, mat).ravel()
    mask = (lab["published_date"] < pd.Timestamp(before)).values if pd.notna(before) else np.ones(len(lab), bool)
    cand = lab[mask].copy()
    cand["match"] = sim[mask]
    cand = cand[cand["match"] > 0.05].sort_values("match", ascending=False).head(k)
    return cand


def retender_history(key, upto):
    """Every tender in the full 39,411 history with the same title, up to this tender's date."""
    h = load_history()
    g = h[(h["title_key"] == key) & (key != "")].copy()
    if pd.notna(upto):
        g = g[g["published_date"] <= pd.Timestamp(upto) + pd.Timedelta(days=1)]
    return g.sort_values("published_date")


def possible_saving(value):
    """S8: median award ratio 0.961 with one bid vs 0.900 with 4+ bids -> about 6% of the value."""
    s = load_settings()
    if value is None or pd.isna(value):
        return None
    gap = s["ratio_one_bid"] - s["ratio_four_plus"]
    return value * gap, gap


def shap_table(record):
    s = load_settings()
    rows = []
    for c in s["clues"]:
        rows.append({"clue": c, "name": CLUE_NAMES[c], "push": float(record["shap_" + c]), "value": clue_display(c, record[c])})
    t = pd.DataFrame(rows)
    t["size"] = t["push"].abs()
    return t.sort_values("size", ascending=False)


def odd_clues(record, n=3):
    s = load_settings()
    out = []
    for k in ["odd_1", "odd_2", "odd_3"][:n]:
        c = record[k]
        normal = s["iforest_median"][c]
        out.append({"clue": c, "name": CLUE_NAMES[c], "this": clue_display(c, record[c]), "normal": clue_display(c, normal)})
    return out


def top_reason_sentence(record):
    t = shap_table(record)
    t = t[t["clue"] != "months_to_fy_end"]
    top = t.iloc[0]
    way = "pushes it up" if top["push"] > 0 else "pulls it down"
    return top["name"] + " (" + top["value"] + ") " + way + " the most."


# ---------------------------------------------------------------- GenAI review brief
def brief_facts(record):
    """The ONLY facts the AI is allowed to use."""
    t = shap_table(record)
    t = t[t["clue"] != "months_to_fy_end"]
    up = t[t["push"] > 0].head(2)
    facts = {}
    facts["Tender"] = str(record["title"])[:180]
    facts["Department"] = str(record["dept_main"])
    facts["Value"] = money(record.get("estimated_value"))
    facts["Published"] = nice_date(record.get("published_date"))
    facts["Days to submit bids"] = str(int(record["bid_window_days"]))
    facts["Risk band"] = record["band"]
    if record.get("rank") is not None and pd.notna(record.get("rank")) and record.get("n_month"):
        facts["Rank"] = str(int(record["rank"])) + " of " + str(int(record["n_month"]))
    facts["Check level"] = record["check"]
    reasons = []
    for _, r in up.iterrows():
        reasons.append(r["name"] + " = " + r["value"])
    facts["Main reasons (SHAP)"] = "; ".join(reasons) if reasons else "no clue pushes it up strongly"
    facts["Unusual"] = "yes" if record["unusual"] == 1 else "no"
    if record["unusual"] == 1:
        oc = odd_clues(record, 2)
        facts["Odd clues"] = "; ".join([o["name"] + " " + o["this"] + " (normal " + o["normal"] + ")" for o in oc])
    if record.get("dq"):
        facts["Data alert"] = record["dq"]
    facts["Re-tender within 60 days"] = "yes" if record["retender_60d"] == 1 else "no"
    return facts


def template_brief(record, hindi=False):
    """Written by rules, used when no AI key is set or the AI call fails."""
    f = brief_facts(record)
    rank = (" (rank " + f["Rank"] + ")") if "Rank" in f else ""
    if not hindi:
        txt = ("This tender, \"" + f["Tender"][:90] + "\" from " + f["Department"] + " (" + f["Value"] + "), is in the "
               + f["Risk band"] + " band" + rank + " with check level " + f["Check level"] + ". ")
        txt += "The main reasons are: " + f["Main reasons (SHAP)"] + ". "
        txt += "Bidders had " + f["Days to submit bids"] + " days to submit. "
        if f["Unusual"] == "yes":
            txt += "It is also unusual: " + f["Odd clues"] + ". "
        if "Data alert" in f:
            txt += "Data alert: " + f["Data alert"] + ". "
        txt += "Suggested step: look at why competition may be low here. This is a screening note, not a finding of wrongdoing."
        return txt
    band_hi = {"High": "हाई", "Medium": "मीडियम", "Low": "लो"}[f["Risk band"]]
    yes_no = {"Yes": "हाँ", "No": "नहीं"}
    rank_hi = ""
    if "Rank" in f:
        a, b = f["Rank"].split(" of ")
        rank_hi = " (" + b + " में से " + a + "वाँ स्थान)"
    t = shap_table(record)
    t = t[(t["clue"] != "months_to_fy_end") & (t["push"] > 0)].head(2)
    reasons = []
    for _, r in t.iterrows():
        reasons.append(CLUE_HI[r["clue"]] + " = " + yes_no.get(r["value"], r["value"]))
    txt = ("यह टेंडर (" + f["Department"] + ", " + f["Value"] + ") " + band_hi + " बैंड में है" + rank_hi + ", जाँच स्तर " + f["Check level"] + "। ")
    if reasons:
        txt += "मुख्य कारण: " + "; ".join(reasons) + "। "
    txt += "बोली के लिए " + f["Days to submit bids"] + " दिन मिले। "
    if f["Unusual"] == "yes":
        oc = odd_clues(record, 2)
        odd = []
        for o in oc:
            odd.append(CLUE_HI[o["clue"]] + " " + yes_no.get(o["this"], o["this"]) + " (सामान्य " + yes_no.get(o["normal"], o["normal"]) + ")")
        txt += "यह टेंडर असामान्य भी है: " + "; ".join(odd) + "। "
    if "Data alert" in f:
        txt += "डेटा चेतावनी: " + f["Data alert"] + "। "
    txt += "सुझाव: देखें कि यहाँ प्रतिस्पर्धा कम क्यों हो सकती है। यह केवल जाँच के लिए संकेत है, गलत काम का सबूत नहीं।"
    return txt


def _secret(name):
    try:
        return st.secrets.get(name)
    except Exception:
        return os.environ.get(name)


def ai_available():
    return bool(_secret("GEMINI_API_KEY") or _secret("GROQ_API_KEY"))


def ai_brief(record, hindi=False):
    """Ask a free LLM (Gemini or Groq) for a 4-5 line brief using ONLY the facts. Returns (text, source)."""
    import requests
    facts = brief_facts(record)
    lines = "\n".join(["- " + k + ": " + v for k, v in facts.items()])
    lang = "Hindi (Devanagari script)" if hindi else "plain simple English"
    prompt = ("You write short review briefs for government auditors. Using ONLY the facts below, write 4-5 short sentences in "
              + lang + ". Say which band the tender is in and why, mention anything unusual or any data alert, and end with one "
              "suggested check. Do not invent any number, name or fact that is not in the list. Never say fraud or corruption; "
              "say it is a screening note, not proof of wrongdoing.\n\nFACTS:\n" + lines)
    gk = _secret("GEMINI_API_KEY")
    qk = _secret("GROQ_API_KEY")
    try:
        if gk:
            model = _secret("GEMINI_MODEL") or "gemini-2.0-flash"
            url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + gk
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}}, timeout=25)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip(), "AI (Gemini)"
        if qk:
            model = _secret("GROQ_MODEL") or "llama-3.3-70b-versatile"
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": "Bearer " + qk},
                              json={"model": model, "temperature": 0.2, "messages": [{"role": "user", "content": prompt}]}, timeout=25)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip(), "AI (Groq)"
    except Exception as e:
        return template_brief(record, hindi), "Template (AI call failed: " + type(e).__name__ + ")"
    return template_brief(record, hindi), "Template (no AI key set)"


def fact_check(text, record):
    """Grounding check: every number in the brief must appear in the facts. Returns (found, total, missing)."""
    facts = brief_facts(record)
    blob = " ".join(facts.values()).replace(",", "")
    nums = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
    nums = [n for n in nums if n not in ("0",)]
    missing = [n for n in nums if n not in blob]
    return len(nums) - len(missing), len(nums), missing


# ---------------------------------------------------------------- one-page PDF
def tender_pdf(record, brief_text=None, note=""):
    from fpdf import FPDF

    def clean(t):
        t = str(t).replace("–", "-").replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"').replace("₹", "Rs ")
        return t.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, 12)
    pdf.add_page()
    pdf.set_fill_color(2, 21, 31)
    pdf.rect(0, 0, 210, 26, "F")
    pdf.set_text_color(255, 221, 123)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(12, 7)
    pdf.cell(0, 8, "TenderLens - tender review sheet")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(220, 230, 233)
    pdf.set_xy(12, 16)
    pdf.cell(0, 6, clean("Screening support, not fraud detection. Made " + datetime.now().strftime("%d %b %Y")))
    pdf.set_text_color(2, 21, 31)
    pdf.set_xy(12, 32)
    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(186, 6, clean(record["title"])[:300])
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, clean(str(record.get("tender_id", "New tender")) + "  |  " + str(record["dept_main"])))
    pdf.ln(2)
    rank = ""
    if record.get("rank") is not None and pd.notna(record.get("rank")) and record.get("n_month"):
        rank = " (rank " + str(int(record["rank"])) + " of " + str(int(record["n_month"])) + ")"
    rows = [
        ("Risk band", record["band"] + rank),
        ("Check level", record["check"]),
        ("Unusual", "Yes" if record["unusual"] == 1 else "No"),
        ("Data alert", record.get("dq") or "None"),
        ("Value", money(record.get("estimated_value"))),
        ("Published", nice_date(record.get("published_date"))),
        ("Last date for bids", nice_date(record.get("last_date"))),
        ("Days to submit bids", str(int(record["bid_window_days"]))),
    ]
    for k, v in rows:
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(48, 6, clean(k))
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, clean(v), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Why (SHAP pushes, + means more risk)", new_x="LMARGIN", new_y="NEXT")
    t = shap_table(record)
    mx = max(0.05, t["size"].max())
    for _, r in t.iterrows():
        y = pdf.get_y()
        pdf.set_x(12)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(70, 6, clean(r["name"] + " (" + r["value"] + ")"))
        w = 50 * r["size"] / mx
        if r["push"] >= 0:
            pdf.set_fill_color(224, 160, 0)
            pdf.rect(132, y + 1, max(w, 0.5), 4, "F")
        else:
            pdf.set_fill_color(10, 166, 166)
            pdf.rect(132 - max(w, 0.5), y + 1, max(w, 0.5), 4, "F")
        pdf.set_draw_color(2, 21, 31)
        pdf.line(132, y, 132, y + 6)
        pdf.set_xy(184, y)
        pdf.cell(0, 6, format(r["push"], "+.3f"), new_x="LMARGIN", new_y="NEXT")
    if record["unusual"] == 1:
        pdf.ln(1)
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Odd clues (Isolation Forest)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for o in odd_clues(record, 2):
            pdf.set_x(12)
            pdf.cell(0, 5, clean("- " + o["name"] + ": " + o["this"] + " (normal " + o["normal"] + ")"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Review brief", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(12)
    txt = brief_text if brief_text and not re.search(r"[ऀ-ॿ]", brief_text) else template_brief(record)
    pdf.multi_cell(186, 5, clean(txt))
    if note:
        pdf.ln(2)
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Auditor note", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(12)
        pdf.multi_cell(186, 5, clean(note))
    pdf.set_auto_page_break(False)
    pdf.set_y(-16)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(74, 95, 102)
    pdf.cell(0, 5, "Data: Assam e-tenders via CivicDataLab. TenderLens by Sindhu Marupaka (Imarticus PGA56 Capstone 2).")
    return bytes(pdf.output())


# ---------------------------------------------------------------- records
def record_from_list(tender_id):
    df = load_tenders()
    r = df[df["tender_id"] == tender_id]
    if len(r) == 0:
        return None
    rec = r.iloc[0].to_dict()
    rec["source"] = "list"
    return rec
