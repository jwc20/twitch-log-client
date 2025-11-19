from django.utils import timezone
from django.conf import settings

from pathlib import Path
from datetime import datetime
import re
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()


conn = sqlite3.connect(os.getenv("SQLITE_DATABASE", "tlc.sqlite3"))
cursor = conn.cursor()

settings.configure(USE_TZ=True, TIME_ZONE="UTC")
chat_message_pattern = r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.+)$"
chat_message_with_foreign_username_pattern = r"^\[(\d{2}:\d{2}:\d{2})\]\s+([\w\u0080-\uFFFF]+)\s+(\w+):\s+(.+)$"

filename = Path("./example/sodapoppin-316092067675.log")








def store_db(created_at, timestamp, channel_name, username, message_text):
    cursor.execute(
        "INSERT INTO tlc_chatmessage (created_at, timestamp, channel_name, username, message) VALUES (?, ?, ?, ?, ?)",
        (created_at, timestamp, channel_name, username, message_text),
    )
    conn.commit()


def add_example_data():
    print(f"Adding example data, started at {timezone.now().isoformat()}")
    with open(filename, "r", encoding="utf-8") as f:
        data = [line for line in f]
        stream_date = data[0].split("at ")[1].strip().split(" ")[0]
        print(f"stream date: {stream_date}")

        try:
            for item in data[1:]:
                message = item.strip()
                match = re.match(chat_message_pattern, message)
                if match:
                    timestamp_str = f"{stream_date} {match.group(1)}"
                    naive_timestamp = datetime.strptime(
                        timestamp_str, "%Y-%m-%d %H:%M:%S"
                    )
                    aware_timestamp = timezone.make_aware(naive_timestamp)
                    try:
                        store_db(
                            created_at=timezone.now(),
                            timestamp=aware_timestamp,
                            channel_name="sodapoppin",
                            username=match.group(2),
                            message_text=match.group(3),
                        )
                    except Exception as e:
                        print(e)
                else:
                    print(f"Failed to match: {message}")

        except Exception as e:
            print(e)

    print(f"finished at {timezone.now().isoformat()}")
    return


def extract_non_matching_message_to_file():
    non_matching_message_count = 0
    foreign_username_count = 0
    
    try:
        with (
            open(filename, "r", encoding="utf-8") as r,
            open("non_matching_messages.txt", "w", encoding="utf-8") as w,
        ):
            data = [line for line in r][1:]
            try:
                for item in data:
                    message = item.strip()
                    match = re.match(chat_message_pattern, message)
                    
                    if not match:
                        non_matching_message_count += 1
                        # print(message)

                        foreign_username_match = re.match(chat_message_with_foreign_username_pattern, message)

                        if foreign_username_match:
                            foreign_username_count += 1
                            continue

                        
                        w.write(message)
                        w.write("\n")
                        
            except Exception as e:
                print(e)

    except Exception as e:
        print(e)

    print(" ")
    print(f"non_matching_message_count: {non_matching_message_count}")
    print(f"foreign_username_count: {foreign_username_count}")

    d = non_matching_message_count - foreign_username_count

    print(d)
    
    return


def delete_all():
    print("Deleting all data...")
    cursor.execute("delete from tlc_chatmessage")
    conn.commit()
    return


def main():
    # delete_all()
    # add_example_data()
    extract_non_matching_message_to_file()
    


if "__main__" == __name__:
    main()
    conn.close()
