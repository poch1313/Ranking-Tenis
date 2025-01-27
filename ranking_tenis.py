import pandas as pd
import streamlit as st
from datetime import datetime

# Initialize default data
players = ["Marinkovic", "Joseto", "Hernan", "Pavez", "Bozzo", "Bishara", "Hederra", "Poch", "Juande", "Hans"]
points = [1000 for _ in players]

# Initialize session state for rankings and match history
if "rankings" not in st.session_state:
    st.session_state.rankings = pd.DataFrame({
        "Player": players,
        "Points": points,
        "Matches Played": [0 for _ in players],
        "Wins": [0 for _ in players],
        "Losses": [0 for _ in players]
    })

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

    # Update matches played, wins, and losses
    rankings.loc[rankings['Player'] == winner, 'Matches Played'] += 1
    rankings.loc[rankings['Player'] == loser, 'Matches Played'] += 1
    rankings.loc[rankings['Player'] == winner, 'Wins'] += 1
    rankings.loc[rankings['Player'] == loser, 'Losses'] += 1

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
