import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exocortex.db import init_db  # noqa: E402


if __name__ == "__main__":
    init_db()
    print("Database initialized at data/events.db")
