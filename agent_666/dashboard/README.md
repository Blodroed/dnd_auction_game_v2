# 🎯 DoomGuy666 Agent Management Dashboard

A comprehensive real-time dashboard for monitoring and managing the DoomGuy666 auction game agent. This dashboard provides live statistics, settings management, vulture analysis, and performance tracking.

## 🌟 Features

### 📊 Agent Statistics Panel (Left Quarter)
- **Current Gold**: Live gold balance
- **Current Points**: Total points earned
- **Bid Win Rate**: Percentage of successful bids
- **Active Strategy**: Currently running strategy mode

### ⚙️ Live Settings Management (Right Three-Quarters)
- **Strategy Configuration**
  - Aggression Multiplier (0.5x - 5.0x)
  - Max Bid Ratio (10% - 100%)
  - High Value Threshold (5 - 50 points)

- **Bid Mode Settings**
  - Mode Selection (Even Steven, All In, Spread Bet, Conservative)
  - Focus Ratio (10% - 100%)

- **Economy Management**
  - Spending Ratio (10% - 100%)
  - Minimum Reserve Gold (0 - 50)
  - Toggle switches for limits and emergency spending

### 🦅 Vulture Mode Analysis
- **Dice Heatmap**: Visual representation of dice combinations by exploitation potential
  - Green zones: Low competition opportunities
  - Red zones: High competition areas
  - Color intensity represents vulture score

- **Top Opportunities Table**: Ranked list of best vulture targets
  - Dice combination (e.g., "3d6", "1d20")
  - Vulture score (0.000 - 1.000)
  - Average competition level
  - No-bid percentage
  - Recommendation level (HIGH/MEDIUM/LOW)

### 📈 Performance Charts (Bottom Half)
- **Gold Chart** (Left): Gold progression over rounds
- **Points Chart** (Right): Points accumulation over rounds
- **Agent Highlighting**: Your agent is highlighted with:
  - Thicker line (4px vs 2px)
  - Star markers
  - "🎯 DoomGuy666 (YOU)" label
  - Enhanced visibility while others are dimmed

## 🚀 Getting Started

### Prerequisites
```bash
pip install dash plotly pandas watchdog
```

### Running the Dashboard
```bash
cd agent_666/dashboard
python run_dashboard.py
```

Or directly:
```bash
python app.py
```

### Dashboard URL
Open your browser to: `http://localhost:8050`

## 🔧 How It Works

### Real-Time Updates
- **File Monitoring**: Watches the `logs/` directory for new game data
- **Auto-Refresh**: Updates every 1 second during active games
- **Agent Detection**: Automatically identifies your agent in multiplayer games

### Settings Auto-Save
- Changes to settings are immediately saved to `data/settings.json`
- Agent picks up new settings on next game round
- No restart required for most setting changes

### Agent Identification
The dashboard identifies your agent using:
1. Agent ID from log entries (`a_id` field)
2. Player ID patterns containing "doom" or "666"
3. Manual configuration in settings

## 📁 File Structure

```
dashboard/
├── app.py                 # Main dashboard application
├── layout.py             # UI layout and components
├── callbacks.py          # Real-time update logic
├── utlils.py            # Data processing utilities
├── run_dashboard.py     # Test/launch script
├── assets/
│   └── styles.css       # Custom styling
└── data/
    └── settings.json    # Agent configuration (auto-updated)
```

## 🎮 Usage Tips

### Monitoring Performance
1. Start the dashboard before running games
2. Launch your agent and start playing
3. Watch real-time stats update as games progress
4. Use the vulture heatmap to identify profitable opportunities

### Adjusting Strategy
1. Use sliders to adjust aggression and bid ratios
2. Switch bid modes based on game conditions
3. Monitor win rate changes after adjustments
4. Save different configurations for different game types

### Vulture Analysis
1. Green areas in the heatmap show low-competition dice
2. Focus bidding on HIGH recommendation dice combinations
3. Avoid RED zones unless you have significant advantages
4. Build data over multiple games for accurate analysis

## 🐛 Troubleshooting

### No Data Showing
- Ensure games are running and generating logs
- Check that log files are in `../logs/` directory
- Verify agent is properly identified in logs

### Settings Not Saving
- Check file permissions on `data/settings.json`
- Ensure dashboard has write access to the directory
- Look for error messages in the console

### Performance Issues
- Reduce update interval in production (change `interval=1000` to higher value)
- Limit log file sizes for better performance
- Clear old log files periodically

## 🔮 Advanced Features

### Custom Agent Highlighting
The dashboard automatically detects and highlights your agent, but you can customize this by:
1. Modifying the `agent_info` in settings
2. Adding custom detection patterns in `utlils.py`
3. Adjusting highlighting styles in `assets/styles.css`

### Extending Vulture Analysis
Add new metrics by:
1. Modifying `analyze_vulture_opportunities()` in `utlils.py`
2. Adding new columns to the opportunities table
3. Implementing custom scoring algorithms

### Mobile Support
The dashboard includes responsive design for mobile devices:
- Collapsible panels on small screens
- Touch-friendly controls
- Optimized layouts for tablets and phones

## 📊 Data Sources

### Log Files
- Format: JSONL (JSON Lines)
- Location: `../logs/agent_*.jsonl`
- Auto-detection of newest files
- Real-time monitoring of changes

### Settings Files
- Format: JSON
- Location: `data/settings.json`
- Auto-save on changes
- Backup creation for safety

## 🎯 Performance Metrics

### Calculated Statistics
- **Bid Win Rate**: Successful bids / Total bids
- **Vulture Score**: Composite score based on competition and opportunity
- **Gold Efficiency**: Points per gold spent
- **Round Performance**: Average gains per round

### Update Frequency
- Charts: Every 1 second
- Settings: Immediate on change
- Vulture Analysis: Every data update
- File Monitoring: Real-time file system events

---

## 🏆 Built For Champions

This dashboard is designed for serious auction game competitors who want:
- **Data-Driven Decisions**: Make informed bids based on analysis
- **Real-Time Adaptation**: Adjust strategies during games
- **Performance Tracking**: Monitor improvement over time
- **Competitive Advantage**: Identify and exploit vulture opportunities

*May your bids be swift and your victories legendary!* 🐉⚔️