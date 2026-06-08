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
