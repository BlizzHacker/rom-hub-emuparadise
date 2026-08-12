import pytest

from emuparadise.listing import (
    Entry,
    clean_title,
    parse_search,
    parse_size,
    search_url,
    split_path,
)


def test_parses_every_block(search_html):
    entries = parse_search(search_html)
    assert [e.rom_id for e in entries] == [
        "55137", "47733", "153961", "12021", "70504", "90001", "91002",
    ]


def test_section_id_comes_from_data_filter(search_html):
    first = parse_search(search_html)[0]
    assert first.section_id == "13"
    assert first.system_name == "Nintendo Entertainment System"


def test_title_drops_the_appended_medium(search_html):
    entries = parse_search(search_html)
    assert entries[0].title == "Contra (USA)"        # not "Contra (USA) ROM"
    assert entries[2].title == "Neo Contra (Europe) (En,Fr,De)"   # not "... ISO"
    assert entries[6].title == "Contra DOS Port"     # not "... Game"


def test_a_title_containing_a_double_hyphen_and_comma_survives(search_html):
    # "Contra (US -- Asia, set 1)" is a real MAME title. A character
    # allowlist would have dropped it; the validation is structural for
    # exactly this reason.
    mame = [e for e in parse_search(search_html) if e.section_id == "7"][0]
    assert mame.title == "Contra (US -- Asia, set 1)"
    assert mame.path.endswith("/Contra_(US_--_Asia,_set_1)/12021")


@pytest.mark.parametrize("text,expected", [
    ("92K", 94208),
    ("13M", 13631488),
    ("1.1G", 1181116006),
    ("512", 512),
])
def test_sizes_are_binary_units(text, expected):
    assert parse_size(text) == expected


@pytest.mark.parametrize("text", ["", "unknown", "big", "K", "-4M"])
def test_unparseable_size_is_none_not_zero(text):
    assert parse_size(text) is None


def test_clean_title_leaves_an_ordinary_title_alone():
    assert clean_title("Contra") == "Contra"
    # "Rome" ends in a medium-shaped substring but is not one.
    assert clean_title("Rome") == "Rome"


@pytest.mark.parametrize("path", [
    "Nintendo_Entertainment_System_ROMs/Contra_(USA)/55137",
    "M.A.M.E._-_Multiple_Arcade_Machine_Emulator_ROMs/Contra_(US_--_Asia,_set_1)/12021",
    "Apple_][_ROMs/Alcazar_The_Forgotten_Fortress_(1985)(Activision)[cr]/57756",
    "Amstrad_CPC_ROMs/Gryzor_[t1]_&_Combat_School_Demo_(UK)_(1987)/130322",
])
def test_accepts_real_shapes_including_awkward_titles(path):
    assert split_path(path) is not None


@pytest.mark.parametrize("path", [
    "",
    "Section/Title",                    # two segments
    "Section/Title/NotANumber",
    "Section/Title/55137/extra",        # four segments
    "../../etc/passwd",
    "Section/../55137",
    "Section/Title/55137?x=1",
    "Section/Title/55137#frag",
    "https://evil.example/Section/Title/1",
    "Section/Ti tle/55137",             # whitespace
    "Section//55137",                   # empty segment
])
def test_rejects_anything_that_is_not_exactly_a_rom_path(path):
    assert split_path(path) is None


def test_dot_segments_are_rejected_even_though_the_shape_fits():
    assert split_path("../Title/55137") is None
    assert split_path("Section/../55137") is None
    assert split_path("./Title/55137") is None


def test_url_keeps_the_characters_that_are_part_of_the_id():
    entry = Entry(
        "Amstrad_CPC_ROMs/Gryzor_[t1]_&_Combat_School_Demo_(UK)_(1987)/130322",
        "Amstrad_CPC_ROMs", "130322", "Gryzor",
    )
    # Brackets, ampersand and parens are real path characters here; escaping
    # them would produce a link that 404s.
    assert entry.page_url == (
        "https://www.emuparadise.me/Amstrad_CPC_ROMs/"
        "Gryzor_[t1]_&_Combat_School_Demo_(UK)_(1987)/130322"
    )


def test_blocks_without_a_rom_link_are_skipped_not_raised_on():
    assert parse_search('<div class="roms">nothing here</div>') == []
    assert parse_search("") == []
    assert parse_search("<html><body>no results</body></html>") == []


def test_duplicate_blocks_collapse():
    block = (
        '<div class="roms"><a data-filter="13" href="/S_ROMs/T/1">T ROM</a>'
        '<b>System:</b> <a href="/roms/roms.php?sysid=13">NES</a>'
        "<b>Size:</b> 1K </div>"
    )
    assert len(parse_search(block + block)) == 1


def test_search_url_is_the_sites_own_shape():
    assert search_url("contra") == (
        "https://www.emuparadise.me/roms/search.php?query=contra"
    )
