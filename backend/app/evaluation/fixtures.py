from __future__ import annotations

from app.github.pull_request_loader import PullRequestFile, PullRequestSnapshot
from app.github.service import GitHubFile, RepositorySnapshot


def repository_fixture(fixture_id: str = "repository-basic@v1") -> RepositorySnapshot:
    if fixture_id == "python_app@v1":
        return _python_app_fixture()
    if fixture_id == "go_service@v1":
        return _go_service_fixture(moved=False)
    if fixture_id == "go_service_moved@v1":
        return _go_service_fixture(moved=True)
    if fixture_id == "ts_frontend@v1":
        return _ts_frontend_fixture()
    return RepositorySnapshot(
        owner="example",
        name="service",
        default_branch="main",
        html_url="https://github.com/example/service",
        description="Fixture service for deterministic evaluation",
        primary_language="Python",
        topics=[],
        tree_paths=[
            "pyproject.toml",
            "app/main.py",
            "app/services/checkout.py",
            "tests/test_checkout.py",
        ],
        top_level_directories=["app", "tests"],
        selected_paths=["pyproject.toml", "app/main.py", "app/services/checkout.py", "tests/test_checkout.py"],
        files=[
            GitHubFile("pyproject.toml", 'dependencies = ["fastapi", "pydantic"]', 40, "manifest"),
            GitHubFile("app/main.py", "from fastapi import FastAPI\napp = FastAPI()", 42, "entry_point"),
            GitHubFile(
                "app/services/checkout.py",
                "from app.db import pool\n\nclass CheckoutService:\n    async def process_checkout(self):\n        return await pool.acquire()\n",
                108,
                "source_code",
            ),
            GitHubFile(
                "tests/test_checkout.py",
                "from app.services.checkout import CheckoutService\n\nasync def test_process_checkout():\n    assert CheckoutService\n",
                102,
                "test_code",
            ),
        ],
        truncated=False,
    )


def pull_request_fixture(fixture_id: str = "pull-request-basic@v1") -> PullRequestSnapshot:
    if fixture_id == "go_pr_static@v1":
        return PullRequestSnapshot(
            owner="example",
            repo="billing",
            number=12,
            title="Tune invoice creation path",
            state="open",
            html_url="https://github.com/example/billing/pull/12",
            base_branch="main",
            head_branch="feature/invoice-path",
            author="developer",
            changed_files=1,
            files=[
                PullRequestFile(
                    filename="billing/service.go",
                    status="modified",
                    additions=12,
                    deletions=3,
                    changes=15,
                    patch="@@ func (s *BillingService) CreateInvoice(ctx context.Context) error",
                ),
            ],
            truncated=False,
        )
    return PullRequestSnapshot(
        owner="example",
        repo="service",
        number=8,
        title="Update FastAPI dependency and app entry point",
        state="open",
        html_url="https://github.com/example/service/pull/8",
        base_branch="main",
        head_branch="feature/update-fastapi",
        author="developer",
        changed_files=2,
        files=[
            PullRequestFile(
                filename="pyproject.toml",
                status="modified",
                additions=2,
                deletions=1,
                changes=3,
                patch="@@ fastapi dependency",
            ),
            PullRequestFile(
                filename="app/main.py",
                status="modified",
                additions=8,
                deletions=2,
                changes=10,
                patch="@@ app entry point",
            ),
        ],
        truncated=False,
    )


def _python_app_fixture() -> RepositorySnapshot:
    return RepositorySnapshot(
        owner="example",
        name="python-app",
        default_branch="main",
        html_url="https://github.com/example/python-app",
        description="FastAPI checkout service fixture",
        primary_language="Python",
        topics=["fastapi"],
        tree_paths=[
            "pyproject.toml",
            "app/main.py",
            "app/services/checkout.py",
            "tests/test_checkout.py",
        ],
        top_level_directories=["app", "tests"],
        selected_paths=["pyproject.toml", "app/main.py", "app/services/checkout.py", "tests/test_checkout.py"],
        files=[
            GitHubFile("pyproject.toml", 'dependencies = ["fastapi", "pydantic"]', 40, "manifest"),
            GitHubFile("app/main.py", "from fastapi import FastAPI\nfrom app.services.checkout import CheckoutService\napp = FastAPI()\n", 89, "entry_point"),
            GitHubFile(
                "app/services/checkout.py",
                "from app.db.pool import ConnectionPool\n\nclass CheckoutService:\n    async def process_checkout(self):\n        return await ConnectionPool().acquire()\n",
                142,
                "source_code",
            ),
            GitHubFile(
                "tests/test_checkout.py",
                "from app.services.checkout import CheckoutService\n\nasync def test_process_checkout():\n    assert CheckoutService\n",
                102,
                "test_code",
            ),
        ],
        truncated=False,
    )


