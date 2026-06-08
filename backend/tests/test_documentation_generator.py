from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.documentation.documentation_generator import DocumentationGenerator
from app.github.service import GitHubFile, RepositorySnapshot
from app.reporting.report_generator import ReportGenerator


def test_documentation_generator_builds_fastapi_onboarding_guide():
    snapshot = RepositorySnapshot(
        owner="example",
        name="api",
        default_branch="main",
        html_url="https://github.com/example/api",
        description="Example API service",
        primary_language="Python",
        topics=[],
        tree_paths=["README.md", "pyproject.toml", "app/main.py", "app/api/routes.py", "tests/test_api.py"],
        top_level_directories=["app", "tests"],
        selected_paths=["README.md", "pyproject.toml", "app/main.py"],
        files=[
            GitHubFile("README.md", "# Example API", 13, "readme"),
            GitHubFile("pyproject.toml", 'dependencies = ["fastapi", "pydantic"]', 38, "manifest"),
            GitHubFile("app/main.py", "from fastapi import FastAPI\napp = FastAPI()", 45, "entry_point"),
        ],
        truncated=False,
    )

    guide = _generate_guide(snapshot)

    assert guide.title == "Onboarding Guide for example/api"
    assert _section_titles(guide) == [
        "Project Overview",
        "Technology Stack",
        "How To Run",
        "Architecture Summary",
        "Key Components",
        "Common Workflows",
        "Useful Files",
        "Assumptions",
    ]
    assert any("FastAPI" in item.text for item in _section(guide, "Technology Stack").items)
    assert any(item.evidence == ["pyproject.toml"] for item in _section(guide, "How To Run").items)
    assert any("Use the test directory" in item.text for item in _section(guide, "Common Workflows").items)


def test_documentation_generator_uses_package_json_scripts_as_run_evidence():
    snapshot = RepositorySnapshot(
        owner="example",
        name="web",
        default_branch="main",
        html_url=None,
        description=None,
        primary_language="TypeScript",
        topics=[],
        tree_paths=["package.json", "vite.config.ts", "src/main.tsx"],
        top_level_directories=["src"],
        selected_paths=["package.json", "vite.config.ts", "src/main.tsx"],
        files=[
            GitHubFile(
                "package.json",
                """
                {
                  "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "test": "vitest"
                  },
                  "dependencies": {
                    "react": "latest",
                    "vite": "latest",
                    "typescript": "latest"
                  }
                }
                """,
                238,
                "manifest",
            ),
            GitHubFile("vite.config.ts", "import { defineConfig } from 'vite'", 36, "config"),
            GitHubFile("src/main.tsx", "import React from 'react'", 25, "entry_point"),
        ],
        truncated=False,
    )

    guide = _generate_guide(snapshot)
    how_to_run = _section(guide, "How To Run")

    assert any(item.text == "Run `npm run dev` for the `dev` script." for item in how_to_run.items)
    assert all(item.evidence == ["package.json"] for item in how_to_run.items)
    assert any("The `build` workflow is available through `package.json`." in item.text for item in _section(guide, "Common Workflows").items)


def test_documentation_generator_detects_spring_maven_run_command():
    snapshot = RepositorySnapshot(
        owner="example",
        name="spring-service",
        default_branch="main",
        html_url=None,
        description=None,
        primary_language="Java",
        topics=[],
        tree_paths=["pom.xml", "mvnw", "src/main/java/com/example/Application.java"],
        top_level_directories=["src"],
        selected_paths=["pom.xml", "src/main/java/com/example/Application.java"],
        files=[
            GitHubFile("pom.xml", "<artifactId>spring-boot-starter-web</artifactId>", 48, "manifest"),
            GitHubFile(
                "src/main/java/com/example/Application.java",
                "class Application {}",
                20,
                "entry_point",
            ),
        ],
        truncated=False,
    )

    guide = _generate_guide(snapshot)
    how_to_run = _section(guide, "How To Run")

    assert any("`./mvnw spring-boot:run`" in item.text for item in how_to_run.items)
    assert any(item.evidence == ["pom.xml"] for item in how_to_run.items)


def test_documentation_generator_marks_missing_run_evidence_as_assumption():
    snapshot = RepositorySnapshot(
        owner="example",
        name="unknown",
        default_branch="main",
        html_url=None,
        description=None,
        primary_language=None,
        topics=[],
        tree_paths=["src/main.py"],
        top_level_directories=["src"],
        selected_paths=["src/main.py"],
        files=[GitHubFile("src/main.py", "print('hello')", 14, "entry_point")],
        truncated=False,
    )

    guide = _generate_guide(snapshot)
    how_to_run = _section(guide, "How To Run")

    assert len(how_to_run.items) == 1
    assert how_to_run.items[0].text == "No evidence-backed run command was detected from inspected files."
    assert how_to_run.items[0].evidence == []
    assert "No explicit run command was found in inspected files; inspect project-specific docs before running locally." in guide.assumptions


def _generate_guide(snapshot: RepositorySnapshot):
    analysis = RepositoryAnalyzer().analyze(snapshot)
    report = ReportGenerator().generate(snapshot, analysis)
    return DocumentationGenerator().generate_onboarding_guide(snapshot, analysis, report.report)


def _section_titles(guide) -> list[str]:
    return [section.title for section in guide.sections]


def _section(guide, title: str):
    return next(section for section in guide.sections if section.title == title)
