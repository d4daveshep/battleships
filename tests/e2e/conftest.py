"""
Pytest configuration for E2E tests.

These tests use Playwright for browser-based end-to-end testing.
"""

import subprocess
import time
import pytest
from playwright.sync_api import Browser, Page, sync_playwright
import httpx


BASE_URL = "http://localhost:8000/"


@pytest.fixture(scope="session")
def fastapi_server():
    """Start FastAPI server for the entire test session"""
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--port", "8000", "--host", "0.0.0.0"]
    )

    # Wait for server to be ready with health check
    for _ in range(30):  # 30 second timeout
        try:
            with httpx.Client() as client:
                response = client.get(f"{BASE_URL}health", timeout=1)
                if response.status_code == 200:
                    break
        except:
            time.sleep(1)
    else:
        process.kill()
        raise RuntimeError("FastAPI server failed to start")

    yield process
    process.terminate()
    process.wait()


@pytest.fixture(scope="function")
def browser():
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser, fastapi_server):
    """Page fixture that depends on running server"""
    page: Page = browser.new_page()
    page.set_default_timeout(5000)  # 5 seconds
    yield page
    page.close()


@pytest.fixture
def reset_lobby_state(fastapi_server):
    """Reset lobby state before each E2E test"""
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}test/reset-lobby")
        assert response.status_code == 200
    yield
    # Cleanup after test
    with httpx.Client() as client:
        client.post(f"{BASE_URL}test/reset-lobby")
