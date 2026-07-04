"""Relevance scoring for vacancies.

Balanced scoring: keywords (40) + salary (25) + company (20) + source bonus (15)
Max: 100 points
"""

import re
from typing import Optional


# Keywords that increase relevance (AI/ML/tech leadership)
HIGH_VALUE_KEYWORDS = [
    # AI/ML
    (r"\bAI\b|\bML\b|искусственн\w+\s+интеллект|машинн\w+\s+обучени|machine learning|artificial intelligence", 12),
    (r"\bCTO\b|\bCIO\b|\bCPO\b|\bCEO\b", 10),
    (r"директор по (?:ИТ|цифров\w+|технологиям|инновац)", 8),
    (r"техническ\w+ директор", 8),
    (r"руководител\w+ (?:ИТ|разработк|инфраструктур|проект|команд)", 6),
    (r"архитектор", 5),
    (r"DevOps|SRE|Platform Engineer", 4),
    (r"Kubernetes|K8s|Docker|облак\w+|cloud", 3),
    (r"Python|Golang|Rust", 2),
    (r"data engineer|дата инженер|Big Data", 4),
]

# Negative keywords (less relevant)
LOW_VALUE_KEYWORDS = [
    (r"стажёр|intern|помощник|ассистент", -15),
    (r"младш\w+|junior|начинающ\w+", -10),
    (r"тестировщик|QA(?!.*автоматиз)", -3),
]

# Company quality signals
PREMIUM_COMPANIES = [
    "яндекс", "yandex", "касперский", "kaspersky", "сбер", "sber",
    "т-банк", "тбанк", "ozon", "озон", "vk", "вконтакте",
    "mail.ru", "мэйл.ру", "avito", "авито", "wildberries", "вайлдберриз",
    "headhunter", "хедхантер", "jetbrains",
    "alphabet", "google", "microsoft", "amazon", "meta", "apple",
    "linux", "red hat", "oracle", "sap", "intel", "nvidia",
    "яндекс.облако", "selectionkit", "skyeng", "skillbox",
]

# Source bonus — ensures fair distribution between platforms
SOURCE_BONUS = {
    "hh": 10,        # Large pool, good data
    "superjob": 8,   # Decent data
    "habr": 5,       # Already gets high keyword scores
    "zarplata": 7,   # Good coverage
    "rabota": 6,
    "avito": 6,
}


def _parse_salary_numeric(salary: Optional[str]) -> int:
    """Extract max numeric value from salary string."""
    if not salary:
        return 0
    numbers = re.findall(r"[\d\s]+", salary.replace(" ", ""))
    nums = []
    for n in numbers:
        try:
            val = int(n.replace(" ", "").replace("\xa0", ""))
            if val > 1000:
                nums.append(val)
        except ValueError:
            pass
    return max(nums) if nums else 0


def _salary_score(salary: Optional[str]) -> int:
    """Score based on salary. 0-25 points."""
    val = _parse_salary_numeric(salary)
    if val >= 500000:
        return 25
    elif val >= 400000:
        return 22
    elif val >= 300000:
        return 20
    elif val >= 250000:
        return 17
    elif val >= 200000:
        return 14
    elif val >= 150000:
        return 11
    elif val >= 100000:
        return 8
    elif val > 0:
        return 4
    return 0


def _keyword_score(title: str, company: Optional[str] = None) -> int:
    """Score based on title keywords. 0-40 points."""
    text = (title + " " + (company or "")).lower()
    score = 0

    for pattern, weight in HIGH_VALUE_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            score += weight

    for pattern, weight in LOW_VALUE_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            score += weight

    return max(0, min(40, score))


def _company_score(company: Optional[str]) -> int:
    """Score based on company reputation. 0-20 points."""
    if not company:
        return 3
    company_lower = company.lower()
    for premium in PREMIUM_COMPANIES:
        if premium in company_lower:
            return 20
    return 5


def _remote_score(is_remote: bool) -> int:
    """Remote work bonus. 0-5 points."""
    return 5 if is_remote else 0


def _source_bonus(source: str) -> int:
    """Platform bonus for fair distribution. 0-10 points."""
    return SOURCE_BONUS.get(source, 5)


def score_vacancy(vacancy: dict) -> int:
    """Calculate total relevance score. 0-100."""
    salary = vacancy.get("salary")
    title = vacancy.get("title", "")
    company = vacancy.get("company")
    remote = vacancy.get("remote", False)
    source = vacancy.get("source", "")

    total = (
        _keyword_score(title, company)
        + _salary_score(salary)
        + _company_score(company)
        + _remote_score(remote)
        + _source_bonus(source)
    )
    return max(0, min(100, total))


def score_label(score: int) -> str:
    """Get emoji label for score."""
    if score >= 60:
        return "🔥"
    elif score >= 45:
        return "⭐"
    elif score >= 30:
        return "✅"
    else:
        return "📋"


def score_text(score: int) -> str:
    """Get text label for score."""
    if score >= 60:
        return "Высокая"
    elif score >= 45:
        return "Выше среднего"
    elif score >= 30:
        return "Средняя"
    else:
        return "Стандартная"
