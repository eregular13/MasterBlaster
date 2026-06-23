from pathlib import Path

from scripts.generate_release_notes import generate_release_notes


def test_generate_release_notes_includes_changelog_section():
    notes = generate_release_notes("1.0.0", include_announcement=False)
    assert "MasterBlaster 1.0.0" in notes
    assert "Deny-by-default" in notes
    assert "Seven reviewed simulator-only adapters" in notes


def test_generate_release_notes_script_writes_file(tmp_path):
    from scripts.generate_release_notes import main

    output = tmp_path / "notes.md"
    assert main(["--version", "1.0.0", "--output", str(output), "--no-announcement"]) == 0
    assert output.exists()
    assert "Quick Start" in output.read_text(encoding="utf-8")