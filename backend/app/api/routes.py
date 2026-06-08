from fastapi import APIRouter, HTTPException

from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.github.service import GitHubError, GitHubService
from app.reporting.report_generator import ReportGenerator
from app.schemas import AnalyzeRepositoryRequest, AnalyzeRepositoryResponse

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
