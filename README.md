# Streaks
This is an AI Vibe Coding App
""" build it """
pyinstaller --name "FlameKeeper" --onefile --windowed --add-data "data.json;." --add-data "settings.json;." --icon="fire.ico" FlameKeeper.py
