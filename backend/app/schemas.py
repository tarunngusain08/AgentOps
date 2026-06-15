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


class IncidentInvestigationRequest(BaseModel):
    scenario_id: str = Field(..., min_length=1)
    repository_url: str | None = None


class TraceableTextModel(BaseModel):
    text: str
    evidence_ids: list[str]


class EvidenceItemModel(BaseModel):
    id: str
    type: str
    source: str
    timestamp: str
    description: str


class RepositorySignalModel(BaseModel):
    component: str
    path: str
    reason: str
    confidence: float


class TimelineEventModel(BaseModel):
    timestamp: str
    type: str
    description: str
    evidence_ids: list[str]


class RootCauseModel(BaseModel):
    category: str
    title: str
    explanation: TraceableTextModel
    evidence_ids: list[str]


class IncidentAnalysisMetadata(BaseModel):
    fixture_id: str
    fixture_version: str
    repository_analyzed: bool
    repository_components_matched: list[str]
    evidence_count: int
    analysis_duration_ms: int
    confidence_score: int
    analysis_mode: str = "heuristic"
    truncated: bool


class IncidentRCA(BaseModel):
    summary: TraceableTextModel
    impact: TraceableTextModel
    timeline: list[TimelineEventModel]
    evidence: list[EvidenceItemModel]
    repository_context: list[RepositorySignalModel]
    suspected_root_cause: RootCauseModel
    mitigation: TraceableTextModel
    prevention: TraceableTextModel
    assumptions: list[str]
    confidence: str
    metadata: IncidentAnalysisMetadata


class IncidentInvestigationResponse(BaseModel):
    scenario_id: str
    analysis_metadata: IncidentAnalysisMetadata
    rca: IncidentRCA


class EvaluationRunRequest(BaseModel):
    suite_id: str = Field(default="mvp-demo-suite@v1", min_length=1)
    version_label: str = Field(default="local-dev", min_length=1)


class EvaluationCompareRequest(BaseModel):
    suite_id: str = Field(default="mvp-demo-suite", min_length=1)
    suite_version: str = Field(default="v1", min_length=1)
    baseline_run_id: str = Field(..., min_length=1)
    candidate_run_id: str = Field(..., min_length=1)


class EvaluationSuitesResponse(BaseModel):
    suites: list[dict[str, str | int | list[str]]]
