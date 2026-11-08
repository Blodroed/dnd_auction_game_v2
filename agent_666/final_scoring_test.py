#!/usr/bin/env python3
"""
Final test of the complete vulture scoring improvements.
Tests both the reduced aggression multiplier AND the improved scoring formula.
"""

def calculate_combined_scoring(expected_value, mean_bid, std_bid, 
                             aggression_multiplier=1.5, high_value_threshold=15):
    """Combined improvements: lower aggression + better scoring."""
    # Calculate base_bid with new lower aggression
    base_bid = (mean_bid + std_bid) * aggression_multiplier
    
    # Use more conservative estimate (60% of base_bid)
    reasonable_bid = base_bid * 0.6
    
    value_per_gold = expected_value / max(reasonable_bid, 1)
    base_score = value_per_gold
    
    # Bonus for high-value auctions
    if expected_value > high_value_threshold:
        base_score *= 1.5
    
    # Additional bonus for extremely high expected values
    if expected_value > 20:
        base_score *= 1.3
    
    return base_score, reasonable_bid, base_bid

def main():
    print("=== Final Vulture Scoring System ===\n")
    
    scenarios = [
        {"name": "Low Value Auction", "expected_value": 8.5, "mean_bid": 300, "std_bid": 137},
        {"name": "Medium Value Auction", "expected_value": 12.0, "mean_bid": 280, "std_bid": 145},
        {"name": "High Value Auction", "expected_value": 18.0, "mean_bid": 350, "std_bid": 120},
        {"name": "Very High Value Auction", "expected_value": 25.0, "mean_bid": 400, "std_bid": 160},
    ]
    
    print("Comparison: Original vs Final Improved System")
    print("=" * 70)
    print(f"{'Scenario':<25} {'EV':<6} {'Original':<12} {'Final':<12} {'Improvement'}")
    print("-" * 70)
    
    for scenario in scenarios:
        ev = scenario["expected_value"]
        mean_bid = scenario["mean_bid"]
        std_bid = scenario["std_bid"]
        
        # Original system
        original_base_bid = (mean_bid + std_bid) * 2.4
        original_score = ev / max(original_base_bid, 1)
        
        # Final improved system
        final_score, final_reasonable_bid, final_base_bid = calculate_combined_scoring(
            ev, mean_bid, std_bid, 1.5
        )
        
        improvement = (final_score / original_score) if original_score > 0 else 0
        
        print(f"{scenario['name']:<25} {ev:<6.1f} {original_score:<12.4f} {final_score:<12.4f} {improvement:<8.1f}x")
    
    print(f"\n{'Strategy Details':<25} {'Original':<15} {'Final'}")
    print("-" * 55)
    print(f"{'Aggression Multiplier':<25} {'2.4':<15} {'1.5'}")
    print(f"{'Bid Calculation':<25} {'(mean+std)*2.4':<15} {'(mean+std)*1.5*0.6'}")
    print(f"{'High Value Bonus':<25} {'None':<15} {'1.5x for EV>15'}")
    print(f"{'Very High Value Bonus':<25} {'None':<15} {'1.3x for EV>20'}")
    
    print("\n=== Key Improvements ===")
    print("✓ Reduced aggression multiplier: 2.4 → 1.5 (37% reduction)")
    print("✓ More realistic bid estimates: base_bid * 0.6 instead of full base_bid")
    print("✓ Value-based bonuses for high expected value auctions")
    print("✓ Better differentiation between auction qualities")
    print("✓ More interpretable scoring range")

if __name__ == "__main__":
    main()