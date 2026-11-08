"""
Settings Verification Tool for DoomGuy666 Agent

This tool provides comprehensive verification that agent settings are being
loaded, applied, and updated correctly across all components.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SettingsVerifier:
    """Comprehensive settings verification and validation tool."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.settings_file = self.base_path / "data" / "settings.json"
        self.dashboard_settings_file = self.base_path / "dashboard" / "data" / "settings.json"
        
    def load_settings(self) -> Dict[str, Any]:
        """Load the main settings file."""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            logger.info(f"✅ Successfully loaded settings from: {self.settings_file}")
            return settings
        except Exception as e:
            logger.error(f"❌ Failed to load settings: {e}")
            return {}
    
    def verify_critical_settings(self, settings: Dict[str, Any]) -> bool:
        """Verify all critical settings are present and valid."""
        logger.info("🔍 Verifying critical settings...")
        
        critical_checks = []
        
        # Check bid mode
        bid_mode = settings.get('bid_modes', {}).get('current_mode')
        if bid_mode == 'MEAN_GREEN':
            logger.info(f"✅ Bid Mode: {bid_mode} (DEFAULT - CORRECT)")
            critical_checks.append(True)
        else:
            logger.warning(f"⚠️ Bid Mode: {bid_mode} (Expected: MEAN_GREEN)")
            critical_checks.append(False)
        
        # Check strategy settings
        strategy = settings.get('strategy', {})
        aggression = strategy.get('aggression_multiplier', 0)
        max_bid_ratio = strategy.get('max_bid_ratio', 0)
        high_value_threshold = strategy.get('high_value_threshold', 0)
        
        logger.info(f"🎯 Strategy Settings:")
        logger.info(f"   - Aggression Multiplier: {aggression}")
        logger.info(f"   - Max Bid Ratio: {max_bid_ratio}")
        logger.info(f"   - High Value Threshold: {high_value_threshold}")
        
        critical_checks.append(aggression > 0)
        critical_checks.append(0 < max_bid_ratio <= 1.0)
        critical_checks.append(high_value_threshold > 0)
        
        # Check economy settings
        economy = settings.get('economy', {})
        spending_ratio = economy.get('spending_ratio', 0)
        min_reserve = economy.get('min_reserve_gold', 0)
        
        logger.info(f"🏦 Economy Settings:")
        logger.info(f"   - Spending Ratio: {spending_ratio}")
        logger.info(f"   - Min Reserve Gold: {min_reserve}")
        logger.info(f"   - Max Bet Limit Enabled: {economy.get('use_max_bet_limit', False)}")
        
        critical_checks.append(0 < spending_ratio <= 1.0)
        critical_checks.append(min_reserve >= 0)
        
        # Check metadata
        meta = settings.get('meta', {})
        last_updated = meta.get('last_updated', 'Unknown')
        version = meta.get('version', 'Unknown')
        
        logger.info(f"📋 Metadata:")
        logger.info(f"   - Version: {version}")
        logger.info(f"   - Last Updated: {last_updated}")
        
        all_passed = all(critical_checks)
        if all_passed:
            logger.info("✅ All critical settings verification PASSED")
        else:
            logger.error("❌ Some critical settings verification FAILED")
        
        return all_passed
    
    def verify_settings_consistency(self) -> bool:
        """Check consistency between different settings sections."""
        logger.info("🔄 Verifying settings consistency...")
        
        settings = self.load_settings()
        if not settings:
            return False
        
        consistency_checks = []
        
        # Check bid mode vs strategy alignment
        bid_mode = settings.get('bid_modes', {}).get('current_mode')
        focus_ratio = settings.get('bid_modes', {}).get('focus_ratio', 0)
        
        if bid_mode == 'MEAN_GREEN' and 0.4 <= focus_ratio <= 0.8:
            logger.info(f"✅ Bid mode {bid_mode} and focus ratio {focus_ratio} are well-aligned")
            consistency_checks.append(True)
        else:
            logger.warning(f"⚠️ Potential misalignment: {bid_mode} with focus ratio {focus_ratio}")
            consistency_checks.append(False)
        
        # Check spending vs reserve consistency
        spending_ratio = settings.get('economy', {}).get('spending_ratio', 0)
        min_reserve = settings.get('economy', {}).get('min_reserve_gold', 0)
        
        if spending_ratio < 1.0 or min_reserve > 0:
            logger.info(f"✅ Spending ratio {spending_ratio} and reserve {min_reserve} provide safety buffer")
            consistency_checks.append(True)
        else:
            logger.warning(f"⚠️ No safety buffer: spending={spending_ratio}, reserve={min_reserve}")
            consistency_checks.append(False)
        
        # Check risk level consistency
        risk_level = settings.get('safety', {}).get('risk_level', 'unknown')
        max_total_bid = settings.get('safety', {}).get('max_total_bid', 1.0)
        
        logger.info(f"🛡️ Risk Management:")
        logger.info(f"   - Risk Level: {risk_level}")
        logger.info(f"   - Max Total Bid: {max_total_bid}")
        
        consistency_checks.append(max_total_bid < 1.0)
        
        all_consistent = all(consistency_checks)
        if all_consistent:
            logger.info("✅ Settings consistency verification PASSED")
        else:
            logger.warning("⚠️ Some settings consistency checks FAILED")
        
        return all_consistent
    
    def test_settings_loading_in_components(self) -> bool:
        """Test that components can properly load and use the settings."""
        logger.info("🧪 Testing settings loading in components...")
        
        component_tests = []
        
        try:
            # Test settings manager
            from settings_manager import get_settings_manager
            settings_manager = get_settings_manager()
            
            # Test bid mode loading
            bid_config = settings_manager.get('bid_modes', {})
            current_mode = bid_config.get('current_mode')
            
            if current_mode == 'MEAN_GREEN':
                logger.info(f"✅ Settings Manager loaded bid mode: {current_mode}")
                component_tests.append(True)
            else:
                logger.error(f"❌ Settings Manager bid mode mismatch: {current_mode}")
                component_tests.append(False)
            
            # Test strategy loading
            strategy_config = settings_manager.get('strategy', {})
            aggression = strategy_config.get('aggression_multiplier')
            
            if aggression and aggression > 0:
                logger.info(f"✅ Settings Manager loaded aggression: {aggression}")
                component_tests.append(True)
            else:
                logger.error(f"❌ Settings Manager aggression loading failed: {aggression}")
                component_tests.append(False)
            
        except Exception as e:
            logger.error(f"❌ Settings Manager component test failed: {e}")
            component_tests.append(False)
        
        try:
            # Test bid mode selector
            from bid_modes import BidModeSelector
            
            settings = self.load_settings()
            bid_selector = BidModeSelector(settings.get('bid_modes', {}))
            
            current_config = bid_selector.get_current_config()
            if current_config.get('current_mode') == 'mean_green':  # Note: returns string value
                logger.info(f"✅ BidModeSelector loaded correctly: {current_config['current_mode']}")
                component_tests.append(True)
            else:
                logger.error(f"❌ BidModeSelector mode mismatch: {current_config.get('current_mode')}")
                component_tests.append(False)
                
        except Exception as e:
            logger.error(f"❌ BidModeSelector component test failed: {e}")
            component_tests.append(False)
        
        all_components_passed = all(component_tests)
        if all_components_passed:
            logger.info("✅ All component loading tests PASSED")
        else:
            logger.error("❌ Some component loading tests FAILED")
        
        return all_components_passed
    
    def verify_dashboard_sync(self) -> bool:
        """Verify dashboard is in sync with main settings."""
        logger.info("📊 Verifying dashboard synchronization...")
        
        try:
            # Check if dashboard settings file exists
            if self.dashboard_settings_file.exists():
                with open(self.dashboard_settings_file, 'r') as f:
                    dashboard_settings = json.load(f)
                logger.info("✅ Dashboard settings file found")
            else:
                logger.info("ℹ️ Dashboard settings file not found (using main settings)")
                return True
            
            # Compare critical settings
            main_settings = self.load_settings()
            
            sync_checks = []
            
            # Check bid mode sync
            main_bid_mode = main_settings.get('bid_modes', {}).get('current_mode')
            dash_bid_mode = dashboard_settings.get('bid_modes', {}).get('current_mode')
            
            if main_bid_mode == dash_bid_mode:
                logger.info(f"✅ Bid mode synchronized: {main_bid_mode}")
                sync_checks.append(True)
            else:
                logger.warning(f"⚠️ Bid mode out of sync: main={main_bid_mode}, dash={dash_bid_mode}")
                sync_checks.append(False)
            
            all_synced = all(sync_checks)
            if all_synced:
                logger.info("✅ Dashboard synchronization verification PASSED")
            else:
                logger.warning("⚠️ Dashboard synchronization issues detected")
            
            return all_synced
            
        except Exception as e:
            logger.error(f"❌ Dashboard sync verification failed: {e}")
            return False
    
    def create_settings_report(self) -> str:
        """Generate a comprehensive settings report."""
        logger.info("📋 Generating comprehensive settings report...")
        
        settings = self.load_settings()
        if not settings:
            return "❌ Failed to load settings for report"
        
        report_lines = [
            "="*60,
            "🎯 DOOMGUY666 AGENT SETTINGS VERIFICATION REPORT",
            "="*60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Settings File: {self.settings_file}",
            "",
            "📊 CRITICAL SETTINGS:",
            f"  Bid Mode: {settings.get('bid_modes', {}).get('current_mode', 'UNKNOWN')}",
            f"  Aggression: {settings.get('strategy', {}).get('aggression_multiplier', 'UNKNOWN')}",
            f"  Max Bid Ratio: {settings.get('strategy', {}).get('max_bid_ratio', 'UNKNOWN')}",
            f"  Spending Ratio: {settings.get('economy', {}).get('spending_ratio', 'UNKNOWN')}",
            f"  Min Reserve: {settings.get('economy', {}).get('min_reserve_gold', 'UNKNOWN')}",
            "",
            "🎮 BID MODE DETAILS:",
            f"  Current Mode: {settings.get('bid_modes', {}).get('current_mode', 'UNKNOWN')}",
            f"  Focus Ratio: {settings.get('bid_modes', {}).get('focus_ratio', 'UNKNOWN')}",
            f"  Spread Factor: {settings.get('bid_modes', {}).get('spread_factor', 'UNKNOWN')}",
            f"  Max Single Bid: {settings.get('bid_modes', {}).get('max_single_bid_ratio', 'UNKNOWN')}",
            "",
            "🏦 ECONOMY SETTINGS:",
            f"  Spending Ratio: {settings.get('economy', {}).get('spending_ratio', 'UNKNOWN')}",
            f"  Min Reserve Gold: {settings.get('economy', {}).get('min_reserve_gold', 'UNKNOWN')}",
            f"  Max Bet Limit: {settings.get('economy', {}).get('use_max_bet_limit', 'UNKNOWN')}",
            f"  Emergency Spending: {settings.get('economy', {}).get('emergency_spending_enabled', 'UNKNOWN')}",
            "",
            "🛡️ SAFETY SETTINGS:",
            f"  Risk Level: {settings.get('safety', {}).get('risk_level', 'UNKNOWN')}",
            f"  Max Total Bid: {settings.get('safety', {}).get('max_total_bid', 'UNKNOWN')}",
            f"  Emergency Stop Loss: {settings.get('safety', {}).get('emergency_stop_loss', 'UNKNOWN')}",
            "",
            "📋 METADATA:",
            f"  Version: {settings.get('meta', {}).get('version', 'UNKNOWN')}",
            f"  Last Updated: {settings.get('meta', {}).get('last_updated', 'UNKNOWN')}",
            f"  Created By: {settings.get('meta', {}).get('created_by', 'UNKNOWN')}",
            "="*60
        ]
        
        report = "\n".join(report_lines)
        logger.info("✅ Settings report generated successfully")
        return report
    
    def run_full_verification(self) -> bool:
        """Run all verification tests and return overall result."""
        logger.info("🚀 Starting full settings verification...")
        
        tests = []
        
        # Load settings
        settings = self.load_settings()
        if not settings:
            logger.error("❌ Cannot proceed without settings")
            return False
        
        # Run all verification tests
        tests.append(self.verify_critical_settings(settings))
        tests.append(self.verify_settings_consistency())
        tests.append(self.test_settings_loading_in_components())
        tests.append(self.verify_dashboard_sync())
        
        # Generate report
        report = self.create_settings_report()
        print("\n" + report)
        
        # Overall result
        all_passed = all(tests)
        
        if all_passed:
            logger.info("🎉 ALL VERIFICATION TESTS PASSED - Settings are working correctly!")
        else:
            logger.error("❌ SOME VERIFICATION TESTS FAILED - Check logs for details")
        
        return all_passed

def main():
    """Run the settings verification tool."""
    print("🔍 DoomGuy666 Agent Settings Verification Tool")
    print("=" * 50)
    
    verifier = SettingsVerifier()
    success = verifier.run_full_verification()
    
    if success:
        print("\n✅ VERIFICATION COMPLETE: All systems operational!")
    else:
        print("\n❌ VERIFICATION FAILED: Check settings and components!")
    
    return success

if __name__ == "__main__":
    main()