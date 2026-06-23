from masterblaster_control.p9_plugin_review import discover_submissions, review_queue_markdown


def test_review_queue_discovers_demo_submission():
    items = discover_submissions()
    assert len(items) >= 1
    assert any(item.plugin_id == "plugin.community.demo" for item in items)


def test_review_queue_markdown_renders_table():
    md = review_queue_markdown()
    assert "# Plugin Review Queue" in md
    assert "plugin.community.demo" in md or "Community Demo" in md