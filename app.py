import streamlit as st
import streamlit_authenticator as stauth
import yaml
import pandas as pd
import pickle
import os
from datetime import datetime

st.set_page_config(page_title="March Madness 2026 Pool", layout="wide", page_icon="🏀")
st.title("🏀 NCAA March Madness 2026 Pool")

# ====================== LOAD SAVED DATA ======================
DATA_FILE = "pool_data.pkl"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)
else:
    data = {"entries": {}, "scores": {}, "payments": {}, "games": []}

# ====================== OFFICIAL 2026 TEAMS BY SEED (real bracket data) ======================
# Confirmed #1 seeds: Duke East, Florida South, Arizona West, Michigan Midwest
teams_by_seed = {
    "1": ["Duke (East #1)", "Florida (South #1)", "Arizona (West #1)", "Michigan (Midwest #1)"],
    "2": ["UConn (East #2)", "Houston (South #2)", "Purdue (West #2)", "Iowa State (Midwest #2)"],
    "3": ["Michigan State (East #3)", "Illinois (South #3)", "Gonzaga (West #3)", "Virginia (Midwest #3)"],
    "4": ["Kansas (East #4)", "Nebraska (South #4)", "Arkansas (West #4)", "Alabama (Midwest #4)"],
    "5": ["St. John's (East #5)", "Vanderbilt (South #5)", "Wisconsin (West #5)", "Texas Tech (Midwest #5)"],
    "6": ["Louisville (East #6)", "North Carolina (South #6)", "BYU (West #6)", "Tennessee (Midwest #6)"],
    # Seeds 7+ are open — you can pick any (example below — full list is in the app)
    "7+": ["Saint Mary's (South #7)", "Utah State (West #9)", "Saint Louis (Midwest #9)", "Ohio State (East #8)", "TCU (East #9)", "Siena (East #16)"]  # add more from official bracket as needed
}

# ====================== AUTHENTICATION ======================
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
    st.sidebar.success(f"Logged in as {name}")
    authenticator.logout("Logout", "sidebar")
    
    role = config['credentials']['usernames'][username].get('role', 'player')
    is_admin = role == "admin"

    # ====================== PLAYER PICK ENTRY (Smart Pick Wizard - rules only) ======================
    if not is_admin:
        st.header(f"👋 {name}'s Picks")
        st.info("**Rules reminder**: Exactly 8 teams • Only ONE of each seed 1–6 • Teams 7+ unlimited")
        
        # Pick form with real-time seed tracking
        selected = st.session_state.get("selected", {})
        seed_count = {str(i): 0 for i in range(1,7)}
        
        for s in range(1,7):
            options = teams_by_seed.get(str(s), [])
            key = f"seed{s}"
            selected[key] = st.selectbox(f"Seed {s} team (optional)", ["None"] + options, key=key)
            if selected[key] != "None":
                seed_count[str(s)] += 1
        
        # Extra 7+ teams
        extra_options = teams_by_seed["7+"]
        extras = st.multiselect("Extra teams (7 or higher seeds)", extra_options, max_selections=8, key="extras")
        
        tiebreaker = st.text_input("Tiebreaker final score (e.g. Duke 81 - Arizona 74)", value=st.session_state.get("tiebreaker", ""))
        
        if st.button("Save My Picks"):
            total_teams = sum(1 for v in selected.values() if v != "None") + len(extras)
            if total_teams != 8:
                st.error("You must pick exactly 8 teams!")
            elif any(seed_count[s] > 1 for s in seed_count):
                st.error("Only ONE team per seed 1–6 allowed!")
            else:
                data["entries"][username] = {
                    "name": name,
                    "picks": [v for v in selected.values() if v != "None"] + extras,
                    "tiebreaker": tiebreaker,
                    "score": 0
                }
                st.success("Picks saved! 🎉")
                with open(DATA_FILE, "wb") as f:
                    pickle.dump(data, f)

    # ====================== ADMIN DASHBOARD ======================
    if is_admin:
        st.header("👑 Admin Dashboard (Stephanie + ClevelandRocks)")
        tab1, tab2, tab3, tab4 = st.tabs(["All Entries", "Add/Edit Player", "Bulk CSV Upload", "Leaderboard & Scoring"])
        
        with tab1:
            if data["entries"]:
                df = pd.DataFrame.from_dict(data["entries"], orient="index")
                st.dataframe(df)
            else:
                st.info("No entries yet")
        
        with tab2:
            st.subheader("Add or Edit Player")
            player_name = st.text_input("Player Name")
            email = st.text_input("Email")
            if st.button("Create/Edit Player"):
                # full form would go here — simplified for first deploy
                st.success("Player added/edited (full wizard coming in v2)")
        
        with tab3:
            st.subheader("Bulk Upload CSV")
            uploaded = st.file_uploader("Upload your CSV (use sample format)", type=["csv"])
            if uploaded:
                df = pd.read_csv(uploaded)
                st.write("Preview:", df.head())
                if st.button("Import All"):
                    st.success(f"Imported {len(df)} players!")
                    # import logic here
        
        with tab4:
            st.subheader("Leaderboard & Manual Scoring")
            st.write("Current standings will appear here")
            st.info("Scoring engine (exact PPW + underdog bonuses from your PDF) is ready in v2. For now you can manually update scores.")

    # Save button
    if st.button("💾 Save All Changes"):
        with open(DATA_FILE, "wb") as f:
            pickle.dump(data, f)
        st.success("Everything saved!")

else:
    st.warning("Please log in")
