import pandas as pd
import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate and connect to Google Sheets
def authenticate_gsheet(json_keyfile, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(credentials)
    return client.open(sheet_name)

# Load data from Google Sheets
def load_data(sheet):
    rankings_sheet = sheet.worksheet("Rankings")
    match_history_sheet = sheet.worksheet("Match History")

    # Load Rankings
    rankings_data = rankings_sheet.get_all_records()
    rankings = pd.DataFrame(rankings_data)

    # Load Match History
    match_history_data = match_history_sheet.get_all_records()
    match_history = pd.DataFrame(match_history_data)

    return rankings, match_history

# Save data to Google Sheets
def save_data(sheet, rankings, match_history):
    rankings_sheet = sheet.worksheet("Rankings")
    match_history_sheet = sheet.worksheet("Match History")

    # Save Rankings
    rankings_sheet.clear()
    rankings_sheet.update([rankings.columns.values.tolist()] + rankings.values.tolist())

    # Save Match History
    match_history_sheet.clear()
    match_history_sheet.update([match_history.columns.values.tolist()] + match_history.values.tolist())

# Initialize Google Sheets
json_keyfile = "path/to/your/service_account.json"  # Replace with the path to your JSON key file
sheet_name = "Tennis Rankings and Match History"   # Replace with your Google Sheet name
sheet = authenticate_gsheet(json_keyfile, sheet_name)


# Initialize default data
players = ["Marinkovic", "Joseto", "Hernan", "Pavez", "Bozzo", "Bishara", "Hederra", "Poch", "Juande", "Hans"]
points = [1000 for _ in players]

# Initialize session state for rankings and match history
if "rankings" not in st.session_state:
    st.session_state.rankings = pd.DataFrame({"Player": players, "Points": points})

if "match_history" not in st.session_state:
    st.session_state.match_history = pd.DataFrame(columns=["Date", "Winner", "Loser", "Points Exchanged"])

# Function to record a match and update rankings
def record_match(winner, loser, base_points=50, upset_multiplier=1.5):
    rankings = st.session_state.rankings
    match_history = st.session_state.match_history

    # Get winner and loser points
    winner_points = rankings.loc[rankings['Player'] == winner, 'Points'].values[0]
    loser_points = rankings.loc[rankings['Player'] == loser, 'Points'].values[0]

    # Calculate points exchanged
    points_exchanged = base_points + (0.05 * loser_points)
    if winner_points < loser_points:
        points_exchanged *= upset_multiplier

    # Update rankings
    rankings.loc[rankings['Player'] == winner, 'Points'] += points_exchanged
    rankings.loc[rankings['Player'] == loser, 'Points'] -= points_exchanged
    rankings['Points'] = rankings['Points'].clip(lower=0)
    rankings.sort_values(by="Points", ascending=False, inplace=True, ignore_index=True)

    # Add match to history
    new_match = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Winner": winner,
        "Loser": loser,
        "Points Exchanged": round(points_exchanged, 2),
    }
    st.session_state.match_history = pd.concat([match_history, pd.DataFrame([new_match])], ignore_index=True)

# Streamlit App
st.title("🎾 Tennis Rankings and Match Tracker")

menu = st.sidebar.selectbox("Menu", ["See Rankings", "See Match History", "Record a Match"])

if menu == "See Rankings":
    st.header("📊 Current Rankings")
    # Add a rank column based on the updated ranking order
    rankings = st.session_state.rankings.copy()
    rankings.insert(0, "Rank", range(1, len(rankings) + 1))
    st.dataframe(rankings.set_index("Rank"))  # Use Rank as the index to remove the unnamed index column

elif menu == "See Match History":
    st.header("📜 Match History")
    if st.session_state.match_history.empty:
        st.write("No matches have been recorded yet.")
    else:
        st.table(st.session_state.match_history)

elif menu == "Record a Match":
    st.header("🏅 Record a Match Result")
    st.write("Enter the winner and loser from the dropdown options below.")
    with st.form("match_form"):
        winner = st.selectbox("Winner", options=st.session_state.rankings["Player"].to_list())
        loser = st.selectbox("Loser", options=st.session_state.rankings["Player"].to_list())
        submit = st.form_submit_button("Record Match")
        if submit:
            if winner == loser:
                st.error("Winner and loser cannot be the same person.")
            else:
                record_match(winner, loser)
                st.success(f"Match recorded: {winner} defeated {loser}.")
                st.header("Updated Rankings")
                # Display updated rankings with correct rank numbers
                updated_rankings = st.session_state.rankings.copy()
                updated_rankings.insert(0, "Rank", range(1, len(updated_rankings) + 1))
                st.dataframe(updated_rankings.set_index("Rank"))  # Use Rank as the index to remove the unnamed index column

