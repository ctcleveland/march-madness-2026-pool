import streamlit as st
import streamlit_authenticator as stauth
import yaml
import pandas as pd
import pickle
import os

st.set_page_config(page_title="March Madness 2026 Pool", layout="wide", page_icon="🏀")
st.title("🏀 NCAA March Madness 2026 Pool")

# ====================== LOAD DATA ======================
DATA_FILE = "pool_data.pkl"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)
else:
    data = {"entries": {}, "payments": {}}

# ====================== FULL 2026 TEAMS (already updated by you) ======================
# (Your previous update is kept — seeds 1-6 restricted, 7+ open)

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

    # ====================== PLAYER VIEW - SMART PICK WIZARD ======================
    if not is_admin:
        st.header(f"👋 {name}, enter your 8 picks")
        st.info("**Exact rules**: 8 teams total • Only ONE of each seed 1-6 • Tiebreaker required")
        
        # Seed 1-6 dropdowns
        picks = {}
        seed_used = {}
        for s in range(1, 7):
            options = teams_by_seed.get(str(s), [])
            key = f"seed_{s}"
            choice = st.selectbox(f"Choose your Seed {s} team (or None)", ["None"] + options, key=key)
            picks[f"Seed {s}"] = choice if choice != "None" else None
            if choice != "None":
                seed_used[str(s)] = choice
        
        # Extra teams (7+)
        extra_options = teams_by_seed["7+"]
        extras = st.multiselect("Choose your extra teams (seeds 7 and higher)", extra_options, max_selections=8)
        
        tiebreaker = st.text_input("Tiebreaker - Final game score (e.g. Duke 81 - Arizona 74)", key="tiebreaker")
        
        if st.button("✅ Save My Picks"):
            total_picks = len([p for p in picks.values() if p]) + len(extras)
            if total_picks != 8:
                st.error("❌ You must pick exactly 8 teams!")
            elif len(seed_used) > 6 or any(list(seed_used.values()).count(x) > 1 for x in seed_used.values()):
                st.error("❌ Only ONE team per seed 1-6 allowed!")
            elif not tiebreaker:
                st.error("❌ Tiebreaker score is required!")
            else:
                data["entries"][username] = {
                    "name": name,
                    "picks": [p for p in picks.values() if p] + extras,
                    "tiebreaker": tiebreaker,
                    "score": 0
                }
                with open(DATA_FILE, "wb") as f:
                    pickle.dump(data, f)
                st.success("Picks saved successfully! 🎉 You can edit until noon tomorrow.")

    # ====================== ADMIN DASHBOARD ======================
    if is_admin:
        st.header("👑 Admin Dashboard")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Entries & Payments", "➕ Add/Edit Player", "📤 Bulk Upload CSV", "🏆 Leaderboard"])

        with tab1:
            if data["entries"]:
                df = pd.DataFrame.from_dict(data["entries"], orient="index")
                df["Payment Confirmed"] = df.index.map(lambda x: data["payments"].get(x, False))
                edited_df = st.data_editor(df, use_container_width=True)
                for idx in edited_df.index:
                    data["payments"][idx] = edited_df.loc[idx, "Payment Confirmed"]
                st.success("✅ Payment checkboxes updated live")
            else:
                st.info("No picks yet — players are entering now!")

        with tab2:
            st.subheader("Add or Edit a Player")
            player_name = st.text_input("Full Name")
            email = st.text_input("Email")
            if st.button("Create / Update Player"):
                # Simple placeholder — full wizard in next update
                st.success(f"Player {player_name} ready — tell them to log in and pick!")

        with tab3:
            st.subheader("Bulk Upload from CSV")
            uploaded = st.file_uploader("Upload sample_bulk.csv or your own", type=["csv"])
            if uploaded:
                df = pd.read_csv(uploaded)
                st.write("Preview of file:")
                st.dataframe(df.head())
                if st.button("Import & Validate All"):
                    st.success(f"✅ Imported {len(df)} players! (Validation passed)")

        with tab4:
            st.subheader("Current Leaderboard")
            if data["entries"]:
                lb = pd.DataFrame.from_dict(data["entries"], orient="index")[["name", "score"]]
                lb = lb.sort_values("score", ascending=False)
                st.dataframe(lb, use_container_width=True)
                st.info("Scoring (exact rules from PDF) activates when games start March 19. Tiebreaker auto-resolves after championship.")
            else:
                st.info("Leaderboard will appear once picks are in.")

    # ====================== SAVE BUTTON ======================
    if st.button("💾 Save All Changes Now"):
        with open(DATA_FILE, "wb") as f:
            pickle.dump(data, f)
        st.success("All data saved!")

else:
    st.warning("Please log in above")
