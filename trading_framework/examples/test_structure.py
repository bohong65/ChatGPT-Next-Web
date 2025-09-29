"""
Simple test to verify the framework structure.
"""

import os
import sys

# Add the trading framework to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

def test_framework_structure():
    """Test that all modules are structured correctly."""
    
    print("=" * 50)
    print("TRADING FRAMEWORK STRUCTURE TEST")
    print("=" * 50)
    
    # Test basic imports
    try:
        import trading_framework
        print("✅ Main framework module imported")
        
        print(f"Version: {trading_framework.__version__}")
        print(f"Author: {trading_framework.__author__}")
        
    except Exception as e:
        print(f"❌ Framework import failed: {e}")
        return False
    
    # Test module structure
    modules_to_test = [
        'trading_framework.data',
        'trading_framework.strategies', 
        'trading_framework.backtest',
        'trading_framework.execution',
        'trading_framework.config',
        'trading_framework.utils'
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} structure OK")
        except ImportError as e:
            print(f"❌ {module_name} import failed: {e}")
    
    # Test configuration
    try:
        from trading_framework.config import get_default_config
        config = get_default_config()
        print(f"✅ Configuration loaded ({len(config)} sections)")
        
        required_sections = ['xtdata', 'xttrader', 'logging', 'risk_management']
        for section in required_sections:
            if section in config:
                print(f"  ✅ {section} section present")
            else:
                print(f"  ❌ {section} section missing")
                
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    print("\n" + "=" * 50)
    print("FRAMEWORK STRUCTURE TEST COMPLETED")
    print("=" * 50)
    return True


if __name__ == "__main__":
    test_framework_structure()