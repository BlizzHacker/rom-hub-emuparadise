"""The mapping must not contain a slug somebody invented.

Same load-bearing check as the rest of this family: a wrong slug fails
nowhere at runtime, it just files the ROM under another machine.
"""

import pytest

from emuparadise.platforms import PLATFORMS, UNMAPPED, platform_for

romarr_platforms = pytest.importorskip(
    "romarr.platforms",
    reason="ROMarr is not importable here; run in ROMarr's venv to check slugs",
)

#: Every section id EmuParadise publishes on /roms-isos-games.php
#: (66 sections, surveyed 2026-08-12). Pinned so an upstream addition shows
#: up as a failure rather than as silently missing results.
PUBLISHED = set(range(1, 45)) | {46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
                                 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68}
PUBLISHED -= {45, 65}  # not issued by the site


@pytest.mark.parametrize("section_id,slug", sorted(PLATFORMS.items()))
def test_every_slug_is_one_romarr_actually_has(section_id, slug):
    resolved = romarr_platforms.resolve(slug)
    assert resolved is not None, f"section {section_id} -> {slug!r} is not a ROMarr platform"
    assert resolved.slug == slug, (
        f"section {section_id} -> {slug!r} resolves to {resolved.slug!r}, not itself"
    )


def test_the_table_and_the_skips_together_cover_the_published_sections():
    assert set(PLATFORMS) | set(UNMAPPED) == PUBLISHED


def test_a_section_is_either_mapped_or_skipped_never_both():
    assert not set(PLATFORMS) & set(UNMAPPED)


def test_every_skip_says_why():
    for section_id, reason in UNMAPPED.items():
        assert len(reason) > 20, f"section {section_id} is skipped without a real reason"


def test_counts_are_what_the_readme_claims():
    assert len(PLATFORMS) == 52
    assert len(UNMAPPED) == 14


def test_unknown_section_returns_nothing_rather_than_a_guess():
    assert platform_for(999) is None
    assert platform_for(26) is None      # Neo Geo -- deliberately ambiguous
    assert platform_for(59) is None      # BBC Micro -- no ROMarr platform
    assert platform_for("") is None
    assert platform_for(None) is None
    assert platform_for("not-a-number") is None


def test_id_may_arrive_as_the_string_the_page_carries():
    # data-filter is an HTML attribute, so it arrives as text.
    assert platform_for("13") == platform_for(13) == "nes"


def test_both_commodore_sections_are_one_machine():
    assert platform_for(33) == platform_for(34) == "c64"


def test_both_spectrum_sections_are_one_machine():
    assert platform_for(35) == platform_for(36) == "zxs"


def test_playstation_demos_file_as_playstation():
    # A demo disc is a PlayStation disc; the section is a curation, not a
    # platform.
    assert platform_for(25) == platform_for(2) == "psx"


def test_arcade_collapse_is_deliberate():
    # MAME, NAOMI and the three Capcom Play Systems are all arcade hardware
    # and ROMarr models arcade as one platform.
    assert {platform_for(i) for i in (7, 30, 54, 55, 66)} == {"arcade"}
