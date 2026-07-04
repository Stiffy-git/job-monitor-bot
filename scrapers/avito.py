"""Avito Rabota scraper — Playwright headless browser (HTML is JS-rendered)."""

import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://www.avito.ru"


def _build_search_url(query: str, city: str) -> str:
    """Build Avito search URL for jobs."""
    city_map = {
        "Санкт-Петербург": "sankt-peterburg",
        "Санкт-Петербург и Ленобласть": "sankt-peterburg",
        "Москва": "moskva",
        "Удалённо": "all",
        "Remote": "all",
    }
    city_slug = city_map.get(city, city.lower().replace(" ", "-"))
    return f"{BASE_URL}/{city_slug}/rabota?q={query}"


async def search_vacancies(
    queries: list[str],
    cities: list[str],
    min_salary: Optional[int] = None,
    proxy: str = "",
) -> list[dict]:
    """Search Avito Rabota vacancies via Playwright.

    Args:
        proxy: Proxy URL, e.g. "http://user:pass@host:port" or "socks5://host:port"

    Returns list of dicts:
        id, source, title, company, url, salary, city, remote, posted_at
    """
    results = []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
        return results

    async with async_playwright() as p:
        launch_args = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        if proxy:
            launch_args["proxy"] = {"server": proxy}
            logger.info(f"Avito: using proxy {proxy}")

        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )
        page = await context.new_page()

        for query in queries:
            for city in cities[:2]:  # Limit cities
                url = _build_search_url(query, city)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    # Wait for JS to render
                    await asyncio.sleep(3)

                    # Check if blocked by captcha
                    page_text = await page.inner_text("body")
                    if "Доступ ограничен" in page_text or "капчи" in page_text:
                        logger.warning(f"Avito: captcha/block detected for {city}/{query}")
                        continue

                    # Wait for items
                    try:
                        await page.wait_for_selector(
                            '[data-marker="item"], .item-card, .vacancy-card',
                            timeout=8000
                        )
                    except Exception:
                        logger.debug(f"Avito: no item markers for {city}/{query}")
                        continue

                    # Extract vacancy data via JavaScript
                    vacancies = await page.evaluate("""() => {
                        const items = document.querySelectorAll('[data-marker="item"], .item-card, .vacancy-card');
                        return Array.from(items).slice(0, 20).map(item => {
                            const titleEl = item.querySelector('h3, a[itemprop="name"], [class*="title"] a, [class*="name"] a');
                            const title = titleEl ? titleEl.textContent.trim() : '';
                            const linkEl = titleEl && titleEl.tagName === 'A' ? titleEl : item.querySelector('a[href*="/vakansii/"], a[href*="/rabota/"]');
                            const url = linkEl ? linkEl.href : '';
                            const companyEl = item.querySelector('[class*="company"], [class*="seller"], [class*="brand"]');
                            const company = companyEl ? companyEl.textContent.trim() : '';
                            const salaryEl = item.querySelector('[class*="price"], [class*="salary"], [class*="compensation"]');
                            const salary = salaryEl ? salaryEl.textContent.trim() : '';
                            const itemId = item.getAttribute('data-item-id') || '';
                            return { title, url, company, salary, itemId };
                        }).filter(v => v.title && v.url);
                    }""")

                    for v in vacancies:
                        item_id = v.get("itemId", "")
                        if not item_id:
                            match = re.search(r"/(\d+)(?:\?|$)", v.get("url", ""))
                            item_id = match.group(1) if match else ""
                        if not item_id:
                            import hashlib
                            item_id = hashlib.md5(v["title"].encode()).hexdigest()[:12]

                        remote = bool(re.search(
                            r"удалённ|удаленн|remote",
                            v["title"] + " " + v.get("company", ""),
                            re.IGNORECASE
                        ))

                        vacancy = {
                            "id": f"avito_{item_id}",
                            "source": "avito",
                            "title": v["title"],
                            "company": v.get("company") or None,
                            "url": v.get("url", ""),
                            "salary": v.get("salary") or None,
                            "city": city,
                            "remote": remote,
                            "posted_at": None,
                        }
                        results.append(vacancy)

                except Exception as e:
                    logger.warning(f"Avito: error for {city}/{query}: {e}")

        await browser.close()

    # Deduplicate
    seen = set()
    unique = []
    for v in results:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)

    return unique
