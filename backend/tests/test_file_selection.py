from app.analyzer.file_selection import classify_file, select_architecture_files


def test_classifies_supported_architecture_files():
    assert classify_file("package.json") == "manifest"
    assert classify_file("backend/pyproject.toml") == "manifest"
    assert classify_file("Dockerfile") == "infrastructure"
    assert classify_file("next.config.js") == "config"
    assert classify_file("src/main.tsx") == "entry_point"
    assert classify_file("src/main/java/com/example/DemoApplication.java") == "entry_point"
    assert classify_file("src/components/Button.tsx") == "source_code"
    assert classify_file("tests/test_checkout.py") == "test_code"
    assert classify_file("README.md") == "readme"


def test_select_architecture_files_respects_limits_and_types():
    paths = [
        "package.json",
        "README.md",
        "src/main.tsx",
        "src/ignored.ts",
        "Dockerfile",
        "vite.config.ts",
        "backend/pyproject.toml",
    ]

    result = select_architecture_files(paths, max_files=3)

    assert result.truncated is True
    assert len(result.paths) == 3
    assert result.paths == ["package.json", "backend/pyproject.toml", "vite.config.ts"]
    assert result.path_types["package.json"] == "manifest"


def test_select_architecture_files_skips_docs_and_selects_test_code():
    paths = [
        "docs_src/example/main.py",
        "fixtures/dom/src/index.js",
        "tests/main.py",
        "app/main.py",
        "fastapi/applications.py",
    ]

    result = select_architecture_files(paths)

    assert "docs_src/example/main.py" not in result.paths
    assert "fixtures/dom/src/index.js" not in result.paths
    assert "tests/main.py" in result.paths
    assert result.path_types["tests/main.py"] == "test_code"
    assert "app/main.py" in result.paths
    assert "fastapi/applications.py" in result.paths


def test_select_architecture_files_caps_nested_manifests():
    paths = ["package.json"] + [f"packages/pkg-{index}/package.json" for index in range(50)]

    result = select_architecture_files(paths)

    assert len(result.paths) == 20
    assert "package.json" in result.paths
