"""
Utility functions for the DoomGuy666 Agent Dashboard.

This module provides utilities for:
- Extracting agent performance data from logs
- Calculating vulture analysis metrics
- Managing real-time data updates
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np


def extract_agent_performance(log_entries: List[Dict], agent_id: str) -> Dict:
    """
    Extract performance metrics for a specific agent from log entries.
    
    Args:
        log_entries: List of log entry dictionaries
        agent_id: The agent ID to analyze (e.g., "local_rand_id_234156")
        
    Returns:
        Dictionary containing performance metrics
    """
    agent_data = []
    bid_wins = 0
    total_bids = 0
    
    for entry in log_entries:
        states = entry.get("states", {})
        prev_auctions = entry.get("prev_auctions", {})
        
        # Find our agent in states
        agent_state = None
        for player_id, state in states.items():
            if agent_id in str(player_id):
                agent_state = state
                break
        
        if agent_state:
            agent_data.append({
                'round': entry.get('round', 0),
                'gold': agent_state.get('gold', 0),
                'points': agent_state.get('points', 0)
            })
        
        # Count bid wins from previous auctions
        for auction_id, auction_result in prev_auctions.items():
            bids = auction_result.get('bids', [])  # bids is a list, not dict
            winner = auction_result.get('winner')
            
            # Check if agent participated in this auction
            agent_participated = False
            for bid in bids:
                if isinstance(bid, dict) and agent_id in str(bid.get('a_id', '')):
                    agent_participated = True
                    break
            
            if agent_participated:
                total_bids += 1
                # Check if agent won (winner is the first bidder in the list for this game)
                if bids and isinstance(bids[0], dict) and agent_id in str(bids[0].get('a_id', '')):
                    bid_wins += 1
    
    # Calculate metrics
    latest_data = agent_data[-1] if agent_data else {'gold': 0, 'points': 0, 'round': 0}
    bid_winrate = bid_wins / total_bids if total_bids > 0 else 0.0
    
    return {
        'gold': latest_data['gold'],
        'points': latest_data['points'],
        'bid_winrate': bid_winrate,
        'current_strategy': 'Vulture Mode',  # Could be extracted from agent logs
        'rounds_played': len(agent_data),
        'total_bids': total_bids,
        'wins': bid_wins
    }


def analyze_vulture_opportunities(log_entries: List[Dict]) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Analyze dice combinations for vulture opportunities.
    
    Args:
        log_entries: List of log entry dictionaries
        
    Returns:
        Tuple of (heatmap_data_df, opportunities_list)
    """
    dice_analysis = {}  # {(num_dice, die_type): {'appearances': count, 'total_bids': count, 'no_bid_rounds': count}}
    
    for entry in log_entries:
        auctions = entry.get("auctions", {})
        prev_auctions = entry.get("prev_auctions", {})
        
        # Analyze current auctions - handle the actual data format: {"die": 6, "num": 3, "bonus": 2}
        for auction_id, auction_data in auctions.items():
            die_type = auction_data.get("die", 6)
            num_dice = auction_data.get("num", 1)
            
            key = (num_dice, die_type)
            if key not in dice_analysis:
                dice_analysis[key] = {'appearances': 0, 'total_bids': 0, 'no_bid_rounds': 0}
            
            dice_analysis[key]['appearances'] += 1
        
        # Analyze previous auctions for bid patterns - same format
        for auction_id, auction_result in prev_auctions.items():
            die_type = auction_result.get("die", 6)
            num_dice = auction_result.get("num", 1)
            bids = auction_result.get("bids", [])
            
            key = (num_dice, die_type)
            if key in dice_analysis:
                dice_analysis[key]['total_bids'] += len(bids)
                if len(bids) == 0:
                    dice_analysis[key]['no_bid_rounds'] += 1
    
    # Create heatmap data
    heatmap_data = []
    opportunities = []
    
    for (num_dice, die_type), stats in dice_analysis.items():
        if stats['appearances'] > 0:
            avg_competition = stats['total_bids'] / stats['appearances']
            no_bid_percentage = stats['no_bid_rounds'] / stats['appearances']
            
            # Calculate vulture score (higher = better opportunity)
            # Factors: low competition, high no-bid percentage, reasonable frequency
            vulture_score = (
                (1.0 - min(avg_competition / 5.0, 1.0)) * 0.4 +  # Lower competition is better
                no_bid_percentage * 0.4 +                        # Higher no-bid rate is better
                min(stats['appearances'] / 10.0, 1.0) * 0.2      # Some frequency needed
            )
            
            heatmap_data.append({
                'num_dice': num_dice,
                'die_type': f"d{die_type}",
                'vulture_score': vulture_score
            })
            
            opportunities.append({
                'dice_combination': f"{num_dice}d{die_type}",
                'vulture_score': vulture_score,
                'avg_competition': avg_competition,
                'no_bid_percentage': no_bid_percentage,
                'appearances': stats['appearances']
            })
    
    # Create heatmap DataFrame
    heatmap_df = pd.DataFrame(heatmap_data)
    if not heatmap_df.empty:
        heatmap_pivot = heatmap_df.pivot(index='num_dice', columns='die_type', values='vulture_score').fillna(0)
    else:
        heatmap_pivot = pd.DataFrame()
    
    # Sort opportunities by vulture score
    opportunities.sort(key=lambda x: x['vulture_score'], reverse=True)
    
    return heatmap_pivot, opportunities[:10]  # Top 10 opportunities


