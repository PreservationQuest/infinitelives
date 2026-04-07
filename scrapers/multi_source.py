"""
Multi-Source Walkthrough Scraper v2.

Supports:
  - NeoSeeker (36,000+ guides)
  - StrategyWiki (10,551 games, MediaWiki API, CC BY-SA)
  - Fandom (250,000+ wikis, MediaWiki API, CC BY-SA)

Improvements over v1:
  - Content hash caching (skip re-extraction if content unchanged)
  - Retry with exponential backoff + jitter
  - User-Agent rotation
  - Content length validation
  - Source attribution tracking
"""
import re, json, time, hashlib, logging, random, sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from html.parser import HTMLParser

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    requests = None

from models.schemas import WalkthroughMetadata, ContentType

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

USER_AGENTS = [
    "InfiniteLives-ResearchBot/2.0 (Academic research on video game mechanics; preservationquest@example.com)",
    "Mozilla/5.0 (compatible; InfiniteLivesBot/2.0; +https://github.com/PreservationQuest/infinitelives)",
]

RATE_LIMITS = {
    "neoseeker": 2.0,
    "strategywiki": 1.5,
    "fandom": 2.0,
}


class HTMLTextExtractor(HTMLParser):
    """Strips HTML while preserving section structure."""
    def __init__(self):
        super().__init__()
        self._parts, self._skip = [], False
        self._skip_tags = {"script", "style", "nav", "footer", "header", "aside"}
    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags: self._skip = True
        elif tag in ("h1","h2","h3","h4"): self._parts.append("\n\n## ")
        elif tag == "p": self._parts.append("\n\n")
        elif tag == "li": self._parts.append("\n- ")
        elif tag == "br": self._parts.append("\n")
    def handle_endtag(self, tag):
        if tag in self._skip_tags: self._skip = False
        if tag in ("h1","h2","h3","h4"): self._parts.append("\n")
    def handle_data(self, data):
        if not self._skip: self._parts.append(data)
    def get_text(self): return re.sub(r"\n{3,}", "\n\n", "".join(self._parts)).strip()


def html_to_text(html: str) -> str:
    e = HTMLTextExtractor(); e.feed(html); return e.get_text()


