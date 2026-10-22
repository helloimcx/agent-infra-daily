#!/usr/bin/env python3
"""Incremental official RSS/Atom and GitHub Release collection. Stdlib only.

Outputs evidence candidates; never automatically creates KG facts or trends.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

BEIJING = timezone(timedelta(hours=8))
ATOM = "{http://www.w3.org/2005/Atom}"
MAX_RESPONSE = 2_000_000
MAX_ITEMS = 5000
RETENTION_DAYS = 90


def stamp(value: str | None) -> str | None:
    if not value:
        return None
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc).isoformat(timespec="seconds")


def clean(value: str | None, limit: int = 420) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value or ""))).strip()[:limit]


def canonical_url(value: str) -> str | None:
    try:
        url = urlsplit(value.strip())
        if url.scheme.lower() != "https" or not url.hostname or url.username:
            return None
        query = sorted((k, v) for k, v in parse_qsl(url.query, keep_blank_values=True)
                       if not k.lower().startswith("utm_") and k.lower() not in
                       {"fbclid", "gclid", "ref", "source"})
        host = url.hostname.lower() + (":" + str(url.port) if url.port else "")
        return urlunsplit(("https", host, url.path.rstrip("/") or "/", urlencode(query), ""))
    except (ValueError, AttributeError):
        return None


def make_item(source: dict, kind: str, title: str, url: str,
              published: str | None, excerpt: str, discovered: str) -> dict | None:
    url = canonical_url(url)
    if not url or not clean(title):
        return None
    return {
        "id": hashlib.sha256(url.encode()).hexdigest()[:24],
        "source_id": source["id"], "source_kind": kind,
        "topic": source["topic"], "priority": source["priority"],
        "title": clean(title, 250), "url": url,
        "published_at": stamp(published), "first_discovered_at": discovered,
        "excerpt": clean(excerpt), "evidence_status": "unverified_candidate",
    }


def _node(parent: ET.Element, *paths: str) -> ET.Element | None:
    for path in paths:
        found = parent.find(path)
        if found is not None:
            return found
    return None


def _text(node: ET.Element | None) -> str:
    return "".join(node.itertext()).strip() if node is not None else ""


def parse_feed(payload: bytes, source: dict, discovered: str) -> list[dict]:
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise ValueError("XML DTD/entities forbidden")
    root = ET.fromstring(payload)
    out = []
    if root.tag.lower() in {"rss", "rdf", "{http://purl.org/rss/1.0/}rdf"}:
        channel = _node(root, "channel")
        if channel is None:
            channel = root
        nodes = channel.findall("item") or root.findall("{http://purl.org/rss/1.0/}item")
        for entry in nodes:
            item = make_item(source, "rss", _text(_node(entry, "title")),
                             _text(_node(entry, "link")),
                             _text(_node(entry, "pubDate", "{http://purl.org/dc/elements/1.1/}date")),
                             _text(_node(entry, "description")), discovered)
            if item:
                out.append(item)
    elif root.tag in {ATOM + "feed", "feed"}:
        for entry in root.findall(ATOM + "entry") + root.findall("entry"):
            links = entry.findall(ATOM + "link") + entry.findall("link")
            link = next((x.get("href", "") for x in links if x.get("rel", "alternate") == "alternate"
                         and x.get("type", "text/html") in {"", "text/html"}), "")
            link = link or next((x.get("href", "") for x in links), "")
            item = make_item(source, "atom", _text(_node(entry, ATOM + "title", "title")),
                             link, _text(_node(entry, ATOM + "published", ATOM + "updated",
                                               "published", "updated")),
                             _text(_node(entry, ATOM + "summary", ATOM + "content",
                                               "summary", "content")), discovered)
            if item:
                out.append(item)
    else:
        raise ValueError("unsupported RSS/Atom root")
    return out


def parse_releases(payload: bytes, source: dict, discovered: str) -> list[dict]:
    releases = json.loads(payload)
    if not isinstance(releases, list):
        raise ValueError("GitHub releases response must be an array")
    out = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        item = make_item(source, "github_release",
                         release.get("name") or release.get("tag_name") or "",
                         release.get("html_url", ""),
                         release.get("published_at") or release.get("created_at"),
                         release.get("body") or "", discovered)
        if item:
            item["release_tag"] = release.get("tag_name")
            out.append(item)
    return out


def fetch_http(url: str, headers: dict) -> tuple[bytes | None, int, dict]:
    try:
        with urlopen(Request(url, headers=headers), timeout=18) as response:
            limit = 8_000_000 if urlsplit(url).hostname == "api.github.com" else MAX_RESPONSE
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError("response exceeds configured safety bound")
            return data, response.status, {k.lower(): v for k, v in response.headers.items()}
    except HTTPError as error:
        if error.code == 304:
            return None, 304, {}
        raise


def candidate_events(items: list[dict]) -> list[dict]:
    """Conservative title clustering; groups are unverified, not semantic claims."""
    groups: list[list[dict]] = []
    for item in items:
        title = re.sub(r"[\W_]+", " ", item["title"].casefold()).strip()
        joined = False
        for group in groups:
            other = group[0]
            reference = re.sub(r"[\W_]+", " ", other["title"].casefold()).strip()
            if "github_release" in {item["source_kind"], other["source_kind"]}:
                continue
            a, b = item.get("published_at"), other.get("published_at")
            if a and b and abs((datetime.fromisoformat(a) -
                                datetime.fromisoformat(b)).total_seconds()) > 3 * 86400:
                continue
            if item["topic"] == other["topic"] and min(len(title), len(reference)) >= 24 \
                    and SequenceMatcher(None, title, reference).ratio() >= .94:
                group.append(item)
                joined = True
                break
        if not joined:
            groups.append([item])
    return [
        {"event_candidate_id": "ec-" + hashlib.sha256(group[0]["id"].encode()).hexdigest()[:16],
         "representative_title": group[0]["title"], "topic": group[0]["topic"],
         "item_ids": [x["id"] for x in group],
         "source_ids": sorted({x["source_id"] for x in group}),
         "status": "needs_verification"}
        for group in groups
    ]


def collect(config: dict, state: dict, now: datetime, fetch=fetch_http,
            max_age_hours: int = 72) -> tuple[dict, dict]:
    now = now.astimezone(timezone.utc)
    seen = state.setdefault("items", {})
    validators = state.setdefault("validators", {})
    discovered = now.isoformat(timespec="seconds")
    checks = {"ok": [], "not_modified": [], "errors": []}
    sources = [dict(x, kind="feed") for x in config.get("feeds", [])]
    sources += [dict(x, id="release:" + x["repo"], kind="github_release",
                     url="https://api.github.com/repos/" + x["repo"] + "/releases?per_page=10")
                for x in config.get("github_releases", [])]
    for source in sources:
        sid = source["id"]
        headers = {"User-Agent": "AgentInfraIntel/1.0 (github.com/helloimcx/agent-infra-daily)",
                   "Accept": "application/atom+xml, application/rss+xml, application/json;q=0.9"}
        previous = validators.get(sid, {})
        if previous.get("etag"):
            headers["If-None-Match"] = previous["etag"]
        if previous.get("last_modified"):
            headers["If-Modified-Since"] = previous["last_modified"]
        if source["kind"] == "github_release":
            headers["Accept"] = "application/vnd.github+json"
            if os.environ.get("GITHUB_TOKEN"):
                headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
        try:
            payload, status, response_headers = fetch(source["url"], headers)
            if status == 304:
                checks["not_modified"].append(sid)
                continue
            if status != 200 or payload is None:
                raise ValueError("unexpected HTTP status " + str(status))
            incoming = parse_releases(payload, source, discovered) if source["kind"] == "github_release" \
                else parse_feed(payload, source, discovered)
            for item in incoming:
                old = seen.get(item["id"])
                if old:
                    item["first_discovered_at"] = old["first_discovered_at"]
                seen[item["id"]] = item
            validators[sid] = {"etag": response_headers.get("etag"),
                               "last_modified": response_headers.get("last-modified")}
            checks["ok"].append({"id": sid, "entries": len(incoming)})
        except Exception as exc:
            checks["errors"].append({"id": sid, "error": str(exc)[:250]})
    cutoff = now - timedelta(days=RETENTION_DAYS)
    retained = {}
    for key, item in seen.items():
        timestamp = stamp(item.get("published_at") or item.get("first_discovered_at"))
        if timestamp and datetime.fromisoformat(timestamp) >= cutoff:
            retained[key] = item
    if len(retained) > MAX_ITEMS:
        newest = sorted(retained.values(),
                        key=lambda item: item.get("published_at") or item["first_discovered_at"],
                        reverse=True)[:MAX_ITEMS]
        retained = {item["id"]: item for item in newest}
    state["items"] = retained
    window = now - timedelta(hours=max_age_hours)
    recent = []
    for item in retained.values():
        timestamp = stamp(item.get("published_at") or item.get("first_discovered_at"))
        if timestamp and window <= datetime.fromisoformat(timestamp) <= now + timedelta(hours=3):
            recent.append(item)
    recent.sort(key=lambda item: item.get("published_at") or item["first_discovered_at"],
                reverse=True)
    # Prevent high-volume research feeds from crowding out primary product releases.
    balanced, per_source = [], {}
    for item in recent:
        sid = item["source_id"]
        if per_source.get(sid, 0) >= 20:
            continue
        per_source[sid] = per_source.get(sid, 0) + 1
        balanced.append(item)
        if len(balanced) >= 180:
            break
    recent = balanced
    snapshot = {
        "schema_version": "1.0", "beijing_date": now.astimezone(BEIJING).date().isoformat(),
        "generated_at": discovered, "lookback_hours": max_age_hours,
        "status": "partial" if checks["errors"] else "ok",
        "source_checks": checks, "item_count": len(recent),
        "items": recent, "event_candidates": candidate_events(recent),
        "usage_note": "Unverified candidates: verify first-party evidence, actual event time and independent sources before any trend/claim update."
    }
    return state, snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="intel/sources.json")
    parser.add_argument("--state", default="intel/.state/state.json")
    parser.add_argument("--output", default="intel/output/candidates.json")
    parser.add_argument("--max-age-hours", type=int, default=72)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    path = Path(args.state)
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    state, result = collect(config, state, datetime.now(timezone.utc),
                            max_age_hours=args.max_age_hours)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checks = result["source_checks"]
    print(f"date={result['beijing_date']} items={result['item_count']} "
          f"ok={len(checks['ok'])} not_modified={len(checks['not_modified'])} "
          f"errors={len(checks['errors'])}")
    for failure in checks["errors"]:
        print(f"WARNING {failure['id']}: {failure['error']}", file=sys.stderr)
    return 0 if checks["ok"] or checks["not_modified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
