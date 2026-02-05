"""Mutation testing report generation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from spectre.mutant.engine import MutantStatus, MutationTestResult


class MutationReport:
    """Generate mutation testing reports."""

    def __init__(self, result: MutationTestResult) -> None:
        self.result = result
        self.console = Console()

    def print_summary(self) -> None:
        """Print summary to console."""
        table = Table(title="Mutation Testing Summary")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Mutants", str(self.result.total_mutants))
        table.add_row("Killed", str(self.result.killed))
        table.add_row("Survived", str(self.result.survived))
        table.add_row("Timeout", str(self.result.timeout))
        table.add_row("Errors", str(self.result.errors))
        table.add_row(
            "Mutation Score",
            f"{self.result.mutation_score:.1f}%",
        )

        self.console.print(table)

    def print_survivors(self) -> None:
        """Print details of surviving mutants."""
        survivors = self.result.survivors

        if not survivors:
            self.console.print(
                Panel(
                    "[green]All mutants were killed![/green]",
                    title="Survivors",
                )
            )
            return

        table = Table(title=f"Surviving Mutants ({len(survivors)})")

        table.add_column("File", style="cyan")
        table.add_column("Line", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Description")

        for survivor in survivors:
            table.add_row(
                survivor.mutation.file_path,
                str(survivor.mutation.line_number),
                survivor.mutation.mutation_type.name,
                survivor.mutation.description,
            )

        self.console.print(table)

    def print_detailed(self) -> None:
        """Print detailed report of all mutations."""
        table = Table(title="All Mutations")

        table.add_column("Status", style="bold")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Type")
        table.add_column("Description")
        table.add_column("Duration")

        status_colors = {
            MutantStatus.KILLED: "green",
            MutantStatus.SURVIVED: "red",
            MutantStatus.TIMEOUT: "yellow",
            MutantStatus.ERROR: "red",
            MutantStatus.PENDING: "grey",
        }

        for result in self.result.results:
            color = status_colors.get(result.status, "white")
            table.add_row(
                f"[{color}]{result.status.name}[/{color}]",
                result.mutation.file_path,
                str(result.mutation.line_number),
                result.mutation.mutation_type.name,
                result.mutation.description[:40],
                f"{result.duration:.2f}s",
            )

        self.console.print(table)

    def to_json(self) -> str:
        """Convert report to JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_mutants": self.result.total_mutants,
                "killed": self.result.killed,
                "survived": self.result.survived,
                "timeout": self.result.timeout,
                "errors": self.result.errors,
                "mutation_score": self.result.mutation_score,
            },
            "results": [
                {
                    "status": r.status.name,
                    "duration": r.duration,
                    "mutation": {
                        "type": r.mutation.mutation_type.name,
                        "file": r.mutation.file_path,
                        "line": r.mutation.line_number,
                        "original": r.mutation.original,
                        "mutated": r.mutation.mutated,
                        "description": r.mutation.description,
                    },
                }
                for r in self.result.results
            ],
        }
        return json.dumps(data, indent=2)

    def save_json(self, path: Path) -> None:
        """Save JSON report to file."""
        path.write_text(self.to_json())
        self.console.print(f"Report saved to: {path}")

    def to_html(self) -> str:
        """Generate HTML report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mutation Testing Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .killed {{ color: green; }}
        .survived {{ color: red; font-weight: bold; }}
        .timeout {{ color: orange; }}
        .error {{ color: red; }}
        .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>Mutation Testing Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p class="score">Mutation Score: {self.result.mutation_score:.1f}%</p>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Mutants</td><td>{self.result.total_mutants}</td></tr>
            <tr><td>Killed</td><td>{self.result.killed}</td></tr>
            <tr><td>Survived</td><td>{self.result.survived}</td></tr>
            <tr><td>Timeout</td><td>{self.result.timeout}</td></tr>
            <tr><td>Errors</td><td>{self.result.errors}</td></tr>
        </table>
    </div>

    <h2>All Mutations</h2>
    <table>
        <tr>
            <th>Status</th>
            <th>File</th>
            <th>Line</th>
            <th>Type</th>
            <th>Description</th>
            <th>Duration</th>
        </tr>
"""
        for r in self.result.results:
            status_class = r.status.name.lower()
            html += f"""
        <tr>
            <td class="{status_class}">{r.status.name}</td>
            <td>{r.mutation.file_path}</td>
            <td>{r.mutation.line_number}</td>
            <td>{r.mutation.mutation_type.name}</td>
            <td>{r.mutation.description}</td>
            <td>{r.duration:.2f}s</td>
        </tr>
"""

        html += """
    </table>

    <h2>Surviving Mutants</h2>
"""
        survivors = self.result.survivors
        if survivors:
            html += "<table><tr><th>File</th><th>Line</th><th>Original</th><th>Mutated</th></tr>"
            for s in survivors:
                html += f"""
        <tr>
            <td>{s.mutation.file_path}</td>
            <td>{s.mutation.line_number}</td>
            <td><code>{s.mutation.original}</code></td>
            <td><code>{s.mutation.mutated}</code></td>
        </tr>
"""
            html += "</table>"
        else:
            html += "<p class='killed'>All mutants were killed!</p>"

        html += """
</body>
</html>
"""
        return html

    def save_html(self, path: Path) -> None:
        """Save HTML report to file."""
        path.write_text(self.to_html())
        self.console.print(f"HTML report saved to: {path}")


def create_progress() -> Progress:
    """Create a progress bar for mutation testing."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )
