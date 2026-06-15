from __future__ import annotations


class EvaluationError(Exception):
    code = "EVALUATION_ERROR"
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class EvaluationSuiteNotFoundError(EvaluationError):
    code = "EVAL_SUITE_NOT_FOUND"
    status_code = 404


class EvaluationSuiteValidationError(EvaluationError):
    code = "EVAL_SUITE_VALIDATION_ERROR"
    status_code = 500


class EvaluationRunNotFoundError(EvaluationError):
    code = "EVAL_RUN_NOT_FOUND"
    status_code = 404


class EvaluationRunReadError(EvaluationError):
    code = "EVAL_RUN_READ_ERROR"
    status_code = 500


class ImplementationVersionError(EvaluationError):
    code = "IMPLEMENTATION_VERSION_ERROR"
    status_code = 500


class StateFileInvalidError(EvaluationError):
    code = "STATE_FILE_INVALID"
    status_code = 500

