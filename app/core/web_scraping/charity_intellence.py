
import json
import logging

from configuration import Settings
from core.domain import ScrapePageResult
from core.storage import Storage
from core.utils import StandardFileNaming
from core.web_scrape import WebScraper
from injector import inject
from playwright.async_api import Page, async_playwright

logger = logging.getLogger(__name__)


class WebScraperCharityIntellence(WebScraper):
    BASE_URL = "https://www.charityintelligence.ca/charity-profiles/a-z-charity-listing"

    @inject
    def __init__(self, storage: Storage, settings: Settings):
        super().__init__(storage, settings)
        self._file_naming = StandardFileNaming()
        self._current_page = 1
        self._max_pages = None

    async def _aget_urls(self, urls: list[str], max_pages: int | None = None) -> list[str]:
        """
        Collect charity URLs from the listing pages up to max_pages.

        Args:
            max_pages: Maximum number of pages to collect URLs from. None for all pages.

        Returns:
            List of charity URLs
        """
        self._current_page = 1
        self._max_pages = max_pages
        all_charity_urls = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=self._scrape_settings.headers['User-Agent']
            )

            try:
                page = await context.new_page()
                await self._navigate_to_listing_page(page)

                while True:
                    # Extract charity links from current page
                    charity_links = await self._extract_charity_links(page)
                    all_charity_urls.extend(charity_links)

                    # Check if we should continue to next page
                    if not await self._should_continue_to_next_page(page):
                        break

                    # Navigate to next page
                    if not await self._go_to_next_page(page):
                        break

            finally:
                await browser.close()

        return all_charity_urls

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

    async def _extract_charity_links(self, page: Page) -> list[str]:
        """Extract all charity links from the current page."""
        # This is a placeholder - we'll need to identify the correct selector
        charity_links = await page.eval_on_selector_all(
            "selector-for-charity-links",
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

    async def _should_continue_to_next_page(self, page: Page) -> bool:
        """Determine if we should continue to the next page."""
        if self._max_pages and self._current_page >= self._max_pages:
            return False

        # Check if there is a next page button
        next_button = await page.query_selector("selector-for-next-button")
        return bool(next_button)

    async def _go_to_next_page(self, page: Page) -> bool:
        """Attempt to navigate to the next page."""
        try:
            await page.click("selector-for-next-button")
            await page.wait_for_load_state('networkidle')
            self._current_page += 1
            logger.info(f"Navigated to page {self._current_page}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to next page: {str(e)}")
            return False

    async def _navigate_to_listing_page(self, page: Page):
        """Navigate to the main listing page and handle any initial setup."""
        await page.goto(self.BASE_URL, wait_until='networkidle')
        logger.info(f"Navigated to main listing page: {self.BASE_URL}")
