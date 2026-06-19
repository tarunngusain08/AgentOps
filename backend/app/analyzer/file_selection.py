from __future__ import annotations

from dataclasses import dataclass

README_NAMES = {"readme", "readme.md"}
MANIFEST_NAMES = {
    "package.json",
    "pom.xml",
    "build.gradle",
    "requirements.txt",
    "pyproject.toml",
    "cargo.toml",
    "go.mod",
}
INFRA_NAMES = {"docker-compose.yml", "dockerfile"}
CONFIG_NAMES = {"next.config.js", "vite.config.ts", "application.yml"}
ENTRY_POINT_NAMES = {
    "main.py",
    "app.py",
    "applications.py",
    "server.ts",
    "server.js",
    "index.ts",
    "index.js",
    "main.go",
    "main.tsx",
    "app.tsx",
}
ENTRY_POINT_SUFFIXES = ("Application.java",)
EXCLUDED_ENTRY_DIRECTORIES = {
    "doc",
    "docs",
    "docs_src",
    "fixture",
    "fixtures",
    "test",
    "tests",
    "__tests__",
}
EXCLUDED_TOP_LEVEL_ENTRY_DIRECTORIES = {"example", "examples"}
TYPE_LIMITS = {
    "manifest": 20,
    "config": 10,
    "infrastructure": 10,
    "entry_point": 20,
    "source_code": 40,
    "test_code": 20,
    "readme": 1,
}
SOURCE_CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go"}
SOURCE_ROOTS = {"app", "src", "backend", "frontend", "lib", "pkg", "cmd", "internal"}
TEST_ROOTS = {"test", "tests", "__tests__"}
SOURCE_EXCLUDED_ROOTS = {"docs", "doc", "docs_src", "fixtures", "fixture", "examples", "example", "vendor", "node_modules"}


@dataclass(frozen=True)
class FileSelectionResult:
    paths: list[str]
    path_types: dict[str, str]
    truncated: bool


def select_architecture_files(tree_paths: list[str], max_files: int = 100) -> FileSelectionResult:
    selected: list[str] = []
    path_types: dict[str, str] = {}
    type_counts = {source_type: 0 for source_type in TYPE_LIMITS}

    candidates = sorted(
        (path for path in tree_paths if _is_supported_file_path(path)),
        key=_path_priority,
    )
    for source_type in ("manifest", "config", "infrastructure", "entry_point", "source_code", "test_code", "readme"):
        for path in candidates:
            if len(selected) >= max_files:
                return FileSelectionResult(paths=selected, path_types=path_types, truncated=True)
            if path in path_types:
                continue
            if classify_file(path) == source_type:
                if type_counts[source_type] >= TYPE_LIMITS[source_type]:
                    continue
                selected.append(path)
                path_types[path] = source_type
                type_counts[source_type] += 1

    return FileSelectionResult(paths=selected, path_types=path_types, truncated=False)


def classify_file(path: str) -> str | None:
    basename = path.rsplit("/", 1)[-1]
    lowered = basename.lower()

    if lowered in MANIFEST_NAMES:
        return "manifest"
    if lowered in CONFIG_NAMES:
        return "config"
    if lowered in INFRA_NAMES:
        return "infrastructure"
    if basename.endswith(ENTRY_POINT_SUFFIXES) and _is_not_docs_or_tests(path):
        return "entry_point"
    if _is_entry_candidate_path(path) and lowered in ENTRY_POINT_NAMES:
        return "entry_point"
    if _is_entry_candidate_path(path) and _is_likely_framework_entry(path):
        return "entry_point"
    if _is_test_code_path(path):
        return "test_code"
    if _is_source_code_path(path):
        return "source_code"
    if lowered in README_NAMES and "/" not in path:
        return "readme"
    return None


def _is_likely_framework_entry(path: str) -> bool:
    normalized = path.replace("\\", "/")
    lowered = normalized.lower()
    return lowered in {
        "src/app.tsx",
        "src/main.tsx",
        "src/index.tsx",
        "src/app.jsx",
        "src/main.jsx",
        "src/index.jsx",
        "src/app.js",
        "src/main.js",
        "src/index.js",
        "app/main.py",
        "app/app.py",
    }


def _is_entry_candidate_path(path: str) -> bool:
    if not _is_not_docs_or_tests(path):
        return False
    return len(path.replace("\\", "/").split("/")) <= 4


def _is_not_docs_or_tests(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    if parts and parts[0].lower() in EXCLUDED_TOP_LEVEL_ENTRY_DIRECTORIES:
        return False
    if any(part.lower() in EXCLUDED_ENTRY_DIRECTORIES for part in parts[:-1]):
        return False
    return True


def _is_supported_file_path(path: str) -> bool:
    if path.endswith("/"):
        return False
    if path.startswith(".git/"):
        return False
    return classify_file(path) is not None


def _path_priority(path: str) -> tuple[int, str]:
    return (_source_priority(path), path.count("/"), path.lower())


def _is_source_code_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    if not parts:
        return False
    if _extension(path) not in SOURCE_CODE_EXTENSIONS:
        return False
    root = parts[0].lower()
    if root in SOURCE_EXCLUDED_ROOTS:
        return False
    return root in SOURCE_ROOTS or len(parts) <= 3


def _is_test_code_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    basename = parts[-1].lower()
    if _extension(path) not in SOURCE_CODE_EXTENSIONS:
        return False
    return (
        any(part.lower() in TEST_ROOTS for part in parts[:-1])
        or basename.startswith("test_")
        or basename.endswith("_test.go")
        or ".test." in basename
        or ".spec." in basename
    )


def _extension(path: str) -> str:
    basename = path.rsplit("/", 1)[-1]
    if "." not in basename:
        return ""
    return "." + basename.rsplit(".", 1)[-1].lower()


def _source_priority(path: str) -> int:
    source_type = classify_file(path)
    order = {
        "manifest": 0,
        "config": 1,
        "infrastructure": 2,
        "entry_point": 3,
        "source_code": 4,
        "test_code": 5,
        "readme": 6,
    }
    return order.get(source_type or "", 99)
