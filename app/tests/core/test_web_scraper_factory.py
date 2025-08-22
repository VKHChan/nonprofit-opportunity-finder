"""
Tests for the WebScraperFactory
"""
import pytest
from core.web_scraping import (
    WebScraperCharityIntellence,
    WebScraperFactory,
    WebScraperGeneric,
)


@pytest.fixture
def factory(injector) -> WebScraperFactory:
    """Get a configured factory from the injector"""
    return injector.get(WebScraperFactory)


def test_get_generic_scraper(factory: WebScraperFactory):
    """Test getting the generic scraper"""
    scraper = factory.get_generic_scraper()
    assert isinstance(scraper, WebScraperGeneric)
    assert scraper is factory.generic_scraper  # Should be the same instance


def test_get_charity_scraper(factory: WebScraperFactory):
    """Test getting the charity scraper"""
    scraper = factory.get_charity_scraper()
    assert isinstance(scraper, WebScraperCharityIntellence)
    assert scraper is factory.charity_scraper  # Should be the same instance


def test_factory_injection(injector):
    """Test that factory gets properly constructed by injector"""
    # First request should work
    factory = injector.get(WebScraperFactory)
    assert isinstance(factory, WebScraperFactory)
    assert isinstance(factory.generic_scraper, WebScraperGeneric)
    assert isinstance(factory.charity_scraper, WebScraperCharityIntellence)

    # Second request should work (testing dependency injection works)
    factory2 = injector.get(WebScraperFactory)
    assert isinstance(factory2, WebScraperFactory)
    assert isinstance(factory2.generic_scraper, WebScraperGeneric)
    assert isinstance(factory2.charity_scraper, WebScraperCharityIntellence)
