from app.analyzer.repository_analyzer import RepositoryAnalysis
from app.github.service import RepositorySnapshot
from app.schemas import (
    AnalysisMetadata,
    AnalyzeRepositoryResponse,
    ArchitectureReport,
    Component,
    RepositoryInfo,
)


class ReportGenerator:
    def generate(
        self,
        snapshot: RepositorySnapshot,
        analysis: RepositoryAnalysis,
    ) -> AnalyzeRepositoryResponse:
        return AnalyzeRepositoryResponse(
            repository=RepositoryInfo(
                owner=snapshot.owner,
                name=snapshot.name,
                default_branch=snapshot.default_branch,
                html_url=snapshot.html_url,
            ),
            analysis_metadata=AnalysisMetadata(
                files_inspected=len(snapshot.files),
                directories_inspected=len(snapshot.top_level_directories),
                analysis_mode="heuristic",
                truncated=snapshot.truncated,
            ),
            report=ArchitectureReport(
                overview=analysis.overview,
                technology_stack=analysis.technology_stack,
                components=[
                    Component(
                        name=component.name,
                        responsibility=component.responsibility,
                        evidence=component.evidence,
                    )
                    for component in analysis.components
                ],
                entry_points=analysis.entry_points,
                important_files=analysis.important_files,
                relationships=analysis.relationships,
                assumptions=analysis.assumptions,
            ),
        )
