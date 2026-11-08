import json
from pathlib import Path
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
from layout import create_layout, apply_chart_template, create_vulture_opportunities_table, create_empty_vulture_heatmap, create_empty_opportunities_table
from callbacks import register_callbacks, register_settings_verification_callbacks

def process_gold_data(log_file_path):
    """
    Process the log file to extract total gold for each player.

    Args:
        log_file_path (str): Path to the JSONL log file.

    Returns:
        dict: A dictionary mapping player IDs to their total gold.
    """
    total_gold = {}

    # Read the log file line by line
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            data = json.loads(line)
            states = data.get("states", {})

            # Accumulate gold for each player
            for player_id, state in states.items():
                gold = state.get("gold", 0)
                total_gold[player_id] = total_gold.get(player_id, 0) + gold

    return total_gold

def process_gold_data_by_round(log_file_path):
    """
    Process the log file to extract gold data for each player by round.

    Args:
        log_file_path (str): Path to the JSONL log file.

    Returns:
        pd.DataFrame: A DataFrame with columns for round, player ID, and gold.
    """
    data = []

    # Read the log file line by line
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            entry = json.loads(line)
            round_number = entry.get("round", 0)
            states = entry.get("states", {})

            for player_id, state in states.items():
                gold = state.get("gold", 0)
                data.append({"Round": round_number, "Player ID": player_id, "Gold": gold})

    return pd.DataFrame(data)

def process_points_data_by_round(log_file_path):
    """
    Process the log file to extract points data for each player by round.

    Args:
        log_file_path (str): Path to the JSONL log file.

    Returns:
        pd.DataFrame: A DataFrame with columns for round, player ID, and points.
    """
    data = []

    # Read the log file line by line
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            entry = json.loads(line)
            round_number = entry.get("round", 0)
            states = entry.get("states", {})

            for player_id, state in states.items():
                points = state.get("points", 0)
                data.append({"Round": round_number, "Player ID": player_id, "Points": points})

    return pd.DataFrame(data)

# Rename the dungeon_dice Mode table to a D&D-themed name
dungeon_dice_mode_table_title = "Dungeon Dice Insights"

# Example: Auto-populate missing dice values in the dataframe
def auto_populate_dice_values(df, dice_values):
    # Ensure the 'dice_column' exists in the dataframe
    if 'dice_column' not in df.columns:
        df['dice_column'] = [None] * len(df)

    for dice in dice_values:
        if dice not in df['dice_column'].values:
            df = pd.concat([df, pd.DataFrame({'dice_column': [dice], 'value_column': [0]})], ignore_index=True)
    return df

# Ensure all lists in the dictionary have the same length
def equalize_list_lengths(data_dict):
    max_length = max(len(lst) for lst in data_dict.values())
    for key, lst in data_dict.items():
        if len(lst) < max_length:
            data_dict[key].extend([None] * (max_length - len(lst)))
    return data_dict

# Function to transform data into the desired table format
def transform_to_table_format(data_dict):
    die_formats = data_dict["Die Format"]
    num_die = data_dict["Num Die"]
    times_appeared = data_dict["Times Appeared"]
    amount_of_bids = data_dict["Amount of Bids"]
    mean_price = data_dict["Mean Price"]

    # Create a list of dictionaries, each representing a row in the table
    table_data = []

    for i in range(len(num_die)):
        row = {"Die/amount": num_die[i]}
        for die in die_formats:
            row[die] = f"({times_appeared[i] if i < len(times_appeared) else 0}, {amount_of_bids[i] if i < len(amount_of_bids) else 0}, {mean_price[i] if i < len(mean_price) else 0})"
        table_data.append(row)

    return pd.DataFrame(table_data)

# Initialize Dash app
app = Dash(__name__)

def load_agent_settings():
    """Load agent settings from the settings file."""
    try:
        settings_path = Path(__file__).parent.parent / "data" / "settings.json"
        with open(settings_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return {}

def create_initial_charts():
    """Create initial empty charts."""
    # Create empty dataframes
    empty_df = pd.DataFrame({"Round": [0], "Player ID": ["Waiting for data..."], "Gold": [0]})
    empty_points_df = pd.DataFrame({"Round": [0], "Player ID": ["Waiting for data..."], "Points": [0]})
    
    # Create initial charts
    gold_fig = px.line(
        empty_df,
        x="Round",
        y="Gold",
        color="Player ID",
        title="💰 Gold per Player by Round",
        markers=True
    )
    gold_fig = apply_chart_template(gold_fig, "💰 Gold per Player by Round")
    
    points_fig = px.line(
        empty_points_df,
        x="Round",
        y="Points",
        color="Player ID",
        title="⭐ Points per Player by Round",
        markers=True
    )
    points_fig = apply_chart_template(points_fig, "⭐ Points per Player by Round")
    
    return gold_fig, points_fig

if __name__ == "__main__":
    # Load current settings for the dashboard
    current_settings = load_agent_settings()
    
    # Create initial charts
    gold_fig, points_fig = create_initial_charts()
    
    # Create initial agent stats (will be updated by callbacks)
    initial_agent_stats = {
        'gold': 0,
        'points': 0,
        'bid_winrate': 0.0,
        'current_strategy': 'Vulture Mode',
        'rounds_played': 0,
        'total_bids': 0,
        'wins': 0
    }

    # Example vulture heatmap (empty initially)
    vulture_heatmap_fig = create_empty_vulture_heatmap()
    
    # Example vulture opportunities table (empty initially)
    vulture_table = create_empty_opportunities_table()

    # Set app title and layout
    app.title = "🎯 DoomGuy666 Agent Management Dashboard"

    # Set the comprehensive app layout
    app.layout = create_layout(
        fig=gold_fig,
        points_fig=points_fig,
        vulture_heatmap_fig=vulture_heatmap_fig,
        vulture_table=vulture_table,
        agent_stats=initial_agent_stats,
        current_settings=current_settings
    )

    # Register all callbacks
    register_callbacks(app)
    register_settings_verification_callbacks(app)

    print("🚀 Starting DoomGuy666 Agent Management Dashboard...")
    print("📊 Dashboard URL: http://localhost:8050")
    print("⚙️ Settings will auto-save when changed")
    print("📈 Charts will auto-update when games are running")
    
    app.run(debug=True, port=8050)