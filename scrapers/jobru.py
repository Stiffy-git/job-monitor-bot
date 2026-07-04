"""job.ru scraper (HTML parsing)."""

import hashlib
import logging
import re
from typing import Optional
from urllib.parse import quote

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.job.ru"


def _build_search_url(query: str, city: str) -> str:
    """Build job.ru search URL."""
    city_map = {
        "Санкт-Петербург": "sankt-peterburg",
        "Москва": "moskva",
        "Удалённо": "udaljonno",
        "Remote": "udaljonno",
    }
    city_slug = city_map.get(city, city.lower().replace(" ", "-"))
    return f"{BASE_URL}/vacancy/search/?text={quote(query)}&city={city_slug}"


async def search_vacancies(
    queries: list[str],
    cities: list[str],
    min_salary: Optional[int] = None,
) -> list[dict]:
    results = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        for query in queries:
            for city in cities[:2]:
                url = _build_search_url(query, city)
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=15),
                        allow_redirects=True
                    ) as resp:
                        if resp.status != 200:
                            continue
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # job.ru vacancy links pattern: /vacancy/NNNNN/
                        links = soup.find_all("a", href=re.compile(r"/vacancy/\d+/?"))
                        seen_urls = set()
                        for link in links:
                            href = link.get("href", "")
                            if href in seen_urls:
                                continue
                            # Skip non-vacancy links
                            if not re.search(r"/vacancy/\d+/?$", href):
                                continue
                            seen_urls.add(href)
                            try:
                                vacancy = _parse_link(link, href, city)
                                if vacancy:
                                    results.append(vacancy)
                            except Exception as e:
                                logger.debug(f"job.ru parse error: {e}")
                except Exception as e:
                    logger.error(f"job.ru error for {query}: {e}")

    seen = set()
    return [v for v in results if v["id"] not in seen and not seen.add(v["id"])]


def _parse_link(link, url: str, city: str) -> Optional[dict]:
    title = link.get_text(strip=True)
    # Skip navigation items
    skip_words = ["войти", "регистрация", "создать резюме", "сервисы", "вакансии", "компании"]
    if not title or len(title) < 5 or title.lower() in skip_words:
        return None

    if url and not url.startswith("http"):
        url = BASE_URL + url

    match = re.search(r"/vacancy/(\d+)", url)
    item_id = match.group(1) if match else hashlib.md5(title.encode()).hexdigest()[:12]

    # Get parent container for salary/company
    parent = link.find_parent(["div", "li", "article"])
    salary = None
    company = None

    if parent:
        # Look for salary
        salary_el = parent.find(string=re.compile(r"\d[\d\s]*(?:₽|руб|RUB)"))
        if salary_el:
            salary = salary_el.strip()

        # Look for company
        company_el = parent.find(class_=re.compile(r"company|employer|firm|organization"))
        if company_el:
            company = company_el.get_text(strip=True)

    remote = bool(re.search(r"удалённ|удаленн|remote", title, re.IGNORECASE))

    return {
        "id": f"jobru_{item_id}",
        "source": "jobru",
        "title": title,
        "company": company,
        "url": url,
        "salary": salary,
        "city": city,
        "remote": remote,
        "posted_at": None,
    }
