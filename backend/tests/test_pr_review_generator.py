from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.github.pull_request_loader import PullRequestFile, PullRequestSnapshot
from app.github.service import GitHubFile, RepositorySnapshot
from app.reporting.report_generator import ReportGenerator
from app.review.diff_analyzer import DiffAnalyzer
from app.review.pr_review_generator import PRReviewGenerator


def test_pr_review_generator_reports_evidence_backed_risks_and_testing_concerns():
    snapshot = _repository_snapshot()
    pr = PullRequestSnapshot(
        owner="example",
        repo="service",
        number=12,
        title="Update service runtime",
        state="open",
        html_url=None,
        base_branch="main",
        head_branch="feature/runtime",
        author="developer",
        changed_files=3,
        files=[
            PullRequestFile("pyproject.toml", "modified", 3, 1, 4, "@@ dependencies"),
            PullRequestFile("app/main.py", "modified", 8, 2, 10, "@@ app"),
            PullRequestFile("Dockerfile", "modified", 2, 0, 2, "@@ docker"),
        ],
        truncated=False,
    )

    review = _generate_review(snapshot, pr)

    assert review.confidence == "High"
    assert review.metadata["changed_files"] == 3
    assert all(finding.evidence for finding in review.findings)
    assert any(finding.category == "potential_risk" and finding.severity == "High" for finding in review.findings)
    assert any(finding.category == "testing_concern" for finding in review.findings)
    assert any(finding.category == "architecture_impact" for finding in review.findings)


def test_pr_review_generator_marks_docs_only_change_low_severity():
    snapshot = _repository_snapshot()
    pr = PullRequestSnapshot(
        owner="example",
        repo="service",
        number=13,
        title="Update docs",
        state="open",
        html_url=None,
        base_branch="main",
        head_branch="docs",
        author="developer",
        changed_files=1,
        files=[PullRequestFile("README.md", "modified", 2, 1, 3, "@@ docs")],
        truncated=False,
    )

    review = _generate_review(snapshot, pr)

    assert review.confidence == "High"
    assert any(
        finding.category == "file_attention" and finding.severity == "Low"
        for finding in review.findings
    )


def test_pr_review_generator_lowers_confidence_when_truncated():
    snapshot = _repository_snapshot()
    pr = PullRequestSnapshot(
        owner="example",
        repo="service",
        number=14,
        title="Large change",
        state="open",
        html_url=None,
        base_branch="main",
        head_branch="large",
        author="developer",
        changed_files=250,
        files=[PullRequestFile("app/main.py", "modified", 8, 2, 10, "@@ app")],
        truncated=True,
    )

    review = _generate_review(snapshot, pr)

    assert review.confidence == "Low"
    assert review.metadata["truncated"] is True


def _generate_review(snapshot: RepositorySnapshot, pr: PullRequestSnapshot):
    analysis = RepositoryAnalyzer().analyze(snapshot)
    report = ReportGenerator().generate(snapshot, analysis)
    diff = DiffAnalyzer().analyze(pr.files, upstream_truncated=pr.truncated)
    return PRReviewGenerator().generate(snapshot, analysis, report.report, pr, diff)


def _repository_snapshot() -> RepositorySnapshot:
    return RepositorySnapshot(
        owner="example",
        name="service",
        default_branch="main",
        html_url="https://github.com/example/service",
        description="Example service",
        primary_language="Python",
        topics=[],
        tree_paths=["pyproject.toml", "app/main.py", "app/api/routes.py", "tests/test_api.py", "Dockerfile"],
        top_level_directories=["app", "tests"],
        selected_paths=["pyproject.toml", "app/main.py", "Dockerfile"],
        files=[
            GitHubFile("pyproject.toml", 'dependencies = ["fastapi"]', 25, "manifest"),
            GitHubFile("app/main.py", "from fastapi import FastAPI", 27, "entry_point"),
            GitHubFile("Dockerfile", "FROM python:3.12", 16, "infrastructure"),
        ],
        truncated=False,
    )
