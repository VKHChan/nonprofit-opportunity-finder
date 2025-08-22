from core.web_scraping import (
    WebScraperCharityIntellence,
    WebScraperFactory,
    WebScraperGeneric,
)
from injector import Binder, Module


class WebScraperModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(WebScraperGeneric, to=WebScraperGeneric)
        binder.bind(WebScraperCharityIntellence,
                    to=WebScraperCharityIntellence)
        binder.bind(WebScraperFactory, to=WebScraperFactory)
