from app.github.pull_request_loader import PullRequestFile
from app.review.diff_analyzer import DiffAnalyzer


def test_diff_analyzer_classifies_changed_files_and_metadata():
    files = [
        PullRequestFile("package.json", "modified", 4, 1, 5, "@@ package"),
        PullRequestFile("Dockerfile", "modified", 2, 0, 2, "@@ docker"),
        PullRequestFile("src/lib/widget.ts", "modified", 10, 4, 14, "@@ source"),
        PullRequestFile("tests/app.test.ts", "modified", 6, 2, 8, "@@ test"),
        PullRequestFile("README.md", "modified", 1, 1, 2, "@@ docs"),
    ]

    analysis = DiffAnalyzer().analyze(files)

    categories = {file.path: file.category for file in analysis.files}
    assert categories["package.json"] == "manifest"
    assert categories["Dockerfile"] == "infrastructure"
    assert categories["src/lib/widget.ts"] == "source"
    assert categories["tests/app.test.ts"] == "test"
    assert categories["README.md"] == "docs"
    assert analysis.high_signal_files == 3
    assert analysis.truncated is False


def test_diff_analyzer_enforces_file_and_patch_limits():
    files = [
        PullRequestFile("package.json", "modified", 1, 1, 2, "x" * 20),
        PullRequestFile("src/server.ts", "modified", 1, 1, 2, "x" * 20),
        PullRequestFile("src/extra.ts", "modified", 1, 1, 2, "x" * 20),
        PullRequestFile("docs/readme.md", "modified", 1, 1, 2, "x" * 20),
    ]

    analysis = DiffAnalyzer(max_changed_files=3, max_patch_bytes=30).analyze(files)

    assert analysis.changed_files == 4
    assert analysis.files_inspected == 1
    assert analysis.patch_bytes == 20
    assert analysis.truncated is True
    assert any("truncated" in assumption.lower() for assumption in analysis.assumptions)
