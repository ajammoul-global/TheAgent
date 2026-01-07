import logging
import sys
from pathlib import Path
from typing import Optional
from .config import settings


# ==================================================================
# LOG LEVELS EXPLANATION
# ==================================================================
"""
Logging Levels (from most to least verbose):

DEBUG    - Detailed information for diagnosing problems
           Example: "Sending prompt to LLM: What is Python?"
           
INFO     - General informational messages  
           Example: "Agent started", "Tool executed successfully"
           
WARNING  - Warning messages (something unexpected but not an error)
           Example: "API rate limit approaching"
           
ERROR    - Error messages (something failed)
           Example: "Failed to connect to Ollama"
           
CRITICAL - Critical errors (system might crash)
           Example: "Out of memory, shutting down"


Which level to use when?
-------------------------
Development: DEBUG (see everything)
Production:  INFO (important events only)
Debugging:   DEBUG (when investigating issues)
"""


# ==================================================================
# FORMATTER SETUP
# ==================================================================

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels.
    Makes logs easier to read in the terminal!
    
    Colors:
    - DEBUG: Cyan
    - INFO: Green  
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red + Bold
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Add colors to the log level name"""
        # Get the color for this level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Color the level name
        record.levelname = f"{color}{record.levelname}{reset}"
        
        # Format the message
        return super().format(record)


# ==================================================================
# LOGGER SETUP FUNCTION
# ==================================================================

def setup_logging(
    name: str = "agent_runtime",
    level: Optional[str] = None,
    log_to_file: Optional[bool] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        name: Logger name (default: "agent_runtime")
        level: Log level (default: from settings.log_level)
        log_to_file: Whether to log to file (default: from settings.log_to_file)
        log_file: Log file path (default: from settings.log_file_path)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logging()
        >>> logger.info("Agent started")
        2024-12-04 10:30:15 - agent_runtime - INFO - Agent started
        
        >>> logger.debug("Debugging info")
        2024-12-04 10:30:16 - agent_runtime - DEBUG - Debugging info
        
        >>> logger.error("Something went wrong!")
        2024-12-04 10:30:17 - agent_runtime - ERROR - Something went wrong!
    """
    
    # Use settings if not provided
    level = level or settings.log_level
    log_to_file = log_to_file if log_to_file is not None else settings.log_to_file
    log_file = log_file or settings.log_file_path
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Clear existing handlers (avoid duplicates)
    logger.handlers.clear()
    
    # ==================================================================
    # CONSOLE HANDLER (always enabled)
    # ==================================================================
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Use colored formatter for console
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_formatter = ColoredFormatter(
        console_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # ==================================================================
    # FILE HANDLER (optional)
    # ==================================================================
    
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Use plain formatter for file (no colors)
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        file_formatter = logging.Formatter(
            file_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger


# ==================================================================
# GLOBAL LOGGER INSTANCE
# ==================================================================

# Create global logger that's imported everywhere
logger = setup_logging()


# ==================================================================
# HELPER FUNCTIONS
# ==================================================================

def log_config():
    """Log the current configuration (useful for debugging)"""
    logger.info("=" * 70)
    logger.info("CONFIGURATION")
    logger.info("=" * 70)
    
    config_dict = settings.to_dict()
    for key, value in config_dict.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("=" * 70)


def set_level(level: str):
    """
    Change log level at runtime.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Example:
        >>> set_level("DEBUG")  # Now see debug messages
        >>> set_level("WARNING")  # Only warnings and errors
    """
    logger.setLevel(getattr(logging, level.upper()))
    logger.info(f"Log level changed to: {level}")

