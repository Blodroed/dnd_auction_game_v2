import json
import os
import sys
import threading
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dash.dependencies import Output, Input, State
from dash import callback_context, html
import pandas as pd
import plotly.express as px
from layout import apply_chart_template, highlight_agent_in_chart, create_vulture_heatmap, create_vulture_opportunities_table
from utlils import extract_agent_performance, analyze_vulture_opportunities, get_agent_id_from_logs

# Add parent directory to path for settings_monitor import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import settings monitor
try:
    from settings_monitor import get_settings_monitor
    SETTINGS_MONITOR_AVAILABLE = True
    logger.info("✅ Settings monitor imported successfully")
except ImportError as e:
    SETTINGS_MONITOR_AVAILABLE = False
    logger.warning(f"⚠️ Settings monitor not available: {e}")
    
    # Create a mock monitor for when the real one isn't available
    class MockMonitor:
        def get_dashboard_verification_data(self):
            return {
                'status': '❌ UNAVAILABLE',
                'bid_mode': 'UNKNOWN',
                'last_updated': 'N/A',
                'default_correct': False,
                'issues_count': 1,
                'issues': ['Settings monitor unavailable'],
                'timestamp': 'N/A'
            }
    
    def get_settings_monitor():
        return MockMonitor()

# Global cache for log data and agent information
class LogDataCache:
    def __init__(self):
        self.current_file = None
        self.file_position = 0
        self.cached_data = []
        self.gold_df = pd.DataFrame()
        self.points_df = pd.DataFrame()
        self.agent_info = {"name": "DoomGuy666", "a_id": "", "player_id": "doom_agent_666"}
        self.agent_stats = {
            'gold': 0,
            'points': 0,
            'bid_winrate': 0.0,
            'current_strategy': 'Unknown',
            'rounds_played': 0,
            'total_bids': 0,
            'wins': 0,
            'last_round_gold': 0,
            'last_round_points': 0,
            'gold_change': 0,
            'points_change': 0
        }
        self.previous_stats = None
        self.vulture_heatmap_df = pd.DataFrame()
        self.vulture_opportunities = []
        self.lock = threading.Lock()
    
    def update_cache(self, file_path):
        with self.lock:
            try:
                # If file changed, reset cache and read entire file
                if str(file_path) != str(self.current_file):
                    logger.info(f"🎯 Dashboard: Switching to new log file: {file_path}")
                    self.current_file = file_path
                    self.file_position = 0
                    self.cached_data = []
                
                if not file_path or not file_path.exists():
                    return
                
                # For new files or if file is smaller (reset), read entire file
                file_size = file_path.stat().st_size
                if self.file_position > file_size:
                    logger.info(f"🔄 Dashboard: File reset detected, reading entire file")
                    self.file_position = 0
                    self.cached_data = []
                
                # Read lines from current position
                with open(file_path, 'r') as f:
                    f.seek(self.file_position)
                    new_lines = f.readlines()
                    self.file_position = f.tell()
                
                # Parse new lines and add to cache
                new_entries = 0
                for line in new_lines:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            self.cached_data.append(entry)
                            new_entries += 1
                            
                            # Extract agent ID from current_agent field early
                            if "current_agent" in entry and not self.agent_info.get("a_id"):
                                self.agent_info["a_id"] = entry["current_agent"]
                                logger.info(f"🤖 Dashboard: Detected agent ID: {self.agent_info['a_id']}")
                                
                        except json.JSONDecodeError:
                            continue
                
                if new_entries > 0:
                    logger.info(f"📊 Dashboard: Added {new_entries} new log entries, total: {len(self.cached_data)}")
                
                # Update dataframes
                self._rebuild_dataframes()
                
            except Exception as e:
                logger.error(f"❌ Dashboard cache error: {e}")
    
    def _rebuild_dataframes(self):
        """Rebuild dataframes from cached data and update agent stats"""
        gold_data = []
        points_data = []
        agent_rounds = []
        
        for entry in self.cached_data:
            round_number = entry.get("round", 0)
            states = entry.get("states", {})
            
            # Extract agent information if available - prioritize current_agent field
            if "current_agent" in entry and not self.agent_info.get("a_id"):
                self.agent_info["a_id"] = entry["current_agent"]
            elif "a_id" in entry:
                self.agent_info.update(entry.get("a_id", {}))
            
            for player_id, state in states.items():
                gold = state.get("gold", 0)
                points = state.get("points", 0)
                gold_data.append({"Round": round_number, "Player ID": player_id, "Gold": gold})
                points_data.append({"Round": round_number, "Player ID": player_id, "Points": points})
                
                # Track our agent's performance using exact match
                if (self.agent_info.get("a_id") and 
                    self.agent_info["a_id"] == str(player_id)):
                    agent_rounds.append({
                        'round': round_number,
                        'gold': gold,
                        'points': points
                    })
        
        self.gold_df = pd.DataFrame(gold_data)
        self.points_df = pd.DataFrame(points_data)
        
        # Update agent stats and vulture analysis
        if self.cached_data:
            # Get agent ID if we don't have it
            if not self.agent_info.get("a_id"):
                detected_id = get_agent_id_from_logs(self.cached_data)
                if detected_id:
                    self.agent_info["a_id"] = detected_id
            
            # Extract performance if we have agent ID
            if self.agent_info.get("a_id"):
                # Store previous stats for change tracking
                self.previous_stats = self.agent_stats.copy() if self.agent_stats else None
                
                # Update current stats
                new_stats = extract_agent_performance(self.cached_data, self.agent_info["a_id"])
                if new_stats:
                    self.agent_stats = new_stats
                    
                    # Calculate changes from previous round
                    if self.previous_stats and agent_rounds:
                        latest_round = max(agent_rounds, key=lambda x: x['round'])
                        self.agent_stats['last_round_gold'] = latest_round['gold']
                        self.agent_stats['last_round_points'] = latest_round['points']
                        self.agent_stats['gold_change'] = latest_round['gold'] - self.previous_stats.get('last_round_gold', latest_round['gold'])
                        self.agent_stats['points_change'] = latest_round['points'] - self.previous_stats.get('last_round_points', latest_round['points'])
            
            # Analyze vulture opportunities
            try:
                self.vulture_heatmap_df, self.vulture_opportunities = analyze_vulture_opportunities(self.cached_data)
                if not self.vulture_heatmap_df.empty:
                    logger.debug(f"🎲 Dashboard: Generated vulture heatmap with {len(self.vulture_heatmap_df)} dice combinations")
                if self.vulture_opportunities:
                    logger.debug(f"🎯 Dashboard: Found {len(self.vulture_opportunities)} vulture opportunities")
            except Exception as e:
                logger.error(f"❌ Dashboard: Error analyzing vulture opportunities: {e}")
                self.vulture_heatmap_df = pd.DataFrame()
                self.vulture_opportunities = []
    
    def get_dataframes(self):
        with self.lock:
            logger.debug(f"🔍 Cache get_dataframes: gold={len(self.gold_df)}, points={len(self.points_df)}")
            return self.gold_df.copy(), self.points_df.copy()
    
    def get_agent_info(self):
        with self.lock:
            logger.debug(f"🤖 Cache get_agent_info: agent_id={self.agent_info.get('a_id', 'None')}")
            return self.agent_info.copy(), self.agent_stats.copy()
    
    def get_vulture_data(self):
        with self.lock:
            logger.debug(f"🎯 Cache get_vulture_data: heatmap={self.vulture_heatmap_df.shape}, opps={len(self.vulture_opportunities)}")
            return self.vulture_heatmap_df.copy(), self.vulture_opportunities.copy()