def parse_dice_string(dice_str: str) -> Tuple[int, int]:
    """
    Parse a dice string like '3d6+2' into number of dice and die type.
    
    Args:
        dice_str: String representation of dice (e.g., '3d6+2', '1d20', '2d8')
        
    Returns:
        Tuple of (number_of_dice, die_type)
    """
    try:
        # Remove any modifiers (+X, -X)
        clean_dice = dice_str.split('+')[0].split('-')[0]
        
        if 'd' not in clean_dice:
            return 1, 6  # Default fallback
        
        parts = clean_dice.split('d')
        num_dice = int(parts[0]) if parts[0] else 1
        die_type = int(parts[1]) if parts[1] else 6
        
        return num_dice, die_type
    except (ValueError, IndexError):
        return 1, 6  # Default fallback


def get_agent_id_from_logs(log_entries: List[Dict]) -> Optional[str]:
    """
    Extract the agent ID from log entries.
    
    Args:
        log_entries: List of log entry dictionaries
        
    Returns:
        Agent ID string if found, None otherwise
    """
    for entry in log_entries:
        # Check for current_agent field (the actual field in log data)
        if "current_agent" in entry:
            return entry["current_agent"]
            
        # Legacy check for a_id field
        if "a_id" in entry:
            agent_info = entry["a_id"]
            return agent_info.get("a_id")
        
        # Fallback: look for DoomGuy patterns in states
        states = entry.get("states", {})
        for player_id in states.keys():
            if "doom" in str(player_id).lower() or "666" in str(player_id):
                return player_id
    
    return None


def load_latest_logs(logs_dir: Path, max_entries: int = 1000) -> List[Dict]:
    """
    Load the latest log entries from the logs directory.
    
    Args:
        logs_dir: Path to the logs directory
        max_entries: Maximum number of entries to load
        
    Returns:
        List of log entry dictionaries
    """
    try:
        # Find the newest log file
        log_files = list(logs_dir.glob("*.jsonl"))
        if not log_files:
            print(f"🔍 No log files found in: {logs_dir}")
            return []
        
        newest_file = max(log_files, key=lambda f: f.stat().st_mtime)
        print(f"📂 Loading latest log file: {newest_file}")
        
        entries = []
        with open(newest_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                        if len(entries) >= max_entries:
                            break
                    except json.JSONDecodeError:
                        continue
        
        print(f"📊 Loaded {len(entries)} log entries")
        return entries
    except Exception as e:
        print(f"❌ Error loading logs: {e}")
        return []


def test_log_data_format(log_entries: List[Dict]) -> None:
    """Test function to check the format of log data."""
    if not log_entries:
        print("❌ No log entries to test")
        return
    
    print(f"🧪 Testing log data format with {len(log_entries)} entries")
    
    # Check first entry
    first_entry = log_entries[0]
    print(f"📋 First entry keys: {list(first_entry.keys())}")
    
    # Check auction data format
    if "auctions" in first_entry:
        auctions = first_entry["auctions"]
        if auctions:
            first_auction = next(iter(auctions.values()))
            print(f"🎲 Auction data format: {first_auction}")
        else:
            print("⚠️ No auctions in first entry")
    
    # Check prev_auctions format
    if "prev_auctions" in first_entry:
        prev_auctions = first_entry["prev_auctions"]
        if prev_auctions:
            first_prev = next(iter(prev_auctions.values()))
            print(f"📜 Previous auction format: {first_prev}")
        else:
            print("ℹ️ No previous auctions in first entry")
    
    # Check states format
    if "states" in first_entry:
        states = first_entry["states"]
        if states:
            first_state = next(iter(states.values()))
            print(f"👤 Agent state format: {first_state}")
        else:
            print("⚠️ No states in first entry")


def calculate_real_time_metrics(log_entries: List[Dict]) -> Dict:
    """
    Calculate real-time performance metrics from recent log entries.
    
    Args:
        log_entries: List of recent log entry dictionaries
        
    Returns:
        Dictionary containing real-time metrics
    """
    if not log_entries:
        return {
            'games_today': 0,
            'avg_gold_per_game': 0,
            'avg_points_per_game': 0,
            'win_streak': 0,
            'last_activity': 'No recent activity'
        }
    
    # Get unique games (assuming each game has increasing round numbers)
    games = {}
    for entry in log_entries:
        round_num = entry.get('round', 0)
        game_id = entry.get('game_id', 'default')  # If available
        
        if game_id not in games:
            games[game_id] = {'max_round': 0, 'final_states': {}}
        
        if round_num > games[game_id]['max_round']:
            games[game_id]['max_round'] = round_num
            games[game_id]['final_states'] = entry.get('states', {})
    
    # Calculate metrics
    total_gold = 0
    total_points = 0
    valid_games = 0
    
    for game_data in games.values():
        final_states = game_data['final_states']
        agent_found = False
        
        for player_id, state in final_states.items():
            if 'doom' in str(player_id).lower() or '666' in str(player_id):
                total_gold += state.get('gold', 0)
                total_points += state.get('points', 0)
                agent_found = True
                break
        
        if agent_found:
            valid_games += 1
    
    return {
        'games_today': valid_games,
        'avg_gold_per_game': total_gold / valid_games if valid_games > 0 else 0,
        'avg_points_per_game': total_points / valid_games if valid_games > 0 else 0,
        'win_streak': 0,  # Would need more complex calculation
        'last_activity': 'Recently active' if log_entries else 'No recent activity'
    }
