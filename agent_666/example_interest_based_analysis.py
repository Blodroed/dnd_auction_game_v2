"""
Example: Using Configurable Interest-Based Timeline Analysis

This example demonstrates how to use the configurable settings for 
interest-based timeline analysis that looks ahead to prevent money loss.
"""

from economy import EconomyAnalyzer
import json

def example_interest_based_strategy():
    """Example of using configurable interest-based timeline analysis."""
    
    # Load settings from configuration file
    with open('data/settings.json', 'r') as f:
        settings = json.load(f)
    
    # Extract economy configuration
    economy_config = settings.get('economy', {})
    
    # Initialize the economy analyzer with your configuration
    economy = EconomyAnalyzer(economy_config)
    
    print("🎯 Interest-Based Timeline Analysis Configuration:")
    print(f"   Base Max Bet Limit: {economy_config.get('max_bet_limit', 0.8):.1%}")
    print(f"   Dynamic Adjustment: {economy_config.get('use_dynamic_max_bet_limit', True)}")
    print(f"   Timeline Look-Ahead: {economy_config.get('timeline_look_ahead', 10)} rounds")
    print(f"   Aggressive Threshold: {economy_config.get('aggressive_spending_threshold', 0.5)}")
    print(f"   Conservative Threshold: {economy_config.get('conservative_spending_threshold', 0.8)}")
    print(f"   Max Adjustment Factor: {economy_config.get('max_adjustment_factor', 1.2)}")
    
    # Example bank state (this would come from the game)
    example_bank_state = {
        "remainder_gold_income": [1000, 800, 1200, 900, 1100, 950, 1050, 800, 1300, 1000],
        "remainder_bank_interest": [1.05, 0.98, 0.92, 0.88, 0.94, 1.02, 1.08, 0.85, 0.91, 1.04],
        "remainder_bank_limit": [2000, 1800, 2200, 1900, 2100, 1950, 2050, 1800, 2300, 2000]
    }
    
    current_round = 0
    available_gold = 2500
    
    # Get economic outlook for the next rounds
    outlook = economy.get_economic_outlook(example_bank_state, current_round)
    
    print(f"\n📈 Economic Outlook (next {outlook['look_ahead_rounds']} rounds):")
    print(f"   Average Future Interest: {outlook['avg_future_interest']:.1%}")
    print(f"   Recommended Strategy: {outlook['recommended_strategy']}")
    
    # Calculate optimal betting limit based on timeline analysis
    max_bet_limit = economy.get_max_bet_limit_for_round(example_bank_state, current_round)
    
    print(f"\n💰 Betting Analysis:")
    print(f"   Available Gold: {available_gold}")
    print(f"   Max Bet Limit: {max_bet_limit:.1%}")
    print(f"   Max Betting Amount: {int(available_gold * max_bet_limit)}")
    
    # Calculate round budget
    budget_info = economy.calculate_round_budget(available_gold, current_round, example_bank_state)
    
    print(f"\n📊 Round Budget Recommendation:")
    print(f"   Spending Budget: {budget_info['spending_budget']}")
    print(f"   Spending Ratio: {budget_info['spending_ratio']:.1%}")
    print(f"   Reserve Amount: {budget_info['reserve_amount']}")
    
    # Show specific scenarios
    print(f"\n🎮 Interest-Based Decision Making:")
    
    future_scenarios = [
        {"round": 3, "interest": 0.88, "description": "Very poor interest rate"},
        {"round": 6, "interest": 1.08, "description": "Good interest rate"},
        {"round": 8, "interest": 0.85, "description": "Terrible interest rate"}
    ]
    
    for scenario in future_scenarios:
        # Simulate future bank state for this scenario
        future_bank_state = {
            "remainder_gold_income": [1000] * 10,
            "remainder_bank_interest": [scenario["interest"]] * 10,
            "remainder_bank_limit": [2000] * 10
        }
        
        future_limit = economy.get_max_bet_limit_for_round(future_bank_state, scenario["round"])
        future_outlook = economy.get_economic_outlook(future_bank_state, scenario["round"])
        
        print(f"   Round {scenario['round']} ({scenario['description']}):")
        print(f"     Interest Rate: {scenario['interest']:.1%}")
        print(f"     Recommended Strategy: {future_outlook['recommended_strategy']}")
        print(f"     Max Bet Limit: {future_limit:.1%}")
        if future_outlook['recommended_strategy'] == 'very_aggressive_spend':
            print(f"     ⚠️  MONEY LOSS DETECTED - BID AGGRESSIVELY!")
        print()

def customize_interest_analysis():
    """Example of customizing the interest-based analysis parameters."""
    
    print("🛠️  Customizing Interest-Based Timeline Analysis:")
    
    # Example: Very aggressive configuration for high-risk play
    aggressive_config = {
        'max_bet_limit': 0.9,  # Allow up to 90% betting
        'use_dynamic_max_bet_limit': True,
        'timeline_look_ahead': 15,  # Look further ahead
        'aggressive_spending_threshold': 0.6,  # Trigger aggressive spending later
        'conservative_spending_threshold': 0.9,  # Almost never be conservative
        'max_adjustment_factor': 1.5,  # Allow very aggressive adjustment
        'interest_threshold': 1.02,  # Lower threshold for good interest
    }
    
    # Example: Conservative configuration for safe play
    conservative_config = {
        'max_bet_limit': 0.6,  # Limit to 60% betting
        'use_dynamic_max_bet_limit': True,
        'timeline_look_ahead': 8,  # Shorter lookahead
        'aggressive_spending_threshold': 0.3,  # Trigger aggressive spending early
        'conservative_spending_threshold': 0.7,  # Be conservative often
        'max_adjustment_factor': 1.1,  # Small adjustments only
        'interest_threshold': 1.08,  # Higher threshold for good interest
    }
    
    configs = [
        ("Aggressive Strategy", aggressive_config),
        ("Conservative Strategy", conservative_config)
    ]
    
    for name, config in configs:
        economy = EconomyAnalyzer(config)
        
        # Test with poor economic conditions
        poor_bank_state = {
            "remainder_gold_income": [800] * 10,
            "remainder_bank_interest": [0.85] * 10,  # Poor interest
            "remainder_bank_limit": [1500] * 10
        }
        
        max_limit = economy.get_max_bet_limit_for_round(poor_bank_state, 0)
        outlook = economy.get_economic_outlook(poor_bank_state, 0)
        
        print(f"\n{name} (Poor Economic Conditions):")
        print(f"   Max Bet Limit: {max_limit:.1%}")
        print(f"   Strategy: {outlook['recommended_strategy']}")
        print(f"   Timeline: {outlook['look_ahead_rounds']} rounds")

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 CONFIGURABLE INTEREST-BASED TIMELINE ANALYSIS")
    print("=" * 60)
    
    example_interest_based_strategy()
    
    print("\n" + "=" * 60)
    customize_interest_analysis()
    
    print("\n" + "=" * 60)
    print("📋 Configuration Options in settings.json:")
    print("""
    "economy": {
        "max_bet_limit": 0.8,                    // Base betting limit (80%)
        "use_dynamic_max_bet_limit": true,       // Enable timeline analysis
        "timeline_look_ahead": 10,               // Rounds to analyze ahead
        "aggressive_spending_threshold": 0.5,    // When to spend aggressively
        "conservative_spending_threshold": 0.8,  // When to be conservative
        "max_adjustment_factor": 1.2,            // Max adjustment multiplier
        "interest_threshold": 1.05               // Good interest rate threshold
    }
    """)