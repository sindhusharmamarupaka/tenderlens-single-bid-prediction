"""Page 7 · Beat the model: you vs TenderLens vs random checking, on a real past month."""
import numpy as np
import pandas as pd
import streamlit as st

import tl_core as T
import tl_ui as U

lst = T.load_tenders()
s = T.load_settings()
names = s["month_names"]
N_SHOW = 30
N_PICK = 10

U.header("Beat the model", "Can you find the single-bid tenders better than TenderLens?",
         "You see 30 real tenders from a past month with only publish-day facts. Pick the 10 you would check. TenderLens picks its 10, random checking picks 10. Then reveal how many really got one bid.")

game = st.session_state.setdefault("game", {"round": 0, "score": {"You": 0, "TenderLens": 0, "Random": 0}, "played": 0})
c1, c2, c3 = st.columns([1.6, 1, 2])
with c1:
    mk = st.selectbox("Month to play", list(names.keys()), format_func=lambda k: names[k], index=3, key="bm_month")
with c2:
    st.write("")
    if st.button("New round", type="primary", width="stretch"):
        game["round"] += 1
        game.pop("revealed", None)
        for k in list(st.session_state.keys()):
            if str(k).startswith("bm_pick_"):
                del st.session_state[k]
with c3:
    sc = game["score"]
    U.md('<div class="tl-card" style="padding:10px 14px;font-size:14px;">Scoreboard after ' + str(game["played"]) + " rounds · You <b>" + str(sc["You"])
         + "</b> · TenderLens <b>" + str(sc["TenderLens"]) + "</b> · Random <b>" + str(sc["Random"]) + "</b> single-bid found</div>")

g = lst[lst["month_key"] == mk]
seed = 1000 + game["round"] * 7 + list(names.keys()).index(mk)
pool = g.sample(N_SHOW, random_state=seed).reset_index(drop=True)
model_pick = set(pool.nsmallest(N_PICK, "fair_risk")["tender_id"])
rand_pick = set(pool.sample(N_PICK, random_state=seed + 1)["tender_id"])
key_base = "bm_pick_" + mk + "_" + str(game["round"]) + "_"
revealed = game.get("revealed") == (mk, game["round"])

mine = set()
for _, r in pool.iterrows():
    if st.session_state.get(key_base + r["tender_id"]):
        mine.add(r["tender_id"])

if revealed:
    yf = int(pool[pool["tender_id"].isin(mine)]["single_bid"].sum())
    mf = int(pool[pool["tender_id"].isin(model_pick)]["single_bid"].sum())
    rf = int(pool[pool["tender_id"].isin(rand_pick)]["single_bid"].sum())
    real = int(pool["single_bid"].sum())
    best = max(yf, mf, rf)
    winners = [n for n, v in [("You", yf), ("TenderLens", mf), ("Random", rf)] if v == best]
    k = st.columns(4)
    k[0].markdown(U.kpi("You found", str(yf), "single-bid in your 10", U.GOLD, U.GOLD if "You" in winners else "#ffffff"), unsafe_allow_html=True)
    k[1].markdown(U.kpi("TenderLens found", str(mf), "single-bid in its 10", U.AMBER, U.GOLD if "TenderLens" in winners else "#ffffff"), unsafe_allow_html=True)
    k[2].markdown(U.kpi("Random found", str(rf), "single-bid in its 10", U.GREY, U.GOLD if "Random" in winners else "#ffffff"), unsafe_allow_html=True)
    k[3].markdown(U.kpi("Single-bid among the 30", str(real), "expected by luck in 10: " + format(real / 3, ".1f"), U.DEEP), unsafe_allow_html=True)
    if len(winners) == 1:
        st.success(winners[0] + " won this round!")
    else:
        st.info("Tie between " + " and ".join(winners) + ".")
    st.caption("Small rounds are noisy: with only 10 picks, luck matters a lot. Over the whole month the fair numbers are on the Model health page. TenderLens's picks use fair replay scores (before the bids were known).")
else:
    st.progress(min(len(mine), N_PICK) / N_PICK, text="You picked " + str(len(mine)) + " of " + str(N_PICK))

grid = st.columns(5)
for i, r in pool.iterrows():
    with grid[i % 5]:
        tid = r["tender_id"]
        days = str(int(r["bid_window_days"])) + " days to bid"
        extra = []
        if r["retender_60d"] == 1:
            extra.append("re-tender")
        if r["value_missing"] == 1:
            extra.append("no value written")
        border = "2px solid transparent"
        top = ""
        if revealed:
            is_one = r["single_bid"] == 1
            border = "3px solid #e0a000" if is_one else "2px solid #d7cfb6"
            marks = []
            if tid in mine:
                marks.append("YOU")
            if tid in model_pick:
                marks.append("MODEL")
            if tid in rand_pick:
                marks.append("RANDOM")
            res = "1 bid" if is_one else str(int(r["number_of_bids"])) + " bids"
            top = ('<div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span class="tl-pill" style="background:'
                   + ("#e0a000" if is_one else "#b8c7cc") + ';font-size:11px;padding:2px 8px;">' + res + '</span><span style="font-size:10px;font-weight:700;color:#05556b;">'
                   + " · ".join(marks) + "</span></div>")
        st.markdown('<div class="tl-game" style="border:' + border + ';">' + top + '<div class="t">' + U.esc(str(r["title"])[:80]) + '</div><div class="m">'
                    + U.esc(str(r["dept_main"])[:38]) + "<br>" + T.money(r["estimated_value"]) + " · " + days
                    + (("<br>" + ", ".join(extra)) if extra else "") + "</div></div>", unsafe_allow_html=True)
        full = len(mine) >= N_PICK and tid not in mine
        st.checkbox("Check this", key=key_base + tid, disabled=revealed or full)

st.write("")
if not revealed:
    if st.button("Reveal the answers", type="primary", disabled=len(mine) != N_PICK, width="stretch"):
        game["revealed"] = (mk, game["round"])
        yf = int(pool[pool["tender_id"].isin(mine)]["single_bid"].sum())
        mf = int(pool[pool["tender_id"].isin(model_pick)]["single_bid"].sum())
        rf = int(pool[pool["tender_id"].isin(rand_pick)]["single_bid"].sum())
        game["score"]["You"] += yf
        game["score"]["TenderLens"] += mf
        game["score"]["Random"] += rf
        game["played"] += 1
        st.rerun()
U.plain("This game shows why a screening tool helps: picking by feel is hard, and the model is a small but steady help over random checking.")
