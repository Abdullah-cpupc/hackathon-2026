"""
Website scraping module using Playwright for AI Chat Backend.
Provides JavaScript rendering capability for dynamic websites.
"""

import re
import asyncio
from typing import List, Dict, Any, Optional, Callable, Set
from urllib.parse import urlparse, urldefrag, urljoin
from xml.etree import ElementTree
import requests
import logging

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import html2text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User agent to avoid being blocked
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': DEFAULT_USER_AGENT
}

# HTML to markdown converter
html_converter = html2text.HTML2Text()
html_converter.ignore_links = False
html_converter.ignore_images = True
html_converter.body_width = 0  # Don't wrap lines


def smart_chunk_markdown(markdown: str, max_len: int = 1000) -> List[str]:
    """
    Hierarchically splits markdown by #, ##, ### headers, then by characters.
    Ensures all chunks < max_len while preserving semantic structure.

    IMPORTANT: Handles content without headers and content before first header.
    """
    if not markdown or not markdown.strip():
        return []

    def split_by_header(md, header_pattern):
        """Split markdown by header pattern, INCLUDING content before first header."""
        indices = [m.start() for m in re.finditer(header_pattern, md, re.MULTILINE)]

        # If no headers found, return the entire content as a single chunk
        if not indices:
            return [md.strip()] if md.strip() else []

        # Include content before first header (if any)
        if indices[0] > 0:
            indices.insert(0, 0)

        indices.append(len(md))
        return [md[indices[i]:indices[i+1]].strip() for i in range(len(indices)-1) if md[indices[i]:indices[i+1]].strip()]

    chunks = []

    # First, try splitting by H1 headers
    h1_sections = split_by_header(markdown, r'^# .+$')

    for h1 in h1_sections:
        if len(h1) > max_len:
            # Try splitting by H2 headers
            h2_sections = split_by_header(h1, r'^## .+$')
            for h2 in h2_sections:
                if len(h2) > max_len:
                    # Try splitting by H3 headers
                    h3_sections = split_by_header(h2, r'^### .+$')
                    for h3 in h3_sections:
                        if len(h3) > max_len:
                            # Last resort: character-based chunking
                            for i in range(0, len(h3), max_len):
                                chunk = h3[i:i+max_len].strip()
                                if chunk:
                                    chunks.append(chunk)
                        elif h3:
                            chunks.append(h3)
                elif h2:
                    chunks.append(h2)
        elif h1:
            chunks.append(h1)

    # Final pass: ensure no chunks exceed max_len
    final_chunks = []
    for c in chunks:
        if len(c) > max_len:
            final_chunks.extend([c[i:i+max_len].strip() for i in range(0, len(c), max_len) if c[i:i+max_len].strip()])
        elif c:
            final_chunks.append(c)

    logger.debug(f"smart_chunk_markdown: input={len(markdown)} chars, output={len(final_chunks)} chunks")
    return [c for c in final_chunks if c]


def is_sitemap(url: str) -> bool:
    """Check if URL is a sitemap."""
    return url.endswith('sitemap.xml') or 'sitemap' in urlparse(url).path


def is_txt(url: str) -> bool:
    """Check if URL is a text or markdown file."""
    return url.endswith('.txt') or url.endswith('.md') or url.endswith('.markdown')


def extract_section_info(chunk: str) -> Dict[str, Any]:
    """Extracts headers and stats from a chunk."""
    headers = re.findall(r'^(#+)\s+(.+)$', chunk, re.MULTILINE)
    header_str = '; '.join([f'{h[0]} {h[1]}' for h in headers]) if headers else ''

    return {
        "headers": header_str,
        "char_count": len(chunk),
        "word_count": len(chunk.split())
    }


def _should_skip_url_static(url: str) -> bool:
    """Static helper to check if a URL should be skipped (file URLs, mailto:, etc.)."""
    url_lower = url.lower()

    # Skip mailto: links
    if url_lower.startswith('mailto:'):
        return True

    # Skip file:// URLs
    if url_lower.startswith('file://'):
        return True

    # Skip URLs with file extensions
    file_extensions = [
        '.pdf', '.zip', '.rar', '.7z', '.tar', '.gz',
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.ico',
        '.css', '.js', '.json', '.xml',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.exe', '.dmg', '.deb', '.rpm', '.msi',
        '.woff', '.woff2', '.ttf', '.eot',  # Font files
    ]

    # Check if URL ends with any file extension
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Check for file extension in path
    for ext in file_extensions:
        if path.endswith(ext) or f'.{ext}' in path:
            return True

    # Check query parameters for file downloads
    if 'download' in parsed.query.lower() or 'attachment' in parsed.query.lower():
        return True

    return False


