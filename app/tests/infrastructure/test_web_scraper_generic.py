# app/tests/infrastructure/test_web_scraper_generic.py

from unittest.mock import AsyncMock, patch

import pytest
from core.storage import Storage
from core.web_scraping import WebScraperGeneric
from injector import Injector
from tests.builders.build import Build

TEXT_CONTENT = "This is important content that is long enough to pass the minimum length check of 50 characters"


@pytest.fixture
def web_scraper(injector):
    scraper = injector.get(WebScraperGeneric)
    yield scraper
    # Reset internal counters and lists
    scraper._total_requests = 0
    scraper._successful_requests = 0
    scraper._failed_requests = 0


class TestWebScraperGeneric:
    """Test each responsibility of WebScraperGeneric"""

    def test_clean_text_removes_extra_whitespace(self, web_scraper):
        """Test the text cleaning function"""
        text = "  Hello  \n  World  \t  "
        result = web_scraper._clean_text(text)
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_extract_content_uses_selectors(self, web_scraper):
        """Test content extraction using selectors"""
        # Setup mock page

        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.text_content.return_value = TEXT_CONTENT
        mock_page.query_selector.return_value = mock_element

        # Test
        content = await web_scraper._aextract_content(mock_page)

        # Verify
        assert content == TEXT_CONTENT
        mock_page.query_selector.assert_called()  # Verify selector was used

    @pytest.mark.asyncio
    async def test_scrape_page_saves_result(self, web_scraper, storage_mock):
        """Test that successful scrape is saved"""
        # Setup
        url = "https://example.com"
        mock_page = AsyncMock()
        mock_page.title.return_value = "Test Title"
        # Mock successful element with content
        mock_element = AsyncMock()
        mock_element.text_content.return_value = TEXT_CONTENT
        # Mock body element with short content (shouldn't be used)
        mock_body = AsyncMock()
        mock_body.text_content.return_value = "Too short"
        # Will succeed on first selector attempt, then return None for all other attempts
        mock_page.query_selector.side_effect = [
            mock_element] + [None] * 10  # First succeeds, rest fail
        mock_page.on = AsyncMock()  # Mock event handlers

        # Test
        result = await web_scraper._ascrape_page(url, mock_page)

        # Verify
        assert result.success
        assert result.title == "Test Title"
        assert result.content == TEXT_CONTENT
        storage_mock.write_json.assert_called_once()  # Verify result was saved

    @pytest.mark.asyncio
    async def test_scrape_page_handles_error(self, web_scraper, storage_mock):
        """Test error handling in page scraping"""
        # Setup
        url = "https://example.com"
        mock_page = AsyncMock()
        mock_page.goto.side_effect = Exception("Failed to load")
        mock_page.on = AsyncMock()  # Mock event handlers

        # Test
        result = await web_scraper._ascrape_page(url, mock_page)

        # Verify
        assert not result.success
        assert "Failed to load" in result.error_message
        storage_mock.write_json.assert_not_called()  # Verify failed result not saved

    @pytest.mark.asyncio
    async def test_scrape_multiple_handles_mixed_results(self, web_scraper):
        """Test scraping multiple URLs with mixed success/failure"""
        # Setup - URLs to test
        urls = [
            "https://example.com/success1",
            "https://example.com/error",
            "https://example.com/success2"
        ]

        # Mock playwright context
        with patch('core.web_scrape.async_playwright') as mock_playwright:
            def create_success_page():
                """Helper to create a fresh success page mock"""
                page = AsyncMock()
                page.title.return_value = "Success Page"
                # Mock successful element with content
                mock_element = AsyncMock()
                mock_element.text_content.return_value = TEXT_CONTENT
                # Mock query_selector to return element for test-selector, None for body

                async def query_selector_mock(selector: str):
                    if selector == "test-selector":
                        return mock_element
                    return None
                page.query_selector = query_selector_mock
                page.goto = AsyncMock()  # Will succeed
                page.on = AsyncMock()  # Mock event handlers
                return page

            def create_error_page():
                """Helper to create a fresh error page mock"""
                page = AsyncMock()
                page.title.return_value = "Error Page"
                # Mock body element with short content
                mock_body = AsyncMock()
                mock_body.text_content.return_value = "Too short"  # Content < 50 chars
                # Mock query_selector to return None for test-selector, short content for body

                async def query_selector_mock(selector: str):
                    if selector == "test-selector":
                        return None
                    if selector == "body":
                        return mock_body  # Return body with short content
                    return None
                page.query_selector = query_selector_mock
                page.goto = AsyncMock()  # Will succeed
                page.on = AsyncMock()  # Mock event handlers
                return page

            # Create fresh page mocks for each URL
            success_page1 = create_success_page()
            error_page = create_error_page()
            success_page2 = create_success_page()

            # Setup browser context to return different pages
            mock_context = AsyncMock()
            mock_context.new_page.side_effect = [
                success_page1, error_page, success_page2]
            mock_context.route = AsyncMock()

            # Setup browser chain
            mock_browser = AsyncMock()
            mock_browser.new_context.return_value = mock_context
            mock_chromium = AsyncMock()
            mock_chromium.launch.return_value = mock_browser
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium = mock_chromium
            mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance

            # Test
            result = await web_scraper.ascrape_multiple(urls)

            # Debug print
            print("\nDebug content for each URL:")
            for url in urls:
                if url in result.successful_urls:
                    print(f"SUCCESS - {url}")
                else:
                    print(f"FAILED - {url}")

            # Verify results
            assert result.total_requests == 3
            assert result.successful_requests == 2
            assert result.failed_requests == 1
            assert len(result.successful_urls) == 2
            assert len(result.failed_urls) == 1
            assert "https://example.com/error" in result.failed_urls
            assert "https://example.com/success1" in result.successful_urls
            assert "https://example.com/success2" in result.successful_urls

            # Verify concurrent behavior
            assert mock_context.new_page.call_count == 3  # Created page for each URL
            assert mock_browser.close.call_count == 1  # Browser was closed
