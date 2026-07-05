"""Job Monitor Bot v2.2 — Minimal stable version"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window


class JobBotApp(App):
    def build(self):
        self.title = 'Job Monitor Bot'
        Window.clearcolor = (0.1, 0.1, 0.15, 1)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        layout.add_widget(Label(
            text='JOB MONITOR',
            font_size=32,
            size_hint_y=None,
            height=50,
            bold=True
        ))

        layout.add_widget(Label(
            text='STOPPED',
            font_size=22,
            size_hint_y=None,
            height=40,
            color=(1, 0.4, 0.4, 1)
        ))

        btn1 = Button(
            text='START BOT',
            font_size=28,
            size_hint_y=None,
            height=90,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        layout.add_widget(btn1)

        btn2 = Button(
            text='STOP BOT',
            font_size=28,
            size_hint_y=None,
            height=90,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        layout.add_widget(btn2)

        btn3 = Button(
            text='SETTINGS',
            font_size=28,
            size_hint_y=None,
            height=90,
            background_color=(0.2, 0.5, 0.8, 1)
        )
        layout.add_widget(btn3)

        layout.add_widget(Label(
            text='Bot will be added in next update',
            font_size=14,
            size_hint_y=None,
            height=30
        ))

        return layout


if __name__ == '__main__':
    JobBotApp().run()
