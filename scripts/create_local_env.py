"""Create a private local .env without replacing an existing file or printing secrets."""

import os
import secrets
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    example = (root / ".env.example").read_text()
    content = example.replace("replace-with-a-generated-secret", secrets.token_urlsafe(64))
    content = content.replace(
        "replace-with-a-generated-database-password", secrets.token_urlsafe(48)
    )
    try:
        descriptor = os.open(root / ".env", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit("An existing .env was preserved. Review it before proceeding.") from None
    with os.fdopen(descriptor, "w") as env_file:
        env_file.write(content)
    print("Created .env with private file permissions. Secrets were not printed.")


if __name__ == "__main__":
    main()
