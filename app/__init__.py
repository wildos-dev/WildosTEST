import logging
import asyncio

import uvicorn

from app.config import env

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if env.DEBUG else logging.INFO)
handler = logging.StreamHandler()
formatter = uvicorn.logging.ColourizedFormatter(
    "{levelprefix:<8} @{name}: {message}", style="{", use_colors=True
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize system monitoring and maintenance
def setup_system_monitoring():
    """Set up system monitoring and maintenance tasks"""
    try:
        from .utils.logging_config import setup_application_logging
        from .tasks.system_maintenance import start_system_maintenance
        
        # Set up logging
        setup_application_logging()
        
        # Start maintenance tasks in background
        asyncio.create_task(start_system_maintenance())
        
        logger.info("System monitoring and maintenance initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize system monitoring: {e}")

# Export system monitoring setup function
__all__ = ["setup_system_monitoring"]
