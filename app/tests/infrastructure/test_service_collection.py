# app/tests/infrastructure/test_service_collection.py
from unittest.mock import patch

import pytest
from configuration import Settings
from core.web_scraping import (
    WebScraperCharityIntellence,
    WebScraperFactory,
    WebScraperGeneric,
)
from core.web_search import SearchEngine
from infrastructure.service_collection import ServiceCollection, ServiceProvider
from tests.builders.build import Build


@pytest.fixture(scope="module")
def service_provider() -> ServiceProvider:
    """Create a service provider with all services registered"""
    # Reset singleton state before creating
    Settings._instance = None
    ServiceProvider._instance = None
    ServiceProvider._injector = None

    # Create test settings using builder
    test_settings = Build.settings()

    # Mock get_settings to return our test settings
    with patch('app.infrastructure.service_collection.get_settings', return_value=test_settings):
        # Create service provider
        return ServiceCollection.add_services()


def test_resolving_core_services(service_provider: ServiceProvider):
    """Test that core services can be resolved"""
    service_types = [
        Settings,
    ]
    _test_resolving_services(service_types, service_provider)


def test_resolving_web_search_services(service_provider: ServiceProvider):
    """Test that web search services can be resolved"""
    service_types = [
        SearchEngine,
    ]
    _test_resolving_services(service_types, service_provider)


def test_resolving_web_scraper_services(service_provider: ServiceProvider):
    """Test that web scraper services can be resolved"""
    service_types = [
        WebScraperFactory,
        WebScraperGeneric,
        WebScraperCharityIntellence,
    ]
    _test_resolving_services(service_types, service_provider)


def _test_resolving_services(service_types: list[type], service_provider: ServiceProvider):
    """Helper to verify that services can be resolved"""
    for service_type in service_types:
        service = service_provider.get(service_type)
        assert service is not None
