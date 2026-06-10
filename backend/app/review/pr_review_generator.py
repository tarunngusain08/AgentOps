from __future__ import annotations

from collections import defaultdict

from app.analyzer.repository_analyzer import RepositoryAnalysis
from app.github.pull_request_loader import PullRequestSnapshot
from app.github.service import RepositorySnapshot
from app.review.models import ChangedFileSignal, DiffAnalysis, Finding, Review
from app.schemas import ArchitectureReport


class PRReviewGenerator:
    def generate(
        self,
        snapshot: RepositorySnapshot,
        analysis: RepositoryAnalysis,
        report: ArchitectureReport,
        pull_request: PullRequestSnapshot,
        diff: DiffAnalysis,
    ) -> Review:
        findings: list[Finding] = []
        findings.extend(self._risk_findings(diff))
        findings.extend(self._breaking_change_findings(diff))
        findings.extend(self._file_attention_findings(diff))
        findings.extend(self._testing_findings(diff))
        findings.extend(self._architecture_findings(analysis, report, diff))

        if not findings:
            findings.append(
                Finding(
                    category="file_attention",
                    severity="Low",
                    description="No architecture-level risks were detected from the changed file set.",
                    evidence=[file.path for file in diff.files[:5]],
                )
            )

        assumptions = _dedupe([*analysis.assumptions, *diff.assumptions])
        confidence = self._confidence(diff, findings)
        metadata = {
            "changed_files": pull_request.changed_files,
            "files_inspected": diff.files_inspected,
            "patch_bytes": diff.patch_bytes,
            "high_signal_files": diff.high_signal_files,
            "analysis_mode": "heuristic",
            "truncated": diff.truncated,
        }
        summary = (
            f"PR #{pull_request.number} changes {pull_request.changed_files} file(s) in "
            f"{snapshot.owner}/{snapshot.name}. The review focuses on architecture-level signals, "
            f"changed-file categories, test coverage signals, and evidence-backed risk indicators."
        )

        return Review(
            summary=summary,
            findings=self._dedupe_findings(findings),
            assumptions=assumptions,
            confidence=confidence,
            metadata=metadata,
        )

    def _risk_findings(self, diff: DiffAnalysis) -> list[Finding]:
        findings = []
        grouped = self._group_by_category(diff.files)
        if grouped["manifest"]:
            findings.append(
                Finding(
                    category="potential_risk",
                    severity="High",
                    description="Dependency or build manifest files changed; verify dependency, build, and packaging behavior.",
                    evidence=_paths(grouped["manifest"]),
                )
            )
        if grouped["infrastructure"]:
            findings.append(
                Finding(
                    category="potential_risk",
                    severity="High",
                    description="Infrastructure or container files changed; verify local and deployment runtime assumptions.",
                    evidence=_paths(grouped["infrastructure"]),
                )
            )
        if grouped["config"]:
            findings.append(
                Finding(
                    category="potential_risk",
                    severity="Medium",
                    description="Configuration files changed; verify environment-specific behavior and startup paths.",
                    evidence=_paths(grouped["config"]),
                )
            )
        if grouped["entry_point"]:
            findings.append(
                Finding(
                    category="potential_risk",
                    severity="High",
                    description="Application entry-point files changed; verify request routing, startup, or bootstrapping behavior.",
                    evidence=_paths(grouped["entry_point"]),
                )
            )
        if diff.changed_files >= 30 or diff.patch_bytes >= 250_000:
            findings.append(
                Finding(
                    category="potential_risk",
                    severity="Medium",
                    description="Large PR size increases review risk; prioritize high-signal files and test coverage.",
                    evidence=_paths(diff.files[:8]),
                )
            )
        return findings

    def _breaking_change_findings(self, diff: DiffAnalysis) -> list[Finding]:
        risky_statuses = {"removed", "renamed"}
        risky_categories = {"manifest", "config", "infrastructure", "entry_point", "source"}
        changed = [
            file
            for file in diff.files
            if file.status in risky_statuses and file.category in risky_categories
        ]
        if not changed:
            return []
        return [
            Finding(
                category="breaking_change",
                severity="High" if any(file.category in {"manifest", "infrastructure", "entry_point"} for file in changed) else "Medium",
                description="Files were removed or renamed in architecture-relevant areas; verify callers, imports, and deployment references.",
                evidence=_paths(changed),
            )
        ]

    def _file_attention_findings(self, diff: DiffAnalysis) -> list[Finding]:
        high_signal = [file for file in diff.files if file.high_signal]
        if high_signal:
            return [
                Finding(
                    category="file_attention",
                    severity="Medium",
                    description="Review these high-signal files first because they influence build, configuration, entry points, or source behavior.",
                    evidence=_paths(high_signal[:12]),
                )
            ]
        docs = [file for file in diff.files if file.category == "docs"]
        if docs and len(docs) == len(diff.files):
            return [
                Finding(
                    category="file_attention",
                    severity="Low",
                    description="Changed files appear documentation-only based on path and extension signals.",
                    evidence=_paths(docs[:12]),
                )
            ]
        return []

    def _testing_findings(self, diff: DiffAnalysis) -> list[Finding]:
        test_files = [file for file in diff.files if file.category == "test"]
        implementation_files = [
            file
            for file in diff.files
            if file.category in {"manifest", "config", "infrastructure", "entry_point", "source"}
        ]
        if implementation_files and not test_files:
            return [
                Finding(
                    category="testing_concern",
                    severity="Medium",
                    description="Implementation, configuration, or build files changed without corresponding test-file changes.",
                    evidence=_paths(implementation_files[:12]),
                )
            ]
        if test_files and implementation_files:
            return [
                Finding(
                    category="testing_concern",
                    severity="Low",
                    description="Test files changed alongside implementation files; verify the tests cover the high-signal changes.",
                    evidence=_paths(test_files[:12]),
                )
            ]
        return []

    def _architecture_findings(
        self,
        analysis: RepositoryAnalysis,
        report: ArchitectureReport,
        diff: DiffAnalysis,
    ) -> list[Finding]:
        findings = []
        component_matches = []
        for component in analysis.components:
            evidence_prefixes = [item.rstrip("/") for item in component.evidence]
            touched = [
                file.path
                for file in diff.files
                if any(file.path == prefix or file.path.startswith(f"{prefix}/") for prefix in evidence_prefixes)
            ]
            if touched:
                component_matches.append((component.name, touched))

        for component_name, paths in component_matches[:5]:
            findings.append(
                Finding(
                    category="architecture_impact",
                    severity="Medium",
                    description=f"{component_name} is touched by this PR; verify component-level behavior and integration points.",
                    evidence=paths[:12],
                )
            )

        touched_entry_points = [
            file.path
            for file in diff.files
            if file.path in report.entry_points or file.category == "entry_point"
        ]
        if touched_entry_points:
            findings.append(
                Finding(
                    category="architecture_impact",
                    severity="High",
                    description="The PR touches likely application entry points, so startup or request-flow behavior may be affected.",
                    evidence=_dedupe(touched_entry_points[:12]),
                )
            )
        return findings

    def _confidence(self, diff: DiffAnalysis, findings: list[Finding]) -> str:
        if diff.truncated or not diff.files:
            return "Low"
        if all(finding.evidence for finding in findings) and diff.patch_bytes > 0:
            return "High"
        return "Medium"

    def _group_by_category(self, files: list[ChangedFileSignal]) -> dict[str, list[ChangedFileSignal]]:
        grouped: dict[str, list[ChangedFileSignal]] = defaultdict(list)
        for file in files:
            grouped[file.category].append(file)
        return grouped

    def _dedupe_findings(self, findings: list[Finding]) -> list[Finding]:
        seen = set()
        result = []
        for finding in findings:
            key = (finding.category, finding.description, tuple(finding.evidence))
            if finding.evidence and key not in seen:
                seen.add(key)
                result.append(finding)
        return result


def _paths(files: list[ChangedFileSignal]) -> list[str]:
    return _dedupe([file.path for file in files if file.path])


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