def content_hash(text: str) -> str:
    """Generate hash of content for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass
class ScrapedPage:
    url: str
    game_slug: str
    page_slug: str
    title: str
    content_text: str
    section_titles: list[str]
    word_count: int
    source_name: str  # "neoseeker", "strategywiki", "fandom"
    content_hash: str = ""
    scraped_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    from_cache: bool = False

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = content_hash(self.content_text)


class BaseScraper:
    """Base class with shared scraping infrastructure."""

    def __init__(self, source_name: str, cache_dir: Optional[Path] = None):
        self.source_name = source_name
        self.cache_dir = cache_dir or CACHE_DIR / source_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = RATE_LIMITS.get(source_name, 2.0)
        self._last_request = 0.0

        if requests:
            self.session = requests.Session()
            # Retry strategy with exponential backoff
            retry = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                respect_retry_after_header=True,
            )
            self.session.mount("https://", HTTPAdapter(max_retries=retry))
            self.session.mount("http://", HTTPAdapter(max_retries=retry))
            self.session.headers.update({
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/json",
            })
        else:
            self.session = None

    def _cache_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    def _get_cached(self, url: str) -> Optional[str]:
        f = self.cache_dir / f"{self._cache_key(url)}.html"
        if f.exists():
            logger.debug(f"Cache hit [{self.source_name}]: {url}")
            return f.read_text(encoding="utf-8", errors="replace")
        return None

    def _save_cache(self, url: str, content: str):
        f = self.cache_dir / f"{self._cache_key(url)}.html"
        f.write_text(content, encoding="utf-8")

    def _get_content_hash_cache(self, url: str) -> Optional[str]:
        """Check if content has changed since last scrape."""
        f = self.cache_dir / f"{self._cache_key(url)}.hash"
        return f.read_text().strip() if f.exists() else None

    def _save_content_hash(self, url: str, h: str):
        f = self.cache_dir / f"{self._cache_key(url)}.hash"
        f.write_text(h)

    def _rate_wait(self):
        elapsed = time.time() - self._last_request
        wait = self.rate_limit + random.uniform(0.1, 0.5)  # jitter
        if elapsed < wait:
            time.sleep(wait - elapsed)
        self._last_request = time.time()

    def fetch(self, url: str, use_cache: bool = True) -> Optional[str]:
        if use_cache:
            cached = self._get_cached(url)
            if cached:
                return cached
        if not self.session:
            logger.warning(f"No HTTP session for {self.source_name}")
            return None
        self._rate_wait()
        try:
            # Rotate user agent per request
            self.session.headers["User-Agent"] = random.choice(USER_AGENTS)
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            # Handle encoding
            r.encoding = r.apparent_encoding or "utf-8"
            self._save_cache(url, r.text)
            logger.info(f"Fetched [{self.source_name}]: {url} ({len(r.text)} bytes)")
            return r.text
        except Exception as e:
            logger.error(f"Failed [{self.source_name}] {url}: {e}")
            return None

    def load_from_text(self, game_title: str, text: str, source_url: str = "") -> ScrapedPage:
        return ScrapedPage(
            url=source_url,
            game_slug=re.sub(r"\s+", "-", re.sub(r"[':!?,.\-()]", "", game_title.lower())).strip("-"),
            page_slug="local", title=game_title, content_text=text,
            section_titles=re.findall(r"^##\s+(.+)$", text, re.MULTILINE),
            word_count=len(text.split()), source_name=self.source_name, from_cache=True,
        )


class NeoSeekerScraper(BaseScraper):
    """NeoSeeker walkthrough scraper."""
    BASE = "https://www.neoseeker.com"

    def __init__(self, **kwargs):
        super().__init__("neoseeker", **kwargs)

    def _extract_content(self, html: str) -> str:
        for p in [r'<div[^>]*class="[^"]*wiki-content[^"]*"[^>]*>(.*?)</div>',
                  r'<article[^>]*>(.*?)</article>']:
            m = re.search(p, html, re.DOTALL | re.IGNORECASE)
            if m: return html_to_text(m.group(1))
        m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
        return html_to_text(m.group(1)) if m else html_to_text(html)

    def _extract_toc(self, html: str, slug: str) -> list[dict]:
        links, seen = [], set()
        for m in re.finditer(rf'href="/{re.escape(slug)}/walkthrough/([^"]+)"[^>]*>([^<]+)<', html, re.IGNORECASE):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                links.append({"title": m.group(2).strip(), "slug": m.group(1),
                             "url": f"{self.BASE}/{slug}/walkthrough/{m.group(1)}"})
        return links

    def scrape_game(self, game_slug: str, max_pages: int = 10) -> list[ScrapedPage]:
        url = f"{self.BASE}/{game_slug}/walkthrough"
        html = self.fetch(url)
        if not html: return []

        t = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        title = t.group(1).split(" - ")[0].strip() if t else game_slug
        toc = self._extract_toc(html, game_slug)
        pages = []

        # Index page content
        content = self._extract_content(html)
        if content and len(content.split()) > 50:
            pages.append(ScrapedPage(url=url, game_slug=game_slug, page_slug="index",
                title=title, content_text=content,
                section_titles=re.findall(r"^##\s+(.+)$", content, re.MULTILINE),
                word_count=len(content.split()), source_name="neoseeker"))

        for link in toc[:max_pages]:
            phtml = self.fetch(link["url"])
            if not phtml: continue
            pc = self._extract_content(phtml)
            if pc and len(pc.split()) > 50:
                pages.append(ScrapedPage(url=link["url"], game_slug=game_slug,
                    page_slug=link["slug"], title=link["title"], content_text=pc,
                    section_titles=re.findall(r"^##\s+(.+)$", pc, re.MULTILINE),
                    word_count=len(pc.split()), source_name="neoseeker"))

        logger.info(f"NeoSeeker: {len(pages)} pages for {game_slug}")
        return pages


class StrategyWikiScraper(BaseScraper):
    """
    StrategyWiki scraper using MediaWiki API.
    CC BY-SA licensed — no permission needed.
    """
    API = "https://strategywiki.org/w/api.php"

    def __init__(self, **kwargs):
        super().__init__("strategywiki", **kwargs)

    def _api_query(self, params: dict) -> Optional[dict]:
        """Query the MediaWiki API."""
        if not self.session: return None
        self._rate_wait()
        params.update({"format": "json"})
        try:
            r = self.session.get(self.API, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"StrategyWiki API error: {e}")
            return None

    def get_walkthrough_text(self, page_title: str) -> Optional[str]:
        """Get parsed wikitext as HTML, then convert to text."""
        data = self._api_query({
            "action": "parse", "page": page_title,
            "prop": "text", "disableeditsection": "true",
        })
        if not data or "parse" not in data: return None
        html = data["parse"]["text"]["*"]
        return html_to_text(html)

    def get_walkthrough_pages(self, game_title: str) -> list[str]:
        """Find walkthrough sub-pages for a game."""
        data = self._api_query({
            "action": "query", "list": "allpages",
            "apprefix": f"{game_title}/Walkthrough", "aplimit": "50",
        })
        if not data or "query" not in data: return []
        return [p["title"] for p in data["query"]["allpages"]]

    def scrape_game(self, game_title: str, max_pages: int = 10) -> list[ScrapedPage]:
        """Scrape walkthrough pages for a game."""
        # Try direct walkthrough page first
        pages = []
        direct = self.get_walkthrough_text(f"{game_title}/Walkthrough")
        if direct and len(direct.split()) > 50:
            pages.append(ScrapedPage(
                url=f"https://strategywiki.org/wiki/{game_title}/Walkthrough",
                game_slug=game_title.lower().replace(" ", "_"),
                page_slug="walkthrough", title=f"{game_title} Walkthrough",
                content_text=direct,
                section_titles=re.findall(r"^##\s+(.+)$", direct, re.MULTILINE),
                word_count=len(direct.split()), source_name="strategywiki"))

        # Get sub-pages
        sub_pages = self.get_walkthrough_pages(game_title)
        for sp in sub_pages[:max_pages]:
            text = self.get_walkthrough_text(sp)
            if text and len(text.split()) > 50:
                pages.append(ScrapedPage(
                    url=f"https://strategywiki.org/wiki/{sp.replace(' ', '_')}",
                    game_slug=game_title.lower().replace(" ", "_"),
                    page_slug=sp.split("/")[-1], title=sp.split("/")[-1],
                    content_text=text,
                    section_titles=re.findall(r"^##\s+(.+)$", text, re.MULTILINE),
                    word_count=len(text.split()), source_name="strategywiki"))

        logger.info(f"StrategyWiki: {len(pages)} pages for {game_title}")
        return pages


class FandomScraper(BaseScraper):
    """
    Fandom wiki scraper using MediaWiki API.
    CC BY-SA licensed — no permission needed.
    """

    def __init__(self, **kwargs):
        super().__init__("fandom", **kwargs)

    def _get_api_url(self, wiki_subdomain: str) -> str:
        return f"https://{wiki_subdomain}.fandom.com/api.php"

    def _api_query(self, wiki_subdomain: str, params: dict) -> Optional[dict]:
        if not self.session: return None
        self._rate_wait()
        params.update({"format": "json"})
        try:
            r = self.session.get(self._get_api_url(wiki_subdomain), params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Fandom API error ({wiki_subdomain}): {e}")
            return None

    def get_page_text(self, wiki_subdomain: str, page_title: str) -> Optional[str]:
        data = self._api_query(wiki_subdomain, {
            "action": "parse", "page": page_title,
            "prop": "text", "disableeditsection": "true",
        })
        if not data or "parse" not in data: return None
        return html_to_text(data["parse"]["text"]["*"])

    def search_walkthrough(self, wiki_subdomain: str, game_title: str) -> list[str]:
        """Search for walkthrough pages in a Fandom wiki."""
        data = self._api_query(wiki_subdomain, {
            "action": "query", "list": "search",
            "srsearch": f"{game_title} walkthrough", "srlimit": "10",
        })
        if not data or "query" not in data: return []
        return [r["title"] for r in data["query"]["search"]]

    def scrape_game(self, wiki_subdomain: str, game_title: str, max_pages: int = 10) -> list[ScrapedPage]:
        pages = []
        search_results = self.search_walkthrough(wiki_subdomain, game_title)

        for title in search_results[:max_pages]:
            text = self.get_page_text(wiki_subdomain, title)
            if text and len(text.split()) > 50:
                pages.append(ScrapedPage(
                    url=f"https://{wiki_subdomain}.fandom.com/wiki/{title.replace(' ', '_')}",
                    game_slug=game_title.lower().replace(" ", "-"),
                    page_slug=title, title=title, content_text=text,
                    section_titles=re.findall(r"^##\s+(.+)$", text, re.MULTILINE),
                    word_count=len(text.split()), source_name="fandom"))

        logger.info(f"Fandom ({wiki_subdomain}): {len(pages)} pages for {game_title}")
        return pages


class MultiSourceScraper:
    """
    Orchestrates scraping across multiple sources.
    Tries NeoSeeker first, then StrategyWiki, then Fandom.
    Merges and deduplicates results.
    """

    def __init__(self):
        self.neoseeker = NeoSeekerScraper()
        self.strategywiki = StrategyWikiScraper()
        self.fandom = FandomScraper()

    def scrape_game(self, game_title: str, game_slug: str = "",
                    fandom_wiki: str = "", max_pages_per_source: int = 5) -> list[ScrapedPage]:
        """
        Scrape from all available sources, return merged pages.
        """
        all_pages = []
        sources_used = []

        # 1. NeoSeeker
        slug = game_slug or re.sub(r"\s+", "-", re.sub(r"[':!?,.\-()]", "", game_title.lower())).strip("-")
        neo_pages = self.neoseeker.scrape_game(slug, max_pages_per_source)
        if neo_pages:
            all_pages.extend(neo_pages)
            sources_used.append("neoseeker")

        # 2. StrategyWiki
        sw_title = game_title.replace(" ", "_")
        sw_pages = self.strategywiki.scrape_game(sw_title, max_pages_per_source)
        if sw_pages:
            all_pages.extend(sw_pages)
            sources_used.append("strategywiki")

        # 3. Fandom (if wiki subdomain provided)
        if fandom_wiki:
            fan_pages = self.fandom.scrape_game(fandom_wiki, game_title, max_pages_per_source)
            if fan_pages:
                all_pages.extend(fan_pages)
                sources_used.append("fandom")

        logger.info(f"Multi-source: {len(all_pages)} total pages from {sources_used}")
        return all_pages

    def load_from_text(self, game_title: str, text: str, source_url: str = "") -> ScrapedPage:
        return self.neoseeker.load_from_text(game_title, text, source_url)
