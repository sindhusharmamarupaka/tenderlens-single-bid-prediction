![Banner](banner.png)

**A machine learning project that learns from 39,000+ real Assam government e-tenders to flag which new tenders are likely to get only one bid, so auditors know where to look first.**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white) ![SQLite](https://img.shields.io/badge/SQLite-05556b?style=for-the-badge&logo=sqlite&logoColor=white) ![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white) ![Status](https://img.shields.io/badge/Status-In%20Progress-e0a000?style=for-the-badge)

> This is a screening tool, not fraud detection. A single bid does not mean anything wrong happened. It only means the tender had no competition, which is worth a closer look.

---

## Project Progress

| Section | Status | Highlights |
|---|---|---|
| S1 Data audit | Done | 39,500 tender files checked, 6,790 have a bidder list |
| S2 Cleaning | Done | 16 cleaning steps, 39,411 unique tenders, cleaning log and data dictionary saved |
| S3 EDA and SQL | Done | 30.1% of tenders got only one bid, 7 charts, results checked again in SQLite |
| S4 Features and time split | Done | 7 model inputs built, time split into train 2,753 / validation 2,270 / test 1,767 |
| S5 Baseline and ML models | Next | |
| S6 NLP on tender titles | Planned | |
| S7 Final model and SHAP | Planned | |
| S8 Anomaly detection | Planned | |
| S9 Deep learning | Planned | |
| S10 Streamlit app | Planned | |
| S11 Report and slides | Planned | |

---

## Business Understanding

When a government office posts a tender, it wants many companies to bid. More bids usually means better prices and fairer selection.

When only one company bids, there is no competition. Sometimes there is a simple reason (very specialised work, remote location). But a high share of single-bid tenders is a known warning sign in public spending.

Auditors cannot check every tender by hand. The question for this project is:

- Can past tenders help predict which new tenders are likely to get only one bid?
- And can we explain why, so the result is useful and not a black box?

---

## Data Understanding

- **Source:** Assam e-tenders portal, collected and shared by [CivicDataLab](https://github.com/CivicDataLab/assam-tenders-data).
- **Period:** April 2016 to May 2023.
- **Size:** 39,500 CSV files, one file per tender.
- Each file has the tender details in the first row, and lists (bidders, documents) in the rows below.
- Older files do not have a bidder list. Only newer files tell us how many companies bid.

| Stage | Count |
|---|---|
| Tender files | 39,500 |
| Unique tenders (after removing 89 duplicates) | 39,411 |
| Tenders with a bidder list (usable for the target) | 6,790 |
| Single-bid tenders | 2,044 (30.1%) |

![Data funnel](reports/figures/S1a_data_funnel.png)

The raw data is not in this repo because it is large and has company names. You can download it from the CivicDataLab link above.

---

## Data Preparation

I cleaned the data in 16 steps (notebook 02). Main things I did:

- Removed 89 duplicate tender IDs.
- Fixed dates and turned them into proper date columns.
- Made the target column: 1 = only one bid, 0 = more than one bid. Tenders with no bidder list stay unknown (not 0).
- Saved every change in `reports/cleaning_log.csv` and described every column in `reports/data_dictionary.csv`.

---

## Key Findings (S3)

**1. Single-bid tenders are going down over time.**
41% in 2021, 32% in 2022, 22% in 2023 (Jan to May).

![Single bid by year](reports/figures/S3a_single_bid_by_year.png)

**2. Some offices see far more single bids than others.**
Among the 21 offices with at least 50 tenders, Food and Civil Supplies is highest at 51% (about 1 in 2). Health and Family Welfare is lowest at 15% (about 1 in 7). 12 of 21 offices are above the overall 30%.

![Single bid by department](reports/figures/S3b_single_bid_by_department.png)

**3. Tenders posted again soon are the strongest signal so far.**
When the same office posts the same tender again within 1 to 60 days, 40% get only one bid, compared to about 30% for first-time tenders.

![Single bid by repeat gap](reports/figures/S3f_single_bid_by_repeat_gap.png)

**4. December 2022 was unusual.**
1,794 tenders were posted in one month (normal is about 400 to 550), mostly road works and health. Only 19% got a single bid. This looks like a year-end budget rush.

**5. Bid window length and tender value are weak signals on their own.**
Single-bid rates stay between 28% and 34% across bid window bands. Tenders with no value listed show fewer single bids (23% vs 31%), mostly because goods-buying offices often leave value blank.

All S3 numbers were checked a second time with SQL queries in SQLite (`sql/eda_queries.sql`).

---

## Feature Engineering and Time Split (S4)

I turned the S3 findings into 7 inputs the model can learn from. Every input is something we know on the day the tender is first posted, so the model never sees the answer early.

| Feature | Simple meaning |
|---|---|
| `dept_rate` | How often this office got single bids in the past (smoothed so small offices do not get extreme values) |
| `log_value` | Tender value on a log scale, so very large tenders do not dominate |
| `value_missing` | 1 if the office did not list a value |
| `bid_window_days` | Days between posting and the bid deadline |
| `months_to_fy_end` | Months left until the financial year ends on 31 March |
| `same_day_lot` | 1 if the same office posted the same tender on the same day (split into lots) |
| `retender_60d` | 1 if the same tender was posted again within 1 to 60 days |

**Time split.** I split by date, not randomly, because in real life the model will always predict future tenders from past ones.

| Set | Period | Tenders | Single-bid rate |
|---|---|---|---|
| Train | Up to Sep 2022 | 2,753 | 36.1% |
| Validation | Oct to Dec 2022 | 2,270 | 27.8% |
| Test | Jan to May 2023 | 1,767 | 23.8% |

![Split single bid rate](reports/figures/S4a_split_single_bid_rate.png)

Things I did to stop information leaking from the future:

- 46 reference numbers were shared across sets. I moved those 291 tenders forward so each group stays in one set.
- `dept_rate` for validation and test uses training tenders only. For training rows, it uses only earlier tenders, never the tender itself.
- Missing values were filled with training medians only (value about Rs 85 lakh, bid window 19 days). The settings are saved in `reports/s4_feature_settings.csv` so the app can use the same numbers later.

The single-bid rate drops from 36% to 28% to 24% across the three sets. The model will need to handle this drift.

---

## Methodology (next steps)

- Compare a simple rule benchmark with Logistic Regression, Random Forest and XGBoost.
- Handle class imbalance with class weights and threshold tuning.
- Choose the model on validation, use the test set only once at the end.
- Explain predictions with SHAP.
- Separately flag unusual tenders with Isolation Forest.
- Show everything in a Streamlit app.

---

## Limitations

- Only 6,790 tenders have a bidder list, so the model learns from a smaller part of the data.
- The single-bid rate changes over time (36% train, 28% validation, 24% test), so results must be checked for drift.
- A single bid is a signal for review, not proof of wrongdoing.

---

## Project Structure & How to Run

To run:

1. Download the raw data from [CivicDataLab](https://github.com/CivicDataLab/assam-tenders-data) and place the zip in `data/raw/`.
2. Install the libraries: `pip install -r requirements.txt`
3. Put the notebooks inside a `notebooks/` folder (the code reads files one folder up).
4. Run the notebooks in order: 01, 02, 03, 04.

---

## Acknowledgements

- Data: Assam e-tenders portal via [CivicDataLab](https://github.com/CivicDataLab/assam-tenders-data).
- Capstone Project 2, PG Data Analytics, Imarticus Learning.

**Sindhu Sharma Marupaka** · [GitHub](https://github.com/sindhusharmamarupaka) · [LinkedIn](https://www.linkedin.com/in/sindhu-sharma-data-analyst)
