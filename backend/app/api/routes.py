from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.documentation.documentation_generator import DocumentationGenerator
from app.github.pull_request_loader import PullRequestLoader
from app.github.service import GitHubError, GitHubService
from app.reporting.report_generator import ReportGenerator
from app.review.diff_analyzer import DiffAnalyzer
from app.review.pr_review_generator import PRReviewGenerator
from app.schemas import (
    AnalyzeRepositoryRequest,
    AnalyzeRepositoryResponse,
    OnboardingGuideResponse,
    PRReviewAnalysisMetadata,
    PullRequestInfo,
    PullRequestReviewRequest,
    PullRequestReviewResponse,
)

router = APIRouter()


@router.post("/repositories/analyze", response_model=AnalyzeRepositoryResponse)
def analyze_repository(request: AnalyzeRepositoryRequest) -> AnalyzeRepositoryResponse:
    service = GitHubService()
    analyzer = RepositoryAnalyzer()
    generator = ReportGenerator()

    try:
        snapshot = service.load_repository(request.repository_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    analysis = analyzer.analyze(snapshot)
    return generator.generate(snapshot, analysis)


@router.post("/repositories/guides/onboarding", response_model=OnboardingGuideResponse)
def generate_onboarding_guide(request: AnalyzeRepositoryRequest) -> OnboardingGuideResponse:
    service = GitHubService()
    analyzer = RepositoryAnalyzer()
    report_generator = ReportGenerator()
    documentation_generator = DocumentationGenerator()

    try:
        snapshot = service.load_repository(request.repository_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    analysis = analyzer.analyze(snapshot)
    analysis_response = report_generator.generate(snapshot, analysis)
    guide = documentation_generator.generate_onboarding_guide(
        snapshot=snapshot,
        analysis=analysis,
        report=analysis_response.report,
    )
    return OnboardingGuideResponse(
        repository=analysis_response.repository,
        analysis_metadata=analysis_response.analysis_metadata,
        guide=asdict(guide),
    )


@router.post("/repositories/pull-requests/review", response_model=PullRequestReviewResponse)
def review_pull_request(request: PullRequestReviewRequest) -> PullRequestReviewResponse:
    service = GitHubService()
    pull_request_loader = PullRequestLoader(service=service)
    analyzer = RepositoryAnalyzer()
    report_generator = ReportGenerator()
    diff_analyzer = DiffAnalyzer()
    review_generator = PRReviewGenerator()

    try:
        snapshot = service.load_repository(request.repository_url)
        pull_request = pull_request_loader.load(
            request.repository_url,
            request.pull_request_number,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    analysis = analyzer.analyze(snapshot)
    analysis_response = report_generator.generate(snapshot, analysis)
    diff = diff_analyzer.analyze(
        pull_request.files,
        upstream_truncated=pull_request.truncated,
    )
    review = review_generator.generate(
        snapshot=snapshot,
        analysis=analysis,
        report=analysis_response.report,
        pull_request=pull_request,
        diff=diff,
    )

    return PullRequestReviewResponse(
        repository=analysis_response.repository,
        pull_request=PullRequestInfo(
            number=pull_request.number,
            title=pull_request.title,
            state=pull_request.state,
            html_url=pull_request.html_url,
            base_branch=pull_request.base_branch,
            head_branch=pull_request.head_branch,
            author=pull_request.author,
        ),
        analysis_metadata=PRReviewAnalysisMetadata(
            changed_files=int(review.metadata["changed_files"]),
            files_inspected=int(review.metadata["files_inspected"]),
            patch_bytes=int(review.metadata["patch_bytes"]),
            high_signal_files=int(review.metadata["high_signal_files"]),
            analysis_mode=str(review.metadata["analysis_mode"]),
            truncated=bool(review.metadata["truncated"]),
        ),
        review=asdict(review),
    )
