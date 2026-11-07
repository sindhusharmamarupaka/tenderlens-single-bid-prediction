# TenderLens app (S10)

## Run it on my Mac
1. Open Terminal in VS Code (tf-metal-env active).
2. Install once:  pip install streamlit plotly fpdf2 requests "numpy<2.0"
3. Go to the app folder:  cd ~/Documents/TenderLens/app
4. Start:  streamlit run app.py
5. The app opens in the browser at http://localhost:8501. Stop it with Ctrl + C.

## Pages
1 Overview · 2 Tender risk list (+ audit budget slider) · 3 Tender detail · 4 Department report card ·
5 Model health · 6 Score new tenders (Predict one tender + upload CSV) · 7 Beat the model · 8 About & behind the model

## Files
- app.py: starts the app and the side menu
- tl_core.py: all the maths (clues, model, SHAP, Isolation Forest, similar tenders, brief, PDF)
- tl_ui.py: colours, cards, badges and charts
- views/: one file per page
- app_data/: tables made by make_app_data.py from my S1–S9 files
- models/: copies of the S7 LogReg + scaler and S8 Isolation Forest
- make_app_data.py: rebuilds app_data/ and models/ (run:  python make_app_data.py)

## AI brief
Without a key the brief is written by a rule-based template (still only real facts).
To switch on the AI: copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and paste a free Gemini or Groq key.
