from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass

from app.github.service import GitHubFile, RepositorySnapshot

SUPPORTED_LANGUAGES = {"Python", "TypeScript", "JavaScript", "Go"}
TRUNCATION_REASONS = {"file_limit", "byte_limit", "unsupported_language", "none"}


@dataclass(frozen=True)
class RepositoryIndexedFile:
    path: str
    language: str
    role: str
    directory_group: str


@dataclass(frozen=True)
class RepositorySymbol:
    name: str
    kind: str
    language: str
    path: str
    line: int
    container: str | None = None


@dataclass(frozen=True)
class RepositoryImport:
    module: str
    language: str
    path: str
    line: int


@dataclass(frozen=True)
class RepositoryTestLink:
    test_path: str
    source_path: str
    reason: str


@dataclass(frozen=True)
class RepositoryIndexMetadata:
    files_indexed: int
    symbols_found: int
    imports_found: int
    tests_found: int
    truncated: bool
    truncation_reason: str


@dataclass(frozen=True)
class RepositoryIndex:
    files: list[RepositoryIndexedFile]
    symbols: list[RepositorySymbol]
    imports: list[RepositoryImport]
    tests: list[RepositoryTestLink]
    metadata: RepositoryIndexMetadata


class RepositoryIndexer:
    def __init__(self, max_files: int = 100):
        self.max_files = max_files

    def build(self, snapshot: RepositorySnapshot) -> RepositoryIndex:
        indexed_files: list[RepositoryIndexedFile] = []
        symbols: list[RepositorySymbol] = []
        imports: list[RepositoryImport] = []
        supported_files = [file for file in snapshot.files if _language_for_path(file.path) in SUPPORTED_LANGUAGES]
        truncated = snapshot.truncated or len(supported_files) > self.max_files
        truncation_reason = _truncation_reason(snapshot, supported_files, len(supported_files) > self.max_files)

        for file in supported_files[: self.max_files]:
            language = _language_for_path(file.path)
            if language not in SUPPORTED_LANGUAGES:
                continue
            indexed_files.append(
                RepositoryIndexedFile(
                    path=file.path,
                    language=language,
                    role=_role_for_path(file.path, file.source_type),
                    directory_group=_directory_group(file.path),
                )
            )
            extracted_symbols, extracted_imports = _extract_file(file, language)
            symbols.extend(extracted_symbols)
            imports.extend(extracted_imports)

        test_links = _link_tests(indexed_files)
        symbols = _sort_symbols(symbols)
        imports = _sort_imports(imports)
        test_links = sorted(test_links, key=lambda link: (link.test_path, link.source_path, link.reason))
        indexed_files = sorted(indexed_files, key=lambda item: item.path)

        return RepositoryIndex(
            files=indexed_files,
            symbols=symbols,
            imports=imports,
            tests=test_links,
            metadata=RepositoryIndexMetadata(
                files_indexed=len(indexed_files),
                symbols_found=len(symbols),
                imports_found=len(imports),
                tests_found=len(test_links),
                truncated=truncated,
                truncation_reason=truncation_reason,
            ),
        )


def _extract_file(file: GitHubFile, language: str) -> tuple[list[RepositorySymbol], list[RepositoryImport]]:
    if language == "Python":
        return _extract_python(file)
    if language in {"TypeScript", "JavaScript"}:
        return _extract_ts_js(file, language)
    if language == "Go":
        return _extract_go(file)
    return [], []


def _extract_python(file: GitHubFile) -> tuple[list[RepositorySymbol], list[RepositoryImport]]:
    symbols: list[RepositorySymbol] = []
    imports: list[RepositoryImport] = []
    try:
        tree = ast.parse(file.content)
    except SyntaxError:
        return symbols, imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                RepositoryImport(alias.name, "Python", file.path, node.lineno)
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append(RepositoryImport(module or ".", "Python", file.path, node.lineno))
        elif isinstance(node, ast.ClassDef):
            symbols.append(RepositorySymbol(node.name, "class", "Python", file.path, node.lineno))
            for child in node.body:
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    kind = "test_function" if child.name.startswith("test_") else "method"
                    symbols.append(RepositorySymbol(child.name, kind, "Python", file.path, child.lineno, node.name))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if not _has_class_parent(tree, node):
                kind = "test_function" if node.name.startswith("test_") else "function"
                symbols.append(RepositorySymbol(node.name, kind, "Python", file.path, node.lineno))
    return symbols, imports


