from __future__ import annotations

import os
import subprocess

from app.evaluation.errors import ImplementationVersionError


class ImplementationVersionResolver:
    def resolve(self) -> str:
        github_sha = os.getenv("GITHUB_SHA")
        if github_sha:
            return github_sha

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception:
            result = None
        if result and result.stdout.strip():
            return result.stdout.strip()

        app_version = os.getenv("APP_VERSION")
        if app_version:
            return app_version

        raise ImplementationVersionError("Unable to resolve implementation version.")

