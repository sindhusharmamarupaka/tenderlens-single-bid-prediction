# TenderLens model card

## What it does
- Gives each new Assam government tender a single-bid risk band (High / Medium / Low) on the day it is published.
- Screening support only: it tells an auditor where to look first. It is NOT fraud detection.

## Model
- Logistic Regression (class weights balanced) on 7 publish-day clues: Department's past single-bid rate, Tender value (log), Value not written, Days to submit bids, Months to financial year end, Lot posted the same day, Re-tender within 60 days.
- Retrained at the start of every month, learning only from tenders whose bids were already opened (opened only rule).
- App file: models/tenderlens_logreg.joblib, learned on all 6,790 labelled tenders.

## Data
- Assam e-tenders portal via CivicDataLab, Apr 2016 - May 2023; 39,411 tenders, 6,790 with a verified bidder list.
- Target: 1 = exactly one bid, 0 = more than one bid.
- Time split: train to Sep 2022 (2,753), validation Oct-Dec 2022 (2,270), test Jan-May 2023 (1,767).

## Results on test (scored once)
- Test single-bid rate: 23.8%.
- PR-AUC 0.256 vs random 0.241; ROC-AUC 0.552.
- Checking the riskiest 20% (353 tenders) finds 101 single-bid tenders vs 79 by random checking.
- Bootstrap: beats random in 95.8% of 500 re-draws, beats Rule B in 5.2%.
- Real single-bid rate by band: High 28.6%, Medium 24.9%, Low 21.3%.

## Limits
- Drift: single-bid tenders fell from 36.1% (train) to 27.8% (validation) to 23.8% (test), and many clues changed direction after Sep 2022 (new schemes, December road-work wave).
- Label timing: a tender's answer is known only after its bid opening date (about 19 days after publishing).
- Scores are a ranking, not real percentages, so the app shows bands.
- Publish-day clues are weak; the portal cuts descriptions at 250 letters.

## Intended use
- Monthly retraining on tenders whose bids are already opened; show bands, with SHAP reasons and a plain-English brief.
- A human auditor always decides. Do not use it to blame a department or a supplier.