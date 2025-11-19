from nanodjango import Django
from django.db import models
from django.utils import timezone

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import re

load_dotenv()

chat_message_pattern = r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.+)$"

app = Django(
    # ALLOWED_HOSTS=["localhost", "127.0.0.1", "my.example.com"],
    # SECRET_KEY=os.environ["SECRET_KEY"],
    # ADMIN_URL="admin/",
    SQLITE_DATABASE=os.getenv("SQLITE_DATABASE", "db.sqlite3"),
    MIGRATIONS_DIR=os.getenv("MIGRATIONS_DIR", "migrations"),
    DEBUG=os.getenv("DEBUG", False),
)


class ChatMessage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    channel_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    message = models.TextField()


@app.route("/")
def index(request):
    return app.render(request, "index.html")


@app.route("/add_example_data/")
def add_example_data(request):
    filename = Path("./example/sodapoppin-316092067675.log")
    with open(filename, "r", encoding="utf-8") as f:
        data = [line for line in f]
        stream_date = data[0].split("at ")[1].strip().split(" ")[0]
        print(f"stream date: {stream_date}")

        try:
            ChatMessage.objects.all().delete()
            print("Adding example data...")
            print(f"started at {timezone.now().isoformat()}")
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
                        ChatMessage.objects.create(
                            created_at=timezone.now(),
                            timestamp=aware_timestamp,
                            channel_name="sodapoppin",
                            username=match.group(2),
                            message=match.group(3),
                        )
                    except Exception as e:
                        print(e)

        except Exception as e:
            print(e)

    print(f"finished at {timezone.now().isoformat()}")
    return app.render(request, "add_example_data_done.html")


app.templates = {
    "index.html": """
<!DOCTYPE html>
<html>
<head><title>Index Page</title></head>
<body>
    <h1>Index Page</h1>
</body>
</html>
""".strip(),
    "add_example_data_done.html": """
<!DOCTYPE html>
<html>
<body>
    <h1>Completed adding example data</h1>
</body>
</html>
""".strip(),
}
