from pydantic import BaseModel, Field


class AnalyzeRepositoryRequest(BaseModel):
    repository_url: str = Field(..., min_length=1)


class RepositoryInfo(BaseModel):
    owner: str
    name: str
    default_branch: str
    html_url: str | None = None


class AnalysisMetadata(BaseModel):
    files_inspected: int
    directories_inspected: int
    analysis_mode: str = "heuristic"
    truncated: bool


class Component(BaseModel):
    name: str
    responsibility: str
    evidence: list[str]


class ArchitectureReport(BaseModel):
    overview: str
    technology_stack: list[str]
    components: list[Component]
    entry_points: list[str]
    important_files: list[str]
    relationships: list[str]
    assumptions: list[str]


class AnalyzeRepositoryResponse(BaseModel):
    repository: RepositoryInfo
    analysis_metadata: AnalysisMetadata
    report: ArchitectureReport
