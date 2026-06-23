from scripts.scan_prohibited_capabilities import scan_paths, scan_source


def test_scanner_detects_forbidden_imports_and_calls(tmp_path):
    path = tmp_path / "bad.py"
    source = """
import subprocess
import socket

subprocess.run(["echo", "bad"])
eval("1 + 1")
"""

    findings = scan_source(source, path)
    codes = {finding.code for finding in findings}

    assert "FORBIDDEN-IMPORT" in codes
    assert "FORBIDDEN-CALL" in codes


def test_scanner_detects_dangerous_imported_names(tmp_path):
    path = tmp_path / "bad_import_name.py"

    findings = scan_source("from os import system\n", path)

    assert any(finding.code == "FORBIDDEN-IMPORT-NAME" for finding in findings)


def test_scanner_detects_shell_true(tmp_path):
    path = tmp_path / "bad_shell.py"

    findings = scan_source("runner(command, shell=True)\n", path)

    assert any(finding.code == "FORBIDDEN-SHELL" for finding in findings)


def test_scanner_detects_nonliteral_shell_values(tmp_path):
    path = tmp_path / "bad_shell_variable.py"

    findings = scan_source("runner(command, shell=user_controlled)\n", path)

    assert any(finding.code == "FORBIDDEN-SHELL" for finding in findings)


def test_scanner_ignores_harmless_documentation_text(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("Documentation may mention subprocess.run without executable Python.\n", encoding="utf-8")

    assert scan_paths((path,)) == ()
