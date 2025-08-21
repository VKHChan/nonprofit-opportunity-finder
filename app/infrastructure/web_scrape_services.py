from core.web_scrape import WebScraper
from core.web_scraping import WebScraperCharityIntellence, WebScraperGeneric
from injector import Binder, Module


class WebScraperModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(WebScraper, to=WebScraperCharityIntellence)
        binder.bind(WebScraper, to=WebScraperGeneric)
