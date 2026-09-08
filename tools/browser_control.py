"""Browser automation tools backed by Playwright.

Everything is lazy — Playwright is only imported when a browser tool is
actually used, so TARS keeps working on machines without it. A single
headless Chromium instance is reused across calls.
"""
import os

_pw = None
_browser = None
_page = None
DEFAULT_TIMEOUT = 10000  # ms
MAX_TEXT = 3000          # chars of page text returned to the model

_IN_CONTAINER = bool(os.environ.get("IN_DOCKER")) or os.path.exists("/.dockerenv")


def _ensure_browser():
    """Start (once) a headless Chromium and return the shared page."""
    global _pw, _browser, _page
    if _browser is not None:
        return _page

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed. Install it with:\n"
            "    pip install playwright\n"
            "    playwright install chromium"
        )

    _pw = sync_playwright().start()
    try:
        launch_args = ["--no-sandbox"] if _IN_CONTAINER else None
        _browser = _pw.chromium.launch(headless=True, args=launch_args)
        _page = _browser.new_page()
    except Exception as e:
        raise RuntimeError(
            f"Could not launch Chromium for Playwright ({e}).\n"
            "Make sure the browser is installed:\n"
            "    playwright install chromium"
        )
    _page.set_default_timeout(DEFAULT_TIMEOUT)
    return _page


def _snapshot(page):
    """Extract (title, url, trimmed_text) from the current page."""
    try:
        title = page.title()
        url = page.url
        text = page.inner_text("body")
    except Exception:
        return None, None, ""
    text = " ".join(text.split())  # collapse whitespace/newlines
    return title, url, text[:MAX_TEXT]


def _result(title, url, text, extra=None):
    data = {"title": title, "url": url, "page_text": text}
    if extra:
        data.update(extra)
    return data


def browser_navigate(url: str, wait_ms: int = 2500):
    """Open a URL and return the page title, final url and visible text."""
    page = _ensure_browser()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(min(wait_ms, 5000))
    except Exception as e:
        return {"error": f"Could not navigate to {url}: {e}"}
    title, final_url, text = _snapshot(page)
    return _result(title, final_url, text)


def browser_extract(url: str = None):
    """Get readable text from the current page, or navigate to `url` first."""
    page = _ensure_browser()
    if url:
        return browser_navigate(url)
    title, current_url, text = _snapshot(page)
    if not text:
        return {"error": "No page is open. Pass a url."}
    return _result(title, current_url, text)


def browser_search(query: str, max_results: int = 5):
    """Search DuckDuckGo (HTML endpoint) and return result titles + urls."""
    page = _ensure_browser()
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(1500)
    except Exception as e:
        return {"error": f"Search failed: {e}"}

    results = []
    try:
        links = page.query_selector_all("a.result__a")[:max_results]
        for a in links:
            results.append({"title": (a.inner_text() or "").strip(), "url": (a.get_attribute("href") or "")})
    except Exception:
        pass

    if not results:
        title, _, text = _snapshot(page)
        return _result(title, page.url, text, extra={"error": "No results extracted."})
    return _result("Search results", page.url, "", extra={"results": results})


def browser_click(selector: str, url: str = None):
    """Click the first element matching `selector` (CSS)."""
    page = _ensure_browser()
    if url:
        return browser_navigate(url)
    try:
        page.click(selector)
        page.wait_for_timeout(1500)
    except Exception as e:
        return {"error": f"Could not click '{selector}': {e}"}
    title, current_url, text = _snapshot(page)
    return _result(title, current_url, text)


def browser_fill(selector: str, value: str, url: str = None, press_enter: bool = False):
    """Type `value` into the field matching `selector`, optionally pressing Enter."""
    page = _ensure_browser()
    if url:
        nav = browser_navigate(url)
        if "error" in nav:
            return nav
    try:
        page.fill(selector, value)
        if press_enter:
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
    except Exception as e:
        return {"error": f"Could not fill '{selector}': {e}"}
    title, current_url, text = _snapshot(page)
    return _result(title, current_url, text)


def browser_screenshot(url: str = None, path: str = "screenshots/tars_shot.png"):
    """Save a screenshot of the current page (or navigate to `url` first)."""
    page = _ensure_browser()
    if url:
        browser_navigate(url)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        page.screenshot(path=path, full_page=False)
        return {"screenshot": os.path.abspath(path)}
    except Exception as e:
        return {"error": f"Screenshot failed: {e}"}


def browser_close():
    """Close the shared browser instance."""
    global _pw, _browser, _page
    try:
        if _browser:
            _browser.close()
    except Exception:
        pass
    finally:
        _browser = None
        _page = None
        _pw = None
    return {"closed": True}