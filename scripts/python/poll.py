import time
import sqlite3
from datetime import datetime
import re

import os
from pathlib import Path

chat_message_pattern = r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.+)$"

username = "cjw"
channel_name = "sodapoppin"
mac_directory = f"/Users/{username}/Library/Application Support/chatterino/Logs/Twitch/Channels/{channel_name}/"

most_recent_log_file = max(Path(mac_directory).iterdir(), key=os.path.getmtime).name

# for mac m1
filename = mac_directory + most_recent_log_file

# for windows
# TODO


def store_db(message):
    created_at = datetime.now().isoformat()
    timestamp = message.group(1)
    username = message.group(2)
    message_text = message.group(3)
    cursor.execute(
        "INSERT INTO chat_messages (created_at, timestamp, channel_name, username, message_text) VALUES (?, ?, ?, ?, ?)",
        (created_at, timestamp, channel_name, username, message_text),
    )
    conn.commit()
    # print(f"Stored: {line.strip()}")


def poll_and_store_db(filename, poll_interval=0.1):
    with open(filename, "r", encoding="utf-8") as file:
        file.seek(0, 2)
        while True:
            line = file.readline()
            if line:
                message = line.strip()
                match = re.match(chat_message_pattern, message)
                if match:
                    store_db(match)
            else:
                time.sleep(poll_interval)


if "__main__" == __name__:
    try:
        conn = sqlite3.connect("chat_logs.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                timestamp TEXT,
                channel_name TEXT,
                username TEXT,
                message_text TEXT
            )
        """
        )
        conn.commit()
        poll_and_store_db(filename)
    except KeyboardInterrupt:
        print("\nStopping...")
        conn.close()
