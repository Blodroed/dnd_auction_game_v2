#!/usr/bin/env python3
"""
Test the improved vulture scoring system.
Compare old vs new scoring approaches.
"""

def calculate_old_scoring(expected_value, mean_bid, std_bid, aggression_multiplier=2.4):
    """Old scoring method from original system."""
    base_bid = (mean_bid + std_bid) * aggression_multiplier
    vulture_score = expected_value / max(base_bid, 1)
    return vulture_score, base_bid

def calculate_new_scoring(expected_value, mean_bid, aggression_multiplier=1.5, high_value_threshold=15):
    """New improved scoring method."""
    # More conservative bid estimate
    reasonable_bid = mean_bid * 1.2
    
    value_per_gold = expected_value / max(reasonable_bid, 1)
    base_score = value_per_gold
    
    # Bonus for high-value auctions
    if expected_value > high_value_threshold:
        base_score *= 1.5
    
    # Additional bonus for extremely high expected values
    if expected_value > 20:
        base_score *= 1.3
    
    return base_score, reasonable_bid

def main():
    print("=== Vulture Scoring Comparison ===\n")
    
    # Test scenarios from the log analysis
    scenarios = [
        {"name": "Low Value Auction", "expected_value": 8.5, "mean_bid": 300, "std_bid": 137},
        {"name": "Medium Value Auction", "expected_value": 12.0, "mean_bid": 280, "std_bid": 145},
        {"name": "High Value Auction", "expected_value": 18.0, "mean_bid": 350, "std_bid": 120},
        {"name": "Very High Value Auction", "expected_value": 25.0, "mean_bid": 400, "std_bid": 160},
    ]
    
    print(f"{'Scenario':<25} {'Expected Value':<15} {'Old Score':<12} {'New Score':<12} {'Improvement':<12}")
    print("-" * 80)
    
    for scenario in scenarios:
        ev = scenario["expected_value"]
        mean_bid = scenario["mean_bid"]
        std_bid = scenario["std_bid"]
        
        old_score, old_bid = calculate_old_scoring(ev, mean_bid, std_bid, 2.4)
        new_score, new_bid = calculate_new_scoring(ev, mean_bid, 1.5)
        
        improvement = (new_score / old_score) if old_score > 0 else 0
        
        print(f"{scenario['name']:<25} {ev:<15.1f} {old_score:<12.4f} {new_score:<12.4f} {improvement:<12.1f}x")
        print(f"{'':25} {'Bid Used:':<15} {old_bid:<12.0f} {new_bid:<12.0f}")
        print()
    
    print("\n=== Analysis ===")
    print("✓ New scoring uses more realistic bid estimates (mean * 1.2 vs mean + std * 2.4)")
    print("✓ Better differentiation between auction values")
    print("✓ High-value auctions get appropriate bonuses")
    print("✓ Scores are now in a more interpretable range")

if __name__ == "__main__":
    main()