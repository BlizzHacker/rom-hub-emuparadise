import pytest
from conftest import FakeHttp

from rom_hub_sdk import PluginContext

from emuparadise.search import Search


def test_search_maps_sections_and_drops_the_unmappable(search_html):
    http = FakeHttp([(200, search_html)])
    results = Search(PluginContext(config={}, http=http)).search("contra", None, 20)

    # 7 blocks in, 5 out: Neo Geo (26) is ambiguous between ROMarr's
    # neogeoaes and neogeomvs, and Abandonware (51) is heterogeneous.
    assert [(r.platform, r.extra["emuparadise_id"]) for r in results] == [
        ("nes", "55137"),
        ("nds", "47733"),
        ("ps2", "153961"),
        ("arcade", "12021"),
        ("c64", "70504"),
    ]


def test_search_costs_exactly_one_request(search_html):
    http = FakeHttp([(200, search_html)])
    Search(PluginContext(config={}, http=http)).search("contra", None, 20)
    assert http.urls == [
        "https://www.emuparadise.me/roms/search.php?query=contra"
    ]


def test_every_result_says_it_cannot_be_downloaded(search_html):
    # The whole point of this provider: the files are gone, so nothing must
    # ever suggest otherwise.
    http = FakeHttp([(200, search_html)])
    results = Search(PluginContext(config={}, http=http)).search("contra", None, 20)
    assert results
    assert all(r.extra["downloadable"] == "false" for r in results)
    assert all(r.extra["playable"] == "false" for r in results)


def test_search_reports_the_listed_size(search_html):
    http = FakeHttp([(200, search_html)])
    results = Search(PluginContext(config={}, http=http)).search("contra", None, 20)
    assert results[0].size_bytes == 94208           # 92K
    assert results[2].size_bytes == 1181116006      # 1.1G


def test_search_carries_title_url_and_system(search_html):
    http = FakeHttp([(200, search_html)])
    first = Search(PluginContext(config={}, http=http)).search("contra", None, 5)[0]
    assert first.title == "Contra (USA)"
    assert first.url == (
        "https://www.emuparadise.me/Nintendo_Entertainment_System_ROMs/"
        "Contra_(USA)/55137"
    )
    assert first.extra["system"] == "Nintendo Entertainment System"
    assert first.source_id == "Nintendo_Entertainment_System_ROMs/Contra_(USA)/55137"


def test_platform_filter(search_html):
    http = FakeHttp([(200, search_html)])
    results = Search(PluginContext(config={}, http=http)).search("contra", "arcade", 20)
    assert [r.extra["emuparadise_id"] for r in results] == ["12021"]


def test_filtering_to_a_skipped_section_returns_nothing(search_html):
    http = FakeHttp([(200, search_html)])
    assert Search(
        PluginContext(config={}, http=http)
    ).search("contra", "neogeoaes", 20) == []


def test_limit_is_honoured(search_html):
    http = FakeHttp([(200, search_html)])
    assert len(Search(PluginContext(config={}, http=http)).search("contra", None, 2)) == 2


def test_empty_query_makes_no_request():
    http = FakeHttp([])
    assert Search(PluginContext(config={}, http=http)).search("  ", None, 10) == []
    assert http.urls == []


def test_zero_limit_makes_no_request():
    http = FakeHttp([])
    assert Search(PluginContext(config={}, http=http)).search("contra", None, 0) == []
    assert http.urls == []


@pytest.mark.parametrize("status", [403, 429, 503, 500, 404])
def test_a_refusal_is_not_retried(status):
    http = FakeHttp([(status, "")])
    assert Search(PluginContext(config={}, http=http)).search("contra", None, 10) == []
    assert len(http.urls) == 1


def test_no_importer_or_stream_is_exported():
    # The absence is the point: EmuParadise's files are gone, so a download
    # capability would refuse every call it ever got.
    import emuparadise

    assert not hasattr(emuparadise, "importer")
    assert not hasattr(emuparadise, "stream")
