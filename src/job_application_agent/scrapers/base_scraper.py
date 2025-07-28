"""
Base scraper class for job portals.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
import random

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all job portal scrapers."""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]

    async def initialize_browser(self, headless: bool = True):
        """Initialize browser instance."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )

            context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1366, 'height': 768}
            )

            # Add stealth settings
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                window.chrome = {
                    runtime: {},
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)

            self.page = await context.new_page()

        except Exception as e:
            logger.error(f"Failed to initialize browser for {self.platform_name}: {e}")
            raise

    async def close_browser(self):
        """Close browser instance."""
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def random_delay(self, min_seconds: int = 1, max_seconds: int = 3):
        """Add random delay to mimic human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    @abstractmethod
    async def search_jobs(self, keywords: List[str], location: str = "", experience: str = "") -> List[Dict[str, Any]]:
        """Search for jobs on the platform."""
        pass

    @abstractmethod
    async def extract_job_details(self, job_url: str) -> Dict[str, Any]:
        """Extract detailed job information from a job posting."""
        pass

    def clean_text(self, text: str) -> str:
        """Clean and normalize text data."""
        if not text:
            return ""
        return " ".join(text.strip().split())

    def extract_salary_range(self, text: str) -> str:
        """Extract salary information from text."""
        import re
        salary_patterns = [
            r'₹\s*(\d+(?:,\d+)*)\s*-\s*₹\s*(\d+(?:,\d+)*)',
            r'(\d+(?:,\d+)*)\s*-\s*(\d+(?:,\d+)*)\s*LPA',
            r'(\d+(?:.\d+)?)\s*-\s*(\d+(?:.\d+)?)\s*Lakh'
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return ""

    def extract_experience_required(self, text: str) -> str:
        """Extract experience requirements from text."""
        import re
        exp_patterns = [
            r'(\d+)\s*-\s*(\d+)\s*years?',
            r'(\d+)\+\s*years?',
            r'fresher',
            r'entry\s*level'
        ]

        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return ""
