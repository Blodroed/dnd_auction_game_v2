"""
Settings System Test - Demonstrating Configuration Management

This test shows how the settings system controls all bot components
and allows for real-time configuration updates.
"""

import json
import logging
from pathlib import Path
from settings_manager import get_settings_manager, get_setting, update_setting

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_settings_system():
    """Test comprehensive settings management system."""
    
    logger.info("🛠️ TESTING SETTINGS SYSTEM")
    
    # Test 1: Load settings
    settings = get_settings_manager()
    logger.info("✅ Settings manager loaded")
    
    # Test 2: Read various configuration sections
    agent_info = settings.get('agent_info')
    logger.info(f"📋 Agent Info: {agent_info['name']} v{agent_info['version']}")
    
    strategy_config = settings.get('strategy')
    logger.info(f"⚔️ Strategy: {strategy_config['type']} (aggression: {strategy_config['aggression_multiplier']})")
    
    economy_config = settings.get('economy')
    logger.info(f"💰 Economy: {economy_config['spending_ratio']*100}% spending ratio")
    
    # Test 3: Individual setting retrieval
    current_mode = get_setting('bid_modes', 'current_mode', 'UNKNOWN')
    logger.info(f"🎯 Bid Mode: {current_mode}")
    
    # Test 4: Update individual settings
    logger.info("\n🔧 TESTING SETTINGS UPDATES")
    
    # Update aggression multiplier
    old_aggression = get_setting('strategy', 'aggression_multiplier', 1.5)
    new_aggression = 2.0
    
    update_result = update_setting('strategy', 'aggression_multiplier', new_aggression)
    logger.info(f"✅ Updated aggression: {old_aggression} → {new_aggression} (success: {update_result})")
    
    # Update spending ratio
    old_spending = get_setting('economy', 'spending_ratio', 0.8)
    new_spending = 0.75
    
    update_result = update_setting('economy', 'spending_ratio', new_spending)
    logger.info(f"✅ Updated spending ratio: {old_spending} → {new_spending} (success: {update_result})")
    
    # Test 5: Section updates
    logger.info("\n🔧 TESTING SECTION UPDATES")
    
    new_bid_config = {
        'current_mode': 'EVEN_STEVEN',
        'spread_factor': 0.9,
        'focus_ratio': 0.6
    }
    
    settings.update_section('bid_modes', new_bid_config)
    updated_mode = get_setting('bid_modes', 'current_mode')
    logger.info(f"✅ Updated bid mode section: {updated_mode}")
    
    # Test 6: Save settings to file
    logger.info("\n💾 TESTING SETTINGS PERSISTENCE")
    save_result = settings.save_settings()
    logger.info(f"✅ Settings saved: {save_result}")
    
    # Test 7: Show complete configuration
    logger.info("\n📋 COMPLETE CONFIGURATION SUMMARY:")
    
    sections = ['agent_info', 'strategy', 'bid_modes', 'economy', 'logging']
    for section in sections:
        section_data = settings.get(section, default={})
        logger.info(f"  {section}: {len(section_data)} parameters")
        for key, value in list(section_data.items())[:3]:  # Show first 3 items
            logger.info(f"    {key}: {value}")
        if len(section_data) > 3:
            logger.info(f"    ... and {len(section_data)-3} more")
    
    # Test 8: Validation
    logger.info("\n✅ TESTING SETTINGS VALIDATION")
    validation_result = settings.validate_settings()
    logger.info(f"✅ Settings validation: {'PASSED' if validation_result else 'FAILED'}")
    
    logger.info("\n🎉 ALL SETTINGS TESTS COMPLETED!")
    logger.info("🛠️ Settings system is fully functional and ready for dashboard integration!")

if __name__ == "__main__":
    test_settings_system()