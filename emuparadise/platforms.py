"""EmuParadise section id -> RomM/ROMarr platform slug.

Keyed on the **numeric section id**, not on the section's name. EmuParadise
puts that id in three places on a results page -- `data-filter="13"` on the
link, `sysid=13` on the system link beside it, and the last-but-one path
segment is *not* it -- and the id is stable while the display name is
presentational. Keying on `"Nintendo Entertainment System"` would mean a
mapping that a copy edit upstream could break.

Exact-match, no fallback. A section id that is not listed resolves to
nothing and its results are dropped, because guessing files a ROM under the
wrong machine and nothing afterwards reports it.

**All 52 values were checked with `romarr.platforms.resolve()`** and
`tests/test_platforms.py` re-runs that check whenever ROMarr is importable.

The ids come from EmuParadise's own `/roms-isos-games.php`, which lists **66
sections** (surveyed 2026-08-12). 52 map; the other 14 are in `UNMAPPED`
below with the reason each one is refused.
"""

#: EmuParadise section id -> ROMarr platform slug.
PLATFORMS: dict[int, str] = {
    1: "dc",                                    # Sega Dreamcast
    2: "psx",                                   # Sony PlayStation
    3: "saturn",                                # Sega Saturn
    4: "amiga",                                 # Commodore Amiga
    5: "snes",                                  # Super Nintendo
    6: "genesis-slash-megadrive",               # Genesis / Mega Drive
    7: "arcade",                                # M.A.M.E.
    8: "neo-geo-cd",                            # Neo-Geo CD
    9: "n64",                                   # Nintendo 64
    10: "segacd",                               # Sega CD
    11: "gbc",                                  # Game Boy Color
    12: "gb",                                   # Game Boy
    13: "nes",                                  # NES
    14: "gamegear",                             # Game Gear
    15: "sms",                                  # Master System
    16: "turbografx16--1",                      # PC Engine / TurboGrafx-16
    18: "turbografx-16-slash-pc-engine-cd",     # PC Engine CD / TurboGrafx CD
    19: "philips-cd-i",                         # Philips CD-i
    20: "3do",                                  # Panasonic 3DO
    22: "amiga-cd32",                           # Amiga CD32
    23: "sharp-x68000",                         # Sharp X68000
    24: "apple2",                               # Apple ][
    25: "psx",                                  # PlayStation demo discs -- see NOTE
    27: "virtualboy",                           # Virtual Boy
    28: "lynx",                                 # Atari Lynx
    29: "fds",                                  # Famicom Disk System
    30: "arcade",                               # Sega NAOMI
    31: "gba",                                  # Game Boy Advance
    32: "nds",                                  # Nintendo DS
    33: "c64",                                  # C64 Preservation Project
    34: "c64",                                  # C64 (Tapes)
    35: "zxs",                                  # ZX Spectrum (Z80)
    36: "zxs",                                  # ZX Spectrum (Tapes)
    39: "wonderswan",                           # WonderSwan
    40: "wonderswan-color",                     # WonderSwan Color
    41: "ps2",                                  # PlayStation 2
    42: "ngc",                                  # GameCube
    43: "xbox",                                 # Xbox
    44: "psp",                                  # PSP
    47: "atari7800",                            # Atari 7800
    48: "atari5200",                            # Atari 5200
    49: "atari2600",                            # Atari 2600
    50: "jaguar",                               # Atari Jaguar
    54: "arcade",                               # Capcom Play System 1
    55: "arcade",                               # Capcom Play System 2
    57: "atari8bit",                            # Atari 8-bit Family
    61: "sega32",                               # Sega 32X
    62: "acpc",                                 # Amstrad CPC
    63: "atari-st",                             # Atari ST
    64: "pc-fx",                                # NEC PC-FX
    66: "arcade",                               # Capcom Play System 3
    68: "wii",                                  # Nintendo Wii
}

# NOTE on 25, "Sony Playstation - Demos". A demo disc is a PlayStation disc:
# same machine, same medium, same emulator. The section is a curation of the
# catalogue rather than a separate platform, so it maps to `psx` -- which is
# the same reasoning that puts both Commodore 64 sections on `c64` and both
# ZX Spectrum sections on `zxs`.

#: Sections this provider will not answer for, and why. Data rather than
#: prose so `tests/test_platforms.py` can assert the two sets do not overlap
#: and that together they account for all 66 published sections.
UNMAPPED: dict[int, str] = {
    17: "Nokia N-Gage -- ROMarr has no N-Gage platform",
    21: "ScummVM -- a game engine, not a machine; ROMarr has no slug for it",
    26: (
        "Neo Geo -- ROMarr carries neogeoaes and neogeomvs and the section "
        "name does not decide between them"
    ),
    37: (
        "Complete ROM Sets -- one file spanning a whole system, and the "
        "section mixes systems, so there is no single platform to file it as"
    ),
    38: (
        "Neo Geo Pocket / Pocket Color combined -- ROMarr splits these into "
        "neo-geo-pocket and neo-geo-pocket-color, and the section is both"
    ),
    46: "Miscellaneous Games -- deliberately heterogeneous",
    51: "Abandonware Games -- mixed DOS/PC era, no single platform",
    52: (
        "Amiga CD -- ambiguous between the CDTV and CD32 hardware; ROMarr "
        "has amiga-cd32 but the section is not only that"
    ),
    53: "Sony PocketStation -- ROMarr has no PocketStation platform",
    56: "Bandai Playdia -- ROMarr has no Playdia platform",
    58: "Acorn Archimedes -- ROMarr has no Archimedes platform",
    59: "Acorn BBC Micro -- ROMarr has no BBC Micro platform",
    60: "Acorn Electron -- ROMarr has no Electron platform",
    67: (
        "PSX on PSP -- a PlayStation game repackaged to run on a PSP; both "
        "psx and psp are defensible and the metadata does not choose"
    ),
}


def platform_for(section_id) -> str | None:
    """The ROMarr slug for an EmuParadise section id, or nothing.

    Accepts the id as an int or as the string the page carries in
    `data-filter`. Nothing is a real answer and `search` treats it as one.
    """
    try:
        return PLATFORMS.get(int(str(section_id).strip()))
    except (TypeError, ValueError):
        return None
