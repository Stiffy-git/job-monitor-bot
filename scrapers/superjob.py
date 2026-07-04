"""SuperJob.ru scraper."""

import logging
import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.superjob.ru/vacancy/search/"


def _parse_salary(text: str) -> Optional[str]:
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    if not text or "договорная" in text.lower():
        return None
    return text


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

    geo_map = {
        "Санкт-Петербург": "2",
        "Москва": "1",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        for query in queries:
            for city in cities[:2]:
                geo_id = geo_map.get(city, "2")
                params = {
                    "keywords": query,
                    "geo[r][0]": geo_id,
                    "period": "0",
                }
                if min_salary:
                    params["payment_from"] = str(min_salary)

                try:
                    async with session.get(
                        SEARCH_URL, params=params,
                        timeout=aiohttp.ClientTimeout(total=15),
                        allow_redirects=True,
                    ) as resp:
                        if resp.status != 200:
                            continue
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # SuperJob uses f-test-search-result-item
                        items = soup.find_all("div", class_=re.compile(r"f-test-search-result-item"))
                        for item in items[:20]:
                            try:
                                vacancy = _parse_card(item, city)
                                if vacancy:
                                    results.append(vacancy)
                            except Exception as e:
                                logger.debug(f"SuperJob parse error: {e}")
                except Exception as e:
                    logger.error(f"SuperJob error for {query}: {e}")

    seen = set()
    return [v for v in results if v["id"] not in seen and not seen.add(v["id"])]


def _parse_card(item, city: str) -> Optional[dict]:
    # Find vacancy link (f-test-link-*)
    link_el = item.find("a", class_=re.compile(r"f-test-link-"))
    if not link_el:
        link_el = item.find("a", href=re.compile(r"/vakansii/"))
    if not link_el:
        return None

    title = link_el.get_text(strip=True)
    if not title:
        return None

    url = link_el.get("href", "")
    if url and not url.startswith("http"):
        url = "https://www.superjob.ru" + url

    # Extract item ID from URL or class
    match = re.search(r"-(\d+)\.html", url)
    if not match:
        match = re.search(r"vacancy-item-(\d+)", str(item.get("class", [])))
    item_id = match.group(1) if match else ""

    # Salary
    salary_el = item.find("div", class_=re.compile(r"f-test-text-company-item-salary"))
    salary = None
    if salary_el:
        salary_text = salary_el.get_text(" ", strip=True)
        salary = _parse_salary(salary_text)

    # Company
    company_el = item.find("span", class_=re.compile(r"f-test-text-company-item-name"))
    company = company_el.get_text(strip=True) if company_el else None

    remote = bool(re.search(r"удалённ|удаленн|remote", title, re.IGNORECASE))

    return {
        "id": f"sj_{item_id}",
        "source": "superjob",
        "title": title,
        "company": company,
        "url": url,
        "salary": salary,
        "city": city,
        "remote": remote,
        "posted_at": None,
    }
