#!/usr/bin/env python3
"""
Test script for VULTURE MODE implementation according to markdown specifications.
This tests the updated system without requiring a live game server.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vulture_mode_implementation():
    """Test the VULTURE MODE system according to markdown specifications."""
    
    logger.info("🦅🦅🦅 TESTING VULTURE MODE IMPLEMENTATION 🦅🦅🦅")
    
    # Test 1: Import all components successfully
    try:
        from strategies import VultureMode
        from data_handler import VultureDataHandler
        from storage import VultureStorage
        from bid_modes import BidModeSelector
        from economy import EconomyAnalyzer
        from main import doom_bid_controller, DoomAgent
        logger.info("✅ All components imported successfully")
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Initialize VultureMode strategy
    try:
        vulture_strategy = VultureMode()
        logger.info("✅ VultureMode strategy initialized")
    except Exception as e:
        logger.error(f"❌ VultureMode initialization failed: {e}")
        return False
    
    # Test 3: Test vulture agent initialization
    try:
        doom_agent = DoomAgent()
        logger.info(f"✅ Doom agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Doom agent initialization failed: {e}")
        return False
    
    # Test 4: Test vulture mode bid calculation according to markdown specs
    try:
        # Mock game data
        sample_states = {
            "player1": {"gold": 15, "points": 5},
            "player2": {"gold": 12, "points": 3},
            "doom_agent_666": {"gold": 50, "points": 8}  # Our agent with more gold to test spending
        }
        
        sample_prev_auctions = {
            "a1": {
                "bids": [
                    {"agent": "player1", "gold": 5},
                    {"agent": "player2", "gold": 3}
                ]
            }
        }
        
        sample_auctions = {
            "a1": {"num": 2, "die": 6, "bonus": 5},
            "a2": {"num": 1, "die": 12, "bonus": 0}
        }
        
        sample_bank_state = {
            "remainder_gold_income": [1000],
            "remainder_bank_interest": [1.03],
            "remainder_bank_limit": [2000]
        }
        
        # Test doom bidding controller
        bids = doom_bid_controller("doom_agent_666", 1, sample_states, sample_auctions, 
                                  sample_prev_auctions, sample_bank_state)
        logger.info(f"✅ Doom mode bids generated: {bids}")
        
        # Verify aggressive spending (should spend significant portion of gold)
        total_bid = sum(bids.values()) if bids else 0
        available_gold = sample_states["doom_agent_666"]["gold"]
        spend_ratio = total_bid / available_gold if available_gold > 0 else 0
        logger.info(f"📊 Spending ratio: {spend_ratio:.2%} ({total_bid}/{available_gold})")
        
        if spend_ratio < 0.5:
            logger.warning(f"⚠️ Low spending ratio detected - may accumulate gold")
        else:
            logger.info(f"✅ Good spending ratio - prevents gold accumulation")
        
    except Exception as e:
        logger.error(f"❌ Bidding logic test failed: {e}")
        return False
    
    # Test 5: Test historical analysis (using existing test data)
    try:
        log_path = Path("logs/agent_local_rand_id_366039_n4.jsonl")
        if log_path.exists():
            vulture_handler = VultureDataHandler()
            
            # Load some sample data
            with open(log_path, 'r') as f:
                first_line = f.readline()
                sample_data = json.loads(first_line)
            
            # Test analysis processing
            vulture_handler.process_game_state(sample_data)
            insights = vulture_handler.get_green_zones()
            logger.info(f"✅ Historical analysis working, found {len(insights)} insights")
        else:
            logger.info("⚠️ No test log file found, skipping historical analysis test")
    except Exception as e:
        logger.error(f"❌ Historical analysis test failed: {e}")
        return False
    
    # Test 6: Test settings integration
    try:
        settings_file = Path("data/settings.json")
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            logger.info(f"✅ Settings loaded: {settings}")
        else:
            logger.info("⚠️ No settings file found")
    except Exception as e:
        logger.error(f"❌ Settings test failed: {e}")
        return False
    
    logger.info("🎉 ALL TESTS PASSED! DOOM CONTROLLER is ready with configurable strategies and bid modes!")
    return True

if __name__ == "__main__":
    success = test_vulture_mode_implementation()
    sys.exit(0 if success else 1)


def test_vulture_handler_integration_selective_bidding():
    """When a VultureDataHandler favors some dice keys, VultureMode should bid only on those with a high vulture_score."""
    from strategies import VultureMode
    from data_handler import VultureDataHandler

    handler = VultureDataHandler()
    # High score for (6,1), low score for (12,1)
    handler.vulture_scores[(6, 1)] = 0.9
    handler.vulture_scores[(12, 1)] = 0.1

    v = VultureMode()
    sample_auctions = {
        "a1": {"num": 1, "die": 6, "bonus": 0},
        "a2": {"num": 1, "die": 12, "bonus": 0}
    }
    bids = v.calculate_vulture_bids("doom_agent_666", sample_auctions, {}, 40, data_handler=handler)
    assert isinstance(bids, dict)
    # Should only bid on the high scoring auction (6,1)
    assert "a1" in bids and "a2" not in bids


def test_vulture_no_handler_fallback_distribution():
    """When no handler is provided, the VultureMode uses legacy scoring and bids on multiple auctions."""
    from strategies import VultureMode

    v = VultureMode()
    sample_auctions = {
        "a1": {"num": 1, "die": 6, "bonus": 0},
        "a2": {"num": 1, "die": 12, "bonus": 0},
        "a3": {"num": 2, "die": 6, "bonus": 1}
    }
    bids = v.calculate_vulture_bids("doom_agent_666", sample_auctions, {}, 40, data_handler=None)
    assert isinstance(bids, dict)
    # For fallback distribution, we expect bids on at least 2 auctions given enough budget
    assert len(bids) >= 2


def test_vulture_ev_filter_and_pool_contribution():
    """Ensure auctions with expected value <= 0 are skipped and pool contribution occurs."""
    from strategies import VultureMode
    from main import DoomAgent

    v = VultureMode()
    # Auction a1 positive EV, a2 negative EV
    sample_auctions = {
        "a1": {"num": 1, "die": 6, "bonus": 0},
        "a2": {"num": 1, "die": 2, "bonus": -10}
    }
    # No handler - expect only a1 to be considered
    bids = v.calculate_vulture_bids("doom_agent_666", sample_auctions, {}, 40, data_handler=None)
    assert "a2" not in bids

    # Test pool contribution in the doom controller
    doom_agent = DoomAgent()
    dc = doom_agent.doom_controller
    agent_id = doom_agent.settings.get_agent_info().get('player_id', 'doom_agent_666')
    # Give the agent enough points to be able to contribute to the pool
    states = { agent_id: { 'gold': 50, 'points': 20 } }
    bank_state = {
        "remainder_gold_income": [100],
        "remainder_bank_interest": [1.0],
        "remainder_bank_limit": [1000]
    }
    # Call doom_bid_controller with new signature (pool present) and prev_auctions reflecting our wins
    sample_prev_auctions = {
        'a_prev_1': {
            'bids': [
                {'a_id': agent_id, 'gold': 10},
            ],
            'reward': 12
        }
    }
    bids = dc.doom_bid_controller(agent_id, 1, states, sample_auctions, sample_prev_auctions, 0, {}, bank_state)
    # Ensure the last pool contribution is equal to 5% of the previous win (rounded)
    expected = int(round(12 * dc.settings.get('economy', 'pool_contribution_rate', 0.05)))
    assert getattr(dc, '_last_pool_contribution', 0) == expected

    # Now enable highest-single-win configuration and verify behavior
    dc.settings.update('economy', 'pool_contribution_use_highest', True)
    # Two wins: small and big; expect contribution based on highest (12 -> we set to 12 already)
    sample_prev_auctions_two = {
        'a_prev_1': {'bids': [{'a_id': agent_id, 'gold': 10}], 'reward': 5},
        'a_prev_2': {'bids': [{'a_id': agent_id, 'gold': 10}], 'reward': 12},
    }
    bids = dc.doom_bid_controller(agent_id, 1, states, sample_auctions, sample_prev_auctions_two, 0, {}, bank_state)
    expected2 = int(round(12 * dc.settings.get('economy', 'pool_contribution_rate', 0.05)))
    assert getattr(dc, '_last_pool_contribution', 0) == expected2