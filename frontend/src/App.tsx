import { FormEvent, useState } from "react";
import {
  analyzeRepository,
  AnalyzeRepositoryResponse,
  generateOnboardingGuide,
  IncidentInvestigationResponse,
  investigateIncident,
  OnboardingGuideResponse,
  PullRequestReviewResponse,
  reviewPullRequest
} from "./api";

const sampleUrl = "https://github.com/tarunngusain08/AgentOps";
const samplePrNumber = "8";
const sampleScenarioId = "checkout-latency";
type Mode = "architecture" | "onboarding" | "review" | "incident";
type ResultState =
  | { mode: "architecture"; value: AnalyzeRepositoryResponse }
  | { mode: "onboarding"; value: OnboardingGuideResponse }
  | { mode: "review"; value: PullRequestReviewResponse }
  | { mode: "incident"; value: IncidentInvestigationResponse };

const modeLabels: Record<Mode, string> = {
  architecture: "Repository Architecture",
  onboarding: "Onboarding Guide",
  review: "PR Review",
  incident: "Incident RCA"
};

export default function App() {
  const [repositoryUrl, setRepositoryUrl] = useState(sampleUrl);
  const [pullRequestNumber, setPullRequestNumber] = useState(samplePrNumber);
  const [scenarioId, setScenarioId] = useState(sampleScenarioId);
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
      } else if (mode === "onboarding") {
        const response = await generateOnboardingGuide(repositoryUrl);
        setResult({ mode, value: response });
      } else if (mode === "review") {
        const parsedPullRequestNumber = Number.parseInt(pullRequestNumber, 10);
        if (!Number.isInteger(parsedPullRequestNumber) || parsedPullRequestNumber <= 0) {
          throw new Error("Pull request number must be a positive integer.");
        }
        const response = await reviewPullRequest(repositoryUrl, parsedPullRequestNumber);
        setResult({ mode, value: response });
      } else {
        if (scenarioId.trim().length === 0) {
          throw new Error("Scenario ID is required.");
        }
        const response = await investigateIncident(scenarioId.trim(), repositoryUrl.trim() || undefined);
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
            <p className="eyebrow">AgentOps M04</p>
            <h1>{modeLabels[mode]}</h1>
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
          <button
            className={mode === "review" ? "active" : ""}
            onClick={() => setMode("review")}
            type="button"
          >
            PR Review
          </button>
          <button
            className={mode === "incident" ? "active" : ""}
            onClick={() => setMode("incident")}
            type="button"
          >
            Incident RCA
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
            <button
              disabled={
                loading ||
                (mode !== "incident" && repositoryUrl.trim().length === 0) ||
                (mode === "review" && pullRequestNumber.trim().length === 0) ||
                (mode === "incident" && scenarioId.trim().length === 0)
              }
              type="submit"
            >
              {loading ? "Working" : actionLabel(mode)}
            </button>
          </div>
          {mode === "review" ? (
            <div className="pr-number-row">
              <label htmlFor="pull-request-number">Pull request number</label>
              <input
                id="pull-request-number"
                min="1"
                onChange={(event) => setPullRequestNumber(event.target.value)}
                placeholder={samplePrNumber}
                type="number"
                value={pullRequestNumber}
              />
            </div>
          ) : null}
          {mode === "incident" ? (
            <div className="pr-number-row">
              <label htmlFor="scenario-id">Incident scenario</label>
              <input
                id="scenario-id"
                onChange={(event) => setScenarioId(event.target.value)}
                placeholder={sampleScenarioId}
                value={scenarioId}
              />
            </div>
          ) : null}
        </form>

        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      {result?.mode === "architecture" ? <ReportView result={result.value} /> : null}
      {result?.mode === "onboarding" ? <GuideView result={result.value} /> : null}
      {result?.mode === "review" ? <PullRequestReviewView result={result.value} /> : null}
      {result?.mode === "incident" ? <IncidentRCAView result={result.value} /> : null}
      {!result ? <EmptyState mode={mode} /> : null}
    </main>
  );
}

function actionLabel(mode: Mode) {
  if (mode === "architecture") {
    return "Analyze";
  }
  if (mode === "onboarding") {
    return "Generate";
  }
  if (mode === "review") {
    return "Review";
  }
  return "Investigate";
}

