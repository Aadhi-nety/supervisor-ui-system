#!/usr/bin/env python3
"""
Script to start the LiveKit voice agent separately
"""

import asyncio
import logging
import threading
from livekit_worker import main as livekit_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_livekit_worker():
    """Start LiveKit worker in a separate thread"""
    try:
        logger.info("🎧 Starting LiveKit Voice Agent...")
        asyncio.run(livekit_main())
    except Exception as e:
        logger.error(f"🎧 LiveKit worker error: {e}")

if __name__ == "__main__":
    start_livekit_worker()