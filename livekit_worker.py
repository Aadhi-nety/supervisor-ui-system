#!/usr/bin/env python3
"""
LiveKit Worker - Separate process for handling voice calls
"""

import asyncio
import logging
from livekit.agents import WorkerOptions, cli
from ai_agent.livekit_agent import LiveKitSalonAgent
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for LiveKit worker"""
    logger.info("🚀 Starting LiveKit Worker for Voice Calls")
    
    # Create the agent instance
    agent_instance = LiveKitSalonAgent()
    
    # Define the worker function
    async def worker(ctx):
        await agent_instance.handle_call(ctx)
    
    # Start the worker with CLI
    await cli.run_app(WorkerOptions(agent=worker))

if __name__ == "__main__":
    asyncio.run(main())