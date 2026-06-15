from __future__ import annotations

from datetime import UTC, datetime

from app.evaluation.models import EXECUTION_TRACE_SCHEMA_VERSION, ExecutionTrace, TaskResult, TraceSpan

ALLOWED_SPAN_NAMES = {
    "task_start",
    "fixture_load",
    "workflow_execute",
    "scoring",
    "result_persist",
}
MAX_METADATA_VALUE_BYTES = 4096


class ExecutionTraceBuilder:
    def build(self, run_id: str, task: TaskResult) -> ExecutionTrace:
        trace_id = self.trace_id(run_id, task.id)
        spans = [
            self._span("span-001", "task_start", 0, {"task_id": task.id}),
            self._span("span-002", "fixture_load", 1, {"fixture_id": task.fixture_id}),
            self._span("span-003", "workflow_execute", 2, {"workflow": task.workflow}),
            self._span("span-004", "scoring", 3, {"score": task.score, "passed": task.passed}),
            self._span("span-005", "result_persist", 4, {"run_id": run_id}),
        ]
        return ExecutionTrace(
            schema_version=EXECUTION_TRACE_SCHEMA_VERSION,
            trace_id=trace_id,
            run_id=run_id,
            task_id=task.id,
            started_at=datetime.now(UTC).isoformat(),
            duration_ms=0,
            spans=sorted(spans, key=lambda span: (span.start_ms, span.id)),
        )

    @staticmethod
    def trace_id(run_id: str, task_id: str) -> str:
        return f"trace-{run_id}-{task_id}"

    def _span(
        self,
        span_id: str,
        name: str,
        start_ms: int,
        metadata: dict[str, str | int | float | bool | None],
    ) -> TraceSpan:
        if name not in ALLOWED_SPAN_NAMES:
            raise ValueError(f"Unsupported span name: {name}")
        validate_trace_metadata(metadata)
        return TraceSpan(
            id=span_id,
            name=name,
            start_ms=start_ms,
            duration_ms=0,
            status="ok",
            metadata=metadata,
        )


def validate_trace_metadata(metadata: dict[str, object]) -> None:
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ValueError("Trace metadata keys must be strings.")
        if value is not None and not isinstance(value, str | int | float | bool):
            raise ValueError(f"Trace metadata value is not primitive: {key}")
        if isinstance(value, str) and len(value.encode("utf-8")) > MAX_METADATA_VALUE_BYTES:
            raise ValueError(f"Trace metadata value exceeds 4 KB: {key}")
