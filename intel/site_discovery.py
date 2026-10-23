"""Narrow, safe discovery of recently modified URLs from first-party XML sitemaps.

Sitemap lastmod is a *change hint*, never the original event publication time.
Only HTTPS links under the configured official hostname and path prefixes pass.
"""
from __future__ import annotations
from datetime import timedelta
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
MAX_CHILDREN = 12
MAX_DEPTH = 2


def _nodes(root, name):
    return root.findall(NS + name) + root.findall(name)


def _value(parent, name):
    n = parent.find(NS + name)
    if n is None:
        n = parent.find(name)
    return (n.text or "").strip() if n is not None else ""


def page_title(url):
    text = urlsplit(url).path.rstrip("/").split("/")[-1]
    return "Official site update: " + re.sub(r"[-_]+", " ", text).strip()[:175]


def sitemap_discovery(source, now, fetch, stamp, make_item):
    """Read first-party sitemap(s), collecting recent page modifications only.

    HTTP fetching is injected and must implement the existing collector limit.
    Nested sitemap references must remain on the *exact* configured hostname.
    A malformed nested sitemap does not abort verified sibling results, but any
    error is returned to the caller for reporting in source_checks.
    """
    origin = urlsplit(source["url"])
    if origin.scheme != "https" or not origin.hostname:
        raise ValueError("sitemap source must use HTTPS official hostname")
    if not source.get("include_prefixes"):
        raise ValueError("sitemap requires explicit path prefix allowlist")
    cutoff = now - timedelta(days=7)
    seen = set()
    items = {}
    failures = []
    child_count = 0

    def walk(url, depth):
        nonlocal child_count
        host = urlsplit(url)
        if host.scheme != "https" or host.hostname != origin.hostname:
            raise ValueError("cross-origin sitemap reference refused")
        if url in seen:
            return
        seen.add(url)
        payload, status, _ = fetch(url, {"User-Agent": "AgentInfraIntel/1.0",
                                         "Accept": "application/xml, text/xml"})
        if status != 200 or payload is None:
            raise ValueError("sitemap HTTP status " + str(status))
        if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
            raise ValueError("DTD/entity declarations refused")
        root = ET.fromstring(payload)
        kind = root.tag.rsplit("}", 1)[-1]
        if kind == "sitemapindex":
            if depth >= MAX_DEPTH:
                return
            for child in _nodes(root, "sitemap"):
                link = _value(child, "loc")
                if child_count >= MAX_CHILDREN:
                    break
                if not link:
                    continue
                child_count += 1
                try:
                    walk(link, depth + 1)
                except Exception as exc:
                    failures.append(str(exc)[:150])
        elif kind == "urlset":
            for item in _nodes(root, "url"):
                link = _value(item, "loc")
                timestamp = stamp(_value(item, "lastmod"))
                if not timestamp:
                    continue  # no publication/change date: cannot classify as fresh
                from datetime import datetime
                updated = datetime.fromisoformat(timestamp)
                if updated < cutoff or updated > now + timedelta(days=1):
                    continue
                link_parts = urlsplit(link)
                if link_parts.scheme != "https" or link_parts.hostname not in \
                        {origin.hostname, origin.hostname.removeprefix("www.")}:
                    continue
                if not any(link_parts.path.startswith(prefix) for prefix in source["include_prefixes"]):
                    continue
                result = make_item(source, "official_sitemap", page_title(link),
                                   link, None, "Official sitemap URL; timestamp reflects site modification, not publication.",
                                   now.isoformat(timespec="seconds"))
                if result:
                    result["observed_change_at"] = timestamp
                    result["date_basis"] = "site_lastmod_not_publication"
                    items[result["id"]] = result
                if len(items) >= 150:
                    return
        else:
            raise ValueError("unsupported XML sitemap root: " + kind)

    walk(source["url"], 0)
    return list(items.values()), failures