# Global cache instance
cache = LogDataCache()

# Function to get the newest log file
def get_newest_file():
    logs_dir = Path(__file__).parent.parent / "logs"
    try:
        return max(logs_dir.glob("*.jsonl"), key=os.path.getmtime)
    except ValueError:
        return None

# File watcher class
class LogFileWatcher(FileSystemEventHandler):
    def __init__(self):
        self.logs_dir = Path(__file__).parent.parent / "logs"
        
    def on_modified(self, event):
        if not event.is_directory and str(event.src_path).endswith('.jsonl'):
            newest_file = get_newest_file()
            if newest_file:
                cache.update_cache(newest_file)
    
    def on_created(self, event):
        if not event.is_directory and str(event.src_path).endswith('.jsonl'):
            newest_file = get_newest_file()
            if newest_file:
                cache.update_cache(newest_file)

# Start file watcher
observer = None
def start_file_watcher():
    global observer
    if observer is None:
        event_handler = LogFileWatcher()
        observer = Observer()
        logs_dir = Path(__file__).parent.parent / "logs"
        
        logger.info(f"🎯 Dashboard: Starting file watcher for directory: {logs_dir}")
        
        if logs_dir.exists():
            observer.schedule(event_handler, path=str(logs_dir), recursive=False)
            observer.start()
            logger.info(f"✅ Dashboard: File watcher started successfully")
        else:
            logger.warning(f"⚠️ Dashboard: Logs directory does not exist: {logs_dir}")
        
        # Initial cache update and testing
        newest_file = get_newest_file()
        if newest_file:
            logger.info(f"🔍 Dashboard: Found newest file: {newest_file}")
            cache.update_cache(newest_file)
            
            # Test the data format for debugging
            from utlils import test_log_data_format
            test_entries = cache.cached_data[:5] if cache.cached_data else []
            test_log_data_format(test_entries)
        else:
            logger.warning(f"❌ Dashboard: No log files found in: {logs_dir}")

