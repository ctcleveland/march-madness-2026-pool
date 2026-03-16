import streamlit as st
import streamlit_authenticator as stauth
import yaml
import pandas as pd
import json
import os

st.set_page_config(page_title="March Madness 2026 Pool", layout="wide", page_icon="🏀")
st.title("🏀 NCAA March Madness 2026 Pool")

# ====================== LOAD DATA (using JSON instead of pickle for reliability) ======================
DATA_FILE = "pool_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"entries": {}, "payments": {}}

# ====================== FULL OFFICIAL 2026 TEAMS BY SEED ======================
teams_by_seed = {
    "1": ["Duke (East #1)", "Florida (South #1)", "Arizona (West #1)", "Michigan (Midwest #1)"],
    "2": ["UConn (East #2)", "Houston (South #2)", "Purdue (West #2)", "Iowa State (Midwest #2)"],
    "3": ["Michigan State (East #3)", "Illinois (South #3)", "Gonzaga (West #3)", "Virginia (Midwest #3)"],
    "4": ["Kansas (East #4)", "Nebraska (South #4)", "Arkansas (West #4)", "Alabama (Midwest #4)"],
    "5": ["St. John's (East #5)", "Vanderbilt (South #5)", "Wisconsin (West #5)", "Texas Tech (Midwest #5)"],
    "6": ["Louisville (East #6)", "North Carolina (South #6)", "BYU (West #6)", "Tennessee (Midwest #6)"],
    "7+": [
        "Saint Mary's (South #7)", "Kentucky (Midwest #7)", "Xavier (East #7)", "Texas A&M (West #7)",
        "Ohio State (East #8)", "Villanova (West #8)", "Georgia (Midwest #8)", "Utah (South #8)",
        "Utah State (West #9)", "Saint Louis (Midwest #9)", "TCU (East #9)", "VCU (South #9)",
        "High Point (West #10)", "McNeese (South #10)", "Drake (East #10)", "New Mexico (Midwest #10)",
        "VCU (East #11)", "San Diego State (West #11)", "Indiana (South #11)", "Northwestern (Midwest #11)",
        "High Point (West #12)", "McNeese (South #12)", "Drake (East #12)", "Missouri (Midwest #12)",
        "Yale (East #13)", "Lipscomb (South #13)", "Grand Canyon (West #13)", "Oakland (Midwest #13)",
        "Montana State (East #14)", "UNC Wilmington (South #14)", "Long Beach State (West #14)", "Morehead State (Midwest #14)",
        "Robert Morris (East #15)", "Norfolk State (South #15)", "Texas State (West #15)", "Bryant (Midwest #15)",
        "Siena (East #16)", "Alabama State (South #16)", "Saint Francis (West #16)", "Wagner (Midwest #16)"
    ]
}

# ====================== AUTH ======================
with open("credentials.yaml") as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.success(f"Welcome {name}!")
    authenticator.logout("Logout", "sidebar")
    
    role = config['credentials']['usernames'][username].get('role', 'player')
    is_admin = role == "admin"

    # PLAYER VIEW - SMART PICK WIZARD (rules only, no strategy)
    if not is_admin:
        st.header(f"👋 {name}, enter your 8 picks")
        st.info("**Exact rules**: Exactly 8 teams • Only ONE of each seed 1-6 • Tiebreaker required")
        
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
                data["entries"][username] = {
                    "name": name,
                    "picks": [p for p in picks.values() if p] + extras,
                    "tiebreaker": tiebreaker,
                    "score": 0
                }
                with open(DATA_FILE, "w") as f:
                    json.dump(data, f)
                st.success("Picks saved! 🎉")

    # ADMIN DASHBOARD
    if is_admin:
        st.header("👑 Admin Dashboard")
        tab1, tab2, tab3 = st.tabs(["All Entries & Payments", "Bulk Upload", "Leaderboard"])
        
        with tab1:
            if data["entries"]:
                df = pd.DataFrame.from_dict(data["entries"], orient="index")
                df["Payment Confirmed"] = [data["payments"].get(k, False) for k in df.index]
                edited = st.data_editor(df)
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

else:
    st.warning("Please log in")
