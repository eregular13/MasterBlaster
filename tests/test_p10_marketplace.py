from masterblaster_control.p10_marketplace import load_marketplace_catalog, marketplace_markdown


def test_marketplace_catalog_loads_builtin_listings():
    listings = load_marketplace_catalog()
    ids = {entry.plugin_id for entry in listings}
    assert "plugin.builtin.reporting" in ids
    assert "plugin.fixture.observatory" in ids


def test_marketplace_markdown_renders():
    md = marketplace_markdown()
    assert "Plugin Marketplace" in md
    assert "Builtin Reporting" in md