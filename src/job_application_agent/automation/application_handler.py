import logging
import asyncio
import random
from typing import Dict, Any, Optional, TYPE_CHECKING, cast
from playwright.async_api import async_playwright, Page, BrowserContext, ElementHandle

if TYPE_CHECKING:
    from playwright.async_api import Browser

logger = logging.getLogger(__name__)

class ApplicationHandler:
    """Handles automated job applications across different platforms."""

    def __init__(self):
        self.browser: Optional["Browser"] = None
        self.page: Optional[Page] = None

    def _check_page(self) -> Page:
        """Check if page is initialized and return typed page object."""
        if self.page is None:
            raise RuntimeError("Browser page not initialized")
        return cast(Page, self.page)

    async def apply_to_job(self, job_data: Dict[str, Any], cover_letter: Dict[str, Any]) -> bool:
        platform = job_data.get("source_platform", "").lower()
        try:
            if platform == "linkedin":
                return await self._apply_linkedin(job_data, cover_letter)
            elif platform == "naukri":
                return await self._apply_naukri(job_data, cover_letter)
            elif platform == "indeed":
                return await self._apply_indeed(job_data, cover_letter)
            else:
                logger.warning(f"Automated application not supported for {platform}")
                return False
        except Exception as e:
            logger.error(f"Error applying to job {job_data.get('job_id')}: {e}")
            return False

    async def _initialize_browser(self, headless: bool = True):
        """Initialize browser for automation."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context: BrowserContext = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1366, "height": 768},
        )
        self.page = await context.new_page()

    async def _apply_linkedin(self, job_data: Dict[str, Any], cover_letter: Dict[str, Any]) -> bool:
        """Apply to a LinkedIn job (Easy Apply)."""
        try:
            await self._initialize_browser()
            page = self._check_page()
            await page.goto(job_data['source_url'])
            await asyncio.sleep(random.uniform(2, 4))

            easy_apply_button = await page.query_selector('.jobs-apply-button')
            if easy_apply_button:
                await easy_apply_button.click()
                await asyncio.sleep(2)
                success = await self._fill_linkedin_application_form(cover_letter)
                return success
            else:
                logger.info("No Easy Apply button found for LinkedIn job")
                return False

        except Exception as e:
            logger.error(f"Error applying to LinkedIn job: {e}")
            return False
        finally:
            if self.browser:
                await self.browser.close()

    async def _fill_linkedin_application_form(self, cover_letter: Dict[str, Any]) -> bool:
        """Fill LinkedIn application form."""
        try:
            page = self._check_page()
            await page.wait_for_selector('.jobs-easy-apply-modal', timeout=10000)

            max_steps = 5
            for step in range(max_steps):
                await self._fill_common_form_fields()

                cover_letter_field = await page.query_selector(
                    'textarea[name*="cover"], textarea[placeholder*="cover"]'
                )
                if cover_letter_field and cover_letter.get('text'):
                    await cover_letter_field.fill(cover_letter['text'])

                next_button = await page.query_selector('.artdeco-button--primary')
                if next_button:
                    button_text = await next_button.inner_text()
                    await next_button.click()

                    if 'submit' in button_text.lower() or 'send' in button_text.lower():
                        logger.info("LinkedIn application submitted successfully")
                        return True

                    await asyncio.sleep(2)
                else:
                    break

            return False

        except Exception as e:
            logger.error(f"Error filling LinkedIn form: {e}")
            return False

    async def _fill_common_form_fields(self):
        """Fill common form fields with user profile data."""
        from ..core.config import config
        page = self._check_page()

        phone_field = await page.query_selector('input[name*="phone"], input[type="tel"]')
        if phone_field:
            await phone_field.fill(config.user_profile.phone)

        location_field = await page.query_selector(
            'input[name*="location"], input[placeholder*="location"]'
        )
        if location_field and config.user_profile.preferred_locations:
            await location_field.fill(config.user_profile.preferred_locations[0])

    async def _apply_naukri(self, job_data: Dict[str, Any], cover_letter: Dict[str, Any]) -> bool:
        """Apply to a Naukri job."""
        try:
            await self._initialize_browser()
            page = self._check_page()
            await page.goto(job_data['source_url'])
            await asyncio.sleep(random.uniform(2, 4))

            apply_button = await page.query_selector('.apply-button, .btn-apply')
            if apply_button:
                await apply_button.click()
                await asyncio.sleep(2)

                await self._fill_common_form_fields()

                submit_button = await page.query_selector('.btn-submit, .submit-btn')
                if submit_button:
                    await submit_button.click()
                    logger.info("Naukri application submitted successfully")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error applying to Naukri job: {e}")
            return False
        finally:
            if self.browser:
                await self.browser.close()

    async def _apply_indeed(self, job_data: Dict[str, Any], cover_letter: Dict[str, Any]) -> bool:
        """Apply to an Indeed job."""
        try:
            await self._initialize_browser()
            page = self._check_page()
            await page.goto(job_data['source_url'])
            await asyncio.sleep(random.uniform(2, 4))

            apply_button = await page.query_selector('.ia-IndeedApplyButton')
            if apply_button:
                await apply_button.click()
                await asyncio.sleep(2)

                await self._fill_common_form_fields()

                cover_letter_field = await page.query_selector('textarea[name*="coverletter"]')
                if cover_letter_field and cover_letter.get('text'):
                    await cover_letter_field.fill(cover_letter['text'])

                submit_button = await page.query_selector('.ia-continueButton')
                if submit_button:
                    await submit_button.click()
                    logger.info("Indeed application submitted successfully")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error applying to Indeed job: {e}")
            return False
        finally:
            if self.browser:
                await self.browser.close()