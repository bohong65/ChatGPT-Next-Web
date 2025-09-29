"""
Configuration management for the trading framework.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger


# Global configuration cache
_config_cache: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    Returns:
        Configuration dictionary
    """
    global _config_cache
    
    if _config_cache is None:
        _config_cache = load_config()
    
    return _config_cache


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file and environment variables.
    
    Args:
        config_path: Path to configuration file. If None, uses default paths.
        
    Returns:
        Configuration dictionary
    """
    # Default configuration
    config = get_default_config()
    
    # Load from config file
    if config_path is None:
        # Try default config file locations
        possible_paths = [
            'config/config.yaml',
            'config.yaml',
            'trading_framework/config/config.yaml',
            os.path.expanduser('~/.trading_framework/config.yaml')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config = deep_merge(config, file_config)
                    logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
    
    # Override with environment variables
    config = load_environment_variables(config)
    
    return config


def save_config(config: Dict[str, Any], config_path: str = 'config/config.yaml') -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save configuration file
        
    Returns:
        True if saved successfully
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Remove sensitive information before saving
        safe_config = remove_sensitive_data(config)
        
        with open(config_path, 'w') as f:
            yaml.dump(safe_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {e}")
        return False


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        'xtdata': {
            'base_url': 'https://api.xtdata.com',
            'api_key': None,
            'timeout': 30,
            'max_retries': 3
        },
        'xttrader': {
            'base_url': 'https://api.xttrader.com',
            'api_key': None,
            'secret_key': None,
            'timeout': 30,
            'max_retries': 3
        },
        'logging': {
            'level': 'INFO',
            'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}',
            'file': 'logs/trading_framework.log',
            'max_file_size': '10 MB',
            'retention': '30 days'
        },
        'database': {
            'type': 'sqlite',
            'path': 'data/trading_framework.db',
            'backup_enabled': True,
            'backup_interval': '1 day'
        },
        'risk_management': {
            'max_position_size': 0.1,  # 10% of portfolio
            'max_daily_loss': 0.02,    # 2% daily loss limit
            'max_drawdown': 0.1,       # 10% maximum drawdown
            'stop_loss_default': 0.02, # 2% default stop loss
            'take_profit_default': 0.04 # 4% default take profit
        },
        'backtesting': {
            'initial_capital': 100000,
            'commission': 0.001,  # 0.1%
            'slippage': 0.0005,   # 0.05%
            'benchmark_symbol': 'SPY'
        },
        'notifications': {
            'enabled': True,
            'email': {
                'enabled': False,
                'smtp_server': None,
                'smtp_port': 587,
                'username': None,
                'password': None,
                'to_addresses': []
            },
            'webhook': {
                'enabled': False,
                'url': None,
                'timeout': 10
            }
        }
    }


def load_environment_variables(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        config: Base configuration to update
        
    Returns:
        Updated configuration
    """
    # XTData configuration
    if os.getenv('XTDATA_API_KEY'):
        config['xtdata']['api_key'] = os.getenv('XTDATA_API_KEY')
    
    if os.getenv('XTDATA_BASE_URL'):
        config['xtdata']['base_url'] = os.getenv('XTDATA_BASE_URL')
    
    # XTTrader configuration
    if os.getenv('XTTRADER_API_KEY'):
        config['xttrader']['api_key'] = os.getenv('XTTRADER_API_KEY')
    
    if os.getenv('XTTRADER_SECRET_KEY'):
        config['xttrader']['secret_key'] = os.getenv('XTTRADER_SECRET_KEY')
    
    if os.getenv('XTTRADER_BASE_URL'):
        config['xttrader']['base_url'] = os.getenv('XTTRADER_BASE_URL')
    
    # Logging configuration
    if os.getenv('LOG_LEVEL'):
        config['logging']['level'] = os.getenv('LOG_LEVEL')
    
    if os.getenv('LOG_FILE'):
        config['logging']['file'] = os.getenv('LOG_FILE')
    
    # Database configuration
    if os.getenv('DATABASE_PATH'):
        config['database']['path'] = os.getenv('DATABASE_PATH')
    
    # Risk management
    if os.getenv('MAX_POSITION_SIZE'):
        try:
            config['risk_management']['max_position_size'] = float(os.getenv('MAX_POSITION_SIZE'))
        except ValueError:
            logger.warning("Invalid MAX_POSITION_SIZE environment variable")
    
    if os.getenv('MAX_DAILY_LOSS'):
        try:
            config['risk_management']['max_daily_loss'] = float(os.getenv('MAX_DAILY_LOSS'))
        except ValueError:
            logger.warning("Invalid MAX_DAILY_LOSS environment variable")
    
    # Backtesting
    if os.getenv('INITIAL_CAPITAL'):
        try:
            config['backtesting']['initial_capital'] = float(os.getenv('INITIAL_CAPITAL'))
        except ValueError:
            logger.warning("Invalid INITIAL_CAPITAL environment variable")
    
    return config


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge into dict1
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def remove_sensitive_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive data from configuration before saving.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configuration with sensitive data removed
    """
    safe_config = config.copy()
    
    # List of sensitive keys to remove or mask
    sensitive_keys = [
        ['xtdata', 'api_key'],
        ['xttrader', 'api_key'],
        ['xttrader', 'secret_key'],
        ['notifications', 'email', 'password'],
        ['notifications', 'webhook', 'url']
    ]
    
    for key_path in sensitive_keys:
        current = safe_config
        for key in key_path[:-1]:
            if key in current and isinstance(current[key], dict):
                current = current[key]
            else:
                break
        else:
            # Replace with placeholder if exists
            if key_path[-1] in current and current[key_path[-1]]:
                current[key_path[-1]] = '***HIDDEN***'
    
    return safe_config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if configuration is valid
    """
    required_sections = ['xtdata', 'xttrader', 'logging', 'risk_management']
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            return False
    
    # Validate risk management values
    rm_config = config.get('risk_management', {})
    
    if rm_config.get('max_position_size', 0) <= 0 or rm_config.get('max_position_size', 0) > 1:
        logger.error("max_position_size must be between 0 and 1")
        return False
    
    if rm_config.get('max_daily_loss', 0) <= 0 or rm_config.get('max_daily_loss', 0) > 1:
        logger.error("max_daily_loss must be between 0 and 1")
        return False
    
    logger.info("Configuration validation passed")
    return True


def reload_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Reload configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Reloaded configuration
    """
    global _config_cache
    
    _config_cache = load_config(config_path)
    logger.info("Configuration reloaded")
    
    return _config_cache


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation.
    
    Args:
        key_path: Dot-separated path to the configuration value (e.g., 'xtdata.api_key')
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
    config = get_config()
    keys = key_path.split('.')
    
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set_config_value(key_path: str, value: Any) -> None:
    """
    Set a configuration value using dot notation.
    
    Args:
        key_path: Dot-separated path to the configuration value
        value: Value to set
    """
    global _config_cache
    
    if _config_cache is None:
        _config_cache = load_config()
    
    keys = key_path.split('.')
    current = _config_cache
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    logger.debug(f"Set configuration value: {key_path} = {value}")