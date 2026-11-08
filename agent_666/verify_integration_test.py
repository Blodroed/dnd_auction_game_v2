"""
Quick Settings Integration Test

Use this in your agent code to verify settings are loaded correctly:

from verify_integration_test import test_agent_settings_integration

# At the start of your agent
if test_agent_settings_integration():
    print("✅ Settings verified and ready!")
else:
    print("❌ Settings verification failed!")
"""

import logging
from settings_monitor import verify_settings_quick, log_current_settings
from bid_modes import BidModeSelector
from settings_manager import get_settings_manager

logger = logging.getLogger(__name__)

def test_agent_settings_integration() -> bool:
    """
    Quick integration test to verify agent settings are working.
    
    Returns:
        bool: True if all critical settings are working correctly
    """
    logger.info("🧪 Running agent settings integration test...")
    
    test_results = []
    
    # Test 1: Basic settings loading
    try:
        settings_manager = get_settings_manager()
        current_mode = settings_manager.get('bid_modes', 'current_mode', 'UNKNOWN')
        
        if current_mode == 'MEAN_GREEN':
            logger.info("✅ Test 1 PASSED: Settings manager loaded correctly")
            test_results.append(True)
        else:
            logger.error(f"❌ Test 1 FAILED: Expected MEAN_GREEN, got {current_mode}")
            test_results.append(False)
    except Exception as e:
        logger.error(f"❌ Test 1 FAILED: Settings manager error: {e}")
        test_results.append(False)
    
    # Test 2: Bid mode selector functionality
    try:
        bid_selector = BidModeSelector()
        config = bid_selector.get_current_config()
        
        if config['current_mode'] == 'mean_green':  # BidModeSelector returns lowercase
            logger.info("✅ Test 2 PASSED: Bid mode selector working correctly")
            test_results.append(True)
        else:
            logger.error(f"❌ Test 2 FAILED: Bid selector mode: {config.get('current_mode')}")
            test_results.append(False)
    except Exception as e:
        logger.error(f"❌ Test 2 FAILED: Bid mode selector error: {e}")
        test_results.append(False)
    
    # Test 3: Settings monitor verification
    try:
        is_valid = verify_settings_quick()
        if is_valid:
            logger.info("✅ Test 3 PASSED: Settings monitor verification successful")
            test_results.append(True)
        else:
            logger.error("❌ Test 3 FAILED: Settings monitor found issues")
            test_results.append(False)
    except Exception as e:
        logger.error(f"❌ Test 3 FAILED: Settings monitor error: {e}")
        test_results.append(False)
    
    # Test 4: Critical values check
    try:
        settings_manager = get_settings_manager()
        aggression = settings_manager.get('strategy', 'aggression_multiplier', 0)
        spending_ratio = settings_manager.get('economy', 'spending_ratio', 0)
        
        if aggression > 0 and 0 < spending_ratio <= 1.0:
            logger.info("✅ Test 4 PASSED: Critical values are valid")
            test_results.append(True)
        else:
            logger.error(f"❌ Test 4 FAILED: Invalid values - aggression: {aggression}, spending: {spending_ratio}")
            test_results.append(False)
    except Exception as e:
        logger.error(f"❌ Test 4 FAILED: Critical values error: {e}")
        test_results.append(False)
    
    # Summary
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        logger.info(f"🎉 ALL TESTS PASSED: {passed_tests}/{total_tests} - Settings integration verified!")
        log_current_settings()  # Log current settings for reference
        return True
    else:
        logger.error(f"❌ SOME TESTS FAILED: {passed_tests}/{total_tests} - Check settings configuration!")
        return False

def test_bid_mode_switching():
    """Test that bid mode is loaded correctly."""
    logger.info("🔄 Testing bid mode loading...")
    
    try:
        bid_selector = BidModeSelector()
        current_config = bid_selector.get_current_config()
        
        if current_config['current_mode'] == 'mean_green':
            logger.info(f"✅ Bid mode loaded correctly: {current_config['current_mode']}")
            return True
        else:
            logger.error(f"❌ Unexpected bid mode: {current_config['current_mode']}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Bid mode test failed: {e}")
        return False

if __name__ == "__main__":
    # Run integration test
    print("🧪 Agent Settings Integration Test")
    print("=" * 40)
    
    if test_agent_settings_integration():
        print("\n✅ INTEGRATION TEST PASSED")
        print("Your agent settings are working correctly!")
        
        # Test bid mode switching
        print("\n🔄 Testing bid mode switching...")
        if test_bid_mode_switching():
            print("✅ Bid mode switching working correctly!")
        else:
            print("❌ Bid mode switching has issues!")
            
    else:
        print("\n❌ INTEGRATION TEST FAILED")
        print("Check your settings configuration!")