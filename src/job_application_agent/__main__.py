"""
Main entry point for the Job Application Agent.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from job_application_agent.core.agent import JobApplicationAgent
from job_application_agent.core.config import config
from job_application_agent.utils.logger import setup_logging

async def main():
    """Main function to start the job application agent."""
    # Setup logging
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting Job Application Agent...")

    try:
        # Check if encryption key is set
        if not config.database.encryption_key:
            logger.error("FERNET_KEY not set in environment variables!")
            logger.info("Please set FERNET_KEY in your .env file")
            logger.info("You can generate one using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
            sys.exit(1)

        # Initialize and start the agent
        agent = JobApplicationAgent()

        # Start the agent
        await agent.start()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        if 'agent' in locals():
            await agent.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
