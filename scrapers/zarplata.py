"""Zarplata.ru scraper — Playwright with proper error recovery."""

import asyncio
import hashlib
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.zarplata.ru/vacancy"


async def search_vacancies(
    queries: list[str],
    cities: list[str],
    min_salary: Optional[int] = None,
) -> list[dict]:
    results = []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return results

    city_map = {
        "Санкт-Петербург": "sankt-peterburg",
        "Москва": "moskva",
    }

    # Limit queries to avoid browser crash
    limited_queries = queries[:6]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )

        for query in limited_queries:
            for city in cities[:1]:  # Single city only
                try:
                    context = await browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                        ),
                        locale="ru-RU",
                    )
                    page = await context.new_page()

                    city_slug = city_map.get(city, "sankt-peterburg")
                    params = {"q": query, "city": city_slug}
                    if min_salary:
                        params["salary_from"] = str(min_salary)

                    url = SEARCH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
                    await page.goto(url, wait_until="networkidle", timeout=20000)
                    await asyncio.sleep(2)

                    vacancies = await page.evaluate("""() => {
                        const results = [];
                        const links = document.querySelectorAll('a[href*="/vacancy/"]');

                        for (const link of links) {
                            const href = link.href;
                            if (!href.match(/\\/vacancy\\/\\d+/)) continue;

                            const title = link.textContent.trim();
                            if (!title || title.length < 5 || title.length > 100) continue;

                            let card = link;
                            for (let i = 0; i < 5; i++) {
                                if (card.parentElement) card = card.parentElement;
                            }
                            const cardText = card.textContent || '';

                            let salary = '';
                            const salaryMatch = cardText.match(
                                /(\\d[\\d\\s]*(?:\\u2014|\\u2013|-)\\s*\\d[\\d\\s]*\\s*(?:\\u20BD|руб)|\\d[\\d\\s]*\\s*(?:\\u20BD|руб))/u
                            );
                            if (salaryMatch) salary = salaryMatch[1].trim();

                            let company = '';
                            const companyEl = card.querySelector('[class*="company"], [class*="employer"]');
                            if (companyEl) company = companyEl.textContent.trim();

                            results.push({ title, url: href, company, salary });
                        }

                        const seen = new Set();
                        return results.filter(v => {
                            if (seen.has(v.url)) return false;
                            seen.add(v.url);
                            return true;
                        });
                    }""")

                    await context.close()

                    for v in vacancies:
                        match = re.search(r"/vacancy/(\d+)", v.get("url", ""))
                        item_id = match.group(1) if match else hashlib.md5(v["title"].encode()).hexdigest()[:12]

                        remote = bool(re.search(r"удалённ|удаленн|remote", v["title"], re.IGNORECASE))

                        results.append({
                            "id": f"zp_{item_id}",
                            "source": "zarplata",
                            "title": v["title"],
                            "company": v.get("company") or None,
                            "url": v.get("url", ""),
                            "salary": v.get("salary") or None,
                            "city": city,
                            "remote": remote,
                            "posted_at": None,
                        })

                except Exception as e:
                    logger.debug(f"Zarplata: {query}/{city}: {e}")
                    try:
                        await context.close()
                    except Exception:
                        pass

        await browser.close()

    seen = set()
    return [v for v in results if v["id"] not in seen and not seen.add(v["id"])]
