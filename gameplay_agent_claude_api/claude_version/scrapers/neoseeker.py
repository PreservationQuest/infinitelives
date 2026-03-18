"""NeoSeeker Walkthrough Scraper."""
import re, json, time, hashlib, logging, sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from html.parser import HTMLParser

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import requests
except ImportError:
    requests = None

from models.schemas import WalkthroughMetadata

logger = logging.getLogger(__name__)
NEOSEEKER_BASE = "https://www.neoseeker.com"
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
DEFAULT_HEADERS = {"User-Agent": "InfiniteLives-ResearchBot/1.0 (Academic research; preservationquest@example.com)", "Accept": "text/html"}
RATE_LIMIT_SECONDS = 2.0

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text_parts, self._skip = [], False
        self._skip_tags = {"script", "style", "nav", "footer", "header"}
    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags: self._skip = True
        elif tag in ("h1","h2","h3","h4"): self._text_parts.append("\n\n## ")
        elif tag == "p": self._text_parts.append("\n\n")
        elif tag == "li": self._text_parts.append("\n- ")
        elif tag == "br": self._text_parts.append("\n")
    def handle_endtag(self, tag):
        if tag in self._skip_tags: self._skip = False
        if tag in ("h1","h2","h3","h4"): self._text_parts.append("\n")
    def handle_data(self, data):
        if not self._skip: self._text_parts.append(data)
    def get_text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self._text_parts)).strip()

def html_to_text(html_content: str) -> str:
    e = HTMLTextExtractor(); e.feed(html_content); return e.get_text()

def extract_walkthrough_content(html: str) -> str:
    for p in [r'<div[^>]*class="[^"]*wiki-content[^"]*"[^>]*>(.*?)</div>', r'<article[^>]*>(.*?)</article>']:
        m = re.search(p, html, re.DOTALL | re.IGNORECASE)
        if m: return html_to_text(m.group(1))
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    return html_to_text(m.group(1)) if m else html_to_text(html)

def extract_section_titles(text: str) -> list[str]:
    return re.findall(r"^##\s+(.+)$", text, re.MULTILINE)

def extract_toc_links(html: str, game_slug: str) -> list[dict]:
    links, seen = [], set()
    for m in re.finditer(rf'href="/{re.escape(game_slug)}/walkthrough/([^"]+)"[^>]*>([^<]+)<', html, re.IGNORECASE):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            links.append({"title": m.group(2).strip(), "slug": m.group(1), "url": f"{NEOSEEKER_BASE}/{game_slug}/walkthrough/{m.group(1)}"})
    return links

@dataclass
class ScrapedPage:
    url: str; game_slug: str; page_slug: str; title: str; raw_html: str
    content_text: str; section_titles: list[str]; word_count: int
    scraped_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    from_cache: bool = False

class NeoSeekerScraper:
    def __init__(self, cache_dir=None, rate_limit=RATE_LIMIT_SECONDS, headers=None):
        self.cache_dir = cache_dir or CACHE_DIR; self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit; self.headers = headers or DEFAULT_HEADERS
        if requests: self.session = requests.Session(); self.session.headers.update(self.headers)
        else: self.session = None
        self._last_request_time = 0.0

    def _cache_key(self, url): return hashlib.sha256(url.encode()).hexdigest()
    def _get_cached(self, url):
        f = self.cache_dir / f"{self._cache_key(url)}.html"
        return f.read_text(encoding="utf-8") if f.exists() else None
    def _save_cache(self, url, html): (self.cache_dir / f"{self._cache_key(url)}.html").write_text(html, encoding="utf-8")
    def _rate_limit_wait(self):
        e = time.time() - self._last_request_time
        if e < self.rate_limit: time.sleep(self.rate_limit - e)
        self._last_request_time = time.time()

    def fetch_page(self, url, use_cache=True):
        if use_cache:
            c = self._get_cached(url)
            if c: return c
        if not self.session: return None
        self._rate_limit_wait()
        try:
            r = self.session.get(url, timeout=30); r.raise_for_status()
            self._save_cache(url, r.text); return r.text
        except Exception as e: logger.error(f"Failed to fetch {url}: {e}"); return None

    def scrape_walkthrough_index(self, game_slug):
        url = f"{NEOSEEKER_BASE}/{game_slug}/walkthrough"
        html = self.fetch_page(url)
        if not html: return None
        t = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        title = t.group(1).split(" - ")[0].strip() if t else game_slug
        content = extract_walkthrough_content(html)
        return {"game_title": title, "game_slug": game_slug, "url": url, "toc_links": extract_toc_links(html, game_slug), "index_content": content, "section_titles": extract_section_titles(content)}

    def scrape_walkthrough_page(self, game_slug, page_slug):
        url = f"{NEOSEEKER_BASE}/{game_slug}/walkthrough/{page_slug}"
        html = self.fetch_page(url)
        if not html: return None
        content = extract_walkthrough_content(html)
        t = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        return ScrapedPage(url=url, game_slug=game_slug, page_slug=page_slug, title=t.group(1).split(" - ")[0].strip() if t else page_slug, raw_html=html, content_text=content, section_titles=extract_section_titles(content), word_count=len(content.split()))

    def scrape_full_walkthrough(self, game_slug, max_pages=50):
        index = self.scrape_walkthrough_index(game_slug)
        if not index: return []
        pages = []
        if index["index_content"] and len(index["index_content"]) > 200:
            pages.append(ScrapedPage(url=index["url"], game_slug=game_slug, page_slug="index", title=index["game_title"], raw_html="", content_text=index["index_content"], section_titles=index["section_titles"], word_count=len(index["index_content"].split())))
        for i, link in enumerate(index["toc_links"][:max_pages]):
            p = self.scrape_walkthrough_page(game_slug, link["slug"])
            if p and p.word_count > 50: pages.append(p)
        return pages

    def load_from_text(self, game_title, text_content, source_url=""):
        return ScrapedPage(url=source_url, game_slug=game_title.lower().replace(" ", "-"), page_slug="local", title=game_title, raw_html="", content_text=text_content, section_titles=extract_section_titles(text_content), word_count=len(text_content.split()), from_cache=True)
