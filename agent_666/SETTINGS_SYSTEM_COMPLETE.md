# DoomGuy666 Settings System 🛠️

## 📋 **Complete Settings Integration**

The DoomGuy666 agent now features a comprehensive settings system that controls all bot behavior through centralized configuration.

## 🗂️ **Settings Structure**

### **📁 Core Configuration Sections**

#### **🤖 Agent Information**

```json
"agent_info": {
  "name": "DoomGuy666",
  "player_id": "doom_agent_666",
  "version": "2.0.0",
  "description": "Advanced auction agent with Vulture Mode strategies"
}
```

#### **🌐 Connection Settings**

```json
"connection": {
  "host": "localhost",
  "port": 8000,
  "reconnect_attempts": 5,
  "reconnect_delay": 0.5,
  "timeout": 30
}
```

#### **⚔️ Strategy Configuration**

```json
"strategy": {
  "type": "vulture_mode",
  "aggression_multiplier": 1.5,
  "max_bid_ratio": 0.8,
  "min_auctions_target": 3,
  "deadspace_threshold": 2.0,
  "high_value_threshold": 15.0,
  "competition_penalty": 0.15,
  "bonus_weight": 0.25
}
```

#### **🎯 Bid Mode Settings**

```json
"bid_modes": {
  "current_mode": "AGGRESSIVE_SPREAD",
  "focus_ratio": 0.7,
  "min_bid_amount": 1,
  "max_single_bid_ratio": 0.4,
  "spread_factor": 0.8,
  "conservative_multiplier": 0.35
}
```

#### **💰 Economic Parameters**

```json
"economy": {
  "spending_ratio": 0.8,
  "accumulation_penalty": 1.2,
  "interest_threshold": 1.05,
  "emergency_spend_threshold": 0.9,
  "min_reserve_gold": 5,
  "max_budget_per_round": 100
}
```

#### **🔍 Data Analysis Settings**

```json
"data_analysis": {
  "min_vulture_score": 2.0,
  "max_bid_per_auction": 20,
  "competition_analysis_rounds": 5,
  "pattern_detection_enabled": true,
  "learning_rate": 0.1,
  "historical_weight": 0.8
}
```

#### **🗄️ Storage Configuration**

```json
"storage": {
  "max_memory_rounds": 100,
  "auto_save_interval": 10,
  "enable_persistence": true,
  "backup_logs": true,
  "compression_enabled": false
}
```

## 🔧 **Settings Manager API**

### **Basic Usage**

```python
from settings_manager import get_settings_manager, get_setting, update_setting

# Get settings manager
settings = get_settings_manager()

# Read configuration
aggression = get_setting('strategy', 'aggression_multiplier', 1.5)
spending_ratio = get_setting('economy', 'spending_ratio', 0.8)

# Update settings
update_setting('strategy', 'aggression_multiplier', 2.0)
update_setting('economy', 'spending_ratio', 0.75)
```

### **Section Management**

```python
# Get entire sections
strategy_config = settings.get_strategy_config()
economy_config = settings.get_economy_config()
bid_mode_config = settings.get_bid_mode_config()

# Update entire sections
settings.update_section('bid_modes', {
    'current_mode': 'EVEN_STEVEN',
    'spread_factor': 0.9,
    'focus_ratio': 0.6
})
```

### **File Operations**

```python
# Save settings to file
settings.save_settings()

# Check for file updates and reload
settings.check_for_updates()

# Validate settings
is_valid = settings.validate_settings()
```

## 🚀 **Component Integration**

### **How Components Use Settings**

All major components now accept configuration in their constructors:

```python
# Components are initialized with settings
strategy = VultureMode(settings.get_strategy_config())
bid_modes = BidModeSelector(settings.get_bid_mode_config())
economy = EconomyAnalyzer(settings.get_economy_config())
```

### **Real-Time Updates**

Components can be updated during gameplay:

```python
# Check for settings changes and update components
agent.update_configurations()

# Manual component updates
agent.strategy.update_config(new_strategy_settings)
agent.bid_modes.update_config(new_bid_settings)
agent.economy.update_config(new_economy_settings)
```

## 📊 **Benefits of Settings System**

### ✅ **Centralized Control**

- All bot behavior controlled from single `settings.json` file
- No more hardcoded values scattered across modules
- Easy configuration management

### ✅ **Real-Time Updates**

- Settings can be modified during gameplay
- Components automatically reload new configurations
- Hot-swapping of strategies and parameters

### ✅ **Dashboard Ready**

- All parameters exposed for web dashboard control
- Structured configuration sections
- Validation and error handling

### ✅ **Default Fallbacks**

- Robust default configuration if file is missing
- Graceful handling of partial configurations
- Automatic creation of missing settings

### ✅ **Type Safety & Validation**

- Settings validation on load
- Range checking for critical parameters
- Error logging for invalid configurations

## 🎛️ **Key Settings Explained**

### **🎯 Critical Performance Settings**

- **`aggression_multiplier`** (1.5): How aggressive bidding is vs mean+std
- **`spending_ratio`** (0.8): Percentage of gold to spend each round
- **`spread_factor`** (0.8): How much budget to distribute across auctions
- **`deadspace_threshold`** (2.0): Competition level considered "low"

### **🛡️ Safety Settings**

- **`max_total_bid`** (0.95): Maximum percentage of gold to bid total
- **`emergency_spend_threshold`** (0.9): Gold level that triggers emergency spending
- **`accumulation_penalty`** (1.2): Multiplier when gold is accumulating

### **⚡ Performance Settings**

- **`max_memory_rounds`** (100): Rounds to keep in memory
- **`enable_caching`** (true): Cache calculation results
- **`pattern_detection_enabled`** (true): Enable AI pattern recognition

## 🔄 **Settings Updates During Gameplay**

The system checks for settings updates every round:

```python
def vulture_bid_controller(agent_id, current_round, states, auctions, prev_auctions, bank_state):
    # Check for settings updates
    agent.update_configurations()
    
    # Continue with updated configuration...
```

## 📁 **File Locations**

- **Settings File**: `data/settings.json`
- **Settings Manager**: `settings_manager.py`
- **Test Script**: `test_settings.py`
- **Schema**: Defined in `settings_manager.py`

## 🎉 **Result**

**Complete centralized control** of the DoomGuy666 agent through a single configuration file, with real-time updates and dashboard integration ready!

The bot now loads all its behavior parameters from `settings.json`, making it easily configurable and perfect for dashboard control. 🛠️⚡
