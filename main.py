"""
Job Monitor Bot — hourly 7:00-23:30 + daily summary at 22:30
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, time
from pathlib import Path

import yaml

from database import VacancyDB
from publisher import TelegramPublisher
from scrapers import hh, superjob, zarplata, habr, rabota

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("job-monitor")

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def should_exclude(vacancy: dict, config: dict) -> bool:
    exclude = config.get("filters", {}).get("exclude_keywords", [])
    title_lower = vacancy.get("title", "").lower()
    for word in exclude:
        if word.lower() in title_lower:
            return True
    return False


def is_active_hours() -> bool:
    """Check if current time is between 7:00 and 23:30."""
    now = datetime.now().time()
    return time(7, 0) <= now <= time(23, 30)


def is_daily_report_time() -> bool:
    """Check if it's 22:30."""
    now = datetime.now().time()
    return time(22, 25) <= now <= time(22, 35)


async def scrape_all(config: dict, db: VacancyDB) -> int:
    queries = config["search_queries"]
    min_salary = config.get("filters", {}).get("min_salary_rub")
    all_vacancies = []

    scrapers = [
        ("hh.ru", lambda: hh.search_vacancies(queries=queries, areas=config["locations"]["hh"])),
        ("SuperJob", lambda: superjob.search_vacancies(queries=queries, cities=config["locations"]["text"])),
        ("Habr", lambda: habr.search_vacancies(queries=queries, cities=config["locations"]["text"])),
        ("Zarplata", lambda: zarplata.search_vacancies(queries=queries, cities=config["locations"]["text"])),
        ("Rabota.ru", lambda: rabota.search_vacancies(queries=queries, cities=config["locations"]["text"])),
    ]

    for name, fn in scrapers:
        try:
            result = await fn()
            logger.info(f"{name}: {len(result)}")
            all_vacancies.extend(result)
        except Exception as e:
            logger.error(f"{name} error: {e}")

    # Avito (optional)
    avito_proxy = config.get("proxy", {}).get("avito", "")
    if avito_proxy:
        from scrapers import avito
        try:
            result = await avito.search_vacancies(
                queries=queries, cities=config["locations"]["text"], proxy=avito_proxy
            )
            logger.info(f"Avito: {len(result)}")
            all_vacancies.extend(result)
        except Exception as e:
            logger.error(f"Avito error: {e}")

    new_count = 0
    for v in all_vacancies:
        if should_exclude(v, config):
            continue
        if db.mark_found(
            vacancy_id=v["id"], source=v["source"], title=v["title"],
            company=v.get("company"), url=v.get("url"), salary=v.get("salary"),
            city=v.get("city"), remote=v.get("remote", False),
        ):
            new_count += 1

    return new_count


async def main():
    config = load_config()
    token = config["telegram"]["bot_token"]
    channel = config["telegram"]["channel_id"]

    if token == "YOUR_BOT_TOKEN" or channel == "@your_channel":
        logger.error("Set token/channel in config.yaml!")
        sys.exit(1)

    db = VacancyDB(config.get("database", {}).get("path", "vacancies.db"))
    pub = TelegramPublisher(token, channel)

    logger.info("Connecting...")
    if not await pub.test_connection():
        logger.error("Telegram failed")
        sys.exit(1)

    interval = config.get("monitoring", {}).get("check_interval", 3600)
    digest_limit = config.get("monitoring", {}).get("max_posts_per_update", 0)
    if digest_limit == 0:
        digest_limit = 999  # Show all
    daily_report_sent = False

    stop_event = asyncio.Event()
    def handle_signal(*_):
        stop_event.set()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    logger.info(f"Bot started (interval={interval}s, hours=7:00-23:30)")

    while not stop_event.is_set():
        try:
            now = datetime.now()

            # Reset daily flags at midnight
            if now.hour == 0 and now.minute < 5:
                db.reset_daily_shown()
                daily_report_sent = False
                logger.info("Daily flags reset")

            # Only work between 7:00 and 23:30
            if is_active_hours():
                # 1. Scrape
                new_count = await scrape_all(config, db)
                logger.info(f"New: {new_count}")

                # 2. Hourly digest
                digest = db.get_new_vacancies(limit=digest_limit)
                if digest:
                    if await pub.publish_hourly(digest):
                        db.mark_shown([v[0] for v in digest])
                        logger.info(f"Published: {len(digest)}")

                # 3. Daily report at 22:30
                if is_daily_report_time() and not daily_report_sent:
                    all_today = db.get_today_shown()
                    stats = db.get_stats()
                    if await pub.publish_daily(all_today, stats):
                        daily_report_sent = True
                        logger.info("Daily report sent")

            else:
                logger.info("Outside active hours (7:00-23:30), sleeping...")

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass

    db.close()
    logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
