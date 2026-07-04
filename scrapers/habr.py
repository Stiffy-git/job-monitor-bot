"""Habr Career (career.habr.com) scraper."""

import logging
import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_URL = "https://career.habr.com/vacancies"


def _parse_salary(text: str) -> Optional[str]:
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    if not text or "не указана" in text.lower() or "договорная" in text.lower():
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

    city_map = {
        "Санкт-Петербург": "678",
        "Москва": "678",
        "Удалённо": "0",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        for query in queries:
            for city in cities[:2]:
                city_id = city_map.get(city, "678")
                params = {
                    "q": query,
                    "city_id": city_id,
                    "type": "all",
                }
                if min_salary:
                    params["salary_from"] = str(min_salary)

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

                        # Habr uses vacancy-card class
                        cards = soup.find_all("div", class_=re.compile(r"vacancy-card"))
                        for card in cards[:20]:
                            try:
                                vacancy = _parse_card(card, city)
                                if vacancy:
                                    results.append(vacancy)
                            except Exception as e:
                                logger.debug(f"Habr parse error: {e}")
                except Exception as e:
                    logger.error(f"Habr error for {query}: {e}")

    seen = set()
    return [v for v in results if v["id"] not in seen and not seen.add(v["id"])]


def _parse_card(card, city: str) -> Optional[dict]:
    # Title from aria-label of backdrop link
    link_el = card.find("a", class_=re.compile(r"backdrop-link"))
    if not link_el:
        link_el = card.find("a", href=re.compile(r"/vacancies/\d+"))
    if not link_el:
        return None

    title = link_el.get("aria-label", "") or link_el.get_text(strip=True)
    if not title:
        return None

    url = link_el.get("href", "")
    if url and not url.startswith("http"):
        url = "https://career.habr.com" + url

    match = re.search(r"/vacancies/(\d+)", url)
    item_id = match.group(1) if match else ""

    # Company
    company_el = card.find("a", class_=re.compile(r"link-comp"))
    company = None
    if company_el and "/companies/" in (company_el.get("href", "")):
        company = company_el.get_text(strip=True)

    # Salary
    salary_el = card.find(string=re.compile(r"\d+\s*(₽|руб|RUB|\$|€)"))
    salary = _parse_salary(salary_el.strip() if salary_el else None)

    remote = bool(re.search(r"удалённ|удаленн|remote", title, re.IGNORECASE))

    return {
        "id": f"habr_{item_id}",
        "source": "habr",
        "title": title,
        "company": company,
        "url": url,
        "salary": salary,
        "city": city,
        "remote": remote,
        "posted_at": None,
    }
