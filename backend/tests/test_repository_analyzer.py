from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.github.service import GitHubFile, RepositorySnapshot
from app.reporting.report_generator import ReportGenerator


def test_analyzer_detects_fastapi_style_repository():
    snapshot = RepositorySnapshot(
        owner="example",
        name="service",
        default_branch="main",
        html_url="https://github.com/example/service",
        description="Example API service",
        primary_language="Python",
        topics=[],
        tree_paths=[
            "README.md",
            "pyproject.toml",
            "app/main.py",
            "app/api/routes.py",
            "tests/test_api.py",
        ],
        top_level_directories=["app", "tests"],
        selected_paths=["pyproject.toml", "app/main.py", "README.md"],
        files=[
            GitHubFile("pyproject.toml", 'dependencies = ["fastapi", "pydantic"]', 40, "manifest"),
            GitHubFile("app/main.py", "from fastapi import FastAPI\napp = FastAPI()", 45, "entry_point"),
            GitHubFile("README.md", "# Example", 9, "readme"),
        ],
        truncated=False,
    )

    analysis = RepositoryAnalyzer().analyze(snapshot)

    assert "Python" in analysis.technology_stack
    assert "FastAPI" in analysis.technology_stack
    assert "app/main.py" in analysis.entry_points
    assert any(component.name == "API/Application Layer" for component in analysis.components)


def test_report_generator_includes_metadata_and_response_shape():
    snapshot = RepositorySnapshot(
        owner="example",
        name="ui",
        default_branch="main",
        html_url=None,
        description=None,
        primary_language="TypeScript",
        topics=[],
        tree_paths=["package.json", "src/main.tsx"],
        top_level_directories=["src"],
        selected_paths=["package.json", "src/main.tsx"],
        files=[
            GitHubFile(
                "package.json",
                '{"dependencies":{"react":"latest"},"devDependencies":{"vite":"latest"}}',
                72,
                "manifest",
            ),
            GitHubFile("src/main.tsx", "import React from 'react'", 25, "entry_point"),
        ],
        truncated=False,
    )

    analysis = RepositoryAnalyzer().analyze(snapshot)
    response = ReportGenerator().generate(snapshot, analysis)

    assert response.repository.owner == "example"
    assert response.analysis_metadata.files_inspected == 2
    assert response.analysis_metadata.analysis_mode == "heuristic"
    assert "React" in response.report.technology_stack


def test_analyzer_excludes_test_application_entry_points():
    snapshot = RepositorySnapshot(
        owner="spring-projects",
        name="spring-petclinic",
        default_branch="main",
        html_url=None,
        description=None,
        primary_language="CSS",
        topics=[],
        tree_paths=[
            "pom.xml",
            "src/main/java/org/example/PetClinicApplication.java",
            "src/test/java/org/example/MysqlTestApplication.java",
        ],
        top_level_directories=["src"],
        selected_paths=["pom.xml", "src/main/java/org/example/PetClinicApplication.java"],
        files=[
            GitHubFile("pom.xml", "<artifactId>spring-boot-starter-web</artifactId>", 48, "manifest"),
            GitHubFile(
                "src/main/java/org/example/PetClinicApplication.java",
                "class PetClinicApplication {}",
                28,
                "entry_point",
            ),
        ],
        truncated=False,
    )

    analysis = RepositoryAnalyzer().analyze(snapshot)

    assert "Spring Boot" in analysis.technology_stack
    assert "CSS" in analysis.technology_stack
    assert analysis.entry_points == ["src/main/java/org/example/PetClinicApplication.java"]
