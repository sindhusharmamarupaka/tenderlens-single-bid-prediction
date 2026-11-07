# S10 prep: builds every file the TenderLens app reads (run once).
# Reads S1-S9 outputs from the TenderLens project folder, writes app/app_data and app/models.
# Run from the app folder:  python make_app_data.py
import os, json, shutil, warnings
import numpy as np
import pandas as pd
import joblib
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("TL_BASE", os.path.dirname(HERE))   # the TenderLens project folder
APP = os.environ.get("TL_APP", HERE)                       # this app folder
OUT = APP + "/app_data"
os.makedirs(OUT, exist_ok=True)
os.makedirs(APP + "/models", exist_ok=True)

CLUES = ["dept_rate", "log_value", "value_missing", "bid_window_days", "months_to_fy_end", "same_day_lot", "retender_60d"]

# ---------- models ----------
for name in ["tenderlens_logreg.joblib", "tenderlens_scaler.joblib", "tenderlens_iforest.joblib",
             "tenderlens_clues.csv", "tenderlens_band_cutoffs.csv", "tenderlens_iforest_clues.csv", "tenderlens_iforest_cutoff.csv"]:
    shutil.copy(BASE + "/models/" + name, APP + "/models/" + name)
lr = joblib.load(BASE + "/models/tenderlens_logreg.joblib")
sc = joblib.load(BASE + "/models/tenderlens_scaler.joblib")
iso = joblib.load(BASE + "/models/tenderlens_iforest.joblib")
ICLUES = list(pd.read_csv(BASE + "/models/tenderlens_iforest_clues.csv").clue)
ICUT = float(pd.read_csv(BASE + "/models/tenderlens_iforest_cutoff.csv").value.iloc[0])
cut = pd.read_csv(BASE + "/models/tenderlens_band_cutoffs.csv").set_index("band")["score from"]

# ---------- data ----------
f = pd.read_csv(BASE + "/data/processed/features_split.csv", parse_dates=["published_date"])
v2 = pd.read_csv(BASE + "/data/processed/features_split_v2.csv")
cl = pd.read_csv(BASE + "/data/interim/tenders_clean.csv", parse_dates=["published_date", "last_date", "bid_opening_date"])
s4 = pd.read_csv(BASE + "/reports/s4_feature_settings.csv", index_col=0)["value"]
fill = pd.read_csv(BASE + "/reports/s5_fill_values.csv", index_col=0).iloc[:, 0]
dept_rate = pd.read_csv(BASE + "/data/processed/dept_rate_train.csv")
dept_rate.to_csv(OUT + "/dept_rate_train.csv", index=False)

X = sc.transform(f[CLUES])
X_mean = X.mean(axis=0)
f["risk"] = lr.predict_proba(X)[:, 1]
shap = lr.coef_[0] * (X - X_mean)
for i, c in enumerate(CLUES):
    f["shap_" + c] = shap[:, i]
f["anomaly_score"] = -iso.score_samples(v2[ICLUES])
f["unusual"] = (f["anomaly_score"] >= ICUT).astype(int)
for c in ["emd_ratio", "log_fee", "work_period_days", "category", "product_category"]:
    f[c] = v2[c].values
imed = v2[ICLUES].median()
istd = v2[ICLUES].std()
z = ((v2[ICLUES] - imed) / istd).abs()
order = np.argsort(-z.values, axis=1)
f["odd_1"] = [ICLUES[o[0]] for o in order]
f["odd_2"] = [ICLUES[o[1]] for o in order]
f["odd_3"] = [ICLUES[o[2]] for o in order]

# fair scores (what the model said before answers were known)
s5 = pd.read_csv(BASE + "/reports/s5_val_predictions.csv")[["tender_id", "risk"]].rename(columns={"risk": "fair_risk"})
s7 = pd.read_csv(BASE + "/reports/s7_test_predictions.csv")[["tender_id", "risk_main", "work_type"]].rename(columns={"risk_main": "fair_risk"})
fair = pd.concat([s5, s7[["tender_id", "fair_risk"]]])
f = f.merge(fair, on="tender_id", how="left")
f = f.merge(s7[["tender_id", "work_type"]], on="tender_id", how="left")

