"""CLI tool to post manual notes to the Exocortex API."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import List, Optional

import requests


def parse_tags(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    # Allow comma-separated tags or repeated --tag flags.
    tags: List[str] = []
    for part in raw.split(","):
        cleaned = part.strip()
        if cleaned:
            tags.append(cleaned)
    return tags


def build_payload(args: argparse.Namespace) -> dict:
    return {
        "timestamp": (args.timestamp or datetime.utcnow().isoformat()),
        "source_system": args.source_system,
        "channel": args.channel,
        "actor": args.actor,
        "direction": args.direction,
        "summary": args.summary,
        "content": {
            "text": args.text,
            "data": {},
        },
        "tags": parse_tags(args.tags),
        "links": {
            "external_url": None,
            "app": None,
        },
        "raw": {},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a manual note to Exocortex")
    parser.add_argument(
        "summary",
        help="Short summary for the event (e.g. 'Walk idea: voice UI')",
    )
    parser.add_argument(
        "--text",
        help="Optional long-form text content for the note",
    )
    parser.add_argument(
        "--tags",
        help="Comma-separated tags (e.g. 'exo,idea,walk')",
    )
    parser.add_argument(
        "--timestamp",
        help="ISO8601 timestamp; defaults to now (UTC)",
    )
    parser.add_argument(
        "--source-system",
        default="manual_pc",
        dest="source_system",
        help="Source system identifier (default: manual_pc)",
    )
    parser.add_argument(
        "--channel",
        default="note",
        help="Channel/category for the note (default: note)",
    )
    parser.add_argument(
        "--actor",
        help="Actor associated with the event (default: None)",
    )
    parser.add_argument(
        "--direction",
        default="outbound",
        help="Direction for the event (default: outbound)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8081/events",
        help="Exocortex /events endpoint URL",
    )

    args = parser.parse_args()
    payload = build_payload(args)

    response = requests.post(args.api_url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    print(json.dumps({"status": "ok", "event_id": data.get("id")}, indent=2))


if __name__ == "__main__":
    main()
