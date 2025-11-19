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


filename = Path("./example/sodapoppin-316092067675.log")


chat_message_pattern = r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.+)$"

patterns = {
    "stream_live": re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+is live!$"),
    "sub_basic": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+subscribed at Tier (\d+)\.$"
    ),
    "sub_prime_basic": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+subscribed with Prime\.$"
    ),
    "sub_with_months": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+subscribed (?:at Tier (\d+)|with Prime)\.\s+They\'ve subscribed for (\d+) months?!$"
    ),
    "sub_with_streak": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+subscribed (?:at Tier (\d+)|with Prime)\.\s+They\'ve subscribed for (\d+) months?, currently on a (\d+) month streak!$"
    ),
    "sub_advance": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+subscribed at Tier (\d+) for (\d+) months? in advance(?:, reaching (\d+) months cumulatively so far)?!$"
    ),
    "gift_announcement": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+is gifting (\d+) Tier (\d+) Subs? to (\w+)\'s community!\s+They\'ve gifted a total of (\d+) in the channel!$"
    ),
    "gift_individual": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+gifted a Tier (\d+) sub to (\w+)!(?:\s+They have given (\d+) Gift Subs in the channel!)?$"
    ),
    "gift_first": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+gifted a Tier (\d+) sub to (\w+)!\s+This is their first Gift Sub in the channel!$"
    ),
    "anon_gift_announcement": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+AnAnonymousGifter is gifting (\d+) Tier (\d+) Subs? to (\w+)\'s community!$"
    ),
    "anon_gift_individual": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+An anonymous user gifted(?: (\d+) months? of)? a Tier (\d+) sub to (\w+)!$"
    ),
    "timeout": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+has been timed out for (.+)\.$"
    ),
    "permanent_ban": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+has been permanently banned\.$"
    ),
    "raid": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\d+) raiders? from (\w+) have joined!$"
    ),
    "room_mode_on": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+This room is now in (.+) mode\.$"
    ),
    "room_mode_off": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+This room is no longer in (.+) mode\.$"
    ),
    "announcement": re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s+Announcement$"),
    "chat_message": re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.+)$"),
    "chat_message_foreign": re.compile(
        r"^\[(\d{2}:\d{2}:\d{2})\]\s+([\w\u0080-\uFFFF]+)\s+(\w+):\s+(.+)$"
    ),
}

pattern_counts = {
    "stream_live": 0,
    "sub_basic": 0,
    "sub_prime_basic": 0,
    "sub_with_months": 0,
    "sub_with_streak": 0,
    "sub_advance": 0,
    "gift_announcement": 0,
    "gift_individual": 0,
    "gift_first": 0,
    "anon_gift_announcement": 0,
    "anon_gift_individual": 0,
    "timeout": 0,
    "permanent_ban": 0,
    "raid": 0,
    "room_mode_on": 0,
    "room_mode_off": 0,
    "announcement": 0,
    "chat_message": 0,
    "chat_message_foreign": 0,
    "no_match": 0,
}


# Username extraction mapping: pattern_name -> list of indices where usernames are
username_indices = {
    # Stream Events
    "stream_live": [1],  # streamer name
    "raid": [2],  # raider channel name
    "announcement": [],  # no username
    # Subscriptions (subscriber is always at index 1)
    "sub_basic": [1],
    "sub_prime_basic": [1],
    "sub_with_months": [1],
    "sub_with_streak": [1],
    "sub_advance": [1],
    # Gift Subs (gifter, recipient)
    "gift_announcement": [1, 4],  # gifter, channel owner
    "gift_individual": [1, 3],  # gifter, recipient
    "gift_first": [1, 3],  # gifter, recipient
    "anon_gift_announcement": [3],  # channel owner only (anonymous gifter)
    "anon_gift_individual": [2],  # recipient only (anonymous gifter)
    # Moderation
    "timeout": [1],  # user who got timed out
    "permanent_ban": [1],  # user who got banned
    # Room modes
    "room_mode_on": [],  # no username
    "room_mode_off": [],  # no username
    # Chat messages (adjust based on your actual chat patterns)
    "chat_message": [1],  # assuming username at index 1
    "chat_message_foreign": [1, 2],  # display name, username
}


non_chat_patterns = [
    "stream_live",
    "sub_basic",
    "sub_prime_basic",
    "sub_with_months",
    "sub_with_streak",
    "sub_advance",
    "gift_announcement",
    "gift_individual",
    "gift_first",
    "anon_gift_announcement",
    "anon_gift_individual",
    "timeout",
    "permanent_ban",
    "raid",
    "room_mode_on",
    "room_mode_off",
    "announcement",
]


def extract_non_matching_message_to_file():
    try:
        with (
            open(filename, "r", encoding="utf-8") as r,
            open("non_matching_messages.txt", "w", encoding="utf-8") as w,
        ):
            data = [line for line in r][1:]

            for item in data:
                message = item.strip()
                matched = False

                for pattern_name, pattern in patterns.items():
                    if pattern.match(message):
                        pattern_counts[pattern_name] += 1
                        matched = True
                        break

                if not matched:
                    pattern_counts["no_match"] += 1
                    w.write(message)
                    w.write("\n")

    except Exception as e:
        print(f"Error: {e}")

    print(pattern_counts)

    return




def main():
    extract_non_matching_message_to_file()


if "__main__" == __name__:
    main()
    conn.close()