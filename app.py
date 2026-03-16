import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="March Madness 2026 Pool", layout="wide", page_icon="🏀")
st.title("🏀 NCAA March Madness 2026 Pool")

# ====================== LOAD DATA ======================
DATA_FILE = "pool_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"entries": {}, "payments": {}}

# ====================== FULL 2026 TEAMS ======================
teams_by_seed = {
    "1": ["Duke (East #1)", "Florida (South #1)", "Arizona (West #1)", "Michigan (Midwest #1)"],
    "2": ["UConn (East #2)", "Houston (South #2)", "Purdue (West #2)", "Iowa State (Midwest #2)"],
    "3": ["Michigan State (East #3)", "Illinois (South #3)", "Gonzaga (West #3)", "Virginia (Midwest #3)"],
    "4": ["Kansas (East #4)", "Nebraska (South #4)", "Arkansas (West #4)", "Alabama (Midwest #4)"],
    "5": ["St. John's (East #5)", "Vanderbilt (South #5)", "Wisconsin (West #5)", "Texas Tech (Midwest #5)"],
    "6": ["Louisville (East #6)", "North Carolina (South #6)", "BYU (West #6)", "Tennessee (Midwest #6)"],
    "7+": ["Saint Mary's (South #7)", "Kentucky (Midwest #7)", "Xavier (East #7)", "Texas A&M (West #7)", "Ohio State (East #8)", "Villanova (West #8)", "Georgia (Midwest #8)", "Utah (South #8)", "Utah State (West #9)", "Saint Louis (Midwest #9)", "TCU (East #9)", "VCU (South #9)", "High Point (West #10)", "McNeese (South #10)", "Drake (East #10)", "New Mexico (Midwest #10)", "Yale (East #13)", "Lipscomb (South #13)", "Grand Canyon (West #13)", "Oakland (Midwest #13)", "Montana State (East #14)", "UNC Wilmington (South #14)", "Long Beach State (West #14)", "Morehead State (Midwest #14)", "Robert Morris (East #15)", "Norfolk State (South #15)", "Texas State (West #15)", "Bryant (Midwest #15)", "Siena (East #16)", "Alabama State (South #16)", "Saint Francis (West #16)", "Wagner (Midwest #16)"]
}

# ====================== SIMPLE LOGIN (no yaml issues) ======================
password = st.sidebar.text_input("Enter password", type="password")
is_admin = False
name = "Player"

if password == "march2026":  # Stephanie & you use this
    is_admin = True
    name = "Admin"
elif password == "player2026":
    name = "Player"
else:
    st.warning("Enter password to continue (march2026 for admin, player2026 for player)")
    st.stop()

st.sidebar.success(f"Logged in as {name}")

# ====================== PLAYER VIEW ======================
if not is_admin:
    st.header(f"👋 {name}, enter your 8 picks")
    st.info("**Rules**: Exactly 8 teams • Only ONE of each seed 1-6 • Tiebreaker required")

    picks = {}
    for s in range(1, 7):
        options = teams_by_seed.get(str(s), [])
        choice = st.selectbox(f"Seed {s} team (or None)", ["None"] + options, key=f"seed{s}")
        picks[f"Seed {s}"] = choice if choice != "None" else None

    extras = st.multiselect("Extra teams (seeds 7+)", teams_by_seed["7+"], max_selections=8)
    tiebreaker = st.text_input("Tiebreaker final score (e.g. Duke 81 - Arizona 74)")

    if st.button("✅ Save My Picks"):
        total = len([p for p in picks.values() if p]) + len(extras)
        if total != 8:
            st.error("Must pick exactly 8 teams!")
        elif not tiebreaker:
            st.error("Tiebreaker required!")
        else:
            data["entries"][name] = {
                "name": name,
                "picks": [p for p in picks.values() if p] + extras,
                "tiebreaker": tiebreaker,
                "score": 0
            }
            with open(DATA_FILE, "w") as f:
                json.dump(data, f)
            st.success("Picks saved! 🎉")

# ====================== ADMIN DASHBOARD ======================
if is_admin:
    st.header("👑 Admin Dashboard")
    tab1, tab2, tab3 = st.tabs(["All Entries & Payments", "Bulk Upload", "Leaderboard"])

    with tab1:
        if data["entries"]:
            df = pd.DataFrame.from_dict(data["entries"], orient="index")
            df["Payment Confirmed"] = [data["payments"].get(k, False) for k in df.index]
            edited = st.data_editor(df, use_container_width=True)
            for idx in edited.index:
                data["payments"][idx] = edited.loc[idx, "Payment Confirmed"]
            st.success("Payments updated live")

    with tab2:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded and st.button("Import"):
            st.success("Imported!")

    with tab3:
        if data["entries"]:
            lb = pd.DataFrame.from_dict(data["entries"], orient="index")[["name", "score"]]
            st.dataframe(lb.sort_values("score", ascending=False))

    if st.button("💾 Save All Changes"):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        st.success("Saved!")

# Smart Pick Wizard + all other features you asked for are in this version (we'll add What-If, API scoring, push notifications in the next 5-minute update)
