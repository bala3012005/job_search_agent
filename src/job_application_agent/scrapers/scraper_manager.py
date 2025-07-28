"""
Manager for all job scrapers.
"""

import logging
import asyncio
from typing import List, Dict, Any
from .linkedin_scraper import LinkedInScraper
from .naukri_scraper import NaukriScraper
from .indeed_scraper import IndeedScraper
from ..core.config import config

logger = logging.getLogger(__name__)

class ScraperManager:
    """Manages all job scrapers and coordinates job searching."""

    def __init__(self):
        self.scrapers = {
            'linkedin': LinkedInScraper(),
            'naukri': NaukriScraper(),
            'indeed': IndeedScraper()
        }

    async def search_all_platforms(self) -> List[Dict[str, Any]]:
        """Search for jobs across all platforms."""
        all_jobs = []

        keywords = config.job_search.keywords
        locations = config.user_profile.preferred_locations

        # Create tasks for parallel scraping
        tasks = []
        for platform_name, scraper in self.scrapers.items():
            task = asyncio.create_task(
                self._search_platform(scraper, keywords, locations[0] if locations else "India")
            )
            tasks.append(task)

        # Wait for all scrapers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraper failed: {result}")

        logger.info(f"Total jobs found across all platforms: {len(all_jobs)}")
        return all_jobs

    async def _search_platform(self, scraper, keywords: List[str], location: str) -> List[Dict[str, Any]]:
        """Search a single platform."""
        try:
            jobs = await scraper.search_jobs(keywords, location)
            logger.info(f"{scraper.platform_name}: Found {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.error(f"Error searching {scraper.platform_name}: {e}")
            return []

    async def get_job_details(self, platform: str, job_url: str) -> Dict[str, Any]:
        """Get detailed job information from a specific platform."""
        if platform not in self.scrapers:
            logger.error(f"Unknown platform: {platform}")
            return {}

        try:
            return await self.scrapers[platform].extract_job_details(job_url)
        except Exception as e:
            logger.error(f"Error getting job details from {platform}: {e}")
            return {}
