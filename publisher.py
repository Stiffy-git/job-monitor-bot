"""Telegram publisher — sorted by categories."""

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

BRAND = {
    "hh": {"icon": "🔴", "name": "hh"},
    "superjob": {"icon": "💎", "name": "SJ"},
    "habr": {"icon": "⚡", "name": "Habr"},
    "zarplata": {"icon": "🪙", "name": "ZP"},
    "rabota": {"icon": "💼", "name": "Rabota"},
    "avito": {"icon": "🟢", "name": "Avito"},
}

TELEGRAM_LIMIT = 4000


def _category(title: str) -> str:
    """Categorize vacancy by title."""
    t = title.lower()
    if re.search(r"\b(cto|cio|cpo|ceo)\b", t):
        return "🎯 C-level"
    if re.search(r"директор по (?:ит|цифров|технолог)", t):
        return "🏢 Директор ИТ"
    if re.search(r"техническ\w+ директор", t):
        return "⚙️ Технический директор"
    if re.search(r"pmo|проектн\w+ офис|head of project", t):
        return "📋 PMO"
    if re.search(r"product\s*(?:manager|owner|менеджер|владелец)", t):
        return "📦 Продукт"
    if re.search(r"продукт\w+|product", t):
        return "📦 Продукт"
    if re.search(r"руководител\w+ (?:команд|проект|разработк)", t):
        return "👥 Руководитель"
    if re.search(r"архитектор", t):
        return "🏗 Архитектор"
    if re.search(r"devops|sre|platform|инфраструктур", t):
        return "🔧 Инфраструктура"
    if re.search(r"ai|ml|машинн\w+|data scien", t):
        return "🤖 AI/ML"
    return "💼 Другое"


def _t(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n-1] + "…"


def _split_messages(messages: list[str], limit: int = TELEGRAM_LIMIT) -> list[str]:
    result = []
    for msg in messages:
        if len(msg) <= limit:
            result.append(msg)
        else:
            lines = msg.split("\n")
            chunk = []
            chunk_len = 0
            for line in lines:
                if chunk_len + len(line) + 1 > limit and chunk:
                    result.append("\n".join(chunk))
                    chunk = [line]
                    chunk_len = len(line)
                else:
                    chunk.append(line)
                    chunk_len += len(line) + 1
            if chunk:
                result.append("\n".join(chunk))
    return result


class TelegramPublisher:
    def __init__(self, bot_token: str, channel_id: str):
        self.bot = Bot(token=bot_token)
        self.channel_id = channel_id

    def _build_posts(self, vacancies: list) -> list[str]:
        if not vacancies:
            return []

        # Group by category
        by_cat = {}
        for v in vacancies:
            cat = _category(v[2])
            by_cat.setdefault(cat, []).append(v)

        # Sort categories by count (most first)
        sorted_cats = sorted(by_cat.keys(), key=lambda c: -len(by_cat[c]))

        lines = [f"<b>📋 Вакансии</b>  •  {len(vacancies)} новых\n"]

        for cat in sorted_cats:
            items = by_cat[cat]
            lines.append(f"\n{cat}  ({len(items)})")

            for v in items[:15]:  # Show up to 15 per category
                b = BRAND.get(v[1], {"icon": "▪️"})
                title = _t(v[2], 44)
                company = f"  {v[3]}" if v[3] else ""
                lines.append(f"  {b['icon']} <a href=\"{v[4]}\">{title}</a>{company}")

            if len(items) > 15:
                lines.append(f"  ...+{len(items)-15} ещё")

        lines.append(f"\n<i>{datetime.now().strftime('%d.%m %H:%M MSK')}</i>")

        full_text = "\n".join(lines)
        return _split_messages([full_text])

    def _build_report(self, vacancies: list, stats: dict) -> list[str]:
        if not vacancies:
            return ["📊 Сегодня новых вакансий не найдено."]

        date = datetime.now().strftime("%d.%m.%Y")

        # Group by category
        by_cat = {}
        for v in vacancies:
            cat = _category(v[2])
            by_cat.setdefault(cat, []).append(v)

        sorted_cats = sorted(by_cat.keys(), key=lambda c: -len(by_cat[c]))

        parts = []
        header = f"<b>📊 Итоги дня — {date}</b>\n\nВ базе: <b>{stats.get('total', 0)}</b>  •  Показано: <b>{len(vacancies)}</b>\n"

        for cat in sorted_cats:
            items = by_cat[cat]
            section = f"\n{cat}  ({len(items)})\n"

            for v in items[:10]:
                b = BRAND.get(v[1], {"icon": "▪️"})
                title = _t(v[2], 42)
                company = f" — {v[3]}" if v[3] else ""
                section += f"  {b['icon']} <a href=\"{v[4]}\">{title}</a>{company}\n"

            if len(items) > 10:
                section += f"  ...+{len(items)-10} ещё\n"

            parts.append(section)

        messages = []
        current = header
        for part in parts:
            if len(current) + len(part) > TELEGRAM_LIMIT:
                messages.append(current)
                current = part
            else:
                current += part
        if current:
            messages.append(current)

        return messages

    async def publish_hourly(self, vacancies: list) -> bool:
        if not vacancies:
            return False
        messages = self._build_posts(vacancies)
        published = 0
        for text in messages:
            for attempt in range(3):
                try:
                    await self.bot.send_message(
                        chat_id=self.channel_id, text=text,
                        parse_mode=ParseMode.HTML, disable_web_page_preview=True,
                    )
                    published += 1
                    await asyncio.sleep(2)
                    break
                except Exception as e:
                    if "429" in str(e):
                        wait = 36 * (attempt + 1)
                        logger.warning(f"Rate limited, waiting {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        logger.error(f"Error: {e}")
                        break
        return published > 0

    async def publish_daily(self, vacancies: list, stats: dict) -> bool:
        messages = self._build_report(vacancies, stats)
        for text in messages:
            try:
                await self.bot.send_message(
                    chat_id=self.channel_id, text=text,
                    parse_mode=ParseMode.HTML, disable_web_page_preview=True,
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error: {e}")
                return False
        return True

    async def test_connection(self) -> bool:
        try:
            me = await self.bot.get_me()
            logger.info(f"Bot: @{me.username}")
            await self.bot.send_message(
                chat_id=self.channel_id,
                text="✅ Бот запущен. Вакансии по категориям — каждый час.",
                parse_mode=ParseMode.HTML,
            )
            return True
        except Exception as e:
            logger.error(f"Failed: {e}")
            return False