keep = ["tender_id", "emd_amount", "tender_fee", "last_date", "bid_opening_date", "number_of_bids", "location",
        "contract_form", "title_key", "department", "has_award", "awarded_value", "winning_supplier", "cancelled", "giant_value"]
f = f.merge(cl[keep], on="tender_id", how="left")

# month groups used in S7 (val dated before Oct -> Oct, test dated 2022 -> Jan, Apr+May together)
p = f["published_date"].dt.to_period("M")
grp = p.astype(str)
grp = np.where((f["split"] == "val") & (p < pd.Period("2022-10")), "2022-10", grp)
grp = np.where((f["split"] == "test") & (p < pd.Period("2023-01")), "2023-01", grp)
f["month_key"] = pd.Series(grp).replace({"2023-05": "2023-04"}).values
names = {"2022-10": "Oct 2022", "2022-11": "Nov 2022", "2022-12": "Dec 2022", "2023-01": "Jan 2023",
         "2023-02": "Feb 2023", "2023-03": "Mar 2023", "2023-04": "Apr–May 2023"}

# anonymise suppliers S1, S2... by number of wins (S8 rule)
w = f["winning_supplier"].fillna("").str.upper().str.replace(r"[^A-Z0-9 ]", " ", regex=True).str.split().str.join(" ")
wins = w[w != ""].value_counts()
code = {}
for i, name in enumerate(wins.index):
    code[name] = "S" + str(i + 1)
f["winner"] = w.map(code)
f = f.drop(columns=["winning_supplier"])

# data quality alerts
def dq_row(r):
    out = []
    if pd.notna(r.estimated_value) and r.estimated_value < 10000:
        out.append("Value below Rs 10,000")
    if pd.notna(r.bid_window_days) and r.bid_window_days < 3:
        out.append("Only " + str(int(r.bid_window_days)) + " days to bid")
    if pd.notna(r.bid_window_days) and r.bid_window_days > 180:
        out.append("Bid window over 180 days")
    if pd.notna(r.emd_amount) and pd.notna(r.estimated_value) and r.emd_amount > r.estimated_value:
        out.append("EMD bigger than the value")
    if pd.notna(r.last_date) and r.last_date < r.published_date:
        out.append("Last date before published date")
    return "; ".join(out)
f["dq"] = f.apply(dq_row, axis=1)

# whole labelled table (all 6,790) for department cards, similar tenders, the model's memory
lab = f.copy()
lab["month_key"] = np.where(lab["split"] == "train", lab["published_date"].dt.to_period("M").astype(str), lab["month_key"])

# list = val + test months, ranked inside each month
lst = lab[lab["split"] != "train"].copy()
lst["month"] = lst["month_key"].map(names)
lst["rank"] = lst.groupby("month_key")["risk"].rank(ascending=False, method="first").astype(int)
lst["n_month"] = lst.groupby("month_key")["risk"].transform("size")
lst["pct"] = lst["rank"] / lst["n_month"]
lst["band"] = np.where(lst["pct"] <= 0.2, "High", np.where(lst["pct"] <= 0.5, "Medium", "Low"))
big = lst["estimated_value"] >= 1e7
lst["check"] = np.where((lst["band"] == "High") & ((lst["unusual"] == 1) | big), "P1",
                np.where((lst["band"] == "High") | (lst["unusual"] == 1), "P2", "P3"))
lst["fair_rank"] = lst.groupby("month_key")["fair_risk"].rank(ascending=False, method="first").astype(int)

