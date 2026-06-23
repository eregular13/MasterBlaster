from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOTS = ("masterblaster_control", "scripts", "tests")

FORBIDDEN_IMPORTS = {
    "importlib",
    "pickle",
    "requests",
    "socket",
    "subprocess",
    "urllib.request",
    "urllib3",
}

FORBIDDEN_IMPORT_NAMES = {
    "importlib": {"import_module"},
    "os": {
        "popen",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "system",
    },
    "pickle": {"load", "loads"},
    "subprocess": {"call", "check_call", "check_output", "Popen", "run"},
    "urllib": {"request"},
}

FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "importlib.import_module",
    "os.popen",
    "os.spawnl",
    "os.spawnle",
    "os.spawnlp",
    "os.spawnlpe",
    "os.spawnv",
    "os.spawnve",
    "os.spawnvp",
    "os.spawnvpe",
    "os.system",
    "pickle.load",
    "pickle.loads",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.Popen",
    "subprocess.run",
}

FORBIDDEN_NAMES = {"QProcess"}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    code: str
    detail: str

    def format(self, root: Path = REPO_ROOT) -> str:
        try:
            display = self.path.relative_to(root)
        except ValueError:
            display = self.path
        return f"{display}:{self.line}: {self.code}: {self.detail}"


def _module_matches(module: str, forbidden: str) -> bool:
    return module == forbidden or module.startswith(f"{forbidden}.")


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        if base:
            return f"{base}.{node.attr}"
        return node.attr
    return None


def scan_source(source: str, path: Path) -> tuple[Finding, ...]:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return (Finding(path, exc.lineno or 1, "PY-SYNTAX", exc.msg),)

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(_module_matches(alias.name, forbidden) for forbidden in FORBIDDEN_IMPORTS):
                    findings.append(Finding(path, node.lineno, "FORBIDDEN-IMPORT", alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if any(_module_matches(module, forbidden) for forbidden in FORBIDDEN_IMPORTS):
                findings.append(Finding(path, node.lineno, "FORBIDDEN-IMPORT", module))
            for alias in node.names:
                if alias.name in FORBIDDEN_NAMES:
                    findings.append(Finding(path, node.lineno, "FORBIDDEN-NAME", alias.name))
                if alias.name in FORBIDDEN_IMPORT_NAMES.get(module, set()):
                    findings.append(Finding(path, node.lineno, "FORBIDDEN-IMPORT-NAME", f"{module}.{alias.name}"))
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in FORBIDDEN_CALLS:
                findings.append(Finding(path, node.lineno, "FORBIDDEN-CALL", call_name))
            for keyword in node.keywords:
                if keyword.arg == "shell":
                    if not (isinstance(keyword.value, ast.Constant) and keyword.value.value is False):
                        findings.append(Finding(path, node.lineno, "FORBIDDEN-SHELL", "shell is not statically false"))
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            findings.append(Finding(path, node.lineno, "FORBIDDEN-NAME", node.id))
    return tuple(findings)


def iter_python_files(paths: Iterable[Path]) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return tuple(sorted(files))


def scan_paths(paths: Iterable[Path]) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for path in iter_python_files(paths):
        findings.extend(scan_source(path.read_text(encoding="utf-8"), path))
    return tuple(findings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AST scan for prohibited live-execution capabilities.")
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to scan.")
    args = parser.parse_args(argv)
    paths = tuple(args.paths) or tuple(REPO_ROOT / item for item in DEFAULT_SCAN_ROOTS)
    findings = scan_paths(paths)
    for finding in findings:
        print(finding.format(REPO_ROOT), file=sys.stderr)
    if findings:
        return 1
    print("No prohibited Python execution or network primitives detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
