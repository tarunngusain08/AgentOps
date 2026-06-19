from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass

from app.analyzer.file_selection import classify_file
from app.analyzer.repository_index import RepositoryIndex, RepositoryIndexer
from app.github.service import RepositorySnapshot


@dataclass(frozen=True)
class ComponentFinding:
    name: str
    responsibility: str
    evidence: list[str]


@dataclass(frozen=True)
class RepositoryAnalysis:
    technology_stack: list[str]
    components: list[ComponentFinding]
    entry_points: list[str]
    important_files: list[str]
    relationships: list[str]
    assumptions: list[str]
    overview: str
    repository_index: RepositoryIndex


class RepositoryAnalyzer:
    def __init__(self, indexer: RepositoryIndexer | None = None):
        self.indexer = indexer or RepositoryIndexer()

    def analyze(self, snapshot: RepositorySnapshot) -> RepositoryAnalysis:
        technology_stack = self._detect_technology_stack(snapshot)
        components = self._detect_components(snapshot)
        entry_points = self._detect_entry_points(snapshot)
        important_files = self._important_files(snapshot)
        repository_index = self.indexer.build(snapshot)
        relationships = self._relationships(components, technology_stack, repository_index)
        assumptions = self._assumptions(snapshot, repository_index)
        overview = self._overview(snapshot, technology_stack, components, repository_index)

        return RepositoryAnalysis(
            technology_stack=technology_stack,
            components=components,
            entry_points=entry_points,
            important_files=important_files,
            relationships=relationships,
            assumptions=assumptions,
            overview=overview,
            repository_index=repository_index,
        )

    def _detect_technology_stack(self, snapshot: RepositorySnapshot) -> list[str]:
        detected: list[str] = []

        files_by_name = {file.path.rsplit("/", 1)[-1].lower(): file for file in snapshot.files}
        paths = [path.lower() for path in snapshot.tree_paths]
        extension_counts = Counter(_extension(path) for path in snapshot.tree_paths)

        if "pyproject.toml" in files_by_name or "requirements.txt" in files_by_name:
            detected.extend(["Python"])
            text = "\n".join(
                file.content.lower()
                for name, file in files_by_name.items()
                if name in {"pyproject.toml", "requirements.txt"}
            )
            has_fastapi = "fastapi" in text
            if has_fastapi:
                detected.append("FastAPI")
            if "django" in text:
                detected.append("Django")
            if "flask" in text and not has_fastapi:
                detected.append("Flask")
            if "pydantic" in text:
                detected.append("Pydantic")

        package_json = files_by_name.get("package.json")
        if package_json:
            detected.extend(self._detect_package_json_stack(package_json.content))
            if snapshot.name.lower() == "react" or "react" in {topic.lower() for topic in snapshot.topics}:
                detected.append("React")

        if "pom.xml" in files_by_name or "build.gradle" in files_by_name:
            detected.append("Java")
            build_text = "\n".join(
                file.content.lower()
                for name, file in files_by_name.items()
                if name in {"pom.xml", "build.gradle"}
            )
            if "spring-boot" in build_text or "springframework.boot" in build_text:
                detected.append("Spring Boot")

        if "go.mod" in files_by_name:
            detected.append("Go")
            go_mod = files_by_name["go.mod"].content.lower()
            if "gin-gonic/gin" in go_mod:
                detected.append("Gin")
            if "labstack/echo" in go_mod:
                detected.append("Echo")

        if "cargo.toml" in files_by_name:
            detected.append("Rust")
            cargo = files_by_name["cargo.toml"].content.lower()
            if "axum" in cargo:
                detected.append("Axum")
            if "actix-web" in cargo:
                detected.append("Actix Web")

        if extension_counts[".ts"] or extension_counts[".tsx"]:
            detected.append("TypeScript")
        elif extension_counts[".js"] or extension_counts[".jsx"]:
            detected.append("JavaScript")
        if extension_counts[".py"]:
            detected.append("Python")
        if extension_counts[".java"]:
            detected.append("Java")

        if any(path.endswith("dockerfile") for path in paths) or any("docker-compose.yml" in path for path in paths):
            detected.append("Docker")
        if snapshot.primary_language:
            detected.append(snapshot.primary_language)

        return _dedupe(detected) or ["Unknown"]

    def _detect_package_json_stack(self, content: str) -> list[str]:
        stack = ["JavaScript/TypeScript"]
        package_name = ""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            lowered = content.lower()
            dependencies = lowered
        else:
            deps = {}
            deps.update(parsed.get("dependencies") or {})
            deps.update(parsed.get("devDependencies") or {})
            dependencies = " ".join(deps.keys()).lower()
            package_name = str(parsed.get("name") or "").lower()

        if "react" in dependencies or package_name == "react":
            stack.append("React")
        if "next" in dependencies:
            stack.append("Next.js")
        if "vite" in dependencies:
            stack.append("Vite")
        if "express" in dependencies:
            stack.append("Express")
        if "fastify" in dependencies:
            stack.append("Fastify")
        if "typescript" in dependencies:
            stack.append("TypeScript")
        return stack

    def _detect_components(self, snapshot: RepositorySnapshot) -> list[ComponentFinding]:
        components: list[ComponentFinding] = []
        directories = snapshot.top_level_directories

        rules = [
            ({"frontend", "ui", "web", "client"}, "Frontend", "User-facing web application or client surface."),
            ({"backend", "api", "server", "app"}, "API/Application Layer", "Backend application or API entry point."),
            ({"src", "lib", "pkg"}, "Source Modules", "Primary implementation modules."),
            ({"services", "service"}, "Service Layer", "Business logic and workflow coordination."),
            ({"repositories", "repository", "dao", "persistence"}, "Persistence Layer", "Data access and persistence code."),
            ({"db", "database", "migrations"}, "Database", "Database schema, migrations, or persistence configuration."),
            ({"worker", "workers", "jobs"}, "Background Workers", "Asynchronous or scheduled work."),
            ({"docs", "documentation"}, "Documentation", "Project documentation and guides."),
            ({"tests", "test", "__tests__"}, "Tests", "Automated tests and validation code."),
            ({"infra", "deploy", "deployment", "k8s", "terraform"}, "Infrastructure", "Deployment and infrastructure configuration."),
        ]

        for names, component_name, responsibility in rules:
            evidence = [f"{directory}/" for directory in directories if directory.lower() in names]
            if evidence:
                components.append(ComponentFinding(component_name, responsibility, evidence))

        source_root = self._source_root_component(snapshot, components)
        if source_root:
            components.insert(0, source_root)

        if not components:
            manifest_evidence = [file.path for file in snapshot.files if file.source_type == "manifest"]
            if manifest_evidence:
                components.append(
                    ComponentFinding(
                        "Application",
                        "Repository root contains the primary application configuration and source layout.",
                        manifest_evidence[:3],
                    )
                )

        return components

    def _source_root_component(
        self,
        snapshot: RepositorySnapshot,
        existing_components: list[ComponentFinding],
    ) -> ComponentFinding | None:
        existing_evidence = {
            evidence.rstrip("/")
            for component in existing_components
            for evidence in component.evidence
        }
        ignored = {
            "docs",
            "doc",
            "documentation",
            "tests",
            "test",
            "__tests__",
            "examples",
            "example",
            "scripts",
        }
        code_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs"}
        evidence: list[str] = []

        for directory in snapshot.top_level_directories:
            lowered = directory.lower()
            if lowered in ignored or directory in existing_evidence:
                continue
            if lowered == snapshot.name.lower() or any(
                path.startswith(f"{directory}/") and _extension(path) in code_extensions
                for path in snapshot.tree_paths
            ):
                evidence.append(f"{directory}/")

        if not evidence:
            return None

        return ComponentFinding(
            "Source Modules",
            "Primary implementation modules inferred from source-bearing top-level directories.",
            evidence[:5],
        )

    def _detect_entry_points(self, snapshot: RepositorySnapshot) -> list[str]:
        entry_points = [file.path for file in snapshot.files if file.source_type == "entry_point"]
        for path in snapshot.tree_paths:
            if classify_file(path) == "entry_point" and path not in entry_points:
                entry_points.append(path)
        return sorted(entry_points)

    def _important_files(self, snapshot: RepositorySnapshot) -> list[str]:
        important = [
            file.path
            for file in snapshot.files
            if file.source_type in {"manifest", "config", "infrastructure", "entry_point", "readme"}
        ]
        important.extend(f"{directory}/" for directory in snapshot.top_level_directories[:12])
        return _dedupe(important)

    def _relationships(
        self,
        components: list[ComponentFinding],
        stack: list[str],
        repository_index: RepositoryIndex,
    ) -> list[str]:
        names = {component.name for component in components}
        relationships: list[str] = []

        if "Frontend" in names and "API/Application Layer" in names:
            relationships.append("Frontend -> API/Application Layer for user-facing requests.")
        if "API/Application Layer" in names and "Service Layer" in names:
            relationships.append("API/Application Layer -> Service Layer for business workflow coordination.")
        if "Service Layer" in names and "Persistence Layer" in names:
            relationships.append("Service Layer -> Persistence Layer for data access.")
        if "Persistence Layer" in names and "Database" in names:
            relationships.append("Persistence Layer -> Database for stored application state.")
        if "Background Workers" in names and "Service Layer" in names:
            relationships.append("Background Workers -> Service Layer for asynchronous processing.")
        if "React" in stack or "Next.js" in stack:
            relationships.append("React/Next.js UI components compose the frontend and call backend or framework routes.")
        if "FastAPI" in stack:
            relationships.append("FastAPI application entry points define routes and delegate request handling to Python modules.")
        if "Spring Boot" in stack:
            relationships.append("Spring Boot application entry point starts controllers, services, and repository-style components.")
        if repository_index.tests:
            relationships.append("Indexed tests map back to source files through deterministic path and stem matching.")
        if repository_index.symbols:
            relationships.append("Static code intelligence identifies shallow symbols and imports for source-level navigation.")

        return relationships or ["Repository structure suggests components collaborate through the main application entry points."]

    def _assumptions(self, snapshot: RepositorySnapshot, repository_index: RepositoryIndex) -> list[str]:
        assumptions = [
            "Analysis is heuristic and based on selected architecture signals, not a full clone or AST-level dependency graph.",
            "README content is optional; file structure, manifests, entry points, and top-level directories are prioritized.",
            "Static code intelligence is shallow and deterministic; it does not perform call graph, type resolution, or semantic analysis.",
        ]
        if snapshot.truncated:
            assumptions.append("GitHub tree or file selection was truncated, so some files may not be represented.")
        if repository_index.metadata.truncated:
            assumptions.append(f"Repository index was truncated because of {repository_index.metadata.truncation_reason}.")
        if repository_index.files and not repository_index.symbols:
            assumptions.append("Supported source files were indexed, but no shallow symbols were detected.")
        if not snapshot.files:
            assumptions.append("No selected files were fetched; report is based mainly on repository metadata and directory structure.")
        return assumptions

    def _overview(
        self,
        snapshot: RepositorySnapshot,
        stack: list[str],
        components: list[ComponentFinding],
        repository_index: RepositoryIndex,
    ) -> str:
        stack_text = ", ".join(stack[:5]) if stack else "unknown technologies"
        component_text = ", ".join(component.name for component in components[:4]) or "repository-level modules"
        description = f" {snapshot.description}" if snapshot.description else ""
        index_text = ""
        if repository_index.metadata.files_indexed:
            index_text = (
                f" Static code intelligence indexed {repository_index.metadata.files_indexed} source file(s) "
                f"and {repository_index.metadata.symbols_found} symbol(s)."
            )
        return (
            f"{snapshot.owner}/{snapshot.name} appears to be a {stack_text} project with "
            f"{component_text}.{description}{index_text}"
        )


def _extension(path: str) -> str:
    match = re.search(r"(\.[A-Za-z0-9]+)$", path)
    return match.group(1).lower() if match else ""


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
