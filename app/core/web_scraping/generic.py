
import logging

from configuration import Settings
from core.storage import Storage
from core.web_scrape import WebScraper
from injector import inject
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class WebScraperGeneric(WebScraper):
    @inject
    def __init__(self, storage: Storage, settings: Settings):
        super().__init__(storage, settings)
        logger.info(f"Scrape settings: {self._scrape_settings}")

    async def _aextract_content(self, page: Page) -> str:
        """Efficient content extraction that stops at first valid selector"""
        for selector in self._scrape_settings.main_content_selectors:
            selector = selector.strip()
            if not selector:
                continue

            logger.debug(f"Trying selector: {selector}")

            try:
                # Find first matching element
                element = await page.query_selector(selector)

                if element:
                    # Get text content immediately
                    text = await element.text_content()
                    cleaned_text = self._clean_text(text)
                    logger.info(f"\nSelector content: {cleaned_text[:100]}...")

                    # Check if content is meaningful
                    logger.info(
                        f"\nContent length check: {len(cleaned_text)} chars")
                    if cleaned_text and len(cleaned_text) > 50:
                        logger.info(f"Selected content from {selector}")
                        return cleaned_text

            except Exception as e:
                logger.debug(f"Error with selector {selector}: {str(e)}")
                continue

        # Fallback to body if no content found
        try:
            body = await page.query_selector('body')
            if body:
                content = await body.text_content()
                cleaned_content = self._clean_text(content)
                print(f"\nBody content: {cleaned_content[:100]}...")
                print(
                    f"\nBody content length check: {len(cleaned_content)} chars")
                if cleaned_content and len(cleaned_content) > 50:
                    return cleaned_content
                return ""
        except Exception as e:
            logger.error(f"Fallback content extraction failed: {str(e)}")

        # Absolute fallback
        return ''

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing excessive whitespace"""
        if not text:
            return ""
        # Replace tabs and newlines with spaces
        text = text.replace('\t', ' ').replace('\n', ' ')
        # Remove multiple spaces
        text = ' '.join(text.split())
        return text.strip()
