"""
Pytest configuration and shared fixtures
"""
import os
import shutil
from unittest.mock import Mock

import pytest
from configuration import Settings
from core.storage import Storage
from injector import Injector, Module, singleton
from tests.builders.settings_builder import build_settings


class TestModule(Module):
    """Test dependency injection module."""

    def __init__(self, storage_mock: Mock, settings: Settings):
        self._storage_mock = storage_mock
        self._settings = settings

    def configure(self, binder):
        binder.bind(Storage, to=self._storage_mock, scope=singleton)
        binder.bind(Settings, to=self._settings, scope=singleton)


@pytest.fixture
def storage_mock():
    return Mock(spec=Storage)


@pytest.fixture
def test_settings():
    return build_settings(
        scraper_concurrent_limit=2,
        scraper_retries=2,
        scraper_timeout=30000,
        # Override default selectors
        scraper_content_selectors=["test-selector"]
    )


@pytest.fixture
def injector(storage_mock, test_settings):
    test_module = TestModule(storage_mock, test_settings)
    return Injector([test_module])


def pytest_sessionfinish(session, exitstatus):
    """Clean up after all tests are done"""
    # Get project root directory (two levels up from tests)
    root_dir = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Clean up __pycache__ directories
        if '__pycache__' in dirnames:
            cache_dir = os.path.join(dirpath, '__pycache__')
            shutil.rmtree(cache_dir)
            print(f"Cleaned up {cache_dir}")

        # Clean up MagicMock directories
        if 'MagicMock' in dirnames:
            mock_dir = os.path.join(dirpath, 'MagicMock')
            shutil.rmtree(mock_dir)
            print(f"Cleaned up {mock_dir}")

    # Also check root directory directly
    magic_mock_root = os.path.join(root_dir, 'MagicMock')
    if os.path.exists(magic_mock_root):
        shutil.rmtree(magic_mock_root)
        print(f"Cleaned up {magic_mock_root}")