def parse_sitemap(sitemap_url: str) -> List[str]:
    """Parse a sitemap.xml and extract URLs, filtering out file URLs and mailto: links."""
    try:
        resp = requests.get(sitemap_url, headers=DEFAULT_HEADERS, timeout=30)
        urls = []

        if resp.status_code == 200:
            tree = ElementTree.fromstring(resp.content)
            all_urls = [loc.text for loc in tree.findall('.//{*}loc') if loc.text]
            # Filter out file URLs and mailto: links
            urls = [url for url in all_urls if url and not _should_skip_url_static(url)]

        logger.info(f"Parsed {len(urls)} URLs from sitemap: {sitemap_url} (filtered out file URLs and mailto: links)")
        return urls
    except Exception as e:
        logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
        return []


def normalize_url(url: str) -> str:
    """Normalize URL by removing fragments."""
    return urldefrag(url)[0]


class PlaywrightCrawler:
    """
    Async Playwright-based crawler with deduplication support.
    Provides JavaScript rendering capability for dynamic websites.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        max_depth: int = 3,
        page_timeout: int = 30000,  # 30 seconds
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self.page_timeout = page_timeout
        self.progress_callback = progress_callback

        # Deduplication: shared visited set across all crawling operations
        self.visited: Set[str] = set()
        self.results: List[Dict[str, Any]] = []
        self.total_urls_estimate = 0

        # Semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Browser instance (reused across pages)
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    def should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped."""
        return _should_skip_url_static(url)

    def is_same_domain(self, url: str, base_domain: str) -> bool:
        """Check if URL belongs to the same domain."""
        try:
            return urlparse(url).netloc == base_domain
        except:
            return False

    async def start_browser(self):
        """Initialize Playwright browser."""
        if not self.browser:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                ]
            )
            self.context = await self.browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True
            )

    async def stop_browser(self):
        """Clean up Playwright browser."""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def crawl_page(
        self,
        url: str,
        depth: int = 0,
        base_domain: str = None
    ) -> List[str]:
        """
        Crawl a single page and extract content.
        Returns list of discovered internal links (for recursive crawling).
        """
        normalized_url = normalize_url(url)

        # Deduplication check
        if normalized_url in self.visited:
            return []

        if self.should_skip_url(normalized_url):
            return []

        # Mark as visited BEFORE crawling to prevent race conditions
        self.visited.add(normalized_url)

        discovered_links = []

        async with self.semaphore:
            page = None
            try:
                page = await self.context.new_page()

                # Navigate with timeout
                response = await page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=self.page_timeout
                )

                # Wait for JS frameworks (React, Vue, etc.) to render
                # First wait for network to be idle
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except:
                    pass  # Timeout is fine, some pages never fully stop loading

                # Then wait a bit more for any remaining JS to execute
                await asyncio.sleep(3)

                # Also try waiting for body content to be non-empty
                try:
                    await page.wait_for_function(
                        'document.body && document.body.innerText.length > 100',
                        timeout=5000
                    )
                except:
                    pass  # Some pages may have less content

                if not response or response.status >= 400:
                    logger.warning(f"Failed to load {url}: status {response.status if response else 'no response'}")
                    return []

                # Check content type
                content_type = response.headers.get('content-type', '').lower()

                if 'text/html' not in content_type and 'text/plain' not in content_type:
                    logger.debug(f"Skipping non-text content: {content_type} for {url}")
                    return []

                # Report progress
                if self.progress_callback:
                    try:
                        self.progress_callback(
                            url,
                            len(self.visited),
                            max(self.total_urls_estimate, len(self.visited))
                        )
                    except:
                        pass

                # Get page content
                html_content = await page.content()

                # Log HTML size for debugging
                logger.debug(f"Raw HTML size: {len(html_content)} chars for {normalized_url}")

                # Also get the text content directly from the page for comparison
                try:
                    text_content = await page.evaluate('() => document.body ? document.body.innerText : ""')
                    logger.debug(f"Text content size: {len(text_content)} chars for {normalized_url}")
                except:
                    text_content = ""

                # Extract page title
                title = await page.title()
                if not title or title.strip() == '':
                    # Fallback to URL path as title
                    title = urlparse(normalized_url).path.strip('/').split('/')[-1] or urlparse(normalized_url).netloc

                # Convert HTML to markdown
                markdown = html_converter.handle(html_content)

                # Log content details for debugging
                markdown_preview = markdown[:300].replace('\n', ' ') if markdown else '(empty)'
                logger.info(f"📄 Page content extracted:")
                logger.info(f"   URL: {normalized_url}")
                logger.info(f"   Title: {title}")
                logger.info(f"   Markdown length: {len(markdown)} chars")
                logger.info(f"   Preview: {markdown_preview}...")

                # Store result
                self.results.append({
                    'url': normalized_url,
                    'markdown': markdown,
                    'title': title
                })

                logger.info(f"Scraped: {normalized_url} (depth={depth})")

                # Extract links for recursive crawling if not at max depth
                if depth < self.max_depth - 1 and base_domain:
                    # Get all links from page
                    links = await page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(href => href.startsWith('http'));
                    }''')

                    for link in links:
                        normalized_link = normalize_url(link)
                        if (normalized_link not in self.visited and
                            not self.should_skip_url(normalized_link) and
                            self.is_same_domain(normalized_link, base_domain)):
                            discovered_links.append(normalized_link)

            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
            finally:
                if page:
                    await page.close()

        return discovered_links

    async def crawl_recursive(
        self,
        start_urls: List[str],
        max_depth: int = None
    ) -> List[Dict[str, Any]]:
        """
        Recursively crawl starting from given URLs, following internal links.
        Uses BFS (breadth-first search) with depth tracking.
        """
        if max_depth is not None:
            self.max_depth = max_depth

        if not start_urls:
            return []

        # Get base domain from first URL
        base_domain = urlparse(start_urls[0]).netloc

        self.total_urls_estimate = len(start_urls) * 10  # Initial estimate

        try:
            await self.start_browser()

            # BFS-style crawling with depth tracking
            current_depth_urls = [normalize_url(url) for url in start_urls]

            for depth in range(self.max_depth):
                if not current_depth_urls:
                    break

                logger.info(f"Crawling depth {depth}: {len(current_depth_urls)} URLs")

                # Filter already visited
                urls_to_crawl = [
                    url for url in current_depth_urls
                    if url not in self.visited and not self.should_skip_url(url)
                ]

                if not urls_to_crawl:
                    break

                # Crawl all URLs at current depth in parallel
                tasks = [
                    self.crawl_page(url, depth, base_domain)
                    for url in urls_to_crawl
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Collect discovered links for next depth
                next_depth_urls = set()
                for result in results:
                    if isinstance(result, list):
                        next_depth_urls.update(result)

                current_depth_urls = list(next_depth_urls)

                # Update estimate
                self.total_urls_estimate = len(self.visited) + len(current_depth_urls)

        finally:
            await self.stop_browser()

        return self.results

    async def crawl_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Crawl a batch of URLs without following links.
        Used for sitemap URLs.
        """
        if not urls:
            return []

        self.total_urls_estimate = len(urls)

        try:
            await self.start_browser()

            # Normalize and deduplicate
            normalized_urls = []
            for url in urls:
                norm_url = normalize_url(url)
                if norm_url not in self.visited and not self.should_skip_url(norm_url):
                    normalized_urls.append(norm_url)

            # Crawl all in parallel (no link following, depth=max to disable)
            tasks = [
                self.crawl_page(url, depth=self.max_depth, base_domain=None)
                for url in normalized_urls
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            await self.stop_browser()

        return self.results


async def crawl_markdown_file(
    url: str,
    visited: Set[str],
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> List[Dict[str, Any]]:
    """Crawl a .txt or markdown file (no browser needed)."""
    normalized = normalize_url(url)

    if normalized in visited:
        return []

    if progress_callback:
        progress_callback(url, 1, 1)

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        visited.add(normalized)
        # Extract title from filename
        title = urlparse(normalized).path.strip('/').split('/')[-1] or normalized
        return [{'url': normalized, 'markdown': response.text, 'title': title}]
    except Exception as e:
        logger.error(f"Failed to crawl {url}: {e}")
        return []


class WebsiteScraper:
    """Website scraper using Playwright for JavaScript rendering."""

    def __init__(
        self,
        chunk_size: int = 1000,
        max_depth: int = 3,
        max_concurrent: int = 5
    ):
        self.chunk_size = chunk_size
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent

    async def scrape_urls(
        self,
        urls: List[str],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs and return processed content.

        Maintains deduplication across all URL types (sitemap, regular, txt).
        Uses Playwright for JavaScript-rendered pages.

        Args:
            urls: List of URLs to scrape
            progress_callback: Optional callback(url, current_index, total_urls)

        Returns:
            List of dictionaries with 'url' and 'markdown' keys
        """
        if not urls:
            return []

        logger.info(f"Starting scrape of {len(urls)} URLs using Playwright")

        # Shared visited set for deduplication across all operations
        visited: Set[str] = set()
        all_results: List[Dict[str, Any]] = []

        for url_index, url in enumerate(urls, 1):
            try:
                norm_url = normalize_url(url)

                if norm_url in visited:
                    logger.info(f"Skipping already visited URL: {url}")
                    continue

                if is_txt(url):
                    # Text/markdown files - no browser needed
                    logger.info(f"Detected .txt/markdown file: {url}")
                    results = await crawl_markdown_file(url, visited, progress_callback)
                    all_results.extend(results)

                elif is_sitemap(url):
                    # Sitemap - parse XML and batch crawl URLs
                    logger.info(f"Detected sitemap: {url}")
                    sitemap_urls = parse_sitemap(url)

                    if sitemap_urls:
                        # Limit to 50 URLs from sitemap
                        limited_urls = sitemap_urls[:50]

                        if progress_callback:
                            progress_callback(url, url_index, len(urls))

                        # Create crawler with shared visited set
                        crawler = PlaywrightCrawler(
                            max_concurrent=self.max_concurrent,
                            max_depth=1,  # No recursive following for sitemap URLs
                            progress_callback=progress_callback
                        )
                        crawler.visited = visited  # Share visited set

                        results = await crawler.crawl_batch(limited_urls)

                        # Update shared visited set
                        visited.update(crawler.visited)
                        all_results.extend(results)
                else:
                    # Regular URL - recursive crawl
                    logger.info(f"Detected regular URL: {url}")

                    if progress_callback:
                        progress_callback(url, url_index, len(urls))

                    crawler = PlaywrightCrawler(
                        max_concurrent=self.max_concurrent,
                        max_depth=self.max_depth,
                        progress_callback=progress_callback
                    )
                    crawler.visited = visited  # Share visited set

                    results = await crawler.crawl_recursive([url])

                    # Update shared visited set
                    visited.update(crawler.visited)
                    all_results.extend(results)

            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue

        logger.info(f"Scraping completed. Found {len(all_results)} unique documents")
        return all_results

    def process_content_for_chromadb(
        self,
        scrape_results: List[Dict[str, Any]]
    ) -> tuple:
        """
        Process scraped content into format suitable for ChromaDB.

        Args:
            scrape_results: Results from scrape_urls

        Returns:
            Tuple of (ids, documents, metadatas)
        """
        ids, documents, metadatas = [], [], []
        chunk_idx = 0

        for doc in scrape_results:
            url = doc['url']
            markdown = doc['markdown']
            title = doc.get('title', url)  # Fallback to URL if no title

            chunks = smart_chunk_markdown(markdown, max_len=self.chunk_size)

            # Log chunking details
            logger.info(f"📦 Chunking page: {url}")
            logger.info(f"   Title: {title}")
            logger.info(f"   Markdown length: {len(markdown)} chars")
            logger.info(f"   Chunks created: {len(chunks)}")

            if len(chunks) == 0 and len(markdown) > 0:
                logger.warning(f"   ⚠️  WARNING: Page has content but produced 0 chunks!")
                logger.warning(f"   Markdown preview: {markdown[:500]}")

            for i, chunk in enumerate(chunks):
                ids.append(f"chunk-{chunk_idx}")
                documents.append(chunk)

                meta = extract_section_info(chunk)
                meta["chunk_index"] = chunk_idx
                meta["source"] = url
                meta["title"] = title
                metadatas.append(meta)

                # Log first few chunks per page
                if i < 2:
                    chunk_preview = chunk[:150].replace('\n', ' ')
                    logger.info(f"   Chunk {i}: {len(chunk)} chars - {chunk_preview}...")

                chunk_idx += 1

        logger.info(f"Processed content into {len(documents)} chunks")
        return ids, documents, metadatas
