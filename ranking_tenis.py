import pandas as pd
import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate and connect to Google Sheets
def authenticate_gsheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(credentials)
    return client.open(sheet_name)

# Initialize default data for Rankings and Match History
def initialize_data(sheet):
    players = ["Marinkovic", "Joseto", "Hernan", "Pavez", "Bozzo", "Bishara", "Hederra", "Poch", "Juande", "Hans"]
    points = [1000 for _ in players]

    # Initialize Rankings
    rankings_sheet = sheet.worksheet("Rankings")
    if len(rankings_sheet.get_all_records()) == 0:
        rankings_df = pd.DataFrame({
            "Player": players,
            "Points": points,
            "Matches Played": [0 for _ in players],
            "Wins": [0 for _ in players],
            "Losses": [0 for _ in players],
        })
        rankings_sheet.update([rankings_df.columns.values.tolist()] + rankings_df.values.tolist())

    # Initialize Match History
    match_history_sheet = sheet.worksheet("Match History")
    if len(match_history_sheet.get_all_records()) == 0:
        match_history_df = pd.DataFrame(columns=["Date", "Winner", "Loser", "Points Exchanged"])
        match_history_sheet.update([match_history_df.columns.values.tolist()])

# Load data from Google Sheets
def load_data(sheet):
    rankings_sheet = sheet.worksheet("Rankings")
    match_history_sheet = sheet.worksheet("Match History")

    rankings_data = rankings_sheet.get_all_records()
    rankings = pd.DataFrame(rankings_data)

    match_history_data = match_history_sheet.get_all_records()
    match_history = pd.DataFrame(match_history_data)

    return rankings, match_history

# Save data to Google Sheets
def save_data(sheet, rankings, match_history):
    rankings_sheet = sheet.worksheet("Rankings")
    match_history_sheet = sheet.worksheet("Match History")

    rankings_sheet.clear()
    rankings_sheet.update([rankings.columns.values.tolist()] + rankings.values.tolist())

    match_history_sheet.clear()
    match_history_sheet.update([match_history.columns.values.tolist()] + match_history.values.tolist())

# Connect to Google Sheets
sheet_name = "Tennis Rankings and Match History"
sheet = authenticate_gsheet(sheet_name)

# Initialize data if needed
initialize_data(sheet)

# Load into session state
rankings, match_history = load_data(sheet)
if "rankings" not in st.session_state:
    st.session_state.rankings = rankings
if "match_history" not in st.session_state:
    st.session_state.match_history = match_history

# Function to record a match and update rankings
def record_match(winner, loser, base_points=50, upset_multiplier=1.5):
    rankings = st.session_state.rankings
    match_history = st.session_state.match_history

    winner_points = rankings.loc[rankings['Player'] == winner, 'Points'].values[0]
    loser_points = rankings.loc[rankings['Player'] == loser, 'Points'].values[0]

    points_exchanged = base_points + (0.05 * loser_points)
    if winner_points < loser_points:
        points_exchanged *= upset_multiplier
    points_exchanged = int(round(points_exchanged))

    rankings.loc[rankings['Player'] == winner, 'Points'] += points_exchanged
    rankings.loc[rankings['Player'] == loser, 'Points'] -= points_exchanged
    rankings['Points'] = rankings['Points'].clip(lower=0)
    rankings['Points'] = rankings['Points'].astype(int)
    rankings.sort_values(by="Points", ascending=False, inplace=True, ignore_index=True)

    rankings.loc[rankings['Player'] == winner, 'Matches Played'] += 1
    rankings.loc[rankings['Player'] == loser, 'Matches Played'] += 1
    rankings.loc[rankings['Player'] == winner, 'Wins'] += 1
    rankings.loc[rankings['Player'] == loser, 'Losses'] += 1

    new_match = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Winner": winner,
        "Loser": loser,
        "Points Exchanged": points_exchanged,
    }
    st.session_state.match_history = pd.concat([match_history, pd.DataFrame([new_match])], ignore_index=True)

    save_data(sheet, st.session_state.rankings, st.session_state.match_history)

# Streamlit UI
st.title("🎾 Ranking Shishi de Tenis")
menu = st.sidebar.selectbox("Menu", ["Ver Ranking", "Ver Historial de Partidos", "Anotar Resultado"])

if menu == "Ver Ranking":
    st.header("📊 Ranking Actual")
    rankings = st.session_state.rankings.copy()
    rankings.insert(0, "Rank", range(1, len(rankings) + 1))
    st.dataframe(rankings.set_index("Rank"))

elif menu == "Ver Historial de Partidos":
    st.header("📜 Historial de Partidos")
    if st.session_state.match_history.empty:
        st.write("No matches have been recorded yet.")
    else:
        st.table(st.session_state.match_history)

elif menu == "Anotar Resultado":
    st.header("🏅 Anotar Resultado")
    st.write("Ingrese el ganador y el perdedor del partido.")

    player_list = st.session_state.rankings["Player"].tolist()

    if len(player_list) < 2:
        st.warning("Debe haber al menos dos jugadores para registrar un partido.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            winner = st.selectbox("Ganador", options=player_list, key="winner_select")
        with col2:
            loser = st.selectbox("Perdedor", options=player_list, key="loser_select")

        if st.button("Registrar Partido"):
            if winner == loser:
                st.error("El ganador y el perdedor no pueden ser el mismo jugador.")
            else:
                record_match(winner, loser)
                st.success(f"¡Partido registrado! {winner} derrotó a {loser}.")
                st.experimental_rerun()
