import asyncio
from typing import Dict, Any


# Global asyncio queue for suggestion processing
# Using a bounded queue to prevent memory issues
suggestion_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1000)