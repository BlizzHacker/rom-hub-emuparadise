# EmuParadise provider for ROM Hub / ROMarr

An RPP v1 provider that searches [EmuParadise](https://www.emuparadise.me).

| Capability | Status |
|---|---|
| `search` | Implemented — the site's own `GET /roms/search.php` endpoint |
| `importer` | **Absent — EmuParadise no longer hosts game files** |
| `stream` | **Absent — EmuParadise hosts no player** |

## Read this first: this is a metadata provider, and that is the site's doing

**EmuParadise stopped distributing game files in 2018.** This was verified
against the live site rather than assumed, because the browse tree is still
completely healthy and it is easy to mistake for a working download source:
`robots.txt` is `Allow: /`, the section index and the
`Games-Starting-With-<letter>` pages all return 200, and the section counts
render live (NES 2,774; MAME 34,305; PSX 5,134).

The download pages also still render the entire download flow, including the
words *"We are preparing your download… Please scroll down to get your download
link!"* — and then say the game is unavailable. Three titles, checked
individually on 2026-08-12:

| Title | Page | Result |
|---|---|---|
| Castlevania (USA) | `/…/55051-download` | `This game is unavailable` |
| Contra (USA) | `/…/55137-download` | `This game is unavailable` |
| Final Fantasy (USA) | `/…/55514-download` | `This game is unavailable` |

So the download *chrome* survived the removal and the files did not. An
`importer` here would be a capability that refuses every call it ever
received, which is worse than not offering one — it would put a download
button in front of an operator that can never work. It is therefore **not
declared in `manifest.toml`**, and every search result carries
`downloadable: "false"`.

What this provider is good for: EmuParadise's catalogue is large, well
labelled and carries per-title regions and sizes, so it is a reasonable
**metadata and discovery** source. Use it to find out what exists and what a
release is called. Get the file somewhere else.

## Platforms

EmuParadise publishes **66 sections** (`/roms-isos-games.php`). **52 map** to a
ROMarr platform; 14 are refused. Every slug was checked with
`romarr.platforms.resolve()`, and `tests/test_platforms.py` re-runs that check
whenever ROMarr is importable.

The mapping is keyed on the **numeric section id**, not the section name —
the id arrives twice on every result (`data-filter` on the link, `sysid` on
the system link beside it) and is stable, whereas the display name is
presentational and a copy edit upstream would break a name-keyed table.

The 14 refusals, with the reason each one is refused:

| Section | Why |
|---|---|
| Nokia N-Gage, Sony PocketStation, Bandai Playdia, Acorn Archimedes, Acorn BBC Micro, Acorn Electron | ROMarr has no platform for these |
| ScummVM | A game engine, not a machine |
| Neo Geo | ROMarr carries `neogeoaes` *and* `neogeomvs`; the section name does not choose |
| Neo Geo Pocket / Pocket Color (combined) | ROMarr splits these; the section is both |
| PSX on PSP | A PlayStation game repackaged for PSP — `psx` and `psp` are both defensible |
| Amiga CD | Ambiguous between CDTV and CD32 hardware |
| Complete ROM Sets, Miscellaneous Games, Abandonware Games | Deliberately heterogeneous — no single platform |

Results in those sections are **dropped**, never emitted under a guessed slug.

Two collapses *are* applied on purpose: MAME, NAOMI and the three Capcom Play
Systems all go to `arcade` (ROMarr models arcade as one platform), and both
Commodore 64 sections, both ZX Spectrum sections, and the PlayStation demo
section fold onto `c64`, `zxs` and `psx` respectively — those are curations of
a catalogue rather than separate machines.

## Install

```sh
rom-hub plugin install https://git.moveweight.com/BlizzHacker/romarr-plugin-emuparadise --ref v0.1.0
rom-hub search "contra" --platform nes
```

The `source_id` is the detail path, `<Section>/<Title>/<id>`.

Path validation here is **structural rather than a character allowlist**,
unlike the Retrostic and RomuLation providers. EmuParadise titles legitimately
contain `( ) [ ] & , . : ! ~` and double hyphens — a real MAME entry is
`Contra_(US_--_Asia,_set_1)` — so enumerating the legal characters would be a
guess that silently drops real results. Instead a path must be exactly three
segments, with no empty or dot segment, a numeric id, and none of the
characters that would change what a URL means.

To list it in ROMarr's **Hub → Plugins** catalogue:

```sh
rom-hub catalog add moveweight-emuparadise \
  https://git.moveweight.com/BlizzHacker/romarr-plugin-emuparadise/raw/tag/v0.1.0/catalog/plugins.json
rom-hub catalog refresh
```

## Config

| Key | Default | Meaning |
|---|---|---|
| `collection` | `EmuParadise` | RomM collection name |

A non-200 — 403, 429, 503 — returns no results and is **not retried**.

## Test

```sh
ROM_HUB_SRC=/opt/rom-hub/src PYTHONPATH=/opt/romarr pytest tests/ -q
```

112 passing. `PYTHONPATH` to ROMarr is what makes the platform-slug checks run
rather than skip.

## Terms

This provider reads only the metadata EmuParadise publishes on its own search
page. It downloads nothing — there is nothing there to download. It grants no
redistribution rights. Operators are responsible for using it in accordance
with applicable law and the source's terms.

## License

MIT — see `LICENSE`.
