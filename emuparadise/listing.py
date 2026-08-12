"""Parse EmuParadise's search results, and rebuild its URLs safely.

`GET /roms/search.php?query=<q>` renders one `<div class="roms">` per hit:

    <div class="roms">
      <a data-filter="13" href="/Nintendo_Entertainment_System_ROMs/Contra_(USA)/55137">Contra (USA) ROM</a><br>
      <b>System:</b> <a href="/roms/roms.php?sysid=13" class="sysname">Nintendo Entertainment System</a>
      <b>Size:</b> 92K <br><br>
    </div>

Which is unusually generous: the section id arrives twice (`data-filter` and
`sysid`), the ROM id is the last path segment, and a size is printed. So the
parse does not have to infer the platform from a display name.

**Path validation is by shape, not by character allowlist.** Unlike the
Retrostic and RomuLation providers -- whose corpora are narrow enough to
enumerate -- EmuParadise titles legitimately contain `( ) [ ] & , . : ! ~`
and a double-hyphen, e.g.
`M.A.M.E._-_Multiple_Arcade_Machine_Emulator_ROMs/Contra_(US_--_Asia,_set_1)/12021`.
Trying to list the legal characters would be a guess that quietly drops real
results. So the rule is structural instead, and strict about the things that
actually matter: exactly three segments, no empty segment, no `.` or `..`
segment, a numeric id, and none of the characters that would change what a
URL means (`/ ? # % \\`, whitespace, control characters).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import quote

BASE = "https://www.emuparadise.me"

#: Characters that would change what a URL means if they rode inside a
#: segment. Whitespace and controls are covered separately.
_UNSAFE = set('/?#%\\"\'<>')

#: Characters kept literal when building a URL: every one of them appears in
#: real EmuParadise titles and is part of the id, so escaping them would
#: produce a link that 404s.
_PATH_SAFE = "/()[]&,.!~+-_"

#: "Contra (USA) ROM" / "Neo Contra ISO" -- the medium is appended to the
#: link text and is not part of the title.
_TITLE_SUFFIX = re.compile(r"\s+(ROMs?|ISOs?|Game)\s*$", re.I)

#: "92K", "13M", "1.1G", "512" (bytes).
_SIZE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)\s*([KMGT])?$", re.I)

_UNITS = {"k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}

_HREF = re.compile(r"^/([^?#]+?)/?$")


@dataclass(frozen=True)
class Entry:
    """One search hit, validated into parts that rebuild a URL."""

    path: str            # "Nintendo_Entertainment_System_ROMs/Contra_(USA)/55137"
    section: str         # "Nintendo_Entertainment_System_ROMs"
    rom_id: str          # "55137"
    title: str           # "Contra (USA)"
    section_id: str = ""     # "13" -- from data-filter
    system_name: str = ""    # "Nintendo Entertainment System"
    size_bytes: int | None = None

    @property
    def page_url(self) -> str:
        # Titles carry (), [], & and commas, which are legal in a path and
        # are part of the id. Percent-encode the rest without mangling them.
        return f"{BASE}/{quote(self.path, safe=_PATH_SAFE)}"


def split_path(value: str) -> tuple[str, str, str] | None:
    """`"<Section>/<Title>/<id>"` -> `(path, section, rom_id)`, or nothing.

    The single gate for every path, whether parsed from a page or handed
    back later as a `source_id`. Structural rather than a character
    allowlist -- see the module docstring for why that is the right trade
    on this site specifically.
    """
    text = str(value or "").strip().strip("/")
    if not text:
        return None
    parts = text.split("/")
    if len(parts) != 3:
        return None
    section, title, rom_id = parts
    if not section or not title or not rom_id.isdecimal():
        return None
    for segment in (section, title):
        if segment in (".", ".."):
            return None
        if any(c in _UNSAFE or c.isspace() or ord(c) < 32 for c in segment):
            return None
    return text, section, rom_id


def parse_size(text: str) -> int | None:
    """`"92K"` -> 94208, `"1.1G"` -> 1181116006, or nothing.

    Binary units: a ROM listing that says 92K means 92 KiB, and reporting a
    number 2.4% off would be worse than reporting none.
    """
    found = _SIZE.match((text or "").strip())
    if not found:
        return None
    value = float(found.group(1))
    unit = (found.group(2) or "").casefold()
    return int(value * _UNITS.get(unit, 1))


def clean_title(text: str) -> str:
    """`"Contra (USA) ROM"` -> `"Contra (USA)"`."""
    return _TITLE_SUFFIX.sub("", (text or "").strip()).strip()


class _ResultParser(HTMLParser):
    """Collect one record per `<div class="roms">`.

    Keyed on the div rather than on a table row, because that is the
    structure EmuParadise actually uses here -- and because the block holds
    two anchors (the ROM and its system) whose roles are distinguished by
    `href` shape, not by position.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.records: list[dict] = []
        self._rec: dict | None = None
        self._depth = 0
        self._capture: str | None = None
        self._buf: list[str] = []
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "div":
            if self._rec is not None:
                self._depth += 1
            elif "roms" in (attr.get("class") or "").split():
                self._rec = {"path": None, "title": "", "section_id": "",
                             "system": "", "size": ""}
                self._depth = 1
                self._text = []
            return
        if self._rec is None:
            return
        if tag == "a":
            href = (attr.get("href") or "").strip()
            found = _HREF.match(href)
            path = split_path(found.group(1)) if found else None
            if path and self._rec["path"] is None:
                self._rec["path"] = path[0]
                self._rec["section_id"] = (attr.get("data-filter") or "").strip()
                self._capture, self._buf = "title", []
            elif "sysid=" in href:
                self._capture, self._buf = "system", []

    def handle_endtag(self, tag: str) -> None:
        if self._rec is None:
            return
        if tag == "a" and self._capture:
            text = " ".join("".join(self._buf).split())
            self._rec[self._capture] = self._rec[self._capture] or text
            self._capture, self._buf = None, []
        elif tag == "div":
            self._depth -= 1
            if self._depth <= 0:
                if self._rec["path"]:
                    # "Size:" is loose text in the block rather than its own
                    # element, so it is read off the accumulated run.
                    blob = " ".join("".join(self._text).split())
                    found = re.search(r"Size:\s*([0-9.]+[KMGT]?)", blob, re.I)
                    self._rec["size"] = found.group(1) if found else ""
                    self.records.append(self._rec)
                self._rec, self._depth, self._text = None, 0, []

    def handle_data(self, data: str) -> None:
        if self._rec is None:
            return
        self._text.append(data)
        if self._capture:
            self._buf.append(data)


def parse_search(markup: str) -> list[Entry]:
    """Every ROM on one search-results page, in the order rendered.

    Blocks without a valid path are skipped rather than raised on: a search
    that found nothing must return empty rather than fail.
    """
    parser = _ResultParser()
    parser.feed(markup or "")
    parser.close()

    out: list[Entry] = []
    seen: set[str] = set()
    for rec in parser.records:
        parts = split_path(rec["path"])
        if parts is None or parts[0] in seen:
            continue
        path, section, rom_id = parts
        title = clean_title(rec["title"])
        if not title:
            continue
        seen.add(path)
        out.append(Entry(
            path=path,
            section=section,
            rom_id=rom_id,
            title=title,
            section_id=rec["section_id"],
            system_name=rec["system"],
            size_bytes=parse_size(rec["size"]),
        ))
    return out


def search_url(query: str) -> str:
    """The request EmuParadise's own search box sends."""
    from urllib.parse import urlencode

    return f"{BASE}/roms/search.php?{urlencode({'query': query})}"
