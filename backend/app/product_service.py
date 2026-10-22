"""Product-page text extraction and chunking for the PriceLens RAG workflow."""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .config import settings

USER_AGENT = "Mozilla/5.0 (compatible; PriceLensAI/1.0; +https://example.com/bot)"
BLOCKED_HOSTS = {"localhost", "localhost.localdomain", "metadata.google.internal"}


def _validate_public_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid public product-page URL beginning with https:// or http://.")
    host = parsed.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError("This URL cannot be fetched. Please use a public product page.")
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_global:
            raise ValueError("This URL cannot be fetched. Please use a public product page.")
    except ValueError as exc:
        if "cannot be fetched" in str(exc):
            raise
        # It's a hostname rather than an IP literal.
        try:
            addresses = {ipaddress.ip_address(row[4][0]) for row in socket.getaddrinfo(host, None)}
            if addresses and any(not address.is_global for address in addresses):
                raise ValueError("This URL cannot be fetched. Please use a public product page.")
        except socket.gaierror:
            # DNS resolution may work in the HTTP client environment; the request below will give a clear error.
            pass
    return url.strip()


def _clean_text(soup: BeautifulSoup, max_chars: int) -> str:
    for node in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "header", "form", "button"]):
        node.decompose()
    main = soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"}) or soup.body or soup
    text = main.get_text("\n", strip=True)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if len(line) > 2]
    # Remove repeated lines and excessive boilerplate without deleting repeated words in product specs.
    unique, seen = [], set()
    for line in lines:
        key = line.casefold()
        if key not in seen:
            seen.add(key)
            unique.append(line)
    return "\n".join(unique)[:max_chars].strip()


def _extract_meta(soup: BeautifulSoup, key: str) -> str:
    tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
    return str(tag.get("content", "")).strip() if tag else ""


def extract_product(url: str) -> dict:
    url = _validate_public_url(url)
    try:
        with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(20.0, connect=10.0), headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        print(
            f"Product page request failed: HTTP {code}, "
            f"URL host: {urlparse(url).hostname}"
        )

        if code in {401, 403, 429}:
            raise RuntimeError(
                "The retailer blocked automated page reading. "
                "Use 'Add text manually' and paste the product specifications "
                "or description."
            ) from exc

        raise RuntimeError(
            f"The product page returned HTTP {code}. "
            "Check the URL or add the product text manually."
        ) from exc

    except httpx.HTTPError as exc:
        raise RuntimeError("Could not read that product page. The site may block automated access; try adding the product information manually.") from exc

    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and not response.text.lstrip().lower().startswith(("<!doctype html", "<html")):
        raise RuntimeError("That link did not return an HTML product page. Try a normal product-page URL or add the text manually.")
    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("h1")
    title = (title_tag.get_text(" ", strip=True) if title_tag else "") or _extract_meta(soup, "og:title") or (soup.title.get_text(" ", strip=True) if soup.title else "")
    description = _extract_meta(soup, "description") or _extract_meta(soup, "og:description")
    image = _extract_meta(soup, "og:image")
    body_text = _clean_text(soup, settings.max_page_chars)
    pieces = [f"Product title: {title}" if title else "", f"Page description: {description}" if description else "", f"Page content:\n{body_text}" if body_text else ""]
    content = "\n\n".join(piece for piece in pieces if piece).strip()
    if len(content) < 80:
        raise RuntimeError("I could not extract enough product information from this page. Paste the product description or specifications using ‘Add text manually’.")
    host = urlparse(str(response.url)).hostname or urlparse(url).hostname or "product website"
    return {
        "name": title[:300] if title else host,
        "brand": "Unknown",
        "category": "Product",
        "model": title[:300] if title else host,
        "source_url": str(response.url),
        "image": image,
        "description": description[:1200],
        "content": content,
        "source_type": "Product webpage",
        "character_count": len(content),
        "highlights": [line for line in body_text.splitlines() if any(word in line.lower() for word in ("warranty", "battery", "capacity", "display", "processor", "features", "specification", "compatibility"))][:8],
    }


def chunk_text(text: str, chunk_size: int = 1100, overlap: int = 160) -> list[str]:
    """Split content by paragraphs, with a bounded overlap for context continuity."""
    text = re.sub(r"\r", "", (text or "")).strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n{1,}|(?<=[.!?])\s{2,}", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        while len(paragraph) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(paragraph[:chunk_size])
            paragraph = paragraph[chunk_size - overlap:]
        candidate = f"{current}\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            tail = current[-overlap:] if current else ""
            current = f"{tail}\n{paragraph}".strip() if tail else paragraph
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if len(chunk) >= 20]
