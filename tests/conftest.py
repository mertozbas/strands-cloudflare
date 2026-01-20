"""
Fixtures and configuration for pytest.
"""

import os
import pytest
from dotenv import load_dotenv


def pytest_configure(config):
    """Load .env file before tests."""
    # Try to load .env from project root
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)


@pytest.fixture
def zone_id():
    """Default zone ID for tests."""
    return os.getenv("CLOUDFLARE_ZONE_ID")


@pytest.fixture
def account_id():
    """Default account ID for tests."""
    return os.getenv("CLOUDFLARE_ACCOUNT_ID")


@pytest.fixture
def has_credentials():
    """Check if Cloudflare credentials are available."""
    return bool(os.getenv("CLOUDFLARE_API_TOKEN") or 
                (os.getenv("CLOUDFLARE_API_KEY") and os.getenv("CLOUDFLARE_EMAIL")))
