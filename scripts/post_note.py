from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import List

import httpx


def parse_tags(raw_tags: str) -> List[str]:
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a manual note to the Exocortex API")
    parser.add_argument("summary", help="Short summary for the note")
    parser.add_argument(
        "text",
        nargs="?",
        default="",
        help="Optional full text content for the note",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8081",
        help="Exocortex API base URL (default: http://localhost:8081)",
    )
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated tags to attach to the note",
    )
    parser.add_argument(
        "--source-system",
        default="manual_cli",
        help="Source system label for the note",
    )
    parser.add_argument(
        "--channel",
        default="note",
        help="Channel label for the note",
    )
    parser.add_argument(
        "--actor",
        default=None,
        help="Optional actor field (e.g. your name)",
    )
    parser.add_argument(
        "--direction",
        default=None,
        help="Optional direction field (e.g. outbound)",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="ISO8601 timestamp for the note (defaults to now in UTC)",
    )

    args = parser.parse_args()

    timestamp = args.timestamp or datetime.now(timezone.utc).isoformat()
    payload = {
        "timestamp": timestamp,
        "source_system": args.source_system,
        "channel": args.channel,
        "actor": args.actor,
        "direction": args.direction,
        "summary": args.summary,
        "content": {"text": args.text, "data": {}},
        "tags": parse_tags(args.tags),
        "links": {},
        "raw": {},
    }

    base_url = args.base_url.rstrip("/")
    response = httpx.post(f"{base_url}/events", json=payload, timeout=10)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
