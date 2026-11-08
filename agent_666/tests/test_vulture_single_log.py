"""
Test VULTURE MODE strategy on a specific log file with dungeon_dice_analysis format
"""

import json
import logging
from pathlib import Path
from collections import defaultdict
from strategies import VultureMode
from dice import average_roll

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_log_file(log_path):
    """Load and parse a single JSONL log file."""
    game_states = []
    with open(log_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    game_states.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line: {e}")
    return game_states

def build_dungeon_dice_analysis(game_states):
    """Build dungeon_dice_analysis from game state data."""
    dungeon_dice_analysis = defaultdict(lambda: {
        "total_auctions": 0,
        "total_bidders": 0,
        "no_bid_count": 0,
        "total_reward": 0,
        "vulture_score": 0.0,
        "min_reward": float('inf'),
        "max_reward": float('-inf'),
        "avg_bonus": 0.0,
        "total_bonus": 0
    })
    
    vulture_opportunities = []
    
    for state in game_states:
        if 'prev_auctions' not in state:
            continue
            
        for auction_id, auction_data in state['prev_auctions'].items():
            if not all(key in auction_data for key in ['die', 'num', 'reward']):
                continue
                
            die = auction_data['die']
            num = auction_data['num']
            reward = auction_data['reward']
            bonus = auction_data.get('bonus', 0)
            bids = auction_data.get('bids', [])
            
            dice_key = f"{num}d{die}"
            num_bidders = len(bids)
            
            # Update analysis data
            analysis = dungeon_dice_analysis[dice_key]
            analysis["total_auctions"] += 1
            analysis["total_bidders"] += num_bidders
            analysis["total_reward"] += reward
            analysis["total_bonus"] += bonus
            
            if num_bidders == 0:
                analysis["no_bid_count"] += 1
                vulture_opportunities.append({
                    "dice_key": dice_key,
                    "reward": reward,
                    "bonus": bonus,
                    "expected": average_roll(die, num, bonus)
                })
                
            analysis["min_reward"] = min(analysis["min_reward"], reward)
            analysis["max_reward"] = max(analysis["max_reward"], reward)
    
    # Calculate final statistics and vulture scores
    for dice_key, analysis in dungeon_dice_analysis.items():
        if analysis["total_auctions"] > 0:
            avg_bidders = analysis["total_bidders"] / analysis["total_auctions"]
            no_bid_rate = analysis["no_bid_count"] / analysis["total_auctions"]
            avg_reward = analysis["total_reward"] / analysis["total_auctions"]
            avg_bonus = analysis["total_bonus"] / analysis["total_auctions"]
            
            analysis["avg_bidders"] = avg_bidders
            analysis["no_bid_rate"] = no_bid_rate
            analysis["avg_reward"] = avg_reward
            analysis["avg_bonus"] = avg_bonus
            
            # Calculate vulture score
            # Higher reward, lower competition, higher no-bid rate = better vulture opportunity
            analysis["vulture_score"] = (
                avg_reward * 0.3 +           # Reward potential
                no_bid_rate * 15.0 +         # No-bid opportunities (heavily weighted)
                max(0, 8.0 - avg_bidders) * 1.0  # Low competition bonus
            )
            
            # Clean up infinity values
            if analysis["min_reward"] == float('inf'):
                analysis["min_reward"] = 0
            if analysis["max_reward"] == float('-inf'):
                analysis["max_reward"] = 0
    
    return dict(dungeon_dice_analysis), vulture_opportunities

def test_vulture_strategy(log_file_path):
    """Test VULTURE MODE strategy on specific log file."""
    logger.info(f"🎯 Testing VULTURE MODE on: {log_file_path}")
    
    # Load game states
    game_states = load_log_file(log_file_path)
    logger.info(f"📊 Loaded {len(game_states)} game states")
    
    if not game_states:
        logger.error("No valid game states found!")
        return
    
    # Build dungeon dice analysis
    dungeon_dice_analysis, vulture_opportunities = build_dungeon_dice_analysis(game_states)
    
    logger.info(f"🎲 Analyzed {len(dungeon_dice_analysis)} dice combinations")
    logger.info(f"🦅 Found {len(vulture_opportunities)} vulture opportunities (0-bid auctions)")
    
    # Initialize VULTURE MODE strategy
    vulture_strategy = VultureMode(
        dungeon_dice_analysis=dungeon_dice_analysis,
        min_vulture_score=1.0,
        bonus_weight=0.2,  # Bonus less important
        min_game_progress=0.0,  # Allow early testing
        force_early=True
    )
    
    # Get insights
    insights = vulture_strategy.get_vulture_insights()
    
    # Print results
    logger.info("=" * 60)
    logger.info("🦅 VULTURE MODE ANALYSIS RESULTS")
    logger.info("=" * 60)
    logger.info(f"📈 Total dice patterns analyzed: {insights['total_patterns']}")
    logger.info(f"📊 Average vulture score: {insights['avg_vulture_score']:.3f}")
    
    logger.info("\n🎯 TOP 10 VULTURE OPPORTUNITIES:")
    for i, opp in enumerate(insights['top_vulture_opportunities'][:10], 1):
        if isinstance(opp, dict):
            logger.info(
                f"   {i:2d}. {opp.get('pattern', 'N/A'):>6s} - Score: {opp.get('vulture_score', 0):6.3f} "
                f"(Auctions: {opp.get('total_auctions', 0):3d}, Avg Bidders: {opp.get('avg_bidders', 0):4.1f}, "
                f"No-bid Rate: {opp.get('no_bid_rate', 0):5.1%}, Avg Reward: {opp.get('avg_reward', 0):5.1f})"
            )
        else:
            logger.warning(f"   {i:2d}. Invalid opportunity data: {opp}")
    
    # Show some interesting vulture opportunities that were missed
    logger.info(f"\n🔍 SAMPLE MISSED OPPORTUNITIES ({min(10, len(vulture_opportunities))} of {len(vulture_opportunities)}):")
    for i, opp in enumerate(vulture_opportunities[:10], 1):
        logger.info(f"   {i:2d}. {opp['dice_key']:>6s} - Reward: {opp['reward']:4.1f}, "
                   f"Expected: {opp['expected']:4.1f}, Bonus: {opp['bonus']:+3d}")
    
    # Test strategy filtering on a sample auction
    if game_states:
        sample_state = game_states[0]
        if 'auctions' in sample_state:
            logger.info(f"\n🧪 TESTING STRATEGY ON SAMPLE AUCTIONS:")
            filtered = vulture_strategy.filter(
                sample_state['auctions'], 
                {"gold": 100, "points": 0}, 
                {"interest": 0.05},
                prev_auctions=sample_state.get('prev_auctions', {}),
                current_round=10,
                total_rounds=50
            )
            logger.info(f"   Strategy identified {len(filtered)} vulture opportunities")
            for auction_id, expected_reward, auction_details in filtered[:5]:
                dice_pattern = f"{auction_details['num']}d{auction_details['die']}"
                logger.info(f"   - {auction_id}: {dice_pattern} (Expected: {expected_reward:.1f})")
    
    # Save results
    results_file = Path("data/vulture_test_results.json")
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            "dungeon_dice_analysis": dungeon_dice_analysis,
            "insights": insights,
            "vulture_opportunities_count": len(vulture_opportunities),
            "sample_opportunities": vulture_opportunities[:20]  # Save sample
        }, f, indent=2)
    
    logger.info(f"💾 Results saved to: {results_file}")
    logger.info("✅ VULTURE MODE test complete!")

if __name__ == "__main__":
    log_path = r"C:\Users\Albert\Documents\skolenotater\5. Semester\IKT110-Ai_Architecture\dnd_auction_game\agent_666\logs\agent_local_rand_id_366039_n4.jsonl"
    test_vulture_strategy(log_path)