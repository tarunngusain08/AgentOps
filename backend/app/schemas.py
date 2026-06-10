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


class GuideItem(BaseModel):
    text: str
    evidence: list[str]


class GuideSection(BaseModel):
    title: str
    items: list[GuideItem]


class Guide(BaseModel):
    title: str
    sections: list[GuideSection]
    evidence: list[str]
    assumptions: list[str]


class OnboardingGuideResponse(BaseModel):
    repository: RepositoryInfo
    analysis_metadata: AnalysisMetadata
    guide: Guide


class PullRequestReviewRequest(BaseModel):
    repository_url: str = Field(..., min_length=1)
    pull_request_number: int = Field(..., gt=0)


class PullRequestInfo(BaseModel):
    number: int
    title: str
    state: str
    html_url: str | None = None
    base_branch: str
    head_branch: str
    author: str | None = None


class PRReviewAnalysisMetadata(BaseModel):
    changed_files: int
    files_inspected: int
    patch_bytes: int
    high_signal_files: int
    analysis_mode: str = "heuristic"
    truncated: bool


class ReviewFinding(BaseModel):
    category: str
    severity: str
    description: str
    evidence: list[str]


class PullRequestReview(BaseModel):
    summary: str
    findings: list[ReviewFinding]
    assumptions: list[str]
    confidence: str
    metadata: dict[str, int | str | bool]


class PullRequestReviewResponse(BaseModel):
    repository: RepositoryInfo
    pull_request: PullRequestInfo
    analysis_metadata: PRReviewAnalysisMetadata
    review: PullRequestReview
