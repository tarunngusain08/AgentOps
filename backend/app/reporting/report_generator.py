from app.analyzer.repository_analyzer import RepositoryAnalysis
from app.analyzer.repository_index import (
    RepositoryIndex,
    RepositoryIndexMetadata,
    RepositoryImport,
    RepositorySymbol,
    RepositoryTestLink,
    directory_group_summaries,
)
from app.github.service import RepositorySnapshot
from app.schemas import (
    AnalysisMetadata,
    AnalyzeRepositoryResponse,
    ArchitectureReport,
    CodeIntelligence,
    CodeIntelligenceMetadata,
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
                code_intelligence=self._code_intelligence(analysis.repository_index),
            ),
        )

    def _code_intelligence(self, index: RepositoryIndex) -> CodeIntelligence:
        assumptions = []
        if not index.files:
            assumptions.append("No supported Python, TypeScript/JavaScript, or Go source files were indexed.")
        if index.metadata.truncated:
            assumptions.append(f"Repository index was truncated because of {index.metadata.truncation_reason}.")
        if index.files and not index.symbols:
            assumptions.append("Source files were indexed, but shallow symbol extraction found no public symbols.")

        return CodeIntelligence(
            languages=sorted({file.language for file in index.files}),
            top_symbols=[self._format_symbol(symbol) for symbol in self._top_symbols(index.symbols)],
            important_imports=[self._format_import(item) for item in self._top_imports(index.imports)],
            test_links=[self._format_test_link(link) for link in index.tests[:8]],
            directory_groups=directory_group_summaries(index),
            assumptions=assumptions,
            metadata=self._metadata(index.metadata),
        )

    def _top_symbols(self, symbols: list[RepositorySymbol]) -> list[RepositorySymbol]:
        priority = {
            "package": 0,
            "class": 1,
            "type": 1,
            "function": 2,
            "method": 2,
            "constant": 3,
            "test_function": 4,
        }
        return sorted(symbols, key=lambda item: (priority.get(item.kind, 99), item.path, item.container or "", item.name))[:12]

    def _top_imports(self, imports: list[RepositoryImport]) -> list[RepositoryImport]:
        important = [
            item
            for item in imports
            if not item.module.startswith(".") or item.module in {".", ".."}
        ]
        return sorted(important or imports, key=lambda item: (item.path, item.module))[:12]

    def _format_symbol(self, symbol: RepositorySymbol) -> str:
        name = f"{symbol.container}.{symbol.name}" if symbol.container else symbol.name
        return f"{name} ({symbol.kind}) in {symbol.path}"

    def _format_import(self, item: RepositoryImport) -> str:
        return f"{item.module} imported by {item.path}"

    def _format_test_link(self, link: RepositoryTestLink) -> str:
        return f"{link.test_path} -> {link.source_path} ({link.reason})"

    def _metadata(self, metadata: RepositoryIndexMetadata) -> CodeIntelligenceMetadata:
        return CodeIntelligenceMetadata(
            files_indexed=metadata.files_indexed,
            symbols_found=metadata.symbols_found,
            imports_found=metadata.imports_found,
            tests_found=metadata.tests_found,
            truncated=metadata.truncated,
            truncation_reason=metadata.truncation_reason,
        )
