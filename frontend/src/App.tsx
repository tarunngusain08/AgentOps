import { FormEvent, useState } from "react";
import {
  analyzeRepository,
  AnalyzeRepositoryResponse,
  generateOnboardingGuide,
  OnboardingGuideResponse
} from "./api";

const sampleUrl = "https://github.com/fastapi/fastapi";
type Mode = "architecture" | "onboarding";
type ResultState =
  | { mode: "architecture"; value: AnalyzeRepositoryResponse }
  | { mode: "onboarding"; value: OnboardingGuideResponse };

export default function App() {
  const [repositoryUrl, setRepositoryUrl] = useState(sampleUrl);
  const [mode, setMode] = useState<Mode>("architecture");
  const [result, setResult] = useState<ResultState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      if (mode === "architecture") {
        const response = await analyzeRepository(repositoryUrl);
        setResult({ mode, value: response });
      } else {
        const response = await generateOnboardingGuide(repositoryUrl);
        setResult({ mode, value: response });
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="analysis-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">AgentOps M02</p>
            <h1>{mode === "architecture" ? "Repository Architecture" : "Onboarding Guide"}</h1>
          </div>
          <span className="mode-pill">Heuristic</span>
        </div>

        <div className="mode-toggle" role="group" aria-label="Output mode">
          <button
            className={mode === "architecture" ? "active" : ""}
            onClick={() => setMode("architecture")}
            type="button"
          >
            Architecture Report
          </button>
          <button
            className={mode === "onboarding" ? "active" : ""}
            onClick={() => setMode("onboarding")}
            type="button"
          >
            Onboarding Guide
          </button>
        </div>

        <form className="repo-form" onSubmit={handleSubmit}>
          <label htmlFor="repository-url">GitHub repository URL</label>
          <div className="input-row">
            <input
              id="repository-url"
              value={repositoryUrl}
              onChange={(event) => setRepositoryUrl(event.target.value)}
              placeholder={sampleUrl}
            />
            <button disabled={loading || repositoryUrl.trim().length === 0} type="submit">
              {loading ? "Working" : mode === "architecture" ? "Analyze" : "Generate"}
            </button>
          </div>
        </form>

        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      {result?.mode === "architecture" ? <ReportView result={result.value} /> : null}
      {result?.mode === "onboarding" ? <GuideView result={result.value} /> : null}
      {!result ? <EmptyState mode={mode} /> : null}
    </main>
  );
}

function GuideView({ result }: { result: OnboardingGuideResponse }) {
  const { repository, analysis_metadata, guide } = result;

  return (
    <section className="report-grid">
      <article className="report-section report-wide">
        <div className="section-title">
          <h2>{guide.title}</h2>
          <span>{repository.default_branch}</span>
        </div>
        <p>
          {repository.owner}/{repository.name}
        </p>
      </article>

      {guide.sections.map((section) => (
        <article
          className={section.title === "Project Overview" || section.title === "Key Components" ? "report-section report-wide" : "report-section"}
          key={section.title}
        >
          <h2>{section.title}</h2>
          <div className="guide-item-list">
            {section.items.map((item) => (
              <div className="guide-item" key={`${section.title}-${item.text}`}>
                <p>{item.text}</p>
                {item.evidence.length > 0 ? (
                  <div className="evidence-list">
                    {item.evidence.map((evidence) => (
                      <code key={evidence}>{evidence}</code>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </article>
      ))}

      <ListSection title="Guide Evidence" items={guide.evidence} />

      <article className="report-section">
        <h2>Analysis Metadata</h2>
        <MetadataList metadata={analysis_metadata} />
      </article>
    </section>
  );
}

function ReportView({ result }: { result: AnalyzeRepositoryResponse }) {
  const { report, repository, analysis_metadata } = result;

  return (
    <section className="report-grid">
      <article className="report-section report-wide">
        <div className="section-title">
          <h2>{repository.owner}/{repository.name}</h2>
          <span>{repository.default_branch}</span>
        </div>
        <p>{report.overview}</p>
      </article>

      <ListSection title="Technology Stack" items={report.technology_stack} />
      <ListSection title="Entry Points" items={report.entry_points} />

      <article className="report-section report-wide">
        <h2>Components</h2>
        <div className="component-list">
          {report.components.map((component) => (
            <div className="component-item" key={component.name}>
              <h3>{component.name}</h3>
              <p>{component.responsibility}</p>
              <div className="evidence-list">
                {component.evidence.map((item) => (
                  <code key={item}>{item}</code>
                ))}
              </div>
            </div>
          ))}
        </div>
      </article>

      <ListSection title="Important Files" items={report.important_files} />
      <ListSection title="Relationships" items={report.relationships} />
      <ListSection title="Assumptions" items={report.assumptions} />

      <article className="report-section">
        <h2>Analysis Metadata</h2>
        <MetadataList metadata={analysis_metadata} />
      </article>
    </section>
  );
}

function MetadataList({
  metadata
}: {
  metadata: AnalyzeRepositoryResponse["analysis_metadata"] | OnboardingGuideResponse["analysis_metadata"];
}) {
  return (
    <dl className="metadata-list">
      <div>
        <dt>Files inspected</dt>
        <dd>{metadata.files_inspected}</dd>
      </div>
      <div>
        <dt>Directories inspected</dt>
        <dd>{metadata.directories_inspected}</dd>
      </div>
      <div>
        <dt>Mode</dt>
        <dd>{metadata.analysis_mode}</dd>
      </div>
      <div>
        <dt>Truncated</dt>
        <dd>{metadata.truncated ? "Yes" : "No"}</dd>
      </div>
    </dl>
  );
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="report-section">
      <h2>{title}</h2>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">None detected.</p>
      )}
    </article>
  );
}

function EmptyState({ mode }: { mode: Mode }) {
  return (
    <section className="empty-state">
      <h2>Ready</h2>
      <p>
        Submit a public GitHub repository to generate{" "}
        {mode === "architecture" ? "the architecture report." : "a new-engineer onboarding guide."}
      </p>
    </section>
  );
}
