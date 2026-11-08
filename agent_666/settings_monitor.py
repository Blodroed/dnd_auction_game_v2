"""
Real-time Settings Monitor for DoomGuy666 Agent

This module provides real-time monitoring and verification of settings
updates for integration with the dashboard and main agent.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SettingsStatus:
    """Status of settings verification."""
    is_valid: bool
    bid_mode: str
    last_updated: str
    issues: list
    timestamp: str

class RealTimeSettingsMonitor:
    """Monitor settings changes and verify correctness in real-time."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.settings_file = self.base_path / "data" / "settings.json"
        self.last_check_time = None
        self.last_settings_hash = None
        
    def get_current_status(self) -> SettingsStatus:
        """Get current settings status with validation."""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            issues = []
            
            # Check bid mode
            bid_mode = settings.get('bid_modes', {}).get('current_mode', 'UNKNOWN')
            if bid_mode not in ['MEAN_GREEN', 'EVEN_STEVEN', 'ALL_OR_NOTHING', 'HIGHER_LOWER', 'AGGRESSIVE_SPREAD']:
                issues.append(f"Invalid bid mode: {bid_mode}")
            
            # Check critical values
            aggression = settings.get('strategy', {}).get('aggression_multiplier', 0)
            if aggression <= 0:
                issues.append(f"Invalid aggression multiplier: {aggression}")
            
            spending_ratio = settings.get('economy', {}).get('spending_ratio', 0)
            if not (0 < spending_ratio <= 1.0):
                issues.append(f"Invalid spending ratio: {spending_ratio}")
            
            max_bid_ratio = settings.get('strategy', {}).get('max_bid_ratio', 0)
            if not (0 < max_bid_ratio <= 1.0):
                issues.append(f"Invalid max bid ratio: {max_bid_ratio}")
            
            last_updated = settings.get('meta', {}).get('last_updated', 'Unknown')
            
            return SettingsStatus(
                is_valid=len(issues) == 0,
                bid_mode=bid_mode,
                last_updated=last_updated,
                issues=issues,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to get settings status: {e}")
            return SettingsStatus(
                is_valid=False,
                bid_mode='ERROR',
                last_updated='ERROR',
                issues=[f"Failed to load settings: {e}"],
                timestamp=datetime.now().isoformat()
            )
    
    def verify_dashboard_integration(self) -> Dict[str, Any]:
        """Verify dashboard integration is working correctly."""
        status = self.get_current_status()
        
        integration_status = {
            'settings_loaded': status.is_valid,
            'bid_mode': status.bid_mode,
            'last_updated': status.last_updated,
            'dashboard_ready': True,  # Will be updated by dashboard
            'agent_ready': False,     # Will be updated by agent
            'timestamp': status.timestamp,
            'issues': status.issues
        }
        
        # Check if Mean Green is properly set as default
        if status.bid_mode == 'MEAN_GREEN':
            integration_status['default_bid_mode_correct'] = True
            logger.info("✅ Mean Green is correctly set as default bid mode")
        else:
            integration_status['default_bid_mode_correct'] = False
            logger.warning(f"⚠️ Expected MEAN_GREEN as default, got: {status.bid_mode}")
        
        return integration_status
    
    def log_settings_summary(self) -> None:
        """Log a summary of current settings for debugging."""
        status = self.get_current_status()
        
        logger.info("📊 Current Settings Summary:")
        logger.info(f"   - Bid Mode: {status.bid_mode}")
        logger.info(f"   - Valid: {status.is_valid}")
        logger.info(f"   - Last Updated: {status.last_updated}")
        
        if status.issues:
            logger.warning(f"   - Issues: {status.issues}")
        else:
            logger.info("   - No issues detected")
    
    def get_dashboard_verification_data(self) -> Dict[str, Any]:
        """Get data for dashboard verification display."""
        integration_status = self.verify_dashboard_integration()
        
        # Create user-friendly verification data
        verification_data = {
            'status': '✅ VERIFIED' if integration_status['settings_loaded'] else '❌ ISSUES',
            'bid_mode': integration_status['bid_mode'],
            'last_updated': integration_status['last_updated'],
            'default_correct': integration_status.get('default_bid_mode_correct', False),
            'issues_count': len(integration_status['issues']),
            'issues': integration_status['issues'],
            'timestamp': integration_status['timestamp']
        }
        
        return verification_data

# Global monitor instance
_monitor_instance = None

def get_settings_monitor() -> RealTimeSettingsMonitor:
    """Get the global settings monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = RealTimeSettingsMonitor()
    return _monitor_instance

def verify_settings_quick() -> bool:
    """Quick settings verification for use in other modules."""
    monitor = get_settings_monitor()
    status = monitor.get_current_status()
    
    if status.is_valid:
        logger.info(f"✅ Settings verified: {status.bid_mode} mode active")
        return True
    else:
        logger.error(f"❌ Settings issues: {status.issues}")
        return False

def log_current_settings() -> None:
    """Log current settings for debugging purposes."""
    monitor = get_settings_monitor()
    monitor.log_settings_summary()

if __name__ == "__main__":
    # Quick test of the monitor
    monitor = RealTimeSettingsMonitor()
    status = monitor.get_current_status()
    
    print(f"Settings Status: {'✅ VALID' if status.is_valid else '❌ INVALID'}")
    print(f"Bid Mode: {status.bid_mode}")
    print(f"Last Updated: {status.last_updated}")
    
    if status.issues:
        print("Issues:")
        for issue in status.issues:
            print(f"  - {issue}")
    
    print("\nDashboard Verification Data:")
    verification_data = monitor.get_dashboard_verification_data()
    for key, value in verification_data.items():
        print(f"  {key}: {value}")