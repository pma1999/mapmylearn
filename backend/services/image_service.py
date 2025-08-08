import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("image_service.wikimedia")

WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"

class ImageResult(Dict[str, Any]):
    """Simple dictionary-based container for image search results.

    Keys:
        url: Direct image URL (preferably https://upload.wikimedia.org/...)
        title: Image title
        file_page_url: Wikimedia file page URL
        width: Image width (int)
        height: Image height (int)
        mime: MIME type string
        license: Optional license string if available
        thumbnail_url: Optional thumbnail URL if available
    """
    pass


async def _fetch_json(client: httpx.AsyncClient, params: Dict[str, Any], timeout: float) -> Optional[Dict[str, Any]]:
    try:
        resp = await client.get(WIKIMEDIA_API_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.debug(f"Wikimedia API request failed: {e}")
        return None


def _is_acceptable_mime(mime: Optional[str]) -> bool:
    if not mime:
        return False
    mime = mime.lower()
    return any(
        mime.startswith(prefix)
        for prefix in ["image/jpeg", "image/png", "image/webp", "image/svg", "image/gif"]
    )


def _build_file_page_url(title: str) -> str:
    # Wikimedia file pages use /wiki/File:...
    return f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}"


def _filter_and_map_results(data: Dict[str, Any], min_width: int = 600, min_height: int = 400) -> List[ImageResult]:
    pages = (data.get("query") or {}).get("pages") or {}
    results: List[ImageResult] = []

    for _, page in pages.items():
        title = page.get("title") or ""
        imageinfo = page.get("imageinfo") or []
        if not imageinfo:
            continue
        info = imageinfo[0]
        url = info.get("url")
        mime = info.get("mime")
        width = info.get("width") or 0
        height = info.get("height") or 0

        if not url or not url.startswith("https://upload.wikimedia.org/"):
            continue
        if not _is_acceptable_mime(mime):
            continue
        if isinstance(width, int) and isinstance(height, int):
            if width < min_width or height < min_height:
                # Prefer reasonably sized images
                continue

        thumb_url = info.get("thumburl")
        results.append(
            ImageResult(
                url=url,
                title=title,
                file_page_url=_build_file_page_url(title),
                width=width,
                height=height,
                mime=mime,
                license=(info.get("extmetadata") or {}).get("LicenseShortName", {}).get("value") if info.get("extmetadata") else None,
                thumbnail_url=thumb_url,
            )
        )

    return results


async def search_wikimedia_images(
    query: str,
    count: int = 2,
    language: str = "en",
    timeout_seconds: float = 2.0,
) -> List[ImageResult]:
    """Search Wikimedia Commons for images by keyword query.

    Uses MediaWiki API with generator=search over namespace 6 (File:),
    retrieving basic imageinfo including direct URLs.
    """
    if not query or not query.strip():
        return []

    params = {
        "action": "query",
        "format": "json",
        "origin": "*",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,  # File namespace
        "gsrlimit": max(1, min(count * 3, 12)),  # fetch extra to filter
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        # Provide a thumbnail to screen for min sizes when originals are huge
        "iiurlwidth": 1024,
        "iiurlheight": 1024,
        "uselang": language,
    }

    async with httpx.AsyncClient(headers={"User-Agent": "Learni/1.0 (image enrichment)"}) as client:
        data = await _fetch_json(client, params, timeout_seconds)
        if not data:
            return []
        results = _filter_and_map_results(data)
        # Limit to requested count
        return results[: max(0, count)]


async def search_best_image(
    queries: List[str],
    language: str = "en",
    timeout_seconds: float = 2.0,
) -> Optional[ImageResult]:
    """Try multiple queries and return the first acceptable image result."""
    for q in queries:
        images = await search_wikimedia_images(q, count=1, language=language, timeout_seconds=timeout_seconds)
        if images:
            return images[0]
        # small delay to be polite
        await asyncio.sleep(0.05)
    return None

