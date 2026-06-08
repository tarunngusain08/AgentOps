import { FormEvent, useState } from "react";
import { analyzeRepository, AnalyzeRepositoryResponse } from "./api";

const sampleUrl = "https://github.com/fastapi/fastapi";

export default function App() {
  const [repositoryUrl, setRepositoryUrl] = useState(sampleUrl);
  const [result, setResult] = useState<AnalyzeRepositoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await analyzeRepository(repositoryUrl);
      setResult(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Repository analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="analysis-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">AgentOps M01</p>
            <h1>Repository Architecture</h1>
          </div>
          <span className="mode-pill">Heuristic</span>
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
              {loading ? "Analyzing" : "Analyze"}
            </button>
          </div>
        </form>

        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      {result ? <ReportView result={result} /> : <EmptyState />}
    </main>
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
        <dl className="metadata-list">
          <div>
            <dt>Files inspected</dt>
            <dd>{analysis_metadata.files_inspected}</dd>
          </div>
          <div>
            <dt>Directories inspected</dt>
            <dd>{analysis_metadata.directories_inspected}</dd>
          </div>
          <div>
            <dt>Mode</dt>
            <dd>{analysis_metadata.analysis_mode}</dd>
          </div>
          <div>
            <dt>Truncated</dt>
            <dd>{analysis_metadata.truncated ? "Yes" : "No"}</dd>
          </div>
        </dl>
      </article>
    </section>
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

function EmptyState() {
  return (
    <section className="empty-state">
      <h2>Ready</h2>
      <p>Submit a public GitHub repository to generate the M01 architecture report.</p>
    </section>
  );
}
