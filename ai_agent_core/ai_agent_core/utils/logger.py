import logging
import sys
from ai_agent_core.config import settings


def setup_logger(name: str) -> logging.Logger:
    """Setup structured logger tailored for ai_agent_core."""
    logger = logging.getLogger(name)
    
    # Get log level from settings, default to INFO
    log_level = getattr(settings, "LOG_LEVEL", "INFO")
    logger.setLevel(log_level)
    
    if logger.handlers:
        return logger
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger
