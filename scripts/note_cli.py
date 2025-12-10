from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import List

import requests


def parse_tags(tag_args: List[str]) -> List[str]:
    tags: List[str] = []
    for tag in tag_args:
        tags.extend(part.strip().lower() for part in tag.split(",") if part.strip())
    return tags


def build_payload(args: argparse.Namespace) -> dict:
    tags = parse_tags(args.tag or [])
    now_iso = datetime.utcnow().isoformat()
    summary = args.summary or args.note[:80]

    return {
        "timestamp": now_iso,
        "source_system": args.source_system,
        "channel": args.channel,
        "actor": args.actor,
        "direction": args.direction,
        "summary": summary,
        "content": {"text": args.note, "data": {}},
        "tags": tags,
        "links": {},
        "raw": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a manual note to the Exocortex API")
    parser.add_argument("note", help="Full text of the note to store")
    parser.add_argument("--url", default="http://localhost:8000/events", help="Exocortex /events endpoint")
    parser.add_argument("--summary", help="Optional short summary (defaults to first 80 characters)")
    parser.add_argument("--source-system", dest="source_system", default="manual_note", help="Value for source_system field")
    parser.add_argument("--channel", default="note", help="Value for channel field")
    parser.add_argument("--actor", default="matt", help="Actor associated with the event")
    parser.add_argument("--direction", choices=["inbound", "outbound", "system"], help="Direction of the event")
    parser.add_argument(
        "--tag",
        action="append",
        help="Add a tag (can be provided multiple times or as comma-separated values)",
    )

    args = parser.parse_args()
    payload = build_payload(args)

    response = requests.post(args.url, json=payload, timeout=10)
    if response.ok:
        data = response.json()
        print(f"Saved note as event {data.get('id')}")
        return 0

    print(f"Failed to save note: {response.status_code} - {response.text}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