# Register callbacks
def register_callbacks(app):
    # Start the file watcher when registering callbacks
    start_file_watcher()
    
    @app.callback(
        [Output("gold-chart", "figure"), Output("points-chart", "figure"), 
         Output("vulture-heatmap", "figure"), Output("vulture-table-container", "children"),
         Output("agent-data-store", "data")],
        [Input("interval", "n_intervals")]
    )
    def update_charts_and_agent_data(n):
        logger.debug(f"🔄 Dashboard callback triggered (interval #{n})")
        try:
            # Force check for newest file every few intervals
            if n % 5 == 0:  # Check every 5 intervals (~5 seconds)
                newest_file = get_newest_file()
                if newest_file:
                    cache.update_cache(newest_file)
            
            # Get cached data instead of reading from file
            gold_data_df, points_data_df = cache.get_dataframes()
            agent_info, agent_stats = cache.get_agent_info()
            vulture_heatmap_df, vulture_opportunities = cache.get_vulture_data()
            
            logger.debug(f"📊 Callback data check:")
            logger.debug(f"   Gold DF: {len(gold_data_df)} rows, empty: {gold_data_df.empty}")
            logger.debug(f"   Points DF: {len(points_data_df)} rows, empty: {points_data_df.empty}")
            logger.debug(f"   Agent Info: {agent_info}")
            logger.debug(f"   Vulture Opportunities: {len(vulture_opportunities)}")
            
            if gold_data_df.empty or points_data_df.empty:
                logger.warning("❌ No data available - falling back to empty charts")
                raise ValueError("No data available")

            # Update the gold chart
            logger.debug(f"📈 Creating gold chart with {len(gold_data_df)} data points")
            logger.debug(f"   Sample data: {gold_data_df.head(3).to_dict('records')}")
            
            gold_fig = px.line(
                gold_data_df,
                x="Round",
                y="Gold",
                color="Player ID",
                title="💰 Gold per Player by Round",
                markers=True
            )
            gold_fig = apply_chart_template(gold_fig, "💰 Gold per Player by Round")
            
            # Highlight our agent if we have the ID
            if agent_info.get("a_id"):
                gold_fig = highlight_agent_in_chart(gold_fig, agent_info["a_id"], agent_info.get("name", "DoomGuy666"))
                logger.debug(f"✅ Gold chart highlighted for agent: {agent_info['a_id']}")
            
            logger.debug(f"✅ Gold chart created successfully")

            # Update the points chart
            logger.debug(f"⭐ Creating points chart with {len(points_data_df)} data points")
            
            points_fig = px.line(
                points_data_df,
                x="Round",
                y="Points",
                color="Player ID",
                title="⭐ Points per Player by Round",
                markers=True
            )
            points_fig = apply_chart_template(points_fig, "⭐ Points per Player by Round")
            
            # Highlight our agent if we have the ID
            if agent_info.get("a_id"):
                points_fig = highlight_agent_in_chart(points_fig, agent_info["a_id"], agent_info.get("name", "DoomGuy666"))
                logger.debug(f"✅ Points chart highlighted for agent: {agent_info['a_id']}")
            
            logger.debug(f"✅ Points chart created successfully")
            
            # Update vulture heatmap
            if not vulture_heatmap_df.empty:
                vulture_heatmap_fig = create_vulture_heatmap(vulture_heatmap_df)
                logger.debug(f"✅ Vulture heatmap created with {vulture_heatmap_df.shape} data")
            else:
                from layout import create_empty_vulture_heatmap
                vulture_heatmap_fig = create_empty_vulture_heatmap()
            
            # Update vulture opportunities table component
            if vulture_opportunities:
                vulture_table_component = create_vulture_opportunities_table(vulture_opportunities)
                logger.debug(f"✅ Vulture table created with {len(vulture_opportunities)} opportunities")
            else:
                from layout import create_empty_opportunities_table
                vulture_table_component = create_empty_opportunities_table()
                
            # Prepare agent data for store - include updated stats
            agent_data = {
                'agent_info': agent_info,
                'agent_stats': agent_stats,
                'timestamp': n  # Add timestamp to force updates
            }
            
            logger.debug(f"🚀 Returning dashboard data successfully")
            
        except ValueError as e:
            logger.warning(f"❌ ValueError in callback: {e}")
            # No files found, initialize empty charts
            gold_fig = px.line(title="💰 Gold per Player by Round")
            gold_fig = apply_chart_template(gold_fig, "💰 Gold per Player by Round")

            points_fig = px.line(title="⭐ Points per Player by Round")
            points_fig = apply_chart_template(points_fig, "⭐ Points per Player by Round")
            
            from layout import create_empty_vulture_heatmap, create_empty_opportunities_table
            vulture_heatmap_fig = create_empty_vulture_heatmap()
            vulture_table_component = create_empty_opportunities_table()
            
            agent_data = {
                'agent_info': {},
                'agent_stats': {}
            }
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in callback: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback to empty charts
            gold_fig = px.line(title="💰 Gold per Player by Round - ERROR")
            points_fig = px.line(title="⭐ Points per Player by Round - ERROR")
            from layout import create_empty_vulture_heatmap, create_empty_opportunities_table
            vulture_heatmap_fig = create_empty_vulture_heatmap()
            vulture_table_component = create_empty_opportunities_table()
            agent_data = {'agent_info': {}, 'agent_stats': {}}

        return gold_fig, points_fig, vulture_heatmap_fig, vulture_table_component, agent_data
    
    # Stats panel update callback
    @app.callback(
        Output("agent-stats-panel", "children"),
        [Input("agent-data-store", "data")]
    )
    def update_agent_stats_panel(agent_data):
        """Update the agent stats panel with real-time data."""
        if not agent_data or not agent_data.get('agent_stats'):
            logger.debug("📊 No agent data available for stats panel")
            from layout import create_agent_stats_panel
            return [create_agent_stats_panel()]
        
        agent_stats = agent_data.get('agent_stats', {})
        agent_info = agent_data.get('agent_info', {})
        
        logger.debug(f"📊 Updating stats panel for agent: {agent_info.get('a_id', 'Unknown')}")
        logger.debug(f"📊 Stats: Gold={agent_stats.get('gold', 0)}, Points={agent_stats.get('points', 0)}")
        
        from layout import create_agent_stats_panel
        return [create_agent_stats_panel(agent_stats)]
    
    # Bid mode explanation callback
    @app.callback(
        Output("bid-mode-explanation", "children"),
        [Input("bid-mode-dropdown", "value")]
    )
    def update_bid_mode_explanation(selected_mode):
        """Update the explanation text based on selected bid mode."""
        explanations = {
            "MEAN_GREEN": [
                "🎯 ", html.B("Mean Green"), " - The intelligent choice! Uses statistical analysis (mean + standard deviation) to determine optimal bid amounts. ",
                "This mode balances risk and reward by bidding above average levels while staying within budget constraints. Best for consistent performance."
            ],
            "EVEN_STEVEN": [
                "📊 ", html.B("Even Steven"), " - Distributes your budget equally across all selected auctions. ",
                "Simple and predictable strategy that doesn't favor any particular auction. Good for diversification but may miss high-value opportunities."
            ],
            "ALL_OR_NOTHING": [
                "🔥 ", html.B("All or Nothing"), " - Concentrates most of your budget on 1-3 highest value auctions. ",
                "High risk, high reward strategy. Uses focus ratio to determine how many auctions to target. Great when you spot clear winners."
            ],
            "HIGHER_LOWER": [
                "📈 ", html.B("Higher Lower"), " - Allocates 50% of budget to the best auction, then distributes the rest proportionally. ",
                "Balanced approach that emphasizes the most valuable opportunity while still participating in others. Good middle-ground strategy."
            ],
            "AGGRESSIVE_SPREAD": [
                "💥 ", html.B("Aggressive Spread"), " - Spends 85% of available gold aggressively to prevent accumulation. ",
                "Maximum spending strategy that front-loads better auctions. Prevents losing due to hoarding but requires careful risk management."
            ]
        }
        
        return explanations.get(selected_mode, ["Select a bid mode to see explanation."])
    
    # Settings update callbacks
    @app.callback(
        Output("settings-store", "data"),
        [Input("aggression-slider", "value"),
         Input("max-bid-ratio-slider", "value"),
         Input("high-value-input", "value"),
         Input("bid-mode-dropdown", "value"),
         Input("focus-ratio-slider", "value"),
         Input("spending-ratio-slider", "value"),
         Input("min-reserve-input", "value"),
         Input("economy-toggles", "value")]
    )
    def update_settings(aggression, max_bid_ratio, high_value, bid_mode, focus_ratio, 
                       spending_ratio, min_reserve, economy_toggles):
        """Update and save settings when user changes them in the dashboard."""
        
        if callback_context.triggered:
            try:
                # Load current settings
                settings_path = Path(__file__).parent.parent / "data" / "settings.json"
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                
                # Update settings with new values
                settings['strategy']['aggression_multiplier'] = aggression
                settings['strategy']['max_bid_ratio'] = max_bid_ratio
                settings['strategy']['high_value_threshold'] = high_value
                settings['bid_modes']['current_mode'] = bid_mode
                settings['bid_modes']['focus_ratio'] = focus_ratio
                settings['economy']['spending_ratio'] = spending_ratio
                settings['economy']['min_reserve_gold'] = min_reserve
                
                # Handle toggles
                if economy_toggles:
                    settings['economy']['use_max_bet_limit'] = 'use_max_bet_limit' in economy_toggles
                    settings['economy']['emergency_spending_enabled'] = 'emergency_spending' in economy_toggles
                
                # Update timestamp
                from datetime import datetime
                settings['meta']['last_updated'] = datetime.now().isoformat()
                
                # Save updated settings
                with open(settings_path, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                return settings
                
            except Exception as e:
                print(f"Error updating settings: {e}")
                return {}
        
        return {}

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

def register_settings_verification_callbacks(app):
    """Register callbacks for the settings verification panel."""
    
    @app.callback(
        [
            Output('verification-status', 'children'),
            Output('verification-status', 'style'),
            Output('verification-bid-mode', 'children'),
            Output('verification-last-updated', 'children'),
            Output('verification-issues-count', 'children'),
            Output('verification-issues-count', 'style'),
            Output('verification-issues-detail', 'children'),
            Output('verification-issues-detail', 'style')
        ],
        [Input('interval', 'n_intervals')]
    )
    def update_settings_verification(n_intervals):
        """Update the settings verification panel with current status."""
        try:
            monitor = get_settings_monitor()
            verification_data = monitor.get_dashboard_verification_data()
            
            # Status display
            status_text = verification_data['status']
            status_color = "#4CAF50" if "VERIFIED" in status_text else "#F44336"
            status_style = {
                "fontSize": "14px", 
                "fontWeight": "bold", 
                "margin": "5px 0", 
                "textAlign": "center",
                "color": status_color
            }
            
            # Bid mode
            bid_mode = verification_data['bid_mode']
            
            # Last updated (format timestamp)
            last_updated = verification_data['last_updated']
            if last_updated != 'N/A' and 'T' in last_updated:
                # Format ISO timestamp to readable format
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    last_updated = dt.strftime('%H:%M:%S')
                except:
                    last_updated = last_updated[:10]  # Just show date
            
            # Issues count
            issues_count = verification_data['issues_count']
            issues_count_color = "#4CAF50" if issues_count == 0 else "#F44336"
            issues_count_style = {
                "fontSize": "20px", 
                "fontWeight": "bold", 
                "margin": "5px 0", 
                "textAlign": "center",
                "color": issues_count_color
            }
            
            # Issues detail
            issues = verification_data.get('issues', [])
            if issues:
                issues_detail = html.Div([
                    html.H5("⚠️ Issues Found:", style={"color": "#F44336", "marginBottom": "10px"}),
                    html.Ul([
                        html.Li(issue, style={"color": "#ccc", "marginBottom": "5px"}) 
                        for issue in issues
                    ])
                ])
                issues_detail_style = {"display": "block", "marginTop": "15px", "padding": "15px", 
                                     "backgroundColor": "var(--night)", "borderRadius": "8px",
                                     "border": "1px solid #F44336"}
            else:
                issues_detail = []
                issues_detail_style = {"display": "none"}
            
            logger.info(f"🔍 Settings verification updated: {status_text}, Mode: {bid_mode}, Issues: {issues_count}")
            
            return (
                status_text, status_style,
                bid_mode,
                last_updated,
                str(issues_count),
                issues_count_style,
                issues_detail,
                issues_detail_style
            )
            
        except Exception as e:
            logger.error(f"❌ Settings verification callback failed: {e}")
            return (
                "❌ ERROR", 
                {"fontSize": "14px", "fontWeight": "bold", "margin": "5px 0", "textAlign": "center", "color": "#F44336"},
                "UNKNOWN",
                "ERROR",
                "1",
                {"fontSize": "20px", "fontWeight": "bold", "margin": "5px 0", "textAlign": "center", "color": "#F44336"},
                [html.P(f"Verification error: {e}", style={"color": "#F44336"})],
                {"display": "block", "marginTop": "15px", "padding": "15px", 
                 "backgroundColor": "var(--night)", "borderRadius": "8px", "border": "1px solid #F44336"}
            )