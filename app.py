import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="March Madness 2026 Pool", layout="wide", page_icon="🏀")
st.title("🏀 NCAA March Madness 2026 Pool")

# ====================== LOAD DATA ======================
DATA_FILE = "pool_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"entries": {}, "payments": {}}

# ====================== DEADLINE = NOON PACIFIC TIME ======================
DEADLINE = datetime(2026, 3, 17, 19, 0)  # 12:00 PDT

# ====================== ALL TEAMS ======================
all_teams = [
    "Duke (East #1)", "Florida (South #1)", "Arizona (West #1)", "Michigan (Midwest #1)",
    "UConn (East #2)", "Houston (South #2)", "Purdue (West #2)", "Iowa State (Midwest #2)",
    "Michigan State (East #3)", "Illinois (South #3)", "Gonzaga (West #3)", "Virginia (Midwest #3)",
    "Kansas (East #4)", "Nebraska (South #4)", "Arkansas (West #4)", "Alabama (Midwest #4)",
    "St. John's (East #5)", "Vanderbilt (South #5)", "Wisconsin (West #5)", "Texas Tech (Midwest #5)",
    "Louisville (East #6)", "North Carolina (South #6)", "BYU (West #6)", "Tennessee (Midwest #6)",
    "Saint Mary's (South #7)", "Kentucky (Midwest #7)", "Xavier (East #7)", "Texas A&M (West #7)",
    "Ohio State (East #8)", "Villanova (West #8)", "Georgia (Midwest #8)", "Utah (South #8)",
    "Utah State (West #9)", "Saint Louis (Midwest #9)", "TCU (East #9)", "VCU (South #9)",
    "High Point (West #10)", "McNeese (South #10)", "Drake (East #10)", "New Mexico (Midwest #10)",
    "Yale (East #13)", "Lipscomb (South #13)", "Grand Canyon (West #13)", "Oakland (Midwest #13)",
    "Montana State (East #14)", "UNC Wilmington (South #14)", "Long Beach State (West #14)", "Morehead State (Midwest #14)",
    "Robert Morris (East #15)", "Norfolk State (South #15)", "Texas State (West #15)", "Bryant (Midwest #15)",
    "Siena (East #16)", "Alabama State (South #16)", "Saint Francis (West #16)", "Wagner (Midwest #16)"
]

# ====================== ADMIN EMAILS ======================
ADMIN_EMAILS = ["ctcleveland@gmail.com", "sdougherty5@cox.net"]

# ====================== LOGIN FORM ======================
st.sidebar.header("Login")
email = st.sidebar.text_input("Your Email Address", placeholder="you@email.com")
password = st.sidebar.text_input("Password", type="password")
login_button = st.sidebar.button("Login", key="login_btn")

if st.sidebar.button("Forgot Password?", key="forgot_btn"):
    st.sidebar.info("**Forgot your password?**\n\nContact Stephanie via email or text for assistance.")

if not login_button:
    st.stop()

user_email = email.strip().lower()

if password not in ["march2026", "player2026"]:
    st.error("Incorrect password")
    st.stop()

is_admin = user_email in ADMIN_EMAILS
show_admin = False
if is_admin:
    show_admin = st.sidebar.checkbox("🔧 Switch to Admin Dashboard", value=False, key="admin_toggle")

st.sidebar.success(f"Logged in as {user_email}")

# ====================== PLAYER VIEW ======================
if not show_admin:
    st.header(f"👋 Welcome {user_email}, enter your 8 picks")
    st.info("**Rules**: Exactly 8 teams • At most ONE team from seeds 1–6 • Any number of 7+ seeds OK")

    existing = data["entries"].get(user_email, {})
    default_teams = existing.get("picks", [])
    default_tiebreaker = existing.get("tiebreaker", "")

    if datetime.now() > DEADLINE:
        st.warning("**Picks are now locked after the deadline (Noon Pacific Time). No more changes allowed.**")
        st.write("**Your locked picks:**", default_teams)
        st.write("**Your tiebreaker:**", default_tiebreaker)
    else:
        with st.form("pick_form", clear_on_submit=False):
            selected_teams = st.multiselect(
                "Select your 8 teams (any combination)",
                all_teams,
                default=default_teams,
                max_selections=8
            )
            st.divider()
            st.write("")  
            st.write("")  
            st.write("")  
            tiebreaker = st.text_input(
                "Tiebreaker - Final game score (just the two scores, e.g. 81 - 74)",
                value=default_tiebreaker,
                help="Example: 81 - 74"
            )
            submitted = st.form_submit_button("✅ Save My Picks")  # always clickable

        if submitted:
            # Validation on click only
            seed_count = {}
            for team in selected_teams:
                if "#" in team:
                    seed = team.split("#")[-1].split(")")[0].strip()
                    if seed.isdigit() and int(seed) <= 6:
                        seed_count[seed] = seed_count.get(seed, 0) + 1

            violations = [f"Seed {s}" for s, cnt in seed_count.items() if cnt > 1]

            if violations:
                st.error(f"❌ You picked more than one team from these seeds: {', '.join(violations)}\n\nFix it and try Save again.")
            elif len(selected_teams) != 8:
                st.error(f"❌ You must pick exactly 8 teams (you have {len(selected_teams)}). Fix it and try Save again.")
            elif not tiebreaker:
                st.error("❌ Tiebreaker is required (just the two final scores, e.g. 81 - 74).")
            else:
                data["entries"][user_email] = {
                    "name": user_email,
                    "picks": selected_teams,
                    "tiebreaker": tiebreaker,
                    "score": existing.get("score", 0)
                }
                with open(DATA_FILE, "w") as f:
                    json.dump(data, f)
                st.success("Picks saved! 🎉 You can edit anytime before noon tomorrow.")

# ====================== ADMIN DASHBOARD ======================
else:
    st.header("👑 Admin Dashboard")
    tab1, tab2, tab3 = st.tabs(["All Entries & Payments", "Bulk Upload", "Leaderboard"])

    with tab1:
        if data["entries"]:
            df = pd.DataFrame.from_dict(data["entries"], orient="index")
            df["Payment Confirmed"] = [data["payments"].get(k, False) for k in df.index]
            edited = st.data_editor(df, width="stretch")
            for idx in edited.index:
                data["payments"][idx] = edited.loc[idx, "Payment Confirmed"]
            st.success("✅ Payments updated live")
        else:
            st.info("No picks yet")

    with tab2:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded and st.button("Import All", key="import_btn"):
            st.success("Imported!")

    with tab3:
        if data["entries"]:
            lb = pd.DataFrame.from_dict(data["entries"], orient="index")[["name", "score"]]
            st.dataframe(lb.sort_values("score", ascending=False))

    if st.button("💾 Save Payment Changes", key="admin_save"):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        st.success("Saved!")
