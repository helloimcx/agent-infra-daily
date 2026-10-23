"""Narrow, safe discovery of recently modified URLs from first-party XML sitemaps.

Sitemap lastmod is a *change hint*, never the original event publication time.
Only HTTPS links under the configured official hostname and path prefixes pass.
"""
from __future__ import annotations
from datetime import timedelta
import re
from html.parser import HTMLParser
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


class _OfficialListingParser(HTMLParser):
    """Extract anchor hrefs and nested visible text, ignoring script content."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.active = []
        self.inside_script = 0
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.inside_script += 1
        elif tag == "a" and not self.inside_script:
            self.active.append([dict(attrs).get("href", ""), []])
    def handle_data(self, data):
        if not self.inside_script:
            for anchor in self.active:
                anchor[1].append(data)
    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.inside_script:
            self.inside_script -= 1
        elif tag == "a" and self.active:
            href, parts = self.active.pop()
            self.anchors.append((href, " ".join(parts).strip()))


def official_listing_discovery(source, now, fetch, stamp, make_item):
    """Read an official product-announcements listing for approved article URLs.

    Listing discovery is not publication-date verification. All discovered
    items keep published_at=None and must be checked against the original.
    """
    from urllib.parse import urljoin
    origin = urlsplit(source["url"])
    if origin.scheme != "https" or not origin.hostname:
        raise ValueError("official listing requires HTTPS")
    if not source.get("include_prefixes"):
        raise ValueError("official listing requires approved path prefixes")
    payload, status, _ = fetch(source["url"], {
        "User-Agent": "AgentInfraIntel/1.0",
        "Accept": "text/html"
    })
    if status != 200 or payload is None:
        raise ValueError("official listing unexpected HTTP status")
    if len(payload) > 2_000_000:
        raise ValueError("official listing HTML exceeds 2 MB")
    parser = _OfficialListingParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    items = {}
    for href, label in parser.anchors:
        full = urljoin(source["url"], href)
        target = urlsplit(full)
        if target.scheme != "https" or target.hostname != origin.hostname:
            continue
        if not any(target.path.startswith(prefix) for prefix in source["include_prefixes"]):
            continue
        title = label if len(label.strip()) >= 5 else page_title(full)
        result = make_item(source, "official_listing", title, full, None,
                           "Official website listing. Verify actual publication date and claims on the original.",
                           now.isoformat(timespec="seconds"))
        if result:
            result["date_basis"] = "official_listing_no_verified_publication_time"
            items[result["id"]] = result
        if len(items) >= 40:
            break
    return list(items.values())
