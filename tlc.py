from nanodjango import Django


app = Django(
    SQLITE_DATABASE="tlc.sqlite3",
    MIGRATIONS_DIR="tlc_migrations",
)


@app.route("/")
def index(request):
    return app.render(request, "hello.html")



app.templates = {
    "hello.html": """
<!DOCTYPE html>
<html>
<head><title>Index Page</title></head>
<body>
    <h1>Index Page</h1>
</body>
</html>
""".strip(),
}

