"""hh.ru scraper — Playwright for full data extraction."""

import asyncio
import hashlib
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

SEARCH_URL = "https://hh.ru/search/vacancy"


async def _extract_vacancies(page) -> list[dict]:
    """Extract vacancy data from current page via JavaScript."""
    return await page.evaluate("""() => {
        const results = [];
        const links = document.querySelectorAll('a[href*="/vacancy/"]');

        for (const link of links) {
            const href = link.href;
            if (!href.match(/\\/vacancy\\/\\d+/)) continue;

            const title = link.textContent.trim();
            if (!title || title.length < 5 || title.length > 150) continue;

            let card = link;
            for (let i = 0; i < 8; i++) {
                if (card.parentElement) card = card.parentElement;
            }
            const cardText = card.textContent || '';

            let salary = '';
            const salaryMatch = cardText.match(
                /(\\d[\\d\\s]*(?:\\u2014|\\u2013|-)\\s*\\d[\\d\\s]*\\s*(?:\\u20BD|руб)|\\d[\\d\\s]*\\s*(?:\\u20BD|руб))/u
            );
            if (salaryMatch) salary = salaryMatch[1].trim();

            let company = '';
            const employerLink = card.querySelector('a[href*="/employer/"]');
            if (employerLink) company = employerLink.textContent.trim();

            let city = '';
            const cityMatch = cardText.match(
                /(Санкт-Петербург|Москва|\\u0423\\u0434\\u0430\\u043B\\u0451\\u043D\\u043D\\u043E|Remote)/i
            );
            if (cityMatch) city = cityMatch[1];

            results.push({ title, url: href, company, salary, city });
        }

        const seen = new Set();
        return results.filter(v => {
            if (seen.has(v.url)) return false;
            seen.add(v.url);
            return true;
        });
    }""")


async def search_vacancies(
    queries: list[str],
    areas: list[str],
    min_salary: Optional[int] = None,
    page_num: int = 0,
    per_page: int = 50,
) -> list[dict]:
    """Search hh.ru vacancies via Playwright."""
    results = []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return results

    # Limit queries to avoid browser crash
    limited_queries = queries[:8]
    limited_areas = areas[:2]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )

        for query in limited_queries:
            for area in limited_areas:
                try:
                    page = await context.new_page()
                    params = {
                        "text": query,
                        "area": area,
                        "page": page_num,
                        "per_page": min(per_page, 50),
                    }
                    if min_salary:
                        params["salary"] = str(min_salary)
                        params["only_with_salary"] = "true"

                    url = SEARCH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
                    await page.goto(url, wait_until="networkidle", timeout=25000)
                    await asyncio.sleep(2)

                    vacancies = await _extract_vacancies(page)
                    await page.close()

                    for v in vacancies:
                        item_id = ""
                        match = re.search(r"/vacancy/(\d+)", v.get("url", ""))
                        if match:
                            item_id = match.group(1)
                        if not item_id:
                            item_id = hashlib.md5(v["title"].encode()).hexdigest()[:12]

                        remote = bool(re.search(
                            r"удалённ|удаленн|remote",
                            v["title"] + " " + v.get("city", ""),
                            re.IGNORECASE
                        ))

                        city = v.get("city") or ""
                        if city.lower() in ("удалённо", "remote"):
                            remote = True
                            city = ""

                        results.append({
                            "id": f"hh_{item_id}",
                            "source": "hh",
                            "title": v["title"],
                            "company": v.get("company") or None,
                            "url": v.get("url", ""),
                            "salary": v.get("salary") or None,
                            "city": city or "Санкт-Петербург",
                            "remote": remote,
                            "posted_at": None,
                        })

                except Exception as e:
                    logger.debug(f"hh.ru error for {query}/{area}: {e}")
                    # Try to recover by creating new context
                    try:
                        await context.close()
                        context = await browser.new_context(
                            user_agent=(
                                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            ),
                            locale="ru-RU",
                        )
                    except Exception:
                        pass

        await browser.close()

    seen = set()
    return [v for v in results if v["id"] not in seen and not seen.add(v["id"])]
