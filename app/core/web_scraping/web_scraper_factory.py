"""
Simple factory for accessing different web scrapers
"""
from injector import inject

from .charity_intellence import WebScraperCharityIntellence
from .generic import WebScraperGeneric


class WebScraperFactory:
    """Factory to get specific scraper implementations"""

    @inject
    def __init__(self,
                 generic_scraper: WebScraperGeneric,
                 charity_scraper: WebScraperCharityIntellence):
        self.generic_scraper = generic_scraper
        self.charity_scraper = charity_scraper

    def get_generic_scraper(self) -> WebScraperGeneric:
        """Get the generic web scraper"""
        return self.generic_scraper

    def get_charity_scraper(self) -> WebScraperCharityIntellence:
        """Get the charity intelligence scraper"""
        return self.charity_scraper