def _go_service_fixture(moved: bool) -> RepositorySnapshot:
    source_path = "billing/invoice_service.go" if moved else "billing/service.go"
    test_path = "billing/invoice_service_test.go" if moved else "billing/service_test.go"
    return RepositorySnapshot(
        owner="example",
        name="billing",
        default_branch="main",
        html_url="https://github.com/example/billing",
        description="Go billing service fixture",
        primary_language="Go",
        topics=["go"],
        tree_paths=[
            "go.mod",
            "cmd/billing/main.go",
            source_path,
            test_path,
        ],
        top_level_directories=["billing", "cmd"],
        selected_paths=["go.mod", "cmd/billing/main.go", source_path, test_path],
        files=[
            GitHubFile("go.mod", "module example.com/billing\n\ngo 1.23\n", 36, "manifest"),
            GitHubFile("cmd/billing/main.go", 'package main\n\nimport "example.com/billing/billing"\n\nfunc main() {\n    billing.NewBillingService()\n}\n', 102, "entry_point"),
            GitHubFile(
                source_path,
                'package billing\n\nimport "context"\n\ntype BillingService struct {}\n\nfunc NewBillingService() *BillingService {\n    return &BillingService{}\n}\n\nfunc (s *BillingService) CreateInvoice(ctx context.Context) error {\n    return nil\n}\n',
                218,
                "source_code",
            ),
            GitHubFile(
                test_path,
                'package billing\n\nimport "testing"\n\nfunc TestCreateInvoice(t *testing.T) {\n    service := NewBillingService()\n    if service == nil { t.Fatal("missing service") }\n}\n',
                160,
                "test_code",
            ),
        ],
        truncated=False,
    )


def _ts_frontend_fixture() -> RepositorySnapshot:
    return RepositorySnapshot(
        owner="example",
        name="ts-frontend",
        default_branch="main",
        html_url="https://github.com/example/ts-frontend",
        description="React checkout frontend fixture",
        primary_language="TypeScript",
        topics=["react"],
        tree_paths=[
            "package.json",
            "src/main.tsx",
            "src/components/CheckoutButton.tsx",
            "src/components/CheckoutButton.test.tsx",
        ],
        top_level_directories=["src"],
        selected_paths=["package.json", "src/main.tsx", "src/components/CheckoutButton.tsx", "src/components/CheckoutButton.test.tsx"],
        files=[
            GitHubFile("package.json", '{"scripts":{"dev":"vite","test":"vitest"},"dependencies":{"@vitejs/plugin-react":"latest","react":"latest","typescript":"latest"}}', 132, "manifest"),
            GitHubFile("src/main.tsx", 'import React from "react";\nimport { createRoot } from "react-dom/client";\nimport { CheckoutButton } from "./components/CheckoutButton";\ncreateRoot(document.getElementById("root")!).render(<CheckoutButton />);\n', 203, "entry_point"),
            GitHubFile(
                "src/components/CheckoutButton.tsx",
                'import React from "react";\n\nexport function CheckoutButton() {\n  return <button>Checkout</button>;\n}\n',
                98,
                "source_code",
            ),
            GitHubFile(
                "src/components/CheckoutButton.test.tsx",
                'import { CheckoutButton } from "./CheckoutButton";\n\ntest("renders checkout", () => {\n  expect(CheckoutButton).toBeDefined();\n});\n',
                121,
                "test_code",
            ),
        ],
        truncated=False,
    )
