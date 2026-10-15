"""Isolated production-container smoke. Supply only the documented fake QA environment."""

import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

assert os.getuid() != 0
assert not any((Path("/app") / name).exists() for name in (".env", ".git", "node_modules", ".qa"))
assert Path("staticfiles/staticfiles.json").is_file()
assert not any(path.name.startswith("C:") for path in Path("/app").iterdir())
assert not any("maison-lighthouse" in path.name for path in Path("/app").iterdir())
server = subprocess.Popen(
    [
        "uv",
        "run",
        "--no-sync",
        "--no-dev",
        "gunicorn",
        "--config",
        "deploy/gunicorn.conf.py",
        "config.wsgi:application",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)


def fetch(path):
    request = Request(
        "http://127.0.0.1:8000" + path, headers={"Host": "localhost", "X-Forwarded-Proto": "https"}
    )
    return urlopen(request, timeout=5)


try:
    for _attempt in range(50):
        try:
            with fetch("/healthz/") as response:
                assert json.loads(response.read()) == {"status": "ok"}
            break
        except URLError:
            time.sleep(0.1)
    else:
        raise AssertionError("Gunicorn did not start.")
    with fetch("/demo/") as response:
        html = response.read().decode()
        assert response.status == 200
        assert "noindex" in response.headers["X-Robots-Tag"]
        assert "https://media.example.net" in response.headers["Content-Security-Policy"]
        assert "unsafe-inline" not in response.headers["Content-Security-Policy"]
    stylesheet = re.search(r'<link rel="stylesheet" href="([^"]+)"', html).group(1)
    with fetch(stylesheet) as response:
        assert ".shopping-layout" in response.read().decode()
        assert "immutable" in response.headers["Cache-Control"]
    print(
        "Container smoke passed: non-root uv/Gunicorn, health, disclosure/CSP, "
        "hashed CSS and clean image context."
    )
finally:
    server.terminate()
    _, errors = server.communicate(timeout=15)
    if server.returncode not in (0, -15):
        print(errors.decode())
