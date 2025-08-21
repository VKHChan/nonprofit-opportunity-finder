import pytest
from core.domain import ScrapingResult
from core.web_scrape import WebScraper
from tests.builders.web_scrape_builder import build_scrape_result


@pytest.mark.asyncio
class TestWebScraper:
    @pytest.fixture
    def scraper(self, injector):
        class TestScraper(WebScraper):
            async def _aextract_content(self, page):
                return "test content"

        return injector.get(TestScraper)

    async def test_get_file_name_default_implementation(self, scraper):
        # Arrange
        result = build_scrape_result(
            url="https://test.com/page?param=1"
        )

        # Act
        file_name = scraper._get_file_name(result)

        # Assert
        assert file_name.endswith("_scraped.json")
        assert "test-com" in file_name  # URLs use hyphens
        assert "?" not in file_name  # URL should be cleaned

    async def test_get_statistics_empty(self, scraper):
        # Act
        stats = scraper._get_statistics()

        # Assert
        assert isinstance(stats, ScrapingResult)
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.failed_urls == []
        assert stats.successful_urls == []

    async def test_get_statistics_with_data(self, scraper):
        # Arrange
        scraper._total_requests = 2
        scraper._successful_requests = 1
        scraper._failed_requests = 1
        scraper._failed_urls = ["https://fail.com"]
        scraper._successful_urls = ["https://success.com"]

        # Act
        stats = scraper._get_statistics()

        # Assert
        assert stats.total_requests == 2
        assert stats.successful_requests == 1
        assert stats.failed_requests == 1
        assert stats.failed_urls == ["https://fail.com"]
        assert stats.successful_urls == ["https://success.com"]

    async def test_aget_urls_default_implementation(self, scraper):
        # Arrange
        test_urls = ["https://test1.com", "https://test2.com"]

        # Act
        result = await scraper._aget_urls(test_urls)

        # Assert
        assert result == test_urls  # Default implementation should return urls as-is
