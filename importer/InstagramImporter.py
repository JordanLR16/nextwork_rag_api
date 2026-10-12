import json
import re
from html import unescape
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .ImportedContent import ImportedContent, RecipeImport
from .ImportMedia import ImportMedia


class InstagramImporter(ImportMedia):
    """Import public Instagram post metadata and parse recipe text when present."""

    _SUPPORTED_PATH_RE = re.compile(r"^/(p|reel|reels|tv)/([^/?#]+)/?", re.IGNORECASE)
    _META_RE = re.compile(
        r"<meta\s+[^>]*(?:property|name)=[\"'](?P<name>[^\"']+)[\"'][^>]*content=[\"'](?P<content>[^\"']*)[\"'][^>]*>",
        re.IGNORECASE,
    )
    _META_RE_REVERSED = re.compile(
        r"<meta\s+[^>]*content=[\"'](?P<content>[^\"']*)[\"'][^>]*(?:property|name)=[\"'](?P<name>[^\"']+)[\"'][^>]*>",
        re.IGNORECASE,
    )
    _JSON_LD_RE = re.compile(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(?P<body>.*?)</script>",
        re.IGNORECASE | re.DOTALL,
    )
    _SECTION_MARKERS = {
        "ingredients": re.compile(r"\b(?:ingredients?|you(?:'|’)ll need|what you(?:'|’)ll need)\b\s*:?", re.IGNORECASE),
        "instructions": re.compile(r"\b(?:instructions?|directions?|method|steps?|recipe)\b\s*:?", re.IGNORECASE),
        "substitutions": re.compile(r"\b(?:substitutions?|swaps?|alternatives?)\b\s*:?", re.IGNORECASE),
    }
    _STOP_MARKERS = re.compile(
        r"\b(?:save|follow|comment|share|like|link in bio|#\w+|prep time|cook time|serves|servings)\b",
        re.IGNORECASE,
    )

    def __init__(self, timeout: int = 10):
        """Store the network timeout used when fetching Instagram pages."""
        self.timeout = timeout

    def can_handle(self, url: str) -> bool:
        """Return whether the URL is a supported Instagram post-style URL."""
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return host.endswith("instagram.com") and bool(self._SUPPORTED_PATH_RE.match(parsed.path))

    def import_media(self, url: str, transcript: str | None = None, html: str | None = None) -> ImportedContent:
        """Fetch or read post HTML, extract metadata, and attach a parsed recipe when possible."""
        if not self.can_handle(url):
            raise ValueError(f"Unsupported Instagram URL: {url}")

        page_html = html if html is not None else self._fetch_html(url)
        metadata = self._extract_metadata(page_html)
        shortcode = self._extract_shortcode(url)
        description = self._best_description(metadata)
        author_name = self._extract_author(metadata) or "Unknown Author"
        title = self._extract_title(metadata, description)
        media_type = self._media_type(url, metadata)
        recipe = self._build_recipe(
            url=url,
            author_name=author_name,
            fallback_title=title or "Instagram Recipe",
            caption=description,
            transcript=transcript,
        )

        return ImportedContent(
            platform="instagram",
            original_url=url,
            external_id=shortcode,
            author_name=author_name,
            title=title,
            description=description,
            media_type=media_type,
            thumbnail_url=metadata.get("og:image") or metadata.get("twitter:image"),
            media_url=metadata.get("og:video") or metadata.get("og:video:secure_url"),
            transcript=transcript,
            recipe=recipe,
            metadata=metadata,
            status="recipe_imported" if recipe else "metadata_imported",
        )

    def _fetch_html(self, url: str) -> str:
        """Download the public Instagram HTML with browser-like request headers."""
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def _extract_metadata(self, html: str) -> dict[str, Any]:
        """Collect Open Graph, Twitter card, standard meta, and JSON-LD metadata."""
        metadata: dict[str, Any] = {}
        for match in [*self._META_RE.finditer(html), *self._META_RE_REVERSED.finditer(html)]:
            metadata[match.group("name").strip()] = unescape(match.group("content").strip())

        for match in self._JSON_LD_RE.finditer(html):
            try:
                payload = json.loads(unescape(match.group("body").strip()))
            except json.JSONDecodeError:
                continue
            self._merge_json_ld(metadata, payload)
        return metadata

    def _merge_json_ld(self, metadata: dict[str, Any], payload: Any) -> None:
        """Flatten useful JSON-LD fields into the shared metadata dictionary."""
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            metadata.setdefault("jsonld:type", item.get("@type"))
            metadata.setdefault("jsonld:headline", item.get("headline") or item.get("name"))
            metadata.setdefault("jsonld:description", item.get("description"))
            metadata.setdefault("jsonld:thumbnail", self._first_value(item.get("thumbnailUrl") or item.get("image")))
            author = item.get("author")
            if isinstance(author, dict):
                metadata.setdefault("jsonld:author", author.get("name"))
            elif isinstance(author, str):
                metadata.setdefault("jsonld:author", author)

    def _extract_shortcode(self, url: str) -> str | None:
        """Pull the Instagram shortcode from the supported URL path."""
        match = self._SUPPORTED_PATH_RE.match(urlparse(url).path)
        return match.group(2) if match else None

    def _best_description(self, metadata: dict[str, Any]) -> str | None:
        """Choose the most useful caption or description field from extracted metadata."""
        return self._clean_text(
            metadata.get("og:description")
            or metadata.get("twitter:description")
            or metadata.get("description")
            or metadata.get("jsonld:description")
        )

    def _extract_author(self, metadata: dict[str, Any]) -> str | None:
        """Infer the author from Instagram title metadata or JSON-LD."""
        site = metadata.get("og:title") or metadata.get("twitter:title") or ""
        match = re.search(r"(?:@[\w.]+|[\w.]+)\s+on Instagram", site, re.IGNORECASE)
        if match:
            return match.group(0).split(" on Instagram", 1)[0].strip()
        return self._clean_text(metadata.get("jsonld:author"))

    def _extract_title(self, metadata: dict[str, Any], description: str | None) -> str | None:
        """Pick a post title, falling back to a short title-like caption line."""
        for key in ("jsonld:headline", "og:title", "twitter:title", "title"):
            title = self._clean_text(metadata.get(key))
            if title:
                title = re.sub(r"\s*[-|]\s*Instagram.*$", "", title, flags=re.IGNORECASE).strip()
                if title and not title.lower().endswith("on instagram"):
                    return title
        return self._title_from_text(description)

    def _media_type(self, url: str, metadata: dict[str, Any]) -> str:
        """Classify the import as video for reels or video metadata, otherwise image."""
        if "/reel/" in urlparse(url).path.lower() or metadata.get("og:video") or metadata.get("og:video:secure_url"):
            return "video"
        return "image"

    def _build_recipe(
        self,
        url: str,
        author_name: str,
        fallback_title: str,
        caption: str | None,
        transcript: str | None,
    ) -> RecipeImport | None:
        """Build a recipe from the caption, or from the transcript when the caption has none."""
        caption_recipe = self._parse_recipe_text(caption or "")
        transcript_recipe = self._parse_recipe_text(transcript or "") if not caption_recipe else None
        parsed = caption_recipe or transcript_recipe
        if not parsed:
            return None

        title = parsed.get("title") or self._title_from_text(caption) or fallback_title
        description = self._clean_text(caption)
        return RecipeImport(
            title=title,
            author_name=author_name,
            ingredients=parsed["ingredients"],
            instructions=parsed["instructions"],
            substitutions=parsed.get("substitutions", []),
            tagline=parsed.get("tagline"),
            description=description,
            tags=self._extract_tags(" ".join([caption or "", transcript or ""])),
            source_url=url,
            source_platform="instagram",
        )

    def _parse_recipe_text(self, text: str) -> dict[str, Any] | None:
        """Parse ingredients and instructions from structured or recipe-like text."""
        clean = self._normalize_text(text)
        if not clean:
            return None

        ingredients = self._extract_section(clean, "ingredients")
        instructions = self._extract_section(clean, "instructions")
        substitutions = self._extract_section(clean, "substitutions")

        if not ingredients:
            ingredients = self._infer_ingredients(clean)
        if not instructions:
            instructions = self._infer_instructions(clean)

        if not ingredients or not instructions:
            return None

        return {
            "title": self._title_from_text(clean),
            "ingredients": ingredients,
            "instructions": "\n".join(instructions),
            "substitutions": substitutions,
            "tagline": self._first_sentence(clean),
        }

    def _extract_section(self, text: str, section: str) -> list[str]:
        """Extract a named recipe section bounded by the next known section marker."""
        marker = self._SECTION_MARKERS[section]
        match = marker.search(text)
        if not match:
            return []

        start = match.end()
        end = len(text)
        for name, other_marker in self._SECTION_MARKERS.items():
            if name == section:
                continue
            other = other_marker.search(text, start)
            if other:
                end = min(end, other.start())
        body = text[start:end].strip(" :-\n\t")
        return self._split_list_items(body)

    def _split_list_items(self, body: str) -> list[str]:
        """Split section text into items and drop short social call-to-action lines."""
        if not body:
            return []

        lines = []
        for raw_line in re.split(r"[\n\r]+|(?:\s+[•·]\s+)", body):
            line = re.sub(r"^\s*(?:[-*•·]|\d+[.)])\s*", "", raw_line).strip()
            if not line:
                continue
            if self._STOP_MARKERS.search(line) and len(line.split()) < 8:
                continue
            if len(line) > 180 and "," in line:
                lines.extend(part.strip() for part in line.split(",") if part.strip())
            else:
                lines.append(line)
        if len(lines) <= 1 and ";" in body:
            lines = [part.strip(" .") for part in body.split(";") if part.strip()]
        return [item for item in lines if item]

    def _infer_ingredients(self, text: str) -> list[str]:
        """Find ingredient-like phrases that start with an amount and unit."""
        candidates: list[str] = []
        amount_re = re.compile(
            r"(?:(?:\d+\s*/\s*\d+|\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
            r"(?:cups?|tbsp|tablespoons?|tsp|teaspoons?|oz|ounces?|lb|pounds?|grams?|g|kg|ml|l|cloves?|cans?|packs?)"
            r"[^,.!\n]*)",
            re.IGNORECASE,
        )
        seen = set()
        for match in amount_re.finditer(text):
            item = match.group(0).strip(" .,-")
            key = item.lower()
            if item and key not in seen:
                candidates.append(item)
                seen.add(key)
        return candidates

    def _infer_instructions(self, text: str) -> list[str]:
        """Find instruction-like sentences by looking for common cooking verbs."""
        verbs = r"add|bake|blend|boil|chop|combine|cook|dice|fold|fry|heat|mix|pour|roast|saute|sauté|season|serve|simmer|stir|top|whisk"
        instructions = []
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip()
            if re.search(rf"\b({verbs})\b", sentence, re.IGNORECASE):
                instructions.append(sentence)
        return instructions

    def _extract_tags(self, text: str) -> list[str]:
        """Return unique lowercase hashtag names from caption and transcript text."""
        tags = []
        for tag in re.findall(r"#([A-Za-z0-9_]+)", text):
            normalized = tag.lower()
            if normalized not in tags:
                tags.append(normalized)
        return tags

    def _title_from_text(self, text: str | None) -> str | None:
        """Use the first short line of text as a possible recipe title."""
        if not text:
            return None
        first_line = self._clean_text(text.splitlines()[0])
        if not first_line:
            return None
        first_line = re.sub(r"^.*?:\s*", "", first_line)
        first_line = re.split(r"\b(?:ingredients?|recipe|directions?|instructions?)\b", first_line, flags=re.IGNORECASE)[0]
        first_line = first_line.strip(" -:|")
        if not first_line or len(first_line.split()) > 12:
            return None
        return first_line[:120]

    def _first_sentence(self, text: str) -> str | None:
        """Return a concise first sentence suitable for a recipe tagline."""
        match = re.search(r"(.{15,220}?[.!?])(?:\s|$)", text)
        return self._clean_text(match.group(1)) if match else None

    def _normalize_text(self, text: str) -> str:
        """Decode HTML entities and normalize spacing while preserving line breaks."""
        text = unescape(text or "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _clean_text(self, value: Any) -> str | None:
        """Normalize a value into non-empty text, returning None for blanks."""
        if value is None:
            return None
        text = self._normalize_text(str(value))
        return text or None

    def _first_value(self, value: Any) -> Any:
        """Return the first item from a list, or the original scalar value."""
        if isinstance(value, list):
            return value[0] if value else None
        return value
