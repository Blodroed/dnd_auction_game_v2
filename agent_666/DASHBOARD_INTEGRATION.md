# 🔗 DoomGuy666 Agent Dashboard Integration Guide

This document explains how the dashboard integrates with your DoomGuy666 agent for real-time monitoring and control.

## 🎯 Integration Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Dashboard         │    │   Settings File     │    │   DoomGuy666        │
│   (Port 8050)       │◄──►│   settings.json     │◄──►│   Agent             │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Real-time         │    │   Configuration     │    │   Game Logs         │
│   Updates           │    │   Management        │    │   (logs/*.jsonl)    │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## 🔄 1. Real-Time Settings Integration

### Settings Flow:
1. **Dashboard Changes** → User adjusts sliders/dropdowns in dashboard
2. **Auto-Save** → Changes immediately saved to `data/settings.json`
3. **Agent Reload** → Your agent's `SettingsManager` detects changes
4. **Strategy Update** → New settings applied to bidding strategies

### Code Integration:
Your agent already has the settings manager that automatically picks up changes:

```python
# Your existing settings_manager.py already handles this:
class SettingsManager:
    def load_settings(self) -> Dict[str, Any]:
        # Automatically reloads settings.json when modified
        # Dashboard changes are immediately available
```

## 📊 2. Performance Monitoring Integration

### Log File Monitoring:
The dashboard automatically monitors your agent's performance by:

1. **File Watching** → Monitors `logs/agent_*.jsonl` files in real-time
2. **Data Extraction** → Parses game states, bids, and outcomes
3. **Chart Updates** → Updates gold/points charts every second
4. **Agent Highlighting** → Identifies and highlights your agent in multiplayer games

### Agent ID Detection:
The dashboard finds your agent using these patterns:
```python
# From your log entries, it looks for:
{
  "a_id": {
    "name": "DoomGuy666",
    "a_id": "local_rand_id_234156", 
    "player_id": "doom_agent_666"
  }
}

# Or player IDs containing:
- "doom" (case insensitive)
- "666"
```

## 🦅 3. Vulture Mode Integration

### Automatic Analysis:
The dashboard analyzes your existing vulture data by:

1. **Log Analysis** → Scans all your game logs for dice patterns
2. **Competition Mapping** → Tracks bid competition for each dice combination
3. **Opportunity Scoring** → Calculates vulture scores based on your algorithm
4. **Heatmap Generation** → Visual representation of exploitation opportunities

### Integration with Your Vulture System:
```python
# Dashboard uses your existing vulture analysis logic:
from utlils import analyze_vulture_opportunities

# This function processes the same log data your agent uses
# No changes needed to your existing vulture mode code
```

## 🚀 How to Use Integration

### Step 1: Start Your Agent
```bash
cd agent_666
python main.py
```

### Step 2: Start Dashboard (in separate terminal)
```bash
cd agent_666/dashboard  
python run_dashboard.py
# Opens at http://localhost:8050
```

### Step 3: Play Games
- Your agent plays games and generates logs
- Dashboard automatically detects and displays performance
- Adjust settings in real-time through dashboard

## ⚙️ Configuration Points

### Dashboard Settings → Agent Settings Mapping:

| Dashboard Control | Settings File Path | Agent Component |
|------------------|-------------------|-----------------|
| Aggression Multiplier | `strategy.aggression_multiplier` | `DoomController` |
| Max Bid Ratio | `strategy.max_bid_ratio` | Strategy calculations |
| High Value Threshold | `strategy.high_value_threshold` | Value assessment |
| Bid Mode | `bid_modes.current_mode` | Bid distribution |
| Focus Ratio | `bid_modes.focus_ratio` | Bid concentration |
| Spending Ratio | `economy.spending_ratio` | `EconomyAnalyzer` |
| Min Reserve Gold | `economy.min_reserve_gold` | Economic limits |

### Example Settings Update Flow:
```python
# 1. User moves "Aggression Multiplier" slider to 3.5 in dashboard
# 2. Dashboard callback triggers:
def update_settings(aggression, ...):
    settings['strategy']['aggression_multiplier'] = 3.5
    # Saves to data/settings.json

# 3. Your agent's SettingsManager detects change:
class SettingsManager:
    def get_strategy_config(self):
        return self.settings.get('strategy', {})  # Returns new value 3.5

# 4. DoomController uses new setting:
class DoomController:
    def calculate_bid(self):
        aggression = self.settings.get_strategy_config()['aggression_multiplier']
        # Uses 3.5 for calculations
```

## 📈 Real-Time Data Flow

### Game Logging → Dashboard Updates:
```python
# 1. Your agent logs game state (already implemented):
{
    "round": 15,
    "states": {
        "local_rand_id_234156": {"gold": 45, "points": 23}
    },
    "auctions": {...},
    "prev_auctions": {...}
}

# 2. Dashboard file watcher detects new log entry
# 3. Parses data and updates charts automatically
# 4. Your agent appears highlighted in performance charts
```

## 🔧 Integration Requirements

### No Code Changes Needed:
Your existing agent code works without modifications because:

1. **Settings System** → Already uses `data/settings.json`
2. **Logging System** → Already generates compatible log files  
3. **Component Architecture** → Dashboard reads existing data structures
4. **Vulture Analysis** → Uses same log format and analysis methods

### Optional Enhancements:
If you want deeper integration, you could add:

```python
# In your main.py, add dashboard status logging:
logger.info(f"🎯 Agent stats: Gold={current_gold}, Points={current_points}")
logger.info(f"🦅 Vulture opportunities detected: {len(opportunities)}")

# In your settings manager, add dashboard notification:
def on_settings_changed(self):
    logger.info("⚙️ Settings updated from dashboard")
```

## 🎮 Usage Workflow

### Development Workflow:
1. **Start Dashboard** → Monitor performance in real-time
2. **Run Agent** → Play games while monitoring
3. **Adjust Strategy** → Use dashboard to tweak settings mid-game
4. **Analyze Results** → Use vulture heatmap to optimize strategy
5. **Iterate** → Repeat with refined settings

### Competition Workflow:
1. **Pre-Game Setup** → Use dashboard to configure optimal settings
2. **Live Monitoring** → Watch performance during competitions
3. **Strategy Adaptation** → Adjust aggression based on competition
4. **Vulture Exploitation** → Use heatmap to identify opportunities

## 🔍 Troubleshooting Integration

### Common Issues:

1. **Agent Not Detected** → Check log file contains agent ID info
2. **Settings Not Applying** → Verify `settings.json` permissions
3. **No Performance Data** → Ensure logs directory contains recent `.jsonl` files
4. **Chart Not Updating** → Check file watcher has access to logs folder

### Debug Commands:
```bash
# Check if settings are being updated:
cat agent_666/data/settings.json

# Check if logs are being generated:
ls -la agent_666/logs/*.jsonl

# Test dashboard components:
cd agent_666/dashboard && python -c "from app import app; print('✅ Dashboard OK')"
```

The integration is designed to be seamless - your existing agent architecture already provides all the necessary components for full dashboard functionality! 🚀