def _has_class_parent(tree: ast.AST, target: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and target in node.body:
            return True
    return False


def _extract_ts_js(file: GitHubFile, language: str) -> tuple[list[RepositorySymbol], list[RepositoryImport]]:
    symbols: list[RepositorySymbol] = []
    imports: list[RepositoryImport] = []
    for line_number, line in enumerate(file.content.splitlines(), start=1):
        stripped = line.strip()
        import_match = re.match(r"import\s+(?:.+?\s+from\s+)?[\"']([^\"']+)[\"']", stripped)
        require_match = re.search(r"require\([\"']([^\"']+)[\"']\)", stripped)
        if import_match:
            imports.append(RepositoryImport(import_match.group(1), language, file.path, line_number))
        elif require_match:
            imports.append(RepositoryImport(require_match.group(1), language, file.path, line_number))

        for kind, pattern in (
            ("class", r"(?:export\s+)?class\s+([A-Za-z_$][\w$]*)"),
            ("function", r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"),
            ("constant", r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*="),
        ):
            match = re.match(pattern, stripped)
            if match:
                name = match.group(1)
                symbol_kind = "test_function" if _is_test_path(file.path) and name.lower().startswith("test") else kind
                symbols.append(RepositorySymbol(name, symbol_kind, language, file.path, line_number))
                break
    return symbols, imports


def _extract_go(file: GitHubFile) -> tuple[list[RepositorySymbol], list[RepositoryImport]]:
    symbols: list[RepositorySymbol] = []
    imports: list[RepositoryImport] = []
    in_import_block = False
    for line_number, line in enumerate(file.content.splitlines(), start=1):
        stripped = line.strip()
        package_match = re.match(r"package\s+([A-Za-z_]\w*)", stripped)
        if package_match:
            symbols.append(RepositorySymbol(package_match.group(1), "package", "Go", file.path, line_number))

        if stripped == "import (":
            in_import_block = True
            continue
        if in_import_block and stripped == ")":
            in_import_block = False
            continue
        if in_import_block:
            import_match = re.search(r'"([^"]+)"', stripped)
            if import_match:
                imports.append(RepositoryImport(import_match.group(1), "Go", file.path, line_number))
            continue
        import_match = re.match(r'import\s+(?:[A-Za-z_]\w*\s+)?\"([^\"]+)\"', stripped)
        if import_match:
            imports.append(RepositoryImport(import_match.group(1), "Go", file.path, line_number))

        type_match = re.match(r"type\s+([A-Za-z_]\w*)\s+(struct|interface|[A-Za-z_]\w*)", stripped)
        if type_match:
            symbols.append(RepositorySymbol(type_match.group(1), "type", "Go", file.path, line_number))

        method_match = re.match(r"func\s+\((?:\w+\s+)?\*?([A-Za-z_]\w*)\)\s+([A-Za-z_]\w*)\s*\(", stripped)
        if method_match:
            name = method_match.group(2)
            kind = "test_function" if _is_test_path(file.path) and name.startswith("Test") else "method"
            symbols.append(RepositorySymbol(name, kind, "Go", file.path, line_number, method_match.group(1)))
            continue
        func_match = re.match(r"func\s+([A-Za-z_]\w*)\s*\(", stripped)
        if func_match:
            name = func_match.group(1)
            kind = "test_function" if _is_test_path(file.path) and name.startswith("Test") else "function"
            symbols.append(RepositorySymbol(name, kind, "Go", file.path, line_number))
    return symbols, imports


def _link_tests(files: list[RepositoryIndexedFile]) -> list[RepositoryTestLink]:
    sources = [file for file in files if file.role != "test_code"]
    tests = [file for file in files if file.role == "test_code"]
    links: list[RepositoryTestLink] = []
    for test in tests:
        source = _best_source_for_test(test.path, sources)
        if source:
            links.append(RepositoryTestLink(test.path, source.path, _test_link_reason(test.path, source.path)))
    return links


def _best_source_for_test(test_path: str, sources: list[RepositoryIndexedFile]) -> RepositoryIndexedFile | None:
    test_stem = _normalized_stem(test_path)
    same_dir = test_path.rsplit("/", 1)[0] if "/" in test_path else ""
    candidates = []
    for source in sources:
        source_stem = _normalized_stem(source.path)
        score = 0
        if source_stem and source_stem == test_stem:
            score += 100
        elif source_stem and (source_stem in test_stem or test_stem in source_stem):
            score += 50
        if same_dir and source.path.startswith(f"{same_dir}/"):
            score += 20
        if source.directory_group and source.directory_group in test_path:
            score += 10
        if score:
            candidates.append((score, source.path, source))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (-item[0], item[1]))[0][2]


def _test_link_reason(test_path: str, source_path: str) -> str:
    if _normalized_stem(test_path) == _normalized_stem(source_path):
        return "matching_stem"
    return "directory_group"


def _language_for_path(path: str) -> str:
    lowered = path.lower()
    if lowered.endswith(".py"):
        return "Python"
    if lowered.endswith(".tsx") or lowered.endswith(".ts"):
        return "TypeScript"
    if lowered.endswith(".jsx") or lowered.endswith(".js"):
        return "JavaScript"
    if lowered.endswith(".go"):
        return "Go"
    return "Unsupported"


def _role_for_path(path: str, source_type: str) -> str:
    if _is_test_path(path):
        return "test_code"
    if source_type == "entry_point":
        return "entry_point"
    return "source_code"


def _directory_group(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else "."


def _normalized_stem(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    stem = re.sub(r"\.(test|spec)$", "", name.rsplit(".", 1)[0], flags=re.IGNORECASE)
    stem = re.sub(r"^test[_-]", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[_-]test$", "", stem, flags=re.IGNORECASE)
    return stem.casefold()


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    parts = lowered.split("/")
    name = parts[-1]
    return (
        "tests" in parts
        or "test" in parts
        or "__tests__" in parts
        or name.endswith("_test.go")
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
    )


def _truncation_reason(snapshot: RepositorySnapshot, supported_files: list[GitHubFile], index_file_limit: bool) -> str:
    if index_file_limit:
        return "file_limit"
    reason = getattr(snapshot, "truncation_reason", "none")
    if reason in TRUNCATION_REASONS and reason != "none":
        return reason
    if snapshot.files and not supported_files:
        return "unsupported_language"
    return "none"


def _sort_symbols(symbols: list[RepositorySymbol]) -> list[RepositorySymbol]:
    return sorted(symbols, key=lambda symbol: (symbol.path, symbol.line, symbol.kind, symbol.container or "", symbol.name))


def _sort_imports(imports: list[RepositoryImport]) -> list[RepositoryImport]:
    return sorted(imports, key=lambda item: (item.path, item.line, item.module))


def directory_group_summaries(index: RepositoryIndex) -> list[str]:
    counts = Counter(file.directory_group for file in index.files)
    return [f"{group}: {count} indexed file(s)" for group, count in sorted(counts.items())]
