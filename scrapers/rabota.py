"""Rabota.ru scraper (fallback — site may block datacenter IPs)."""

import hashlib
import logging
import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.rabota.ru/vacancies"


async def search_vacancies(
    queries: list[str],
    cities: list[str],
    min_salary: Optional[int] = None,
) -> list[dict]:
    results = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        for query in queries:
            for city in cities[:1]:
                params = {"keyword": query}
                if min_salary:
                    params["payment_from"] = str(min_salary)

                try:
                    async with session.get(
                        SEARCH_URL, params=params,
                        timeout=aiohttp.ClientTimeout(total=15),
                        allow_redirects=True,
                    ) as resp:
                        if resp.status != 200:
                            logger.debug(f"Rabota.ru returned {resp.status}")
                            continue
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # Look for vacancy links
                        links = soup.find_all("a", href=re.compile(r"/vacancy/\d+"))
                        seen_urls = set()
                        for link in links:
                            url = link.get("href", "")
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)
                            try:
                                vacancy = _parse_link(link, url, city)
                                if vacancy:
                                    results.append(vacancy)
                            except Exception as e:
                                logger.debug(f"Rabota.ru parse error: {e}")
                except Exception as e:
                    logger.error(f"Rabota.ru error for {query}: {e}")

    seen = set()
    return [v for v in results if v["id"] not in seen and not seen.add(v["id"])]


def _parse_link(link, url: str, city: str) -> Optional[dict]:
    title = link.get_text(strip=True)
    if not title or len(title) < 5:
        return None

    if url and not url.startswith("http"):
        url = "https://www.rabota.ru" + url

    match = re.search(r"/vacancy/(\d+)", url)
    item_id = match.group(1) if match else hashlib.md5(title.encode()).hexdigest()[:12]

    parent = link.find_parent("div")
    salary = None
    company = None
    if parent:
        salary_el = parent.find(string=re.compile(r"\d+\s*(₽|руб)"))
        if salary_el:
            salary = salary_el.strip()

        company_el = parent.find(class_=re.compile(r"company|employer"))
        if company_el:
            company = company_el.get_text(strip=True)

    remote = bool(re.search(r"удалённ|удаленн|remote", title, re.IGNORECASE))

    return {
        "id": f"rab_{item_id}",
        "source": "rabota",
        "title": title,
        "company": company,
        "url": url,
        "salary": salary,
        "city": city,
        "remote": remote,
        "posted_at": None,
    }
