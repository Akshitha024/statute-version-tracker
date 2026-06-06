from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from tabulate import tabulate

from ..runner import run_sweep
from ..viz.charts import (
    plot_edit_distance_hist,
    plot_kind_stacked,
    plot_section_heatmap,
    plot_semantic_vs_syntactic,
    plot_top_changed_sections,
)

app = typer.Typer(add_completion=False, help="statute-version-tracker CLI")


@app.command("diff")
def cmd_diff(
    out_dir: Annotated[Path, typer.Option(help="results dir")] = Path("results"),
    n_sections: Annotated[int, typer.Option(help="sections per version")] = 30,
    n_versions: Annotated[int, typer.Option(help="versions to generate")] = 3,
) -> None:
    s = run_sweep(out_dir, n_sections=n_sections, n_versions=n_versions)
    totals = s["totals"]
    rows = [(k, v) for k, v in totals.items()]
    print()
    print(tabulate(rows, headers=["kind", "total"], tablefmt="github"))


@app.command("plots")
def cmd_plots(
    results_dir: Annotated[Path, typer.Option(help="results dir")] = Path("results"),
    figures_dir: Annotated[Path, typer.Option(help="figures dir")] = Path("results/figures"),
) -> None:
    plot_kind_stacked(results_dir / "summary.json", figures_dir / "kind_stacked.png")
    plot_edit_distance_hist(results_dir, figures_dir / "edit_distance_hist.png")
    plot_semantic_vs_syntactic(results_dir, figures_dir / "semantic_vs_syntactic.png")
    plot_section_heatmap(results_dir, figures_dir / "section_heatmap.png")
    plot_top_changed_sections(results_dir, figures_dir / "top_changed_sections.png")
    typer.echo(f"wrote 5 figures to {figures_dir}")


if __name__ == "__main__":
    app()
