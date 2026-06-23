from masterblaster_control.p10_marketplace import (
    load_marketplace_catalog,
    load_war_packs,
    marketplace_markdown,
    war_packs_markdown,
)


def test_marketplace_catalog_loads_builtin_listings():
    listings = load_marketplace_catalog()
    ids = {entry.plugin_id for entry in listings}
    assert "plugin.builtin.reporting" in ids
    assert "plugin.fixture.observatory" in ids


def test_marketplace_markdown_renders():
    md = marketplace_markdown()
    assert "Warlord Marketplace" in md
    assert "War Packs" in md
    assert "Builtin Reporting" in md


def test_war_packs_load():
    packs = load_war_packs()
    assert len(packs) >= 7
    names = {pack.name for pack in packs}
    assert "Total Domination Pack" in names


def test_war_packs_markdown_renders():
    md = war_packs_markdown()
    assert "Web Annihilation Pack" in md