from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
import os
import subprocess
import threading

Window.clearcolor = (0.1, 0.1, 0.15, 1)


class BotManagerApp(App):
    def build(self):
        self.title = 'Job Monitor Bot'

        root = BoxLayout(orientation='vertical', padding=25, spacing=20)

        # Title
        root.add_widget(Label(
            text='JOB MONITOR',
            font_size=36,
            size_hint_y=None,
            height=60,
            bold=True
        ))

        # Status
        self.status = Label(
            text='OFFLINE',
            font_size=24,
            size_hint_y=None,
            height=50,
            color=(1, 0.3, 0.3, 1)
        )
        root.add_widget(self.status)

        # Big buttons
        btn_start = Button(
            text='START BOT',
            font_size=28,
            size_hint_y=None,
            height=100,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_start.bind(on_press=self.start_bot)
        root.add_widget(btn_start)

        btn_stop = Button(
            text='STOP BOT',
            font_size=28,
            size_hint_y=None,
            height=100,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_stop.bind(on_press=self.stop_bot)
        root.add_widget(btn_stop)

        btn_config = Button(
            text='OPEN SETTINGS',
            font_size=28,
            size_hint_y=None,
            height=100,
            background_color=(0.2, 0.5, 0.8, 1)
        )
        btn_config.bind(on_press=self.open_settings)
        root.add_widget(btn_config)

        btn_status = Button(
            text='CHECK STATUS',
            font_size=28,
            size_hint_y=None,
            height=100,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_status.bind(on_press=self.check_status)
        root.add_widget(btn_status)

        # Log
        self.log = Label(
            text='Ready to start',
            font_size=16,
            size_hint_y=None,
            height=80
        )
        root.add_widget(self.log)

        return root

    def start_bot(self, *args):
        def run():
            try:
                self.log.text = 'Starting bot...'
                # Try to start bot process
                bot_dir = os.path.expanduser('~/job-monitor-bot')
                if os.path.exists(bot_dir):
                    subprocess.Popen(
                        ['python3', 'main.py'],
                        cwd=bot_dir,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.log.text = 'Bot started!'
                    self.status.text = 'ONLINE'
                    self.status.color = (0.3, 1, 0.3, 1)
                else:
                    self.log.text = 'Bot not installed. Run setup first.'
            except Exception as e:
                self.log.text = f'Error: {e}'
        threading.Thread(target=run, daemon=True).start()

    def stop_bot(self, *args):
        try:
            subprocess.run(['pkill', '-f', 'python3 main.py'], capture_output=True)
            self.log.text = 'Bot stopped'
            self.status.text = 'OFFLINE'
            self.status.color = (1, 0.3, 0.3, 1)
        except Exception as e:
            self.log.text = f'Error: {e}'

    def check_status(self, *args):
        try:
            result = subprocess.run(['pgrep', '-f', 'python3 main.py'], capture_output=True)
            if result.returncode == 0:
                self.status.text = 'ONLINE'
                self.status.color = (0.3, 1, 0.3, 1)
                self.log.text = 'Bot is running'
            else:
                self.status.text = 'OFFLINE'
                self.status.color = (1, 0.3, 0.3, 1)
                self.log.text = 'Bot is not running'
        except:
            self.log.text = 'Cannot check status'

    def open_settings(self, *args):
        self.log.text = f'Config: ~/job-monitor-bot/config.yaml'


if __name__ == '__main__':
    BotManagerApp().run()