cols = ["tender_id", "month_key", "month", "published_date", "last_date", "bid_opening_date", "dept_main", "department",
        "title", "work_description", "category", "product_category", "work_type", "contract_form", "location",
        "estimated_value", "emd_amount", "tender_fee", "work_period_days", "emd_ratio", "log_fee"] + CLUES + \
       ["days_since_same", "title_key", "risk", "rank", "n_month", "band", "check", "anomaly_score", "unusual",
        "odd_1", "odd_2", "odd_3", "dq", "fair_risk", "fair_rank", "single_bid", "number_of_bids", "awarded_value", "winner"] + \
       ["shap_" + c for c in CLUES]
lst[cols].to_csv(OUT + "/tenders.csv", index=False)
lcols = ["tender_id", "split", "month_key", "published_date", "dept_main", "title", "title_key", "category",
         "estimated_value", "risk", "single_bid", "number_of_bids", "awarded_value", "winner", "unusual"]
lab[lcols].to_csv(OUT + "/labelled.csv", index=False)

# history of all 39,411 tenders (for re-tender history + re-tender clue of new tenders)
h = cl[["tender_id", "title_key", "published_date", "dept_main", "estimated_value", "number_of_bids", "cancelled", "single_bid"]].copy()
h.to_csv(OUT + "/history.csv", index=False)

# ---------- model health: fair catch rate + drift (PSI) ----------
tr = lab[lab["split"] == "train"]
def psi(base, now):
    base = base.dropna()
    now = now.dropna()
    if base.nunique() <= 12:
        cats = sorted(set(base.unique()) | set(now.unique()))
        e = np.array([(base == c).mean() for c in cats])
        a = np.array([(now == c).mean() for c in cats])
    else:
        edges = np.unique(np.quantile(base, np.linspace(0, 1, 11)))
        edges[0] = -np.inf
        edges[-1] = np.inf
        e = np.histogram(base, edges)[0] / len(base)
        a = np.histogram(now, edges)[0] / len(now)
    e = np.clip(e, 1e-4, None)
    a = np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))
DRIFT_CLUES = ["log_value", "value_missing", "bid_window_days", "same_day_lot", "retender_60d"]
rows = []
for mk, g in lst.groupby("month_key"):
    row = {"month_key": mk, "month": names[mk], "tenders": len(g), "single_rate": g["single_bid"].mean() * 100}
    k = max(1, int(round(len(g) * 0.2)))
    top = g.nsmallest(k, "fair_rank")
    row["caught"] = int(top["single_bid"].sum())
    row["single_total"] = int(g["single_bid"].sum())
    row["catch_pct"] = row["caught"] / max(1, row["single_total"]) * 100
    row["high_rate"] = top["single_bid"].mean() * 100
    vals = []
    for c in DRIFT_CLUES:
        v = psi(tr[c], g[c])
        row["psi_" + c] = v
        vals.append(v)
    row["psi"] = float(np.mean(vals))
    row["psi_worst_clue"] = DRIFT_CLUES[int(np.argmax(vals))]
    rows.append(row)
mh = pd.DataFrame(rows)
mh["status"] = np.where(mh["psi"] < 0.1, "Same as training", np.where(mh["psi"] < 0.25, "Some change", "Check the model"))
mh.to_csv(OUT + "/model_health.csv", index=False)

