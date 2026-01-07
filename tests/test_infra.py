"""
Test Infrastructure: Config and Logging

This tests that configuration and logging work correctly.
"""

import sys
sys.path.insert(0, '/home/claude/agent_project')

from infra.config import settings
from infra.logging import logger, log_config


def test_configuration():
    """Test that configuration loads correctly"""
    print("=" * 70)
    print("TEST 1: Configuration")
    print("=" * 70)
    
    # Test settings exist
    print(f"✅ Settings loaded: {settings}")
    
    # Test individual settings
    print(f"✅ Ollama host: {settings.ollama_host}")
    print(f"✅ Ollama model: {settings.ollama_model}")
    print(f"✅ Max iterations: {settings.max_iterations}")
    print(f"✅ Temperature: {settings.temperature}")
    print(f"✅ Log level: {settings.log_level}")
    
    # Test boolean settings
    print(f"✅ Web search enabled: {settings.enable_web_search}")
    print(f"✅ Tasks enabled: {settings.enable_tasks}")
    
    # Test to_dict method
    config_dict = settings.to_dict()
    print(f"✅ Config as dict: {len(config_dict)} settings")
    
    print("\n✅ Configuration works!\n")


def test_logging():
    """Test that logging works correctly"""
    print("=" * 70)
    print("TEST 2: Logging")
    print("=" * 70)
    
    # Test different log levels
    logger.debug("🔍 This is a DEBUG message (detailed info)")
    logger.info("ℹ️  This is an INFO message (general info)")
    logger.warning("⚠️  This is a WARNING message (something unexpected)")
    logger.error("❌ This is an ERROR message (something failed)")
    
    # Test logging with variables
    model_name = "llama3.1:8b"
    logger.info(f"✅ Model loaded: {model_name}")
    
    # Test structured info
    logger.info(f"✅ Agent started with max_iterations={settings.max_iterations}")
    
    print("\n✅ Logging works!\n")


def test_log_config():
    """Test logging the full configuration"""
    print("=" * 70)
    print("TEST 3: Log Configuration")
    print("=" * 70)
    
    # This logs all settings in a nice format
    log_config()
    
    print("\n✅ Log config works!\n")


def demonstrate_usage():
    """Show how to use config and logging in real code"""
    print("=" * 70)
    print("TEST 4: Real-World Usage Example")
    print("=" * 70)
    
    # Example 1: Using config in model initialization
    logger.info("Example: Initializing model with settings...")
    logger.debug(f"  Host: {settings.ollama_host}")
    logger.debug(f"  Model: {settings.ollama_model}")
    logger.debug(f"  Temperature: {settings.temperature}")
    
    # Example 2: Using config in agent
    logger.info("Example: Starting agent...")
    logger.debug(f"  Max iterations: {settings.max_iterations}")
    logger.debug(f"  Timeout: {settings.agent_timeout}s")
    
    # Example 3: Tool configuration
    enabled_tools = []
    if settings.enable_web_search:
        enabled_tools.append("web_search")
    if settings.enable_tasks:
        enabled_tools.append("tasks")
    if settings.enable_calendar:
        enabled_tools.append("calendar")
    
    logger.info(f"Example: Enabled tools: {', '.join(enabled_tools)}")
    
    # Example 4: Error handling
    try:
        # Simulate an error
        raise ConnectionError("Could not connect to Ollama")
    except Exception as e:
        logger.error(f"Example error caught: {e}")
    
    print("\n✅ Usage examples complete!\n")


if __name__ == "__main__":
    print("\n🚀 TESTING INFRASTRUCTURE (Config + Logging)\n")
    
    try:
        test_configuration()
        test_logging()
        test_log_config()
        demonstrate_usage()
        
        print("=" * 70)
        print("🎉 ALL INFRASTRUCTURE TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Configuration system works!")
        print("✅ Logging system works!")
        print("✅ Ready to use in the agent!\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()