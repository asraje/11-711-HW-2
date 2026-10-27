"""HTML/PDF extraction, URL normalization, and hand-written word chunking."""

import io
import json
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from .io import digest


def clean_text(text):
    text = unicodedata.normalize("NFKC", text).replace("\x00", "")
    lines = [re.sub(r"[\t \r\f\v]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def canonical_url(url, base=None):
    parts = urlsplit(urljoin(base or "", url))
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        return None
    host = parts.hostname.lower()
    try:
        port = parts.port
    except ValueError:
        return None
    if ":" in host:
        host = "[" + host + "]"
    if port and (parts.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host += ":" + str(port)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit((parts.scheme.lower(), host, parts.path or "/", urlencode(sorted(query)), ""))


class PageParser(HTMLParser):
    """Preserve headings, paragraphs, and table rows; discard common boilerplate."""

    blocked = {"script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form", "template"}
    blocks = {"p", "div", "section", "article", "main", "li", "tr", "h1", "h2", "h3", "h4", "blockquote", "br"}
    voids = {"br", "hr", "img", "meta", "link", "input", "source", "wbr", "area", "base", "embed", "param", "col", "track"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []
        self.title = []
        self.links = []
        self.jsonld = []
        self.script = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.script = []
        hidden = "hidden" in attrs or attrs.get("aria-hidden") == "true" or bool(re.search(r"display\s*:\s*none", attrs.get("style") or ""))
        if tag not in self.voids:
            self.stack.append((tag, tag in self.blocked or hidden))
        if not any(blocked for _, blocked in self.stack):
            if tag in self.blocks:
                self.parts.append("\n")
            elif tag in {"td", "th"}:
                self.parts.append(" | ")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.voids:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.jsonld.append("".join(self.script))
            self.script = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break
        if tag in self.blocks and not any(blocked for _, blocked in self.stack):
            self.parts.append("\n")

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)
        if any(tag == "title" for tag, _ in self.stack):
            self.title.append(data)
        elif not any(blocked or tag == "head" for tag, blocked in self.stack):
            self.parts.append(data)


def _structured_events(value):
    if isinstance(value, list):
        return [text for item in value for text in _structured_events(item)]
    if not isinstance(value, dict):
        return []
    result = []
    types = value.get("@type", [])
    types = [types] if isinstance(types, str) else types
    if any(isinstance(t, str) and t.endswith("Event") for t in types):
        # Keep dates next to names instead of losing them with JavaScript removal.
        result.append("Event: " + json.dumps({k: value[k] for k in (
            "name", "description", "startDate", "endDate", "eventStatus", "location", "performer", "url") if k in value}, ensure_ascii=False))
    for child in value.values():
        if isinstance(child, (dict, list)):
            result.extend(_structured_events(child))
    return result


def extract(data, content_type, url):
    if "pdf" in content_type.lower() or data.startswith(b"%PDF"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF extraction requires: pip install '.[pdf]'") from exc
        reader = PdfReader(io.BytesIO(data))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        title = str((reader.metadata or {}).get("/Title", ""))
        return {"title": title or urlsplit(url).path.rsplit("/", 1)[-1], "text": clean_text(text), "links": []}
    match = re.search(r"charset=[\"']?([\w-]+)", content_type, re.I)
    encoding = match.group(1) if match else "utf-8"
    try:
        decoded = data.decode(encoding, errors="replace")
    except LookupError:
        decoded = data.decode("utf-8", errors="replace")
    if "text/plain" in content_type:
        return {"title": urlsplit(url).path.rsplit("/", 1)[-1], "text": clean_text(decoded), "links": []}
    if not ("html" in content_type or "<html" in decoded[:1000].lower() or "<!doctype html" in decoded[:1000].lower()):
        raise ValueError("Unsupported content type: " + content_type)
    parser = PageParser()
    parser.feed(decoded)
    events = []
    for raw in parser.jsonld:
        try:
            events.extend(_structured_events(json.loads(raw)))
        except (ValueError, TypeError):
            pass
    # Social handles are often only present in an anchor's href (the visible
    # label may be an icon), so retain Instagram profile URLs as searchable
    # text instead of losing them during HTML cleanup.
    social_profiles = sorted({
        normalized for link in parser.links
        if (normalized := canonical_url(link, url))
        and urlsplit(normalized).hostname
        and urlsplit(normalized).hostname.lower().removeprefix("www.") == "instagram.com"
    })
    social_text = ["Instagram profile: " + link for link in social_profiles]
    text = clean_text("".join(parser.parts) + "\n\n" + "\n".join(events + social_text))
    links = sorted({u for link in parser.links if (u := canonical_url(link, url))})
    return {"title": clean_text("".join(parser.title)), "text": text, "links": links}


def chunk_document(document, size=220, overlap=40):
    """Word-bounded chunks; prefer sentence/paragraph ends in the last half.

    Offsets address the cleaned document text. Overlap is exact in whitespace
    words; embedding/reader token limits must be enforced separately.
    """
    if size < 2 or overlap < 0 or overlap >= size:
        raise ValueError("Require chunk size >= 2 and 0 <= overlap < size")
    text = document["text"]
    words = list(re.finditer(r"\S+", text))
    start = 0
    chunks = []
    while start < len(words):
        end = min(start + size, len(words))
        if end < len(words):
            minimum = start + max(overlap + 1, size // 2)
            for candidate in range(end, minimum - 1, -1):
                token = words[candidate - 1]
                gap = text[token.end():words[candidate].start()]
                if "\n" in gap or re.search(r'[.!?][\"\u201d\u2019)]?$', token.group()):
                    end = candidate
                    break
        left, right = words[start].start(), words[end - 1].end()
        chunks.append({"id": digest(f'{document["id"]}:{left}:{right}')[:24],
                       "document_id": document["id"], "url": document.get("url", ""),
                       "title": document.get("title", ""), "source": document.get("source", ""),
                       "start": left, "end": right, "text": text[left:right]})
        if end == len(words):
            break
        start = end - overlap
    return chunks
