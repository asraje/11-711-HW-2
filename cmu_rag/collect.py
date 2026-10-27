"""Bounded, robots-aware collection with raw snapshots and resumable state."""

import json
import logging
import re
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from .io import digest, read_json, write_json, write_jsonl
from .text import canonical_url, extract

LOG = logging.getLogger(__name__)
AGENT = "CMUHomeworkRAG/1.0"
SKIP = re.compile(r"\.(?:jpg|jpeg|png|gif|svg|webp|ico|mp4|mp3|zip|css|js|woff2?|ics)$", re.I)


class ExcessiveDelay(ValueError):
    """Defer a URL rather than violate its rate limit or block the whole crawl."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Fetcher:
    """Rate-limit every request, including redirects and robots requests.

    Fail closed if robots.txt cannot be checked; a missing robots file permits
    access. Redirect destinations are checked against scope before fetching.
    """

    def __init__(self, delay=1.0, timeout=25, max_bytes=20_000_000, retries=2, max_wait=30):
        if delay < 0 or timeout <= 0 or max_bytes <= 0 or retries < 0 or max_wait < 0:
            raise ValueError("Invalid network limits")
        self.delay, self.timeout, self.max_bytes, self.retries = delay, timeout, max_bytes, retries
        self.max_wait = max_wait
        self.opener = build_opener(NoRedirect())
        self.last = {}
        self.robots = {}
        self.robots_errors = {}

    def _request(self, url, delay=None):
        origin = urlsplit(url).netloc
        for attempt in range(self.retries + 1):
            wait = max(self.delay, delay or 0) - (time.monotonic() - self.last.get(origin, float("-inf")))
            if wait > self.max_wait:
                raise ExcessiveDelay(f"Required wait {wait:.1f}s exceeds max_wait={self.max_wait}s: {url}")
            if wait > 0:
                LOG.info("Rate-limit wait %.1fs before %s", wait, url)
                time.sleep(wait)
            self.last[origin] = time.monotonic()
            LOG.info("Request %d/%d (socket timeout %ss): %s", attempt + 1,
                     self.retries + 1, self.timeout, url)
            try:
                with self.opener.open(Request(url, headers={"User-Agent": AGENT, "Accept-Encoding": "identity"}), timeout=self.timeout) as response:
                    data = response.read(self.max_bytes + 1)
                    if len(data) > self.max_bytes:
                        raise ValueError("Response exceeds max_bytes")
                    return data, response.headers.get("Content-Type", ""), response.status, None
            except HTTPError as exc:
                if exc.code in {301, 302, 303, 307, 308}:
                    target = canonical_url(exc.headers.get("Location", ""), url)
                    exc.close()
                    return b"", "", exc.code, target
                if exc.code not in {429, 500, 502, 503, 504} or attempt == self.retries:
                    raise
                retry_after = exc.headers.get("Retry-After", "")
                if exc.code == 429 and retry_after.isdigit():
                    wait_seconds = float(retry_after)
                    if wait_seconds > self.max_wait:
                        exc.close()
                        raise ExcessiveDelay(
                            f"Server Retry-After {wait_seconds:.0f}s exceeds "
                            f"max_wait={self.max_wait}s; deferring {url}"
                        )
                    LOG.warning("HTTP 429 from %s; honoring Retry-After=%ss", url, retry_after)
                    exc.close()
                    time.sleep(wait_seconds)
                    continue
                LOG.warning("HTTP %s from %s; retrying", exc.code, url)
                exc.close()
                time.sleep(min(float(retry_after), 30) if retry_after.isdigit() else min(2 ** attempt, 10))
            except (URLError, TimeoutError, OSError) as exc:
                if attempt == self.retries:
                    raise
                LOG.warning("Request failed for %s: %s; retrying", url, exc)
                time.sleep(min(2 ** attempt, 10))
        raise RuntimeError("Request retry exhausted")

    def _robots(self, url):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self.robots:
            parser = RobotFileParser(origin + "/robots.txt")
            target = origin + "/robots.txt"
            try:
                for _ in range(6):
                    body, _, status, redirected = self._request(target)
                    if status in {301, 302, 303, 307, 308}:
                        redirected_parts = urlsplit(redirected or "")
                        # Sites commonly publish robots on the www variant of the same host.
                        same_site = (redirected_parts.hostname or "").removeprefix("www.") == (parts.hostname or "").removeprefix("www.")
                        if not redirected or not same_site or redirected_parts.port != parts.port:
                            raise ValueError("Cross-host robots redirect")
                        target = redirected
                        continue
                    parser.parse(body.decode("utf-8", errors="replace").splitlines())
                    break
                else:
                    raise ValueError("Too many robots redirects")
            except HTTPError as exc:
                parser.parse([] if exc.code in {404, 410} else ["User-agent: *", "Disallow: /"])
                if exc.code not in {404, 410}:
                    self.robots_errors[origin] = f"robots HTTP {exc.code}"
                exc.close()
            except (OSError, ValueError) as exc:
                self.robots_errors[origin] = f"{type(exc).__name__}: {exc}"
                LOG.warning("Could not check robots.txt for %s: %s", origin, exc)
                parser.parse(["User-agent: *", "Disallow: /"])
            self.robots[origin] = parser
        return self.robots[origin]

    def fetch(self, url, allowed):
        for _ in range(6):
            if not allowed(url):
                raise PermissionError("URL outside configured scope: " + url)
            robot = self._robots(url)
            if not robot.can_fetch(AGENT, url):
                parts = urlsplit(url)
                reason = self.robots_errors.get(f"{parts.scheme}://{parts.netloc}", "robots.txt disallows access")
                raise PermissionError(reason + ": " + url)
            rate = robot.request_rate(AGENT)
            delay = max(robot.crawl_delay(AGENT) or 0, rate.seconds / rate.requests if rate and rate.requests else 0)
            if delay > self.max_wait:
                raise ExcessiveDelay(f"Robots interval {delay:.1f}s exceeds max_wait={self.max_wait}s; deferring {url}")
            body, content_type, status, redirected = self._request(url, delay)
            if status in {301, 302, 303, 307, 308}:
                if not redirected:
                    raise ValueError("Invalid redirect")
                url = redirected
                continue
            return url, body, content_type
        raise ValueError("Too many redirects")


def in_scope(url, source):
    if not url or SKIP.search(urlsplit(url).path):
        return False
    parts = urlsplit(url)
    for prefix in source["allowed_prefixes"]:
        root = urlsplit(prefix)
        # /about allows /about and /about/... but not /about-something-else.
        path = root.path.rstrip("/")
        if parts.netloc == root.netloc and (not path or parts.path == path or parts.path.startswith(path + "/")):
            return not any(re.search(pattern, url, re.I) for pattern in source.get("exclude_patterns", []))
    return False


def load_sources(path):
    config = read_json(path)
    sources = config.get("sources", [])
    names = set()
    if not sources:
        raise ValueError("Source configuration needs sources")
    for source in sources:
        if not source.get("name") or source["name"] in names:
            raise ValueError("Source names must be nonempty and unique")
        names.add(source["name"])
        for key in ("seeds", "allowed_prefixes"):
            if not source.get(key) or any(canonical_url(u) is None for u in source[key]):
                raise ValueError("Invalid source " + key)
            source[key] = [canonical_url(u) for u in source[key]]
        if any(not in_scope(seed, source) for seed in source["seeds"]):
            raise ValueError("Seed outside scope for " + source["name"])
        if source.get("max_pages", 100) <= 0 or source.get("max_depth", 2) < 0:
            raise ValueError("Invalid source crawl limits")
    return config


def collect(config_path, output_dir, max_pages=100, delay=1.0, retry_failed=False, fetcher=None,
            timeout=25, retries=2, max_wait=30):
    """max_pages bounds this invocation's fetch attempts, not successful documents."""
    if max_pages <= 0:
        raise ValueError("max_pages must be positive")
    config = load_sources(config_path)
    fingerprint = digest(json.dumps(config, sort_keys=True))
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "crawl_state.json"
    sources = {s["name"]: s for s in config["sources"]}
    if state_path.exists():
        state = read_json(state_path)
        if state["config_hash"] != fingerprint:
            raise ValueError("Source configuration changed: use a new output directory")
    else:
        state = {"version": 1, "config_hash": fingerprint, "queue": [], "visited": {}, "documents": {}}
        # Interleave seeds across sources so small budgets retain topic diversity.
        for i in range(max(len(s["seeds"]) for s in sources.values())):
            for source in sources.values():
                if i < len(source["seeds"]):
                    state["queue"].append([source["name"], source["seeds"][i], 0])
    if retry_failed:
        for key, record in list(state["visited"].items()):
            if record["status"] in {"error", "deferred"}:
                state["queue"].append([record["source"], record["url"], record["depth"]])
                del state["visited"][key]
    queue = deque(state["queue"])
    queued = {(s, u) for s, u, _ in queue}
    fetcher = fetcher or Fetcher(delay=delay, timeout=timeout, retries=retries, max_wait=max_wait)
    attempts = 0
    capped = []
    hashes = {d["text_hash"]: key for key, d in state["documents"].items()}
    counts = {name: sum(r["source"] == name for r in state["visited"].values()) for name in sources}

    def save_outputs():
        state["queue"] = list(queue) + capped
        write_json(state_path, state)
        write_jsonl(root / "documents.jsonl", state["documents"].values())
        write_jsonl(root / "manifest.jsonl", state["visited"].values())
        return {
            "attempted_this_run": attempts,
            "documents": len(state["documents"]),
            "pending": len(state["queue"]),
            "pending_at_source_cap": len(capped),
            "status_counts": {
                status: sum(r["status"] == status for r in state["visited"].values())
                for status in ("ok", "duplicate", "too_short", "error", "deferred")
            },
        }

    while queue and attempts < max_pages:
        name, url, depth = queue.popleft()
        key = name + "|" + url
        source = sources[name]
        if key in state["visited"]:
            continue
        if counts[name] >= source.get("max_pages", 100):
            capped.append([name, url, depth])
            continue
        attempts += 1
        counts[name] += 1
        record = {"source": name, "url": url, "depth": depth, "fetched_at": datetime.now(timezone.utc).isoformat()}
        LOG.info("Fetching page %d/%d [%s]: %s", attempts, max_pages, name, url)
        try:
            final, body, content_type = fetcher.fetch(url, lambda u: in_scope(u, source))
            LOG.info("Downloaded %d bytes; extracting: %s", len(body), final)
            raw_id = digest(body)
            raw_path = root / "snapshots" / (raw_id + ".bin")
            raw_path.parent.mkdir(exist_ok=True)
            raw_path.write_bytes(body)
            record.update({"final_url": final, "raw_path": str(raw_path.relative_to(root)), "raw_hash": raw_id, "content_type": content_type})
            page = extract(body, content_type, final)
            if depth < source.get("max_depth", 2):
                for link in page["links"]:
                    if in_scope(link, source) and (name, link) not in queued and name + "|" + link not in state["visited"]:
                        queue.append([name, link, depth + 1])
                        queued.add((name, link))
            if len(page["text"].split()) < config.get("min_words", 20):
                record["status"] = "too_short"
            else:
                text_hash = digest(page["text"])
                if text_hash in hashes:
                    document_id = hashes[text_hash]
                    aliases = state["documents"][document_id]["aliases"]
                    if final not in aliases:
                        aliases.append(final)
                    record.update({"status": "duplicate", "document_id": document_id})
                else:
                    document_id = digest(final)[:24]
                    document = {"id": document_id, "url": final, "aliases": [final], "source": name,
                                "title": page["title"], "text": page["text"], "text_hash": text_hash,
                                "fetched_at": record["fetched_at"], "raw_path": record["raw_path"]}
                    state["documents"][document_id] = document
                    hashes[text_hash] = document_id
                    record.update({"status": "ok", "document_id": document_id})
        except KeyboardInterrupt:
            # Preserve the current URL for a later resume and export completed
            # documents before allowing the interrupt to exit the process.
            queue.appendleft([name, url, depth])
            save_outputs()
            raise
        except ExcessiveDelay as exc:
            record.update({"status": "deferred", "error": str(exc)})
            LOG.warning("Deferred %s: %s", url, exc)
        except Exception as exc:
            # Record a failed page and continue; a site outage must not discard other sources.
            record.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
            LOG.warning("Collection failed for %s: %s", url, exc)
        state["visited"][key] = record
        state["queue"] = list(queue) + capped
        write_json(state_path, state)
        LOG.info("Collected %s: %s", record["status"], url)
    summary = save_outputs()
    write_json(root / "summary.json", summary)
    return summary


def ingest(input_dir, output_path):
    """Import manually downloaded HTML, PDF, or text; never traverse arbitrary JSON."""
    rows, seen = [], set()
    for path in sorted(Path(input_dir).rglob("*")):
        types = {".html": "text/html", ".htm": "text/html", ".pdf": "application/pdf", ".txt": "text/plain"}
        if not path.is_file() or path.suffix.lower() not in types:
            continue
        page = extract(path.read_bytes(), types[path.suffix.lower()], path.resolve().as_uri())
        text_hash = digest(page["text"])
        if not page["text"] or text_hash in seen:
            continue
        seen.add(text_hash)
        rows.append({"id": digest(path.resolve())[:24], "url": path.resolve().as_uri(), "source": "local-import",
                     "title": page["title"], "text": page["text"], "text_hash": text_hash})
    if not rows:
        raise ValueError("No nonempty supported documents found")
    write_jsonl(output_path, rows)
    return {"documents": len(rows)}
