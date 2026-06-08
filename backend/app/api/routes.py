from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.documentation.documentation_generator import DocumentationGenerator
from app.github.service import GitHubError, GitHubService
from app.reporting.report_generator import ReportGenerator
from app.schemas import AnalyzeRepositoryRequest, AnalyzeRepositoryResponse, OnboardingGuideResponse

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
