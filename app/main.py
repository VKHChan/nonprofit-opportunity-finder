#!/usr/bin/env python
"""
Simple script to test the search functionality using ServiceCollection.
Run this script directly to perform a search and see the results.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

from configuration import Settings
from core.chat_model import ChatModelProvider
from core.content_analysis import ContentAnalysisService
from core.storage import Storage
from core.web_scraping import WebScraperFactory
from core.web_search import SearchEngine
from infrastructure.service_collection import ServiceCollection

# Configure logging to show all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


async def main():
    """Run a test search and print the results"""
    # Initialize services
    service_provider = ServiceCollection.add_services()

    # Get the configured search engine from the service provider
    settings = service_provider.get(Settings)
    storage = service_provider.get(Storage)
    search_engine = service_provider.get(SearchEngine)
    web_scraper_factory = service_provider.get(WebScraperFactory)
    content_analysis = service_provider.get(ContentAnalysisService)
    chat_model = service_provider.get(ChatModelProvider)

    # Get search query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "python programming"
    print(f"Searching for: {query}")

    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    folder_path = f"{year}/{month}/{day}"

    """# Perform search
    results = await search_engine.search(query, folder_path)

    # Print results
    if results:
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Title: {result.title}")
            print(f"URL: {result.url}")
            print(f"Description: {result.description[:100]}...")
    else:
        print("No results found or an error occurred.")

    # Scrape the results using the generic scraper
    if results:
        generic_scraper = web_scraper_factory.get_generic_scraper()
        scraping_result = await generic_scraper.ascrape_multiple(
            [result.url for result in results], folder_path)
        print(scraping_result)

        sucess_scrape_path = f"{folder_path}/{settings.web_scrape_settings.scraper_folder_name}/success"
        url_list = storage.list_all_files(sucess_scrape_path)

        if len(url_list) > 0:
            for url in url_list:
                print(f"Analyzing {url}")
                file_name = url.split("/")[-1]
                content = storage.read_json(url)
                analysis = content_analysis.analyze_content(
                    file_name, content, chat_model, folder_path)
                print(analysis)
        else:
            print("No successful scrapes found.")"""

    # Scrape non-profit organizations using the charity intelligence scraper
    charity_scraper = web_scraper_factory.get_charity_scraper()
    charity_urls = await charity_scraper.aget_urls(start_page=1, end_page=3)
    print(charity_urls)

    """scraping_result = await charity_scraper.ascrape_multiple(
        charity_urls, folder_path)
    print(scraping_result)"""


if __name__ == "__main__":
    asyncio.run(main())
