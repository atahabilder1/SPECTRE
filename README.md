<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/EVM-Frontier%20|%20Homestead%20|%20Shanghai-purple?style=for-the-badge" alt="EVM Forks">
  <img src="https://img.shields.io/badge/Tests-181%20Passing-success?style=for-the-badge" alt="Tests">
</p>

<h1 align="center">SPECTRE</h1>

<h3 align="center">Security Protocol for Ethereum Compliance Testing and Runtime Evaluation</h3>

<p align="center">
  A comprehensive security assurance toolkit for testing and validating<br>
  Ethereum Virtual Machine (EVM) implementations across multiple forks.
</p>

<p align="center">
  <strong>Author:</strong> Anik Tahabilder<br>
  <em>PhD Candidate, Department of Computer Science</em><br>
  <em>Wayne State University</em>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#components">Components</a> •
  <a href="#documentation">Documentation</a>
</p>

---

## Overview

**SPECTRE** is an advanced security assurance toolkit designed for Ethereum Virtual Machine (EVM) specification testing. It combines a complete Python EVM implementation with powerful testing tools to ensure correctness, security, and compliance across different Ethereum forks.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 SPECTRE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         miniEELS Core                               │   │
│   │   ┌───────────┐    ┌────────────┐    ┌────────────┐                 │   │
│   │   │  Frontier │ ─► │ Homestead  │ ─► │  Shanghai  │                 │   │
│   │   │  (Base)   │    │  (EIP-2)   │    │ (EIP-3855) │                 │   │
│   │   └───────────┘    └────────────┘    └────────────┘                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│   │     MUTANT      │  │    PHANTOM      │  │   ADVERSARY     │             │
│   │    Mutation     │  │   Differential  │  │      Test       │             │
│   │    Testing      │  │     Fuzzing     │  │   Generation    │             │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Features

| Component | Description |
|-----------|-------------|
| **miniEELS Core** | Complete Python EVM with 140+ opcodes across 3 forks |
| **MUTANT** | Mutation testing engine with 8 specialized operators |
| **PHANTOM** | Differential fuzzer with 5 bytecode generation strategies |
| **ADVERSARY** | Adversarial test generator with 6 test strategies |

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git

### Quick Install

```bash
# Navigate to project directory
cd spectre

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Verify installation
spectre --help
pytest tests/ -v
```

### One-Line Install (after entering project directory)

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install -e .
```

## Quick Start

```bash
# Show SPECTRE info
spectre info

# List available EIPs
spectre adversary list-eips

# Generate test cases for EIP-3855 (PUSH0)
spectre adversary generate --eip 3855 --output fixtures/

# Run differential fuzzing
spectre phantom run --fork-a frontier --fork-b shanghai --count 100

# Run mutation testing
spectre mutant run --fork frontier --quick
```

## Components

### miniEELS Core

Complete Python EVM implementation supporting:

| Fork | Block | Key Features |
|------|-------|--------------|
| Frontier | 0 | Base EVM, 140+ opcodes |
| Homestead | 1,150,000 | EIP-2: CREATE changes |
| Shanghai | 17,034,870 | EIP-3855: PUSH0, EIP-3860: Initcode limits |

### MUTANT - Mutation Testing

| Operator | Description |
|----------|-------------|
| `arithmetic_swap` | Swap +, -, *, / operators |
| `comparison_swap` | Swap <, >, ==, != operators |
| `off_by_one` | Change constants by ±1 |
| `gas_cost` | Modify gas costs |
| `logic_negate` | Negate boolean conditions |
| `return_value` | Change return values |
| `boundary_change` | Modify boundary constants |
| `constant_change` | Change magic numbers |

### PHANTOM - Differential Fuzzing

| Strategy | Description |
|----------|-------------|
| `random` | Random byte sequences |
| `grammar` | Valid EVM bytecode |
| `boundary` | Boundary value testing |
| `opcode_focused` | Target specific opcodes |
| `sequence` | Known patterns |

### ADVERSARY - Test Generation

| Strategy | Focus |
|----------|-------|
| `BOUNDARY` | Input boundary values |
| `OPCODE_INTERACTION` | Opcode combinations |
| `CALL_CONTEXT` | CALL, DELEGATECALL, etc. |
| `GAS_EXHAUSTION` | Gas limit edge cases |
| `FORK_BOUNDARY` | Fork transition behavior |
| `STACK_DEPTH` | Stack limit testing |

## Project Structure

```
spectre/
├── src/
│   ├── ethereum/          # miniEELS Core
│   │   ├── common/        # Core types
│   │   ├── frontier/      # Frontier fork
│   │   ├── homestead/     # Homestead fork
│   │   └── shanghai/      # Shanghai fork
│   └── spectre/           # Security tools
│       ├── mutant/        # Mutation testing
│       ├── phantom/       # Differential fuzzing
│       ├── adversary/     # Test generation
│       └── cli.py         # CLI interface
├── tests/                 # Test suite (181 tests)
├── docs/                  # Documentation
├── fixtures/              # Generated test fixtures
├── manuscript/            # Research materials
└── reports/               # Generated reports
```

## Documentation

| Document | Description |
|----------|-------------|
| [SPECTRE_BOOK.md](docs/SPECTRE_BOOK.md) | Complete guide with chapters and hyperlinks |
| [SPECTRE_RESEARCH_PAPER.md](docs/SPECTRE_RESEARCH_PAPER.md) | Academic paper format |
| [BENCHMARKS.md](docs/BENCHMARKS.md) | Performance benchmarks |
| [THREAT_MODEL.md](docs/THREAT_MODEL.md) | Security analysis |

## Performance

| Metric | Value |
|--------|-------|
| EVM Execution | 13,424 tx/s |
| Differential Fuzzing | 11,083 tests/s |
| Test Generation | 88,319 tests/s |
| Test Suite | 181 tests, 0.30s |

## Citation

If you use SPECTRE in your research, please cite:

```bibtex
@software{spectre2024,
  author = {Tahabilder, Anik},
  title = {SPECTRE: Security Protocol for Ethereum Compliance Testing and Runtime Evaluation},
  year = {2024},
  institution = {Wayne State University}
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Ethereum Foundation for the [Yellow Paper](https://ethereum.github.io/yellowpaper/paper.pdf)
- [ethereum/execution-specs](https://github.com/ethereum/execution-specs) for reference
- Wayne State University Department of Computer Science

---

<p align="center">
  <strong>SPECTRE</strong><br>
  <em>Anik Tahabilder | Wayne State University</em>
</p>
