from configuration import (
    AnthropicSettings,
    LLMSettings,
    LocalSettings,
    Settings,
    WebScrapeSettings,
    WebSearchSettings,
)
from core.domain import SearchProvider
from faker import Faker


def build_web_search_settings(
    *,
    search_engine: SearchProvider | None = None,
    api_key: str | None = None,
    search_limit: str | None = None,
    search_timeout: str | None = None,
    search_retries: str | None = None,
        search_engine_url: str | None = None) -> WebSearchSettings:
    fake = Faker()
    values = {
        "SEARCH_ENGINE": search_engine or fake.random_element(elements=[p for p in SearchProvider]),
        "API_KEY": api_key or fake.uuid4(),
        "SEARCH_LIMIT": search_limit or str(fake.random_int(min=1, max=10)),
        "SEARCH_TIMEOUT": search_timeout or str(fake.random_int(min=1, max=10)),
        "SEARCH_RETRIES": search_retries or str(fake.random_int(min=1, max=5)),
        "SEARCH_ENGINE_URL": search_engine_url or fake.url()
    }
    return WebSearchSettings(values)


def build_settings(**kwargs) -> Settings:
    """Build test settings with fake values"""
    fake = Faker()

    # Create base settings dictionary
    settings_dict = {
        "APP_HOST": "local",
        "LOCAL_STORAGE_PATH": "/tmp/test_storage",

        # Search settings
        "SEARCH_ENGINE": kwargs.get("search_engine", SearchProvider.DUCKDUCKGO),
        "SEARCH_LIMIT": str(kwargs.get("search_limit", 10)),
        "SEARCH_TIMEOUT": str(kwargs.get("search_timeout", 30)),
        "SEARCH_RETRIES": str(kwargs.get("search_retries", 3)),
        "SEARCH_ENGINE_URL": kwargs.get("search_engine_url", "https://api.duckduckgo.com/"),

        # Scraper settings
        "SCRAPER_FOLDER_NAME": "test_scrape",
        "SCRAPER_WAIT_TIME": str(kwargs.get("scraper_wait_time", 1)),
        "SCRAPER_RETRIES": str(kwargs.get("scraper_retries", 3)),
        "SCRAPER_TIMEOUT": str(kwargs.get("scraper_timeout", 10000)),
        "SCRAPER_CONCURRENT_LIMIT": str(kwargs.get("scraper_concurrent_limit", 2)),
        "SCRAPER_HEADERS": '{"User-Agent": "Test Agent"}',
        "SCRAPER_CONTENT_SELECTORS": ["test-selector"],

        # LLM settings
        "LLM_HOST": "anthropic",
        "LLM_PROVIDER": "anthropic",
        "LLM_MODEL_NAME": "claude-3-5-sonnet-20240620",
        "LLM_STREAMING": "true",
        "LLM_FORCE_TOOL_SUPPORT": "false",
        "LLM_TEMPERATURE": "0.7",
        "LLM_TOP_P": "0.95",
        "LLM_MAX_TOKENS": "1000",

        # Anthropic settings
        "ANTHROPIC_API_KEY": "test_api_key"
    }

    # Create a Settings instance without calling __init__
    settings = Settings.__new__(Settings)
    Settings._instance = settings

    # Set required attributes
    settings._settings = settings_dict
    settings._app_host = settings_dict["APP_HOST"]
    settings._web_search_settings = WebSearchSettings(settings_dict)
    settings._web_scrape_settings = WebScrapeSettings(settings_dict)
    settings._local_settings = LocalSettings(settings_dict)
    settings._llm_settings = LLMSettings(settings_dict)
    settings._anthropic_settings = AnthropicSettings(settings_dict)

    return settings
