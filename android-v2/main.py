"""
Job Monitor Bot v2.0 — Self-contained Android app
Bot runs inside the app, no Termux needed.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
import threading
import asyncio
import os
import sys

Window.clearcolor = (0.08, 0.08, 0.12, 1)


# ── Embedded Bot Logic ─────────────────────────────────
import aiohttp
import re
from datetime import datetime, time


def get_config():
    """Load or create default config."""
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path()
        except:
            base = '/sdcard'
        config_path = os.path.join(base, 'jobbot', 'config.yaml')
    else:
        config_path = os.path.expanduser('~/jobbot/config.yaml')

    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write('''telegram:
  bot_token: "YOUR_TOKEN"
  channel_id: "@your_channel"
search_queries:
  - "CIO"
  - "CTO"
  - "IT Director"
locations:
  hh:
    - "2"
  text:
    - "Saint Petersburg"
''')

    # Parse simple YAML
    config = {}
    with open(config_path, 'r') as f:
        content = f.read()

    # Simple parser
    current_section = None
    current_list = None
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line and not line.startswith('-'):
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if val:
                config[key] = val.strip('"').strip("'")
            else:
                current_section = key
                config[key] = {}
        elif line.startswith('-') and current_section:
            item = line[1:].strip().strip('"').strip("'")
            if isinstance(config.get(current_section), dict):
                if current_list not in config[current_section]:
                    config[current_section][current_list] = []
                config[current_section][current_list].append(item)
            elif isinstance(config.get(current_section), list):
                config[current_section].append(item)
        elif ':' in line:
            key, val = line.split(':', 1)
            current_list = key.strip()
            if current_section and isinstance(config.get(current_section), dict):
                config[current_section][current_list] = []

    return config_path, config


async def scrape_hh(queries, areas):
    """Scrape hh.ru vacancies."""
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile Safari/537.36'}

    async with aiohttp.ClientSession(headers=headers) as session:
        for query in queries[:3]:
            for area in areas[:1]:
                try:
                    url = f'https://hh.ru/search/vacancy?text={query}&area={area}'
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            # Simple regex extraction
                            titles = re.findall(r'<a[^>]*href="[^"]*/vacancy/(\d+)"[^>]*>([^<]+)</a>', html)
                            for vid, title in titles[:5]:
                                if len(title) > 5:
                                    results.append({
                                        'id': f'hh_{vid}',
                                        'source': 'hh',
                                        'title': title.strip(),
                                        'url': f'https://hh.ru/vacancy/{vid}'
                                    })
                except Exception as e:
                    pass

    # Deduplicate
    seen = set()
    return [r for r in results if r['id'] not in seen and not seen.add(r['id'])]


async def scrape_superjob(queries):
    """Scrape SuperJob."""
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile Safari/537.36'}

    async with aiohttp.ClientSession(headers=headers) as session:
        for query in queries[:3]:
            try:
                url = f'https://www.superjob.ru/vacancy/search/?keywords={query}'
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        titles = re.findall(r'<a[^>]*href="[^"]*/vakansii/[^"]*-(\d+)\.html"[^>]*>([^<]+)</a>', html)
                        for vid, title in titles[:5]:
                            if len(title) > 5:
                                results.append({
                                    'id': f'sj_{vid}',
                                    'source': 'superjob',
                                    'title': title.strip(),
                                    'url': f'https://www.superjob.ru/vakansii/{vid}.html'
                                })
            except:
                pass

    seen = set()
    return [r for r in results if r['id'] not in seen and not seen.add(r['id'])]


async def scrape_habr(queries):
    """Scrape Habr Career."""
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile Safari/537.36'}

    async with aiohttp.ClientSession(headers=headers) as session:
        for query in queries[:3]:
            try:
                url = f'https://career.habr.com/vacancies?q={query}'
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        titles = re.findall(r'href="/vacancies/(\d+)"[^>]*>([^<]+)</a>', html)
                        for vid, title in titles[:5]:
                            if len(title) > 5:
                                results.append({
                                    'id': f'habr_{vid}',
                                    'source': 'habr',
                                    'title': title.strip(),
                                    'url': f'https://career.habr.com/vacancies/{vid}'
                                })
            except:
                pass

    seen = set()
    return [r for r in results if r['id'] not in seen and not seen.add(r['id'])]


def format_post(vacancies):
    """Format vacancies for Telegram."""
    if not vacancies:
        return None

    lines = [f"📋 <b>Vacancies</b> • {len(vacancies)}\n"]

    # Group by source
    by_source = {}
    for v in vacancies:
        src = v.get('source', 'other')
        by_source.setdefault(src, []).append(v)

    icons = {'hh': '🔴', 'superjob': '💎', 'habr': '⚡'}

    for src, items in by_source.items():
        icon = icons.get(src, '▪️')
        lines.append(f"\n{icon} <b>{src}</b> ({len(items)})")
        for v in items[:10]:
            title = v['title'][:50]
            lines.append(f"  <a href=\"{v['url']}\">{title}</a>")

    lines.append(f"\n<i>{datetime.now().strftime('%d.%m %H:%M')}</i>")
    return "\n".join(lines)


# ── Telegram Sender ────────────────────────────────────

async def send_telegram(token, channel_id, text):
    """Send message to Telegram."""
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={
            'chat_id': channel_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }) as resp:
            return resp.status == 200


# ── Main Bot Runner ────────────────────────────────────

class BotRunner:
    def __init__(self):
        self.running = False
        self.log_callback = None
        self.config_path, self.config = get_config()

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        print(msg)

    async def run_cycle(self):
        """Run one monitoring cycle."""
        token = self.config.get('telegram', {}).get('bot_token', '')
        channel = self.config.get('telegram', {}).get('channel_id', '')

        if not token or token == 'YOUR_TOKEN':
            self.log('❌ Set bot_token in config!')
            return

        self.log('🔍 Scraping hh.ru...')
        hh_results = await scrape_hh(
            self.config.get('search_queries', ['CIO']),
            self.config.get('locations', {}).get('hh', ['2'])
        )
        self.log(f'  hh.ru: {len(hh_results)}')

        self.log('🔍 Scraping SuperJob...')
        sj_results = await scrape_superjob(
            self.config.get('search_queries', ['CIO'])
        )
        self.log(f'  SuperJob: {len(sj_results)}')

        self.log('🔍 Scraping Habr...')
        habr_results = await scrape_habr(
            self.config.get('search_queries', ['CIO'])
        )
        self.log(f'  Habr: {len(habr_results)}')

        all_results = hh_results + sj_results + habr_results
        self.log(f'📊 Total: {len(all_results)}')

        if all_results:
            post = format_post(all_results)
            if post:
                self.log('📤 Sending to Telegram...')
                success = await send_telegram(token, channel, post)
                if success:
                    self.log(f'✅ Published {len(all_results)} vacancies!')
                else:
                    self.log('❌ Failed to send')

    def start(self):
        """Start the bot."""
        if self.running:
            return
        self.running = True
        self.log('🚀 Starting bot...')

        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def main():
                while self.running:
                    try:
                        await self.run_cycle()
                    except Exception as e:
                        self.log(f'❌ Error: {e}')
                    await asyncio.sleep(3600)  # 1 hour

            loop.run_until_complete(main())

        threading.Thread(target=run_loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.log('⏹ Bot stopped')


# ── Android App UI ─────────────────────────────────────

class JobBotApp(App):
    def build(self):
        self.title = 'Job Monitor Bot v2'
        self.bot = BotRunner()
        self.bot.log_callback = self.add_log

        root = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Title
        root.add_widget(Label(
            text='JOB MONITOR',
            font_size=32,
            size_hint_y=None,
            height=50,
            bold=True
        ))

        # Status
        self.status = Label(
            text='STOPPED',
            font_size=22,
            size_hint_y=None,
            height=40,
            color=(1, 0.4, 0.4, 1)
        )
        root.add_widget(self.status)

        # Start button
        btn_start = Button(
            text='START',
            font_size=26,
            size_hint_y=None,
            height=80,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_start.bind(on_press=self.start_bot)
        root.add_widget(btn_start)

        # Stop button
        btn_stop = Button(
            text='STOP',
            font_size=26,
            size_hint_y=None,
            height=80,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_stop.bind(on_press=self.stop_bot)
        root.add_widget(btn_stop)

        # Config path
        root.add_widget(Label(
            text=f'Config: {self.bot.config_path}',
            font_size=12,
            size_hint_y=None,
            height=25,
            color=(0.6, 0.6, 0.6, 1)
        ))

        # Log
        root.add_widget(Label(
            text='Log:',
            font_size=16,
            size_hint_y=None,
            height=25,
            bold=True
        ))

        scroll = ScrollView()
        self.log_label = Label(
            text='Ready. Configure config.yaml and press START.',
            font_size=13,
            size_hint_y=None,
            height=200,
            text_size=(Window.width - 40, None),
            halign='left',
            valign='top'
        )
        self.log_label.bind(size=self.log_label.setter('text_size'))
        scroll.add_widget(self.log_label)
        root.add_widget(scroll)

        return root

    def start_bot(self, *args):
        self.bot.start()
        self.status.text = 'RUNNING'
        self.status.color = (0.3, 1, 0.3, 1)

    def stop_bot(self, *args):
        self.bot.stop()
        self.status.text = 'STOPPED'
        self.status.color = (1, 0.4, 0.4, 1)

    def add_log(self, msg):
        Clock.schedule_once(lambda dt: self._update_log(msg), 0)

    def _update_log(self, msg):
        current = self.log_label.text
        self.log_label.text = f"{current}\n{msg}"[-500:]


if __name__ == '__main__':
    JobBotApp().run()
