export interface AnalyzeRepositoryResponse {
  repository: {
    owner: string;
    name: string;
    default_branch: string;
    html_url?: string | null;
  };
  analysis_metadata: {
    files_inspected: number;
    directories_inspected: number;
    analysis_mode: string;
    truncated: boolean;
  };
  report: {
    overview: string;
    technology_stack: string[];
    components: Array<{
      name: string;
      responsibility: string;
      evidence: string[];
    }>;
    entry_points: string[];
    important_files: string[];
    relationships: string[];
    assumptions: string[];
  };
}

export interface OnboardingGuideResponse {
  repository: {
    owner: string;
    name: string;
    default_branch: string;
    html_url?: string | null;
  };
  analysis_metadata: {
    files_inspected: number;
    directories_inspected: number;
    analysis_mode: string;
    truncated: boolean;
  };
  guide: {
    title: string;
    sections: Array<{
      title: string;
      items: Array<{
        text: string;
        evidence: string[];
      }>;
    }>;
    evidence: string[];
    assumptions: string[];
  };
}

export interface PullRequestReviewResponse {
  repository: {
    owner: string;
    name: string;
    default_branch: string;
    html_url?: string | null;
  };
  pull_request: {
    number: number;
    title: string;
    state: string;
    html_url?: string | null;
    base_branch: string;
    head_branch: string;
    author?: string | null;
  };
  analysis_metadata: {
    changed_files: number;
    files_inspected: number;
    patch_bytes: number;
    high_signal_files: number;
    analysis_mode: string;
    truncated: boolean;
  };
  review: {
    summary: string;
    findings: Array<{
      category: string;
      severity: string;
      description: string;
      evidence: string[];
    }>;
    assumptions: string[];
    confidence: string;
    metadata: Record<string, string | number | boolean>;
  };
}

export interface IncidentInvestigationResponse {
  scenario_id: string;
  analysis_metadata: {
    fixture_id: string;
    fixture_version: string;
    repository_analyzed: boolean;
    repository_components_matched: string[];
    evidence_count: number;
    analysis_duration_ms: number;
    confidence_score: number;
    analysis_mode: string;
    truncated: boolean;
  };
  rca: {
    summary: TraceableText;
    impact: TraceableText;
    timeline: Array<{
      timestamp: string;
      type: string;
      description: string;
      evidence_ids: string[];
    }>;
    evidence: EvidenceItem[];
    repository_context: Array<{
      component: string;
      path: string;
      reason: string;
      confidence: number;
    }>;
    suspected_root_cause: {
      category: string;
      title: string;
      explanation: TraceableText;
      evidence_ids: string[];
    };
    mitigation: TraceableText;
    prevention: TraceableText;
    assumptions: string[];
    confidence: string;
    metadata: IncidentInvestigationResponse["analysis_metadata"];
  };
}

interface TraceableText {
  text: string;
  evidence_ids: string[];
}

interface EvidenceItem {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  description: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function analyzeRepository(repositoryUrl: string): Promise<AnalyzeRepositoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/repositories/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ repository_url: repositoryUrl })
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => undefined);
    const message = errorBody?.detail ?? "Repository analysis failed.";
    throw new Error(message);
  }

  return response.json();
}

export async function generateOnboardingGuide(repositoryUrl: string): Promise<OnboardingGuideResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/repositories/guides/onboarding`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ repository_url: repositoryUrl })
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => undefined);
    const message = errorBody?.detail ?? "Onboarding guide generation failed.";
    throw new Error(message);
  }

  return response.json();
}

export async function reviewPullRequest(
  repositoryUrl: string,
  pullRequestNumber: number
): Promise<PullRequestReviewResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/repositories/pull-requests/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      repository_url: repositoryUrl,
      pull_request_number: pullRequestNumber
    })
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => undefined);
    const message = errorBody?.detail ?? "Pull request review failed.";
    throw new Error(message);
  }

  return response.json();
}

export async function investigateIncident(
  scenarioId: string,
  repositoryUrl?: string
): Promise<IncidentInvestigationResponse> {
  const body: { scenario_id: string; repository_url?: string } = {
    scenario_id: scenarioId
  };
  if (repositoryUrl) {
    body.repository_url = repositoryUrl;
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/incidents/investigate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => undefined);
    const detail = errorBody?.detail;
    const message = typeof detail === "object" ? detail.message : detail;
    throw new Error(message ?? "Incident investigation failed.");
  }

  return response.json();
}
