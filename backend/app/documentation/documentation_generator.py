from __future__ import annotations

import json

from app.analyzer.repository_analyzer import ComponentFinding, RepositoryAnalysis
from app.analyzer.repository_index import RepositoryImport, RepositorySymbol
from app.documentation.guide import Guide, GuideItem, GuideSection
from app.github.service import GitHubFile, RepositorySnapshot
from app.schemas import ArchitectureReport


class DocumentationGenerator:
    def generate_onboarding_guide(
        self,
        snapshot: RepositorySnapshot,
        analysis: RepositoryAnalysis,
        report: ArchitectureReport,
    ) -> Guide:
        assumptions = list(analysis.assumptions)
        sections = [
            self._project_overview(snapshot, report),
            self._technology_stack(analysis, snapshot),
            self._how_to_run(snapshot, assumptions),
            self._architecture_summary(report),
            self._key_components(analysis.components),
            self._code_navigation(analysis),
            self._common_workflows(snapshot),
            self._useful_files(analysis.important_files),
        ]
        assumption_section = GuideSection(
            title="Assumptions",
            items=[GuideItem(text=assumption, evidence=[]) for assumption in _dedupe(assumptions)],
        )
        sections.append(assumption_section)

        evidence = _dedupe(
            evidence
            for section in sections
            for item in section.items
            for evidence in item.evidence
        )

        return Guide(
            title=f"Onboarding Guide for {snapshot.owner}/{snapshot.name}",
            sections=sections,
            evidence=evidence,
            assumptions=_dedupe(assumptions),
        )

    def _project_overview(
        self,
        snapshot: RepositorySnapshot,
        report: ArchitectureReport,
    ) -> GuideSection:
        evidence = self._evidence_for_paths(snapshot, ["README.md"]) or report.important_files[:3]
        text = (
            f"Start with {snapshot.owner}/{snapshot.name}: {report.overview} "
            "Use this guide to understand the repository shape before changing code."
        )
        return GuideSection("Project Overview", [GuideItem(text=text, evidence=evidence)])

    def _technology_stack(
        self,
        analysis: RepositoryAnalysis,
        snapshot: RepositorySnapshot,
    ) -> GuideSection:
        items = [
            GuideItem(
                text=f"{technology} is part of the detected stack.",
                evidence=self._technology_evidence(technology, snapshot),
            )
            for technology in analysis.technology_stack
        ]
        return GuideSection("Technology Stack", items or [GuideItem("No technology stack was detected.", [])])

    def _how_to_run(
        self,
        snapshot: RepositorySnapshot,
        assumptions: list[str],
    ) -> GuideSection:
        items: list[GuideItem] = []
        files_by_name = self._files_by_name(snapshot)

        package_json = files_by_name.get("package.json")
        if package_json:
            items.extend(self._package_json_run_items(package_json))

        if "requirements.txt" in files_by_name:
            items.append(
                GuideItem(
                    text="Install Python dependencies with `python -m pip install -r requirements.txt`.",
                    evidence=["requirements.txt"],
                )
            )
        if "pyproject.toml" in files_by_name:
            items.append(
                GuideItem(
                    text="Use `pyproject.toml` as the source of truth for Python project dependencies and packaging.",
                    evidence=["pyproject.toml"],
                )
            )

        pom = files_by_name.get("pom.xml")
        if pom:
            command = "./mvnw spring-boot:run" if "mvnw" in snapshot.tree_paths else "mvn spring-boot:run"
            if self._is_spring_boot_build(pom.content):
                items.append(
                    GuideItem(
                        text=f"Run the Spring Boot application with `{command}` if the local environment has Java configured.",
                        evidence=["pom.xml"],
                    )
                )
            else:
                items.append(
                    GuideItem(
                        text="Use `pom.xml` as the source of truth for Maven build and dependency commands.",
                        evidence=["pom.xml"],
                    )
                )
        gradle = files_by_name.get("build.gradle")
        if gradle:
            command = "./gradlew bootRun" if "gradlew" in snapshot.tree_paths else "gradle bootRun"
            if self._is_spring_boot_build(gradle.content):
                items.append(
                    GuideItem(
                        text=f"Run the Spring Boot application with `{command}` if the local environment has Java configured.",
                        evidence=["build.gradle"],
                    )
                )
            else:
                items.append(
                    GuideItem(
                        text="Use `build.gradle` as the source of truth for Gradle build and dependency commands.",
                        evidence=["build.gradle"],
                    )
                )
        if "go.mod" in files_by_name:
            entry = self._first_entry_point(snapshot, ".go")
            if entry:
                items.append(GuideItem(text=f"Run the Go entry point with `go run {entry}`.", evidence=["go.mod", entry]))
            else:
                items.append(GuideItem(text="Use `go.mod` to resolve Go modules before running the service.", evidence=["go.mod"]))
        if "cargo.toml" in files_by_name:
            items.append(GuideItem(text="Run the Rust project with `cargo run`.", evidence=["Cargo.toml"]))
        if "docker-compose.yml" in files_by_name:
            items.append(GuideItem(text="Start containerized dependencies or services with `docker compose up`.", evidence=["docker-compose.yml"]))
        if "dockerfile" in files_by_name:
            items.append(GuideItem(text="Build the container image from the repository `Dockerfile`.", evidence=["Dockerfile"]))

        if not items:
            assumptions.append("No explicit run command was found in inspected files; inspect project-specific docs before running locally.")
            items.append(
                GuideItem(
                    text="No evidence-backed run command was detected from inspected files.",
                    evidence=[],
                )
            )

        return GuideSection("How To Run", items)

    def _architecture_summary(self, report: ArchitectureReport) -> GuideSection:
        items = [
            GuideItem(text=report.overview, evidence=report.important_files[:3]),
        ]
        items.extend(
            GuideItem(text=relationship, evidence=report.entry_points[:2] or report.important_files[:2])
            for relationship in report.relationships
        )
        return GuideSection("Architecture Summary", items)

    def _key_components(self, components: list[ComponentFinding]) -> GuideSection:
        items = [
            GuideItem(
                text=f"{component.name}: {component.responsibility}",
                evidence=component.evidence,
            )
            for component in components
        ]
        return GuideSection("Key Components", items or [GuideItem("No major components were detected.", [])])

    def _code_navigation(self, analysis: RepositoryAnalysis) -> GuideSection:
        index = analysis.repository_index
        items: list[GuideItem] = []

        if index.files:
            languages = ", ".join(sorted({file.language for file in index.files}))
            items.append(
                GuideItem(
                    text=f"Use the indexed {languages} files for source-level navigation before deeper code review.",
                    evidence=[file.path for file in index.files[:6]],
                )
            )

        for symbol in self._navigation_symbols(index.symbols):
            items.append(
                GuideItem(
                    text=f"Start with {self._symbol_name(symbol)} in `{symbol.path}` when tracing {symbol.kind.replace('_', ' ')} behavior.",
                    evidence=[symbol.path],
                )
            )

        for link in index.tests[:4]:
            items.append(
                GuideItem(
                    text=f"Read `{link.test_path}` next to `{link.source_path}` because the files have {link.reason.replace('_', ' ')}.",
                    evidence=[link.test_path, link.source_path],
                )
            )

        for item in self._navigation_imports(index.imports):
            items.append(
                GuideItem(
                    text=f"`{item.path}` imports `{item.module}`, which is a useful dependency signal while onboarding.",
                    evidence=[item.path],
                )
            )

        if not items:
            items.append(
                GuideItem(
                    text="No supported Python, TypeScript/JavaScript, or Go code navigation signals were detected in inspected files.",
                    evidence=[],
                )
            )

        return GuideSection("Code Navigation", items[:10])

    def _common_workflows(self, snapshot: RepositorySnapshot) -> GuideSection:
        items: list[GuideItem] = []
        directories = {directory.lower(): directory for directory in snapshot.top_level_directories}

        if "tests" in directories or "test" in directories:
            evidence = f"{directories.get('tests') or directories.get('test')}/"
            items.append(GuideItem("Use the test directory to understand validation coverage and expected behavior.", [evidence]))
        if "docs" in directories:
            items.append(GuideItem("Use the docs directory for deeper framework, API, or contribution context.", [f"{directories['docs']}/"]))
        if "frontend" in directories or "ui" in directories or "web" in directories:
            evidence = directories.get("frontend") or directories.get("ui") or directories.get("web")
            items.append(GuideItem("Review the frontend directory for user-facing flows and UI entry points.", [f"{evidence}/"]))
        if "backend" in directories or "api" in directories or "app" in directories:
            evidence = directories.get("backend") or directories.get("api") or directories.get("app")
            items.append(GuideItem("Review the backend/application directory for API routes and service behavior.", [f"{evidence}/"]))

        package_json = self._files_by_name(snapshot).get("package.json")
        if package_json:
            items.extend(self._package_script_workflows(package_json))

        if not items:
            items.append(GuideItem("Start by reading the important files and entry points listed in this guide.", []))
        return GuideSection("Common Workflows", items)

    def _useful_files(self, important_files: list[str]) -> GuideSection:
        return GuideSection(
            "Useful Files",
            [
                GuideItem(
                    text=f"Review `{path}` early while onboarding.",
                    evidence=[path],
                )
                for path in important_files[:12]
            ],
        )

    def _package_json_run_items(self, package_json: GitHubFile) -> list[GuideItem]:
        scripts = self._package_scripts(package_json)
        preferred = ["dev", "start", "build", "test"]
        items: list[GuideItem] = []

        for script_name in preferred:
            if script_name in scripts:
                command = "npm start" if script_name == "start" else f"npm run {script_name}"
                items.append(
                    GuideItem(
                        text=f"Run `{command}` for the `{script_name}` script.",
                        evidence=["package.json"],
                    )
                )

        for script_name in sorted(scripts):
            if script_name in preferred or len(items) >= 4:
                continue
            items.append(
                GuideItem(
                    text=f"Run `npm run {script_name}` for the `{script_name}` script.",
                    evidence=["package.json"],
                )
            )

        return items

    def _package_script_workflows(self, package_json: GitHubFile) -> list[GuideItem]:
        scripts = self._package_scripts(package_json)
        workflows = []
        for script_name in ("test", "lint", "build", "dev"):
            if script_name in scripts:
                workflows.append(
                    GuideItem(
                        text=f"The `{script_name}` workflow is available through `package.json`.",
                        evidence=["package.json"],
                    )
                )
        return workflows

    def _package_scripts(self, package_json: GitHubFile) -> dict[str, str]:
        try:
            parsed = json.loads(package_json.content)
        except json.JSONDecodeError:
            return {}
        scripts = parsed.get("scripts")
        if not isinstance(scripts, dict):
            return {}
        return {str(name): str(command) for name, command in scripts.items()}

    def _is_spring_boot_build(self, content: str) -> bool:
        lowered = content.lower()
        return "spring-boot" in lowered or "springframework.boot" in lowered

    def _technology_evidence(self, technology: str, snapshot: RepositorySnapshot) -> list[str]:
        lowered = technology.lower()
        evidence_by_name = {
            "javascript/typescript": ["package.json"],
            "javascript": ["package.json"],
            "typescript": ["package.json"],
            "react": ["package.json"],
            "next.js": ["package.json"],
            "vite": ["package.json", "vite.config.ts"],
            "express": ["package.json"],
            "fastify": ["package.json"],
            "python": ["pyproject.toml", "requirements.txt"],
            "fastapi": ["pyproject.toml", "requirements.txt"],
            "pydantic": ["pyproject.toml", "requirements.txt"],
            "django": ["pyproject.toml", "requirements.txt"],
            "flask": ["pyproject.toml", "requirements.txt"],
            "java": ["pom.xml", "build.gradle"],
            "spring boot": ["pom.xml", "build.gradle"],
            "go": ["go.mod"],
            "rust": ["Cargo.toml"],
            "docker": ["Dockerfile", "docker-compose.yml"],
        }
        candidates = evidence_by_name.get(lowered, [])
        evidence = self._evidence_for_paths(snapshot, candidates)
        return evidence or ["GitHub repository metadata"]

    def _evidence_for_paths(self, snapshot: RepositorySnapshot, candidates: list[str]) -> list[str]:
        present = [file.path for file in snapshot.files]
        present.extend(path for path in snapshot.tree_paths if path not in present)
        result = []
        for candidate in candidates:
            for path in present:
                if path == candidate or path.endswith(f"/{candidate}"):
                    result.append(path)
                    break
        return _dedupe(result)

    def _files_by_name(self, snapshot: RepositorySnapshot) -> dict[str, GitHubFile]:
        return {file.path.rsplit("/", 1)[-1].lower(): file for file in snapshot.files}

    def _first_entry_point(self, snapshot: RepositorySnapshot, suffix: str) -> str | None:
        for file in snapshot.files:
            if file.source_type == "entry_point" and file.path.endswith(suffix):
                return file.path
        return None

    def _navigation_symbols(self, symbols: list[RepositorySymbol]) -> list[RepositorySymbol]:
        priority = {"class": 0, "type": 0, "function": 1, "method": 1, "package": 2, "constant": 3}
        return sorted(
            [symbol for symbol in symbols if symbol.kind != "test_function"],
            key=lambda symbol: (priority.get(symbol.kind, 99), symbol.path, symbol.container or "", symbol.name),
        )[:5]

    def _navigation_imports(self, imports: list[RepositoryImport]) -> list[RepositoryImport]:
        return sorted(
            [item for item in imports if not item.module.startswith(".")],
            key=lambda item: (item.path, item.module),
        )[:3]

    def _symbol_name(self, symbol: RepositorySymbol) -> str:
        return f"{symbol.container}.{symbol.name}" if symbol.container else symbol.name


def _dedupe(values) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
