"""SPECTRE CLI - Unified command-line interface."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="spectre")
def main() -> None:
    """SPECTRE - Security assurance toolkit for Ethereum EVM specifications.

    A comprehensive toolkit for testing and validating EVM implementations
    across different forks (Frontier, Homestead, Shanghai).

    Commands:
        mutant    - Run mutation testing on EVM implementation
        phantom   - Run differential fuzzing between forks
        adversary - Generate adversarial test cases for EIPs
    """
    pass


# ============================================================================
# MUTANT Commands
# ============================================================================


@main.group()
def mutant() -> None:
    """MUTANT - Mutation testing for EVM specifications.

    Tests the quality of the test suite by introducing small changes
    (mutations) to the code and checking if tests detect them.
    """
    pass


@mutant.command("run")
@click.option(
    "--fork",
    type=click.Choice(["frontier", "homestead", "shanghai"]),
    default="frontier",
    help="Fork to run mutation testing on",
)
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("src/ethereum"),
    help="Source directory to mutate",
)
@click.option(
    "--test-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("tests"),
    help="Test directory",
)
@click.option(
    "--max-mutants",
    type=int,
    default=None,
    help="Maximum number of mutants to test",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file for report",
)
@click.option("--html", is_flag=True, help="Generate HTML report")
@click.option("--quick", is_flag=True, help="Quick mode with sampling")
def mutant_run(
    fork: str,
    source_dir: Path,
    test_dir: Path,
    max_mutants: int | None,
    output: Path | None,
    html: bool,
    quick: bool,
) -> None:
    """Run mutation testing on EVM implementation."""
    from spectre.mutant.engine import MutationEngine
    from spectre.mutant.report import MutationReport

    console.print(Panel(f"[bold]MUTANT[/bold] - Mutation Testing ({fork})", style="cyan"))

    # Adjust source directory for fork
    fork_source = source_dir / fork
    if not fork_source.exists():
        fork_source = source_dir

    console.print(f"Source: {fork_source}")
    console.print(f"Tests: {test_dir}")

    engine = MutationEngine(
        source_dir=fork_source,
        test_dir=test_dir,
    )

    with console.status("Running mutation tests..."):
        if quick:
            result = engine.run_quick(sample_size=max_mutants or 10)
        else:
            result = engine.run(max_mutants=max_mutants, file_filter=fork)

    # Generate report
    report = MutationReport(result)
    report.print_summary()
    report.print_survivors()

    if output:
        if html:
            report.save_html(output.with_suffix(".html"))
        else:
            report.save_json(output.with_suffix(".json"))


@mutant.command("list-operators")
def mutant_list_operators() -> None:
    """List available mutation operators."""
    from spectre.mutant.operators import ALL_OPERATORS

    table = Table(title="Mutation Operators")
    table.add_column("Name", style="cyan")
    table.add_column("Description")

    for op_class in ALL_OPERATORS:
        table.add_row(op_class.name, op_class.description)

    console.print(table)


# ============================================================================
# PHANTOM Commands
# ============================================================================


@main.group()
def phantom() -> None:
    """PHANTOM - Differential fuzzing for EVM implementations.

    Generates bytecode and compares execution across different forks
    to find divergences in behavior.
    """
    pass


@phantom.command("run")
@click.option(
    "--fork-a",
    type=click.Choice(["frontier", "homestead", "shanghai"]),
    default="frontier",
    help="First fork to compare",
)
@click.option(
    "--fork-b",
    type=click.Choice(["frontier", "homestead", "shanghai"]),
    default="shanghai",
    help="Second fork to compare",
)
@click.option(
    "--count",
    type=int,
    default=100,
    help="Number of test cases to generate",
)
@click.option(
    "--strategy",
    type=click.Choice(["random", "grammar", "boundary", "all"]),
    default="all",
    help="Bytecode generation strategy",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for reproducibility",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file for divergences",
)
def phantom_run(
    fork_a: str,
    fork_b: str,
    count: int,
    strategy: str,
    seed: int | None,
    output: Path | None,
) -> None:
    """Run differential fuzzing between two forks."""
    from spectre.phantom.executor import DifferentialExecutor, Fork
    from spectre.phantom.generator import BytecodeGenerator, GeneratorStrategy

    console.print(
        Panel(f"[bold]PHANTOM[/bold] - Differential Fuzzing ({fork_a} vs {fork_b})", style="magenta")
    )

    # Map fork names to enums
    fork_map = {
        "frontier": Fork.FRONTIER,
        "homestead": Fork.HOMESTEAD,
        "shanghai": Fork.SHANGHAI,
    }

    executor = DifferentialExecutor(
        fork_a=fork_map[fork_a],
        fork_b=fork_map[fork_b],
    )

    # Setup generator
    strategies = None
    if strategy != "all":
        strategy_map = {
            "random": GeneratorStrategy.RANDOM,
            "grammar": GeneratorStrategy.GRAMMAR,
            "boundary": GeneratorStrategy.BOUNDARY,
        }
        strategies = [strategy_map[strategy]]

    generator = BytecodeGenerator(strategies=strategies)
    bytecodes = generator.generate(count=count, seed=seed)

    divergences = []

    def on_divergence(div):
        divergences.append(div)
        console.print(f"[red]Divergence found:[/red] {div.description}")

    with console.status(f"Fuzzing {count} test cases..."):
        result = executor.run(bytecodes, callback=on_divergence)

    # Print summary
    table = Table(title="Fuzzing Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Executions", str(result.total_executions))
    table.add_row("Unexpected Divergences", str(result.unexpected_divergences))
    table.add_row("Expected Divergences", str(result.expected_divergences))
    table.add_row("Divergence Rate", f"{result.divergence_rate:.2f}%")

    console.print(table)

    if output and divergences:
        import json

        data = [
            {
                "type": d.divergence_type.name,
                "bytecode": d.bytecode.code.hex(),
                "description": d.description,
            }
            for d in divergences
        ]
        output.write_text(json.dumps(data, indent=2))
        console.print(f"Divergences saved to: {output}")


@phantom.command("minimize")
@click.argument("bytecode", type=str)
@click.option(
    "--fork-a",
    type=click.Choice(["frontier", "homestead", "shanghai"]),
    default="frontier",
)
@click.option(
    "--fork-b",
    type=click.Choice(["frontier", "homestead", "shanghai"]),
    default="shanghai",
)
def phantom_minimize(bytecode: str, fork_a: str, fork_b: str) -> None:
    """Minimize a divergent bytecode case."""
    from spectre.phantom.executor import Fork
    from spectre.phantom.minimizer import DeltaDebugger

    fork_map = {
        "frontier": Fork.FRONTIER,
        "homestead": Fork.HOMESTEAD,
        "shanghai": Fork.SHANGHAI,
    }

    console.print("[bold]Minimizing bytecode...[/bold]")

    code = bytes.fromhex(bytecode.replace("0x", ""))
    debugger = DeltaDebugger(fork_a=fork_map[fork_a], fork_b=fork_map[fork_b])

    result = debugger.minimize(code)

    console.print(f"Original: {result.original_size} bytes")
    console.print(f"Minimized: {result.minimized_size} bytes")
    console.print(f"Reduction: {result.reduction_percent:.1f}%")
    console.print(f"Iterations: {result.iterations}")
    console.print(f"\nMinimized bytecode: 0x{result.minimized.hex()}")


# ============================================================================
# ADVERSARY Commands
# ============================================================================


@main.group()
def adversary() -> None:
    """ADVERSARY - Adversarial test case generator.

    Generates comprehensive test cases for EIP validation using
    multiple strategies: boundary values, opcode interactions,
    call contexts, gas exhaustion, and more.
    """
    pass


@adversary.command("generate")
@click.option(
    "--eip",
    type=int,
    required=True,
    help="EIP number to generate tests for",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("fixtures"),
    help="Output directory for test files",
)
@click.option(
    "--format",
    type=click.Choice(["json", "eest", "both"]),
    default="both",
    help="Output format",
)
@click.option(
    "--strategy",
    type=click.Choice(["boundary", "interaction", "gas", "fork", "all"]),
    default="all",
    help="Test generation strategy",
)
def adversary_generate(
    eip: int,
    output: Path,
    format: str,
    strategy: str,
) -> None:
    """Generate adversarial test cases for an EIP."""
    from spectre.adversary.generator import TestGenerator
    from spectre.adversary.strategies import StrategyType

    console.print(Panel(f"[bold]ADVERSARY[/bold] - Test Generation (EIP-{eip})", style="yellow"))

    strategy_map = {
        "boundary": [StrategyType.BOUNDARY],
        "interaction": [StrategyType.OPCODE_INTERACTION],
        "gas": [StrategyType.GAS_EXHAUSTION],
        "fork": [StrategyType.FORK_BOUNDARY],
        "all": None,
    }

    generator = TestGenerator()
    suite = generator.generate_for_eip(eip, strategy_types=strategy_map[strategy])

    console.print(f"Generated {len(suite.test_cases)} test cases")

    # Save files
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)

    if format in ("json", "both"):
        path = generator.save_test_suite(suite, output, format="json")
        console.print(f"Saved JSON: {path}")

    if format in ("eest", "both"):
        path = generator.save_test_suite(suite, output, format="eest")
        console.print(f"Saved EEST: {path}")

    # Print test summary
    table = Table(title="Generated Tests by Strategy")
    table.add_column("Strategy", style="cyan")
    table.add_column("Count", style="green")

    strategy_counts: dict[str, int] = {}
    for tc in suite.test_cases:
        name = tc.strategy.name
        strategy_counts[name] = strategy_counts.get(name, 0) + 1

    for name, count in sorted(strategy_counts.items()):
        table.add_row(name, str(count))

    console.print(table)


@adversary.command("list-eips")
def adversary_list_eips() -> None:
    """List known EIPs with test coverage."""
    from spectre.adversary.analyzer import EIPAnalyzer

    analyzer = EIPAnalyzer()

    table = Table(title="Known EIPs")
    table.add_column("EIP", style="cyan")
    table.add_column("Title")
    table.add_column("Category", style="yellow")
    table.add_column("Opcodes", style="green")

    for eip_num in analyzer.list_all_eips():
        eip = analyzer.get_eip(eip_num)
        if eip:
            opcodes = ", ".join(op.name for op in eip.opcodes) or "-"
            table.add_row(
                str(eip.number),
                eip.title[:40],
                eip.category.name,
                opcodes[:30],
            )

    console.print(table)


@adversary.command("analyze")
@click.option("--eip", type=int, required=True, help="EIP to analyze")
def adversary_analyze(eip: int) -> None:
    """Analyze an EIP and show test requirements."""
    from spectre.adversary.analyzer import EIPAnalyzer

    analyzer = EIPAnalyzer()
    spec = analyzer.get_eip(eip)

    if not spec:
        console.print(f"[red]EIP {eip} not found[/red]")
        return

    console.print(Panel(f"[bold]EIP-{eip}:[/bold] {spec.title}", style="cyan"))

    # Opcodes
    if spec.opcodes:
        table = Table(title="Affected Opcodes")
        table.add_column("Opcode", style="cyan")
        table.add_column("Name", style="yellow")
        table.add_column("Change Type")
        table.add_column("Gas Cost", style="green")

        for op in spec.opcodes:
            table.add_row(
                f"0x{op.opcode:02X}",
                op.name,
                op.change_type.name,
                str(op.gas_cost) if op.gas_cost else "-",
            )

        console.print(table)

    # Boundary values
    boundaries = analyzer.get_boundary_values(eip)[:20]
    if boundaries:
        console.print("\n[bold]Key Boundary Values:[/bold]")
        console.print(", ".join(str(b) for b in boundaries))

    # Related EIPs
    related = analyzer.get_related_eips(eip)
    if related:
        console.print(f"\n[bold]Related EIPs:[/bold] {related}")


# ============================================================================
# Info Commands
# ============================================================================


@main.command("info")
def info() -> None:
    """Show information about SPECTRE."""
    console.print(
        Panel(
            """[bold cyan]SPECTRE[/bold cyan] - Security assurance toolkit for Ethereum EVM specifications

[bold]Components:[/bold]
  • [cyan]miniEELS[/cyan] - Python EVM implementation (Frontier, Homestead, Shanghai)
  • [magenta]MUTANT[/magenta] - Mutation testing engine
  • [magenta]PHANTOM[/magenta] - Differential fuzzer
  • [yellow]ADVERSARY[/yellow] - Adversarial test generator

[bold]Usage:[/bold]
  spectre mutant run --fork frontier
  spectre phantom run --fork-a frontier --fork-b shanghai
  spectre adversary generate --eip 3855

[bold]Documentation:[/bold]
  See README.md for full documentation
""",
            title="About SPECTRE",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
