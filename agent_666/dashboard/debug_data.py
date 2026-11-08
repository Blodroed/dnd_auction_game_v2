#!/usr/bin/env python3
"""
Debug script to test the dashboard data processing pipeline
"""

import json
import pandas as pd
from pathlib import Path
from utlils import analyze_vulture_opportunities, extract_agent_performance, get_agent_id_from_logs

def debug_log_processing():
    """Debug the log file processing to identify issues."""
    
    # Load the log file
    log_file = Path(__file__).parent.parent / "logs" / "agent_local_rand_id_722308_n0.jsonl"
    print(f"🔍 Loading log file: {log_file}")
    
    if not log_file.exists():
        print(f"❌ Log file does not exist: {log_file}")
        return
    
    # Read and parse log entries
    log_entries = []
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    log_entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error on line {line_num}: {e}")
                    continue
    
    print(f"📊 Loaded {len(log_entries)} log entries")
    
    if not log_entries:
        print("❌ No valid log entries found")
        return
    
    # Test data frame creation (similar to cache._rebuild_dataframes)
    print("\n🧪 Testing DataFrame Creation:")
    gold_data = []
    points_data = []
    
    for entry in log_entries:
        round_number = entry.get("round", 0)
        states = entry.get("states", {})
        
        for player_id, state in states.items():
            gold = state.get("gold", 0)
            points = state.get("points", 0)
            gold_data.append({"Round": round_number, "Player ID": player_id, "Gold": gold})
            points_data.append({"Round": round_number, "Player ID": player_id, "Points": points})
    
    gold_df = pd.DataFrame(gold_data)
    points_df = pd.DataFrame(points_data)
    
    print(f"📈 Created Gold DataFrame: {len(gold_df)} rows")
    print(f"📈 Created Points DataFrame: {len(points_df)} rows")
    
    # Show sample data
    if not gold_df.empty:
        print("\n💰 Sample Gold Data:")
        print(gold_df.head(10))
        
        print(f"\n📊 Gold DataFrame Info:")
        print(f"   Rounds: {gold_df['Round'].min()} to {gold_df['Round'].max()}")
        print(f"   Players: {gold_df['Player ID'].nunique()}")
        print(f"   Player IDs: {list(gold_df['Player ID'].unique())}")
    
    if not points_df.empty:
        print("\n⭐ Sample Points Data:")
        print(points_df.head(10))
    
    # Test agent ID detection
    print(f"\n🤖 Testing Agent ID Detection:")
    detected_agent_id = get_agent_id_from_logs(log_entries)
    print(f"   Detected Agent ID: {detected_agent_id}")
    
    # Test agent performance extraction
    if detected_agent_id:
        print(f"\n📊 Testing Agent Performance Extraction:")
        agent_stats = extract_agent_performance(log_entries, detected_agent_id)
        print(f"   Agent Stats: {agent_stats}")
    
    # Test vulture analysis
    print(f"\n🎯 Testing Vulture Analysis:")
    try:
        vulture_heatmap_df, vulture_opportunities = analyze_vulture_opportunities(log_entries)
        print(f"   Vulture Heatmap Shape: {vulture_heatmap_df.shape}")
        print(f"   Vulture Opportunities: {len(vulture_opportunities)}")
        
        if not vulture_heatmap_df.empty:
            print(f"   Heatmap DataFrame:")
            print(vulture_heatmap_df)
        
        if vulture_opportunities:
            print(f"   Top 3 Opportunities:")
            for i, opp in enumerate(vulture_opportunities[:3]):
                print(f"     {i+1}. {opp}")
                
    except Exception as e:
        print(f"❌ Vulture analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test current agent tracking from log
    print(f"\n🎮 Testing Current Agent Tracking:")
    for entry in log_entries[-3:]:  # Check last 3 entries
        current_agent = entry.get("current_agent", "Unknown")
        round_num = entry.get("round", "?")
        print(f"   Round {round_num}: Current Agent = {current_agent}")


if __name__ == "__main__":
    debug_log_processing()