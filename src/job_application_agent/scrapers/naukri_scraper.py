"""
Naukri.com job scraper implementation.
"""

import logging
from typing import List, Dict, Any, Optional, cast
from playwright.async_api import Page, ElementHandle
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com job postings."""

    def __init__(self):
        super().__init__("Naukri")
        self.base_url = "https://www.naukri.com"
        self.page: Optional[Page] = None

    def _check_page(self) -> Page:
        """Check if page is initialized and return typed page object."""
        if self.page is None:
            raise RuntimeError("Browser page not initialized")
        return cast(Page, self.page)

    async def search_jobs(self, keywords: List[str], location: str = "India", experience: str = "0-2") -> List[Dict[str, Any]]:
        """Search for jobs on Naukri."""
        jobs = []

        try:
            await self.initialize_browser(headless=True)
            page = self._check_page()

            for keyword in keywords:
                search_url = f"{self.base_url}/java-jobs?k={keyword.replace(' ', '%20')}&l={location}&experience={experience}"
                await page.goto(search_url)
                await self.random_delay(2, 4)

                job_elements = await page.query_selector_all('.jobTuple')

                for element in job_elements[:10]:
                    try:
                        job_data = await self._extract_job_card(element, experience)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        logger.warning(f"Error extracting job from Naukri: {e}")
                        continue

                await self.random_delay(3, 5)

        except Exception as e:
            logger.error(f"Error searching Naukri jobs: {e}")

        finally:
            await self.close_browser()

        logger.info(f"Naukri: Found {len(jobs)} jobs")
        return jobs

    async def _extract_job_card(self, element: ElementHandle, experience: str) -> Optional[Dict[str, Any]]:
        """Extract job information from a single job card element."""
        try:
            title_elem = await element.query_selector('.title')
            company_elem = await element.query_selector('.companyInfo')
            location_elem = await element.query_selector('.locationsContainer')
            link_elem = await element.query_selector('.title a')

            if title_elem and company_elem and link_elem:
                title = await title_elem.inner_text()
                company = await company_elem.inner_text()
                location_text = await location_elem.inner_text() if location_elem else ""
                job_url = await link_elem.get_attribute('href')

                if not job_url:
                    return None

                return {
                    'job_id': f"naukri_{hash(job_url)}",
                    'title': self.clean_text(title),
                    'company': self.clean_text(company),
                    'location': self.clean_text(location_text),
                    'source_platform': self.platform_name,
                    'source_url': job_url,
                    'posted_date': 'recent',
                    'description': '',
                    'requirements': '',
                    'salary_range': '',
                    'experience_required': experience
                }
        except Exception as e:
            logger.warning(f"Error extracting job card data: {e}")
            return None

    async def extract_job_details(self, job_url: str) -> Dict[str, Any]:
        """Extract detailed job information from Naukri."""
        try:
            await self.initialize_browser(headless=True)
            page = self._check_page()
            await page.goto(job_url)
            await self.random_delay(2, 4)

            description_elem = await page.query_selector('.dang-inner-html')
            description = await description_elem.inner_text() if description_elem else ""

            return {
                'description': self.clean_text(description),
                'salary_range': self.extract_salary_range(description),
                'experience_required': self.extract_experience_required(description)
            }

        except Exception as e:
            logger.error(f"Error extracting Naukri job details: {e}")
            return {}

        finally:
            await self.close_browser()