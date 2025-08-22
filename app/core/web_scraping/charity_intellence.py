import asyncio
import json
import logging

from configuration import Settings
from core.domain import ScrapePageResult
from core.storage import Storage
from core.utils import StandardFileNaming
from injector import inject
from playwright.async_api import Page, async_playwright

from .web_scraper import WebScraper

logger = logging.getLogger(__name__)


class WebScraperCharityIntellence(WebScraper):
    BASE_URL = "https://www.charityintelligence.ca/charity-profiles/a-z-charity-listing"

    @inject
    def __init__(self, storage: Storage, settings: Settings):
        super().__init__(storage, settings)
        self._file_naming = StandardFileNaming()
        self._current_page = 1
        self._start_page = 1
        self._end_page = None

    async def aget_urls(self, start_page: int = 1, end_page: int = None) -> list[str]:
        """
        Collect charity URLs from the listing pages up to max_pages.

        Args:
            max_pages: Maximum number of pages to collect URLs from. None for all pages.

        Returns:
            List of charity URLs
        """
        if start_page < 1:
            raise ValueError("Start page must be at least 1")
        if end_page and end_page < start_page:
            raise ValueError("End page must be greater than start page")

        self._current_page = start_page
        self._start_page = start_page
        self._end_page = end_page
        all_charity_urls = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=self._scrape_settings.headers['User-Agent']
            )

            try:
                page = await context.new_page()
                await self._ago_to_start_page(page)
                logger.info(f"start page url: {page.url}")

                while True:
                    logger.info(
                        f"Collecting charity links..")

                    # Extract charity links from current page
                    charity_links = await self._aextract_charity_links(page)
                    all_charity_urls.extend(charity_links)

                    logger.info(
                        f"Number of charity links added: {len(all_charity_urls)}")

                    # Check if we should continue to next page
                    if not await self._ashould_continue_to_next_page(page):
                        break
                    logger.info(f"Navigating to next page..")

                    # Navigate to next page
                    if not await self._ago_to_next_page(page):
                        logger.info(f"No next page found. Ending loop.")
                        break
                    logger.info(f"Next page url: {page.url}")

                    # wait for 10 seconds
                    logger.info(f"Waiting for 5 seconds..")
                    await asyncio.sleep(5)

            finally:
                await browser.close()

        return all_charity_urls

    async def _ago_to_start_page(self, page: Page) -> bool:
        """Navigate to the specified start page."""
        try:
            if self._start_page >= 1:
                start_param = (self._start_page - 1) * 20
                start_url = f"{self.BASE_URL}?start={start_param}"
                logger.info(f"Navigating to start page: {start_url}")
                await page.goto(start_url, wait_until='networkidle')
                logger.info(f"Navigated to start page {self._start_page}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to start page: {str(e)}")
            return False

    async def _ashould_continue_to_next_page(self, page: Page) -> bool:
        """Determine if we should continue to the next page."""
        if self._end_page and self._current_page >= self._end_page:
            logger.info(f"End page {self._end_page} reached.")
            return False

        # Check if there is a next page button
        next_button = await page.query_selector(".pagination .page-link.next")
        if not next_button:
            logger.info(f"No next page button found.")
            return False

        logger.info(f"Should continue to next page.")
        return True

    async def _ago_to_next_page(self, page: Page) -> bool:
        """Attempt to navigate to the next page."""
        try:
            await page.click(".pagination .page-link.next")
            await page.wait_for_load_state('networkidle')
            self._current_page += 1
            logger.info(f"Navigated to page {self._current_page}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to next page: {str(e)}")
            return False

    async def _aextract_charity_links(self, page: Page) -> list[str]:
        """Extract all charity links from the current page."""
        # This is a placeholder - we'll need to identify the correct selector
        charity_links = await page.eval_on_selector_all(
            ".alpha_records.charity_list a.title.lnk",
            "elements => elements.map(el => el.href)"
        )
        logger.info(
            f"Found {len(charity_links)} charity links on page {self._current_page}")
        return charity_links

    async def _get_text(self, page: Page, selector: str) -> str | None:
        """Safely extract text content from an element."""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.text_content()
        except Exception as e:
            logger.debug(
                f"Error extracting text for selector {selector}: {str(e)}")
        return None

    async def _aextract_content(self, page: Page) -> str:

        data = {
            "name": await self._get_text(page, "selector-for-name"),
            "rating": await self._get_text(page, "selector-for-rating"),
            "description": await self._get_text(page, "selector-for-description"),
            "category": await self._get_text(page, "selector-for-category"),
            "location": await self._get_text(page, "selector-for-location"),
        }

        return json.dumps(data)

    def _get_file_name(self, result: ScrapePageResult) -> str:

        data = json.loads(result.content)
        charity_name = data.get("name", "Unknown Charity")
        file_name = charity_name.replace(" ", "_")

        return f"{file_name}_scraped.json"
