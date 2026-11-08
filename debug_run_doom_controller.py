import sys
sys.path.insert(0, 'agent_666')

from main import DoomAgent

# Instantiate agent
print("Initializing DoomAgent...")
agent = DoomAgent()
dc = agent.doom_controller

agent_id = agent.settings.get_agent_info().get('player_id', 'doom_agent_666')

# Test with high gold amount similar to game scenario
states = {agent_id: {'gold': 90000, 'points': 100}}
auctions = {
    f'a{i}': {'num': 2, 'die': 6, 'bonus': i % 3} 
    for i in range(32)
}
prev_auctions = {
    'a_prev': {'bids': [{'a_id': agent_id, 'gold': 500}], 'reward': 50}
}
bank_state = {
    'remainder_gold_income': [1000], 
    'remainder_bank_interest': [1.03], 
    'remainder_bank_limit': [100000]
}

print(f"\nTest scenario: {len(auctions)} auctions, {states[agent_id]['gold']} gold available")
print("=" * 60)

bids = dc.doom_bid_controller(agent_id, 99, states, auctions, prev_auctions, 0, {}, bank_state)
total_bid = sum(bids.values())
spend_pct = (total_bid / states[agent_id]['gold']) * 100

print("\n" + "=" * 60)
print(f"RESULTS:")
print(f"  Bids placed: {len(bids)} auctions")
print(f"  Total bid amount: {total_bid:,} gold")
print(f"  Available gold: {states[agent_id]['gold']:,}")
print(f"  Spend percentage: {spend_pct:.1f}%")
print(f"  Pool contribution: {getattr(dc,'_last_pool_contribution', None)} points")
print("=" * 60)

if spend_pct < 70:
    print("\n⚠️  WARNING: Spending too little! Should spend ~85%")
elif spend_pct > 95:
    print("\n⚠️  WARNING: Spending too much! Might be over-aggressive")
else:
    print("\n✅ Spending looks good!")
