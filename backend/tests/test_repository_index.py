from app.analyzer.repository_index import RepositoryIndexer
from app.evaluation.fixtures import repository_fixture
from app.reporting.report_generator import ReportGenerator
from app.analyzer.repository_analyzer import RepositoryAnalyzer


def test_repository_index_extracts_python_symbols_imports_and_tests():
    index = RepositoryIndexer().build(repository_fixture("python_app@v1"))

    symbol_names = {symbol.name for symbol in index.symbols}
    import_modules = {item.module for item in index.imports}
    test_links = {(link.test_path, link.source_path) for link in index.tests}

    assert "CheckoutService" in symbol_names
    assert "process_checkout" in symbol_names
    assert "app.db.pool" in import_modules
    assert ("tests/test_checkout.py", "app/services/checkout.py") in test_links
    assert all(symbol.line > 0 for symbol in index.symbols)


def test_repository_index_extracts_go_methods_and_imports():
    index = RepositoryIndexer().build(repository_fixture("go_service@v1"))

    symbols = {(symbol.container, symbol.name, symbol.kind) for symbol in index.symbols}
    imports = {item.module for item in index.imports}

    assert ("BillingService", "CreateInvoice", "method") in symbols
    assert (None, "NewBillingService", "function") in symbols
    assert "context" in imports
    assert any(link.test_path == "billing/service_test.go" for link in index.tests)


def test_repository_index_extracts_typescript_symbols_and_test_links():
    index = RepositoryIndexer().build(repository_fixture("ts_frontend@v1"))

    assert any(symbol.name == "CheckoutButton" for symbol in index.symbols)
    assert any(item.module == "react" for item in index.imports)
    assert any(link.test_path == "src/components/CheckoutButton.test.tsx" for link in index.tests)


def test_repository_index_records_truncation_metadata():
    snapshot = repository_fixture("python_app@v1")
    index = RepositoryIndexer(max_files=1).build(snapshot)

    assert index.metadata.files_indexed == 1
    assert index.metadata.truncated is True
    assert index.metadata.truncation_reason == "file_limit"


def test_repository_evolution_keeps_symbol_and_test_link_after_path_move():
    index = RepositoryIndexer().build(repository_fixture("go_service_moved@v1"))

    assert any(symbol.name == "CreateInvoice" for symbol in index.symbols)
    assert any(
        link.test_path == "billing/invoice_service_test.go"
        and link.source_path == "billing/invoice_service.go"
        for link in index.tests
    )


def test_public_code_intelligence_does_not_emphasize_line_numbers():
    snapshot = repository_fixture("go_service@v1")
    analysis = RepositoryAnalyzer().analyze(snapshot)
    report = ReportGenerator().generate(snapshot, analysis).report
    public_text = " ".join(
        [
            *report.code_intelligence.top_symbols,
            *report.code_intelligence.important_imports,
            *report.code_intelligence.test_links,
        ]
    )

    assert any(symbol.line > 0 for symbol in analysis.repository_index.symbols)
    assert ":1" not in public_text
    assert "BillingService.CreateInvoice" in public_text
