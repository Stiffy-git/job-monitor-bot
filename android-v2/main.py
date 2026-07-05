"""Job Monitor Bot v2.1 — Fixed for Android"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import os

Window.clearcolor = (0.08, 0.08, 0.12, 1)


class JobBotApp(App):
    def build(self):
        self.title = 'Job Monitor Bot v2'
        self.running = False

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

        # Config info
        root.add_widget(Label(
            text='Config: /sdcard/jobbot/config.yaml',
            font_size=12,
            size_hint_y=None,
            height=25,
            color=(0.5, 0.5, 0.5, 1)
        ))

        # Log header
        root.add_widget(Label(
            text='Log:',
            font_size=16,
            size_hint_y=None,
            height=25,
            bold=True
        ))

        # Log scroll
        scroll = ScrollView()
        self.log_label = Label(
            text='Ready. Edit config.yaml and press START.',
            font_size=13,
            size_hint_y=None,
            height=300,
            text_size=(Window.width - 40, None),
            halign='left',
            valign='top'
        )
        self.log_label.bind(size=self.log_label.setter('text_size'))
        scroll.add_widget(self.log_label)
        root.add_widget(scroll)

        return root

    def start_bot(self, *args):
        if self.running:
            return
        self.running = True
        self.status.text = 'RUNNING'
        self.status.color = (0.3, 1, 0.3, 1)
        self.add_log('Starting bot...')

        def run_bot():
            try:
                import urllib.request
                import urllib.parse
                import json
                import re
                import time

                # Load config
                config_path = '/sdcard/jobbot/config.yaml'
                if not os.path.exists(config_path):
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)
                    with open(config_path, 'w') as f:
                        f.write('bot_token: YOUR_TOKEN\nchannel_id: @channel\n')

                with open(config_path) as f:
                    config = {}
                    for line in f:
                        line = line.strip()
                        if ':' in line and not line.startswith('#'):
                            k, v = line.split(':', 1)
                            v = v.strip().strip('"').strip("'")
                            if v:
                                config[k.strip()] = v

                token = config.get('bot_token', '')
                channel = config.get('channel_id', '')

                if not token or token == 'YOUR_TOKEN':
                    self.add_log('ERROR: Set bot_token in config!')
                    self.running = False
                    self.status.text = 'ERROR'
                    self.status.color = (1, 0.4, 0.4, 1)
                    return

                self.add_log(f'Token: {token[:10]}...')
                self.add_log(f'Channel: {channel}')

                # Scrape loop
                while self.running:
                    self.add_log('--- Checking vacancies ---')
                    all_results = []

                    # hh.ru
                    queries = ['CIO', 'CTO', 'IT Director']
                    for q in queries:
                        if not self.running:
                            break
                        self.add_log(f'Searching hh.ru: {q}')
                        try:
                            url = f'https://hh.ru/search/vacancy?text={urllib.parse.quote(q)}&area=2'
                            req = urllib.request.Request(url, headers={
                                'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile Safari/537.36'
                            })
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                html = resp.read().decode('utf-8', errors='ignore')
                            matches = re.findall(r'href="[^"]*?/vacancy/(\d+)"[^>]*>([^<]{5,60})</a>', html)
                            for vid, title in matches[:5]:
                                all_results.append({
                                    'source': 'hh',
                                    'title': title.strip(),
                                    'url': f'https://hh.ru/vacancy/{vid}'
                                })
                            self.add_log(f'  hh.ru: found {len(matches)} matches')
                        except Exception as e:
                            self.add_log(f'  hh.ru error: {str(e)[:50]}')

                    # SuperJob
                    for q in queries[:2]:
                        if not self.running:
                            break
                        self.add_log(f'Searching SuperJob: {q}')
                        try:
                            url = f'https://superjob.ru/vacancy/search/?keywords={urllib.parse.quote(q)}'
                            req = urllib.request.Request(url, headers={
                                'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile Safari/537.36'
                            })
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                html = resp.read().decode('utf-8', errors='ignore')
                            matches = re.findall(r'href="[^"]*?-(\d+)\.html"[^>]*>([^<]{5,60})</a>', html)
                            for vid, title in matches[:5]:
                                all_results.append({
                                    'source': 'superjob',
                                    'title': title.strip(),
                                    'url': f'https://superjob.ru/vakansii/{vid}.html'
                                })
                            self.add_log(f'  SuperJob: found {len(matches)} matches')
                        except Exception as e:
                            self.add_log(f'  SuperJob error: {str(e)[:50]}')

                    # Habr
                    for q in queries[:2]:
                        if not self.running:
                            break
                        self.add_log(f'Searching Habr: {q}')
                        try:
                            url = f'https://career.habr.com/vacancies?q={urllib.parse.quote(q)}'
                            req = urllib.request.Request(url, headers={
                                'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile Safari/537.36'
                            })
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                html = resp.read().decode('utf-8', errors='ignore')
                            matches = re.findall(r'href="/vacancies/(\d+)"[^>]*>([^<]{5,60})</a>', html)
                            for vid, title in matches[:5]:
                                all_results.append({
                                    'source': 'habr',
                                    'title': title.strip(),
                                    'url': f'https://career.habr.com/vacancies/{vid}'
                                })
                            self.add_log(f'  Habr: found {len(matches)} matches')
                        except Exception as e:
                            self.add_log(f'  Habr error: {str(e)[:50]}')

                    # Deduplicate
                    seen = set()
                    unique = []
                    for r in all_results:
                        key = r['url']
                        if key not in seen:
                            seen.add(key)
                            unique.append(r)

                    self.add_log(f'Total unique: {len(unique)}')

                    # Send to Telegram
                    if unique and token and channel:
                        icons = {'hh': '🔴', 'superjob': '💎', 'habr': '⚡'}
                        text = f'📋 <b>Vacancies</b> • {len(unique)}\n'
                        by_src = {}
                        for v in unique:
                            by_src.setdefault(v['source'], []).append(v)
                        for src, items in by_src.items():
                            text += f'\n{icons.get(src, "▪")} <b>{src}</b> ({len(items)})\n'
                            for v in items[:10]:
                                text += f'  <a href="{v["url"]}">{v["title"][:45]}</a>\n'

                        self.add_log('Publishing to Telegram...')
                        try:
                            data = urllib.parse.urlencode({
                                'chat_id': channel,
                                'text': text,
                                'parse_mode': 'HTML',
                                'disable_web_page_preview': 'true'
                            }).encode()
                            req = urllib.request.Request(
                                f'https://api.telegram.org/bot{token}/sendMessage',
                                data=data
                            )
                            with urllib.request.urlopen(req, timeout=10) as resp:
                                if resp.status == 200:
                                    self.add_log(f'Published {len(unique)} vacancies!')
                                else:
                                    self.add_log('Failed to publish')
                        except Exception as e:
                            self.add_log(f'Telegram error: {str(e)[:50]}')
                    else:
                        self.add_log('No results to publish')

                    # Wait 1 hour
                    self.add_log('Waiting 1 hour...')
                    for i in range(60):
                        if not self.running:
                            break
                        time.sleep(60)

                self.add_log('Bot stopped')
            except Exception as e:
                self.add_log(f'FATAL: {str(e)}')
                self.running = False
                self.status.text = 'ERROR'
                self.status.color = (1, 0.4, 0.4, 1)

        threading.Thread(target=run_bot, daemon=True).start()

    def stop_bot(self, *args):
        self.running = False
        self.status.text = 'STOPPED'
        self.status.color = (1, 0.4, 0.4, 1)
        self.add_log('Stopping...')

    def add_log(self, msg):
        Clock.schedule_once(lambda dt: self._log(msg), 0)

    def _log(self, msg):
        from datetime import datetime
        t = datetime.now().strftime('%H:%M')
        current = self.log_label.text
        self.log_label.text = f'[{t}] {msg}\n{current}'[:1000]


if __name__ == '__main__':
    JobBotApp().run()