function IncidentRCAView({ result }: { result: IncidentInvestigationResponse }) {
  const { rca, analysis_metadata } = result;
  const evidenceByType = groupIncidentEvidence(rca.evidence);

  return (
    <section className="report-grid">
      <article className="report-section report-wide">
        <div className="section-title">
          <h2>Investigation Overview</h2>
          <span>{rca.confidence} confidence</span>
        </div>
        <TraceableTextView value={rca.summary} />
        <TraceableTextView value={rca.impact} />
      </article>

      <article className="report-section report-wide">
        <h2>Timeline</h2>
        <div className="timeline-list">
          {rca.timeline.map((event) => (
            <div className="timeline-item" key={`${event.timestamp}-${event.type}-${event.description}`}>
              <time>{formatTimestamp(event.timestamp)}</time>
              <p>{event.description}</p>
              <EvidenceIds ids={event.evidence_ids} />
            </div>
          ))}
        </div>
      </article>

      <EvidenceGroup title="Metrics" items={evidenceByType.metric} />
      <EvidenceGroup title="Logs" items={evidenceByType.log} />
      <EvidenceGroup title="Deployment" items={evidenceByType.deployment} />
      <EvidenceGroup title="Code Changes" items={evidenceByType.change} />

      <article className="report-section report-wide">
        <h2>Repository Context</h2>
        {rca.repository_context.length > 0 ? (
          <div className="component-list">
            {rca.repository_context.map((signal) => (
              <div className="component-item" key={`${signal.component}-${signal.path}`}>
                <h3>{signal.component}</h3>
                <p>{signal.reason}</p>
                <div className="evidence-list">
                  <code>{signal.path}</code>
                  <code>{Math.round(signal.confidence * 100)}% confidence</code>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No repository context available.</p>
        )}
      </article>

      <article className="report-section report-wide">
        <div className="section-title">
          <h2>{rca.suspected_root_cause.title}</h2>
          <span>{rca.suspected_root_cause.category}</span>
        </div>
        <TraceableTextView value={rca.suspected_root_cause.explanation} />
      </article>

      <article className="report-section">
        <h2>Mitigation</h2>
        <TraceableTextView value={rca.mitigation} />
      </article>

      <article className="report-section">
        <h2>Prevention</h2>
        <TraceableTextView value={rca.prevention} />
      </article>

      <ListSection title="Assumptions" items={rca.assumptions} />

      <article className="report-section">
        <h2>Analysis Metadata</h2>
        <IncidentMetadataList metadata={analysis_metadata} />
      </article>
    </section>
  );
}

function EvidenceGroup({
  items,
  title
}: {
  items: IncidentInvestigationResponse["rca"]["evidence"];
  title: string;
}) {
  return (
    <article className="report-section">
      <h2>{title}</h2>
      {items.length > 0 ? (
        <div className="evidence-card-list">
          {items.map((item) => (
            <div className="evidence-card" key={item.id}>
              <div className="section-title">
                <h3>{item.id}</h3>
                <span>{formatTimestamp(item.timestamp)}</span>
              </div>
              <p>{item.description}</p>
              <code>{item.source}</code>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">None detected.</p>
      )}
    </article>
  );
}

function TraceableTextView({ value }: { value: { text: string; evidence_ids: string[] } }) {
  return (
    <div className="traceable-text">
      <p>{value.text}</p>
      <EvidenceIds ids={value.evidence_ids} />
    </div>
  );
}

function EvidenceIds({ ids }: { ids: string[] }) {
  return (
    <div className="evidence-list">
      {ids.map((id) => (
        <code key={id}>{id}</code>
      ))}
    </div>
  );
}

function IncidentMetadataList({ metadata }: { metadata: IncidentInvestigationResponse["analysis_metadata"] }) {
  return (
    <dl className="metadata-list">
      <div>
        <dt>Fixture</dt>
        <dd>{metadata.fixture_id}@{metadata.fixture_version}</dd>
      </div>
      <div>
        <dt>Repository</dt>
        <dd>{metadata.repository_analyzed ? "Analyzed" : "Skipped"}</dd>
      </div>
      <div>
        <dt>Evidence</dt>
        <dd>{metadata.evidence_count}</dd>
      </div>
      <div>
        <dt>Score</dt>
        <dd>{metadata.confidence_score}</dd>
      </div>
      <div>
        <dt>Duration</dt>
        <dd>{metadata.analysis_duration_ms}ms</dd>
      </div>
      <div>
        <dt>Mode</dt>
        <dd>{metadata.analysis_mode}</dd>
      </div>
    </dl>
  );
}

function PullRequestReviewView({ result }: { result: PullRequestReviewResponse }) {
  const { repository, pull_request, analysis_metadata, review } = result;
  const findingsByCategory = groupFindings(review.findings);
  const evidence = uniqueEvidence(review.findings);

  return (
    <section className="report-grid">
      <article className="report-section report-wide">
        <div className="section-title">
          <h2>
            PR #{pull_request.number}: {pull_request.title}
          </h2>
          <span>{review.confidence} confidence</span>
        </div>
        <p>{review.summary}</p>
        <div className="evidence-list">
          <code>
            {repository.owner}/{repository.name}
          </code>
          <code>
            {pull_request.head_branch || "head"} -&gt; {pull_request.base_branch || repository.default_branch}
          </code>
        </div>
      </article>

      <FindingSection title="Potential Risks" findings={findingsByCategory.potential_risk} />
      <FindingSection title="Breaking Changes" findings={findingsByCategory.breaking_change} />
      <FindingSection title="Files Requiring Attention" findings={findingsByCategory.file_attention} />
      <FindingSection title="Testing Concerns" findings={findingsByCategory.testing_concern} />
      <FindingSection title="Architecture Impact" findings={findingsByCategory.architecture_impact} />
      <ListSection title="Evidence" items={evidence} />
      <ListSection title="Assumptions" items={review.assumptions} />

      <article className="report-section">
        <h2>Analysis Metadata</h2>
        <PRMetadataList metadata={analysis_metadata} />
      </article>
    </section>
  );
}

function FindingSection({
  findings,
  title
}: {
  findings: PullRequestReviewResponse["review"]["findings"];
  title: string;
}) {
  return (
    <article className="report-section report-wide">
      <h2>{title}</h2>
      {findings.length > 0 ? (
        <div className="finding-list">
          {findings.map((finding) => (
            <div className="finding-item" key={`${finding.category}-${finding.description}`}>
              <div className="finding-title">
                <h3>{finding.description}</h3>
                <span className={`severity severity-${finding.severity.toLowerCase()}`}>
                  {finding.severity}
                </span>
              </div>
              <div className="evidence-list">
                {finding.evidence.map((evidence) => (
                  <code key={evidence}>{evidence}</code>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">None detected.</p>
      )}
    </article>
  );
}

function PRMetadataList({ metadata }: { metadata: PullRequestReviewResponse["analysis_metadata"] }) {
  return (
    <dl className="metadata-list">
      <div>
        <dt>Changed files</dt>
        <dd>{metadata.changed_files}</dd>
      </div>
      <div>
        <dt>Files inspected</dt>
        <dd>{metadata.files_inspected}</dd>
      </div>
      <div>
        <dt>Patch bytes</dt>
        <dd>{metadata.patch_bytes}</dd>
      </div>
      <div>
        <dt>High-signal files</dt>
        <dd>{metadata.high_signal_files}</dd>
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

function groupFindings(findings: PullRequestReviewResponse["review"]["findings"]) {
  return {
    potential_risk: findings.filter((finding) => finding.category === "potential_risk"),
    breaking_change: findings.filter((finding) => finding.category === "breaking_change"),
    file_attention: findings.filter((finding) => finding.category === "file_attention"),
    testing_concern: findings.filter((finding) => finding.category === "testing_concern"),
    architecture_impact: findings.filter((finding) => finding.category === "architecture_impact")
  };
}

function uniqueEvidence(findings: PullRequestReviewResponse["review"]["findings"]) {
  return Array.from(new Set(findings.flatMap((finding) => finding.evidence))).filter(Boolean);
}

function groupIncidentEvidence(evidence: IncidentInvestigationResponse["rca"]["evidence"]) {
  return {
    metric: evidence.filter((item) => item.type === "metric"),
    log: evidence.filter((item) => item.type === "log"),
    deployment: evidence.filter((item) => item.type === "deployment"),
    change: evidence.filter((item) => item.type === "change")
  };
}

function formatTimestamp(timestamp: string) {
  return timestamp.replace("2026-06-10T", "").replace(":00+00:00", " UTC");
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
        {mode === "architecture"
          ? "the architecture report."
          : mode === "onboarding"
            ? "a new-engineer onboarding guide."
            : mode === "review"
              ? "an evidence-backed pull request review."
              : "a deterministic incident RCA."}
      </p>
    </section>
  );
}
