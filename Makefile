.PHONY: help install lint typecheck test diff plots pdf test-artifacts clean

help:
	@echo "make install / lint / typecheck / test - quality gates"
	@echo "make diff      - run the synthetic statute diff sweep"
	@echo "make plots     - regenerate the 5 chart types"
	@echo "make pdf       - render docs/research_report.pdf (needs pandoc+xelatex)"
	@echo "make test-artifacts - regenerate docs/test_results/*"

install: ; uv sync --all-extras
lint:
	uv run ruff check src tests
	uv run ruff format --check src tests
typecheck: ; uv run mypy src
test: ; uv run pytest -m "not slow"
diff: ; uv run statute-tracker diff
plots: ; uv run statute-tracker plots

pdf:
	cd docs/_report && pandoc research_report.md -o ../research_report.pdf --pdf-engine=xelatex --toc --toc-depth=2 --number-sections -V geometry:margin=1in -V fontsize=11pt -V mainfont="Helvetica" -V monofont="Menlo" -V linkcolor=blue -V urlcolor=blue -V linestretch=1.15 || echo "pandoc + xelatex required; see https://pandoc.org/installing.html"

test-artifacts:
	@mkdir -p docs/test_results
	uv run pytest -v > docs/test_results/pytest_output.txt 2>&1 || true
	{ echo "=== ruff check ==="; uv run ruff check src tests; echo "=== ruff format --check ==="; uv run ruff format --check src tests; echo "=== mypy ==="; uv run mypy src; } > docs/test_results/quality_gates.txt 2>&1 || true
	uv run pytest --cov=src -q > docs/test_results/coverage_summary.txt 2>&1 || true

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
