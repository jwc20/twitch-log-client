from nanodjango import Django
from django.db import models

from dotenv import load_dotenv
import os

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
    username = models.CharField(max_length=100, blank=True, null=True)
    message_text = models.TextField(blank=True, null=True)
    message_type = models.CharField(max_length=100)


@app.route("/")
def index(request):
    return app.render(
        request,
        "index.html",
        {
            "messages": ChatMessage.objects.raw(
                "SELECT id, timestamp, username, message_text FROM tlc_chatmessage ORDER BY created_at DESC LIMIT 100"
            )
        },
    )
