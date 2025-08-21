import asyncio
import logging
from datetime import datetime

from configuration import Settings
from core.domain import ScrapePageResult, ScrapingResult
from core.storage import Storage
from core.utils import StandardFileNaming
from injector import inject
from playwright.async_api import BrowserContext, Page, async_playwright

logger = logging.getLogger(__name__)


class WebScrapeDefaultFolders:
    DEFAULT_SUCCESS_STATUS = "success"
    DEFAULT_FAILED_STATUS = "failed"


class WebScraper:
    @inject
    def __init__(self, storage: Storage, settings: Settings):
        # Initialize statistics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._failed_urls: list[str] = []
        self._successful_urls: list[str] = []
        self._storage = storage
        self._scrape_settings = settings.web_scrape_settings

    async def ascrape_multiple(self, urls: list[str], file_path: str | None = None) -> ScrapingResult:
        """
        Implementation of the required WebScraper method.
        If urls is provided, scrapes those specific charity pages.
        If urls is None, scrapes the entire charity listing starting from BASE_URL.

        Args:
            urls: Optional list of specific charity URLs to scrape. If None, scrapes from listing pages
            file_path: Optional path where scraped data will be stored
        """
        urls = await self._aget_urls(urls)
        if not urls:
            return self._get_statistics()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=self._scrape_settings.headers['User-Agent']
            )

            sem = asyncio.Semaphore(self._scrape_settings.concurrent_limit)

            try:
                tasks = [asyncio.create_task(self._aprocess_url(
                    url, context, file_path, sem)) for url in urls]
                await asyncio.gather(*tasks)
            finally:
                await browser.close()

        return self._get_statistics()

    async def _aextract_content(self, page: Page) -> str:
        raise NotImplementedError

    async def _aget_urls(self, urls: list[str], *args, **kwargs) -> list[str]:
        # override this in the subclass if needed
        return urls

    def _get_file_name(self, result: ScrapePageResult) -> str:
        # override this in the subclass if needed
        file_naming = StandardFileNaming()
        return f"{file_naming.clean_url_for_file(result.url)}_scraped.json"

    async def _ascrape_page(self, url: str, page: Page, file_path: str = None) -> ScrapePageResult:
        self._total_requests += 1
        for attempt in range(self._scrape_settings.retries):
            try:
                # Handle popups
                page.on("dialog", lambda dialog: asyncio.create_task(
                    dialog.dismiss()))
                page.on("popup", lambda popup: asyncio.create_task(popup.close()))

                await page.goto(url,
                                timeout=self._scrape_settings.timeout,
                                wait_until='networkidle')
                logger.info(f"Page loaded: {url}")
                logger.info(f"Page title: {await page.title()}")
                content = await self._aextract_content(page)
                logger.info(
                    f"\nExtracted content for {url}: {content[:100] if content else 'EMPTY'}...")
                if not content:  # Empty content is considered a failure
                    logger.error(
                        f"Empty content detected for {url}, raising error")
                    raise ValueError("No content could be extracted")

                result = ScrapePageResult(
                    url=url,
                    created_at=datetime.now(),
                    title=await page.title(),
                    content=content,
                    success=True,
                    error_message=None
                )

                self._successful_requests += 1
                self._successful_urls.append(url)

                file_name = self._get_file_name(result)
                await self._asave_result(result, file_name, file_path)

                return result
            except Exception as e:
                if attempt < self._scrape_settings.retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self._failed_requests += 1
                    self._failed_urls.append(url)
                    return ScrapePageResult(
                        url=url,
                        created_at=datetime.now(),
                        title=None,
                        content=None,
                        success=False,
                        error_message=str(e)
                    )

    async def _aprocess_url(self, url: str, context: BrowserContext, file_path: str = None, sem: asyncio.Semaphore = None) -> ScrapePageResult:
        async with sem:
            page = None
            try:
                page = await context.new_page()
                result = await self._ascrape_page(url, page, file_path)

                return result
            finally:
                if page:
                    await page.close()

    def _get_statistics(self) -> ScrapingResult:
        """Get scraping statistics"""
        return ScrapingResult(
            total_requests=self._total_requests,
            successful_requests=self._successful_requests,
            failed_requests=self._failed_requests,
            failed_urls=self._failed_urls,
            successful_urls=self._successful_urls
        )

    async def _asave_result(self, result: ScrapePageResult, file_name: str, file_path: str | None = None) -> str:
        status = WebScrapeDefaultFolders.DEFAULT_SUCCESS_STATUS if result.success else WebScrapeDefaultFolders.DEFAULT_FAILED_STATUS
        folder_name = f"{self._scrape_settings.scraper_folder_name}/{status}"
        if file_path:
            folder_name = f"{file_path}/{self._scrape_settings.scraper_folder_name}/{status}"

        full_file_name = f"{folder_name}/{file_name}"
        await asyncio.to_thread(
            self._storage.write_json,
            full_file_name,
            result.model_dump()
        )