# ---------- department report cards ----------
after = lab["published_date"] > "2022-09-30"
lab["period"] = np.where(after, "After", "Before")
dc = []
for d, g in lab.groupby("dept_main"):
    r = {"dept_main": d, "tenders": len(g), "single_rate": g["single_bid"].mean() * 100}
    b = g[g["period"] == "Before"]
    a = g[g["period"] == "After"]
    r["n_before"] = len(b)
    r["n_after"] = len(a)
    r["rate_before"] = b["single_bid"].mean() * 100 if len(b) else np.nan
    r["rate_after"] = a["single_bid"].mean() * 100 if len(a) else np.nan
    gv = g[g["estimated_value"].notna() & (~g["giant_value"].astype(bool))]
    r["total_cr"] = gv["estimated_value"].sum() / 1e7
    r["single_cr"] = gv.loc[gv["single_bid"] == 1, "estimated_value"].sum() / 1e7
    aw = g[g["winner"].notna()]
    r["awards"] = len(aw)
    r["firms"] = aw["winner"].nunique()
    if len(aw):
        cnt = aw["winner"].value_counts()
        r["top_firm"] = cnt.index[0]
        r["top_firm_share"] = cnt.iloc[0] / len(aw) * 100
        rep = cnt[cnt >= 3].index
        r["repeat_share"] = aw["winner"].isin(rep).mean() * 100
        shares = cnt / len(aw) * 100
        r["hhi"] = float((shares ** 2).sum())
    dc.append(r)
dc = pd.DataFrame(dc)
allsingle = dc["single_cr"].sum()
dc["share_of_single_money"] = dc["single_cr"] / allsingle * 100
dc = dc.sort_values("single_cr", ascending=False)
dc.to_csv(OUT + "/departments.csv", index=False)

# ---------- small result tables copied for the About / Behind the model pages ----------
for name in ["s7_test_results.csv", "s7_bootstrap.csv", "s7_auditor_view.csv", "s7_risk_bands.csv", "s9_val_results.csv",
             "s9_bootstrap.csv", "s8_competition_price.csv", "s8_cost_of_one_bidder.csv", "s8_check_first.csv",
             "s8_value_at_risk.csv", "s8_repeat_winners.csv", "s5_model_results.csv"]:
    shutil.copy(BASE + "/reports/" + name, OUT + "/" + name)

# ---------- settings ----------
cp = pd.read_csv(BASE + "/reports/s8_competition_price.csv", index_col=0)
st = {
    "clues": CLUES, "iforest_clues": ICLUES, "iforest_cutoff": ICUT,
    "band_cutoffs": {"High": float(cut["High"]), "Medium": float(cut["Medium"])},
    "overall_train_rate": float(s4["overall_train_rate"]), "smoothing_k": float(s4["smoothing_k"]),
    "log_value_median": float(s4["log_value_median"]), "bid_window_median": float(s4["bid_window_median"]),
    "fill": {k: float(fill[k]) for k in fill.index},
    "X_mean": [float(x) for x in X_mean],
    "iforest_median": {k: float(imed[k]) for k in ICLUES}, "iforest_std": {k: float(istd[k]) for k in ICLUES},
    "ratio_one_bid": float(cp.loc["1 bid", "median_ratio"]), "ratio_four_plus": float(cp.loc["4 bids", "median_ratio"]),
    "month_names": names,
}
with open(OUT + "/settings.json", "w") as fh:
    json.dump(st, fh, indent=1)

# ---------- upload template + sample of real NEW tenders (bids not known) ----------
tmpl_cols = ["tender_id", "department", "title", "estimated_value", "published_date", "last_date", "emd_amount", "tender_fee", "work_period_days"]
pd.DataFrame(columns=tmpl_cols).to_csv(OUT + "/upload_template.csv", index=False)
u = cl[cl["single_bid"].isna() & (cl["published_date"] >= "2023-04-01") & (~cl["cancelled"])].copy()
u = u.sort_values("published_date").head(40)
u["department"] = u["dept_main"]
u[tmpl_cols].to_csv(OUT + "/sample_new_tenders.csv", index=False)

print("list", lst.shape, "labelled", lab.shape, "history", h.shape)
print(mh[["month", "tenders", "single_rate", "caught", "single_total", "catch_pct", "psi", "status", "psi_worst_clue"]].round(3).to_string())
print(lst.groupby("band")["single_bid"].mean().round(3))
print("dq", (lst["dq"] != "").sum(), lst["dq"].value_counts().head(8))
for fn in os.listdir(OUT):
    print(fn, os.path.getsize(OUT + "/" + fn))
