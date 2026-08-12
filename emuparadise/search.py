"""Search EmuParadise through the site's own public search endpoint.

`GET /roms/search.php?query=<q>` is what EmuParadise's own search box
submits, so a query costs the site one page render. Its `robots.txt` is
`Allow: /` with no crawl-delay, and the search results are a single page.

**This provider indexes metadata only, and that is not a limitation of the
plugin -- it is the state of the site.** EmuParadise stopped distributing
game files in 2018 and its download pages now say so. Every result therefore
carries `downloadable: "false"`, and `manifest.toml` declares no `importer`.
See the README for the verification.
"""

from __future__ import annotations

from rom_hub_sdk import SearchProvider, SearchResult

from .listing import parse_search, search_url
from .platforms import platform_for


class Search(SearchProvider):
    def search(self, query: str, platform: str | None, limit: int) -> list[SearchResult]:
        limit = max(0, limit)
        text = (query or "").strip()
        if not text or not limit:
            return []

        wanted = str(platform or "").strip().casefold()
        response = self.ctx.http.get(search_url(text))
        # A refusal is an answer. Nothing is retried and nothing is varied.
        if response.status_code != 200:
            return []

        results: list[SearchResult] = []
        for entry in parse_search(response.text):
            mapped = platform_for(entry.section_id)
            # 14 of EmuParadise's 66 sections have no ROMarr platform, or
            # have two and no way to choose. Those results are dropped
            # rather than filed under a guess.
            if mapped is None:
                continue
            if wanted and wanted != mapped.casefold():
                continue
            results.append(SearchResult(
                source_id=entry.path,
                title=entry.title,
                platform=mapped,
                size_bytes=entry.size_bytes,
                url=entry.page_url,
                extra={
                    "emuparadise_id": entry.rom_id,
                    "emuparadise_section_id": entry.section_id,
                    "system": entry.system_name,
                    # Not a capability that failed -- the files are gone.
                    # Stated per result so a caller does not have to learn
                    # it by trying.
                    "downloadable": "false",
                    "playable": "false",
                },
            ))
            if len(results) >= limit:
                break
        return results
