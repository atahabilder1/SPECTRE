# SPECTRE: Complete Documentation

<p align="center">
<strong>Security Protocol for Ethereum Compliance Testing and Runtime Evaluation</strong>
</p>

<p align="center">
<strong>Author:</strong> Anik Tahabilder<br>
<em>PhD Candidate, Department of Computer Science</em><br>
<em>Wayne State University</em>
</p>

<p align="center">
<em>A Comprehensive Security Assurance Toolkit for Ethereum Virtual Machine Specifications</em>
</p>

---

# Table of Contents

## Part I: Introduction
- [1. Overview](#1-overview)
  - [1.1 What is SPECTRE?](#11-what-is-spectre)
  - [1.2 Motivation](#12-motivation)
  - [1.3 Key Components](#13-key-components)
  - [1.4 Architecture](#14-architecture)
- [2. Installation](#2-installation)
  - [2.1 Prerequisites](#21-prerequisites)
  - [2.2 Step-by-Step Installation](#22-step-by-step-installation)
  - [2.3 Verification](#23-verification)
  - [2.4 Troubleshooting](#24-troubleshooting)
- [3. Quick Start](#3-quick-start)
  - [3.1 First Commands](#31-first-commands)
  - [3.2 Running Tests](#32-running-tests)
  - [3.3 Generating Test Cases](#33-generating-test-cases)

## Part II: miniEELS Core - EVM Implementation
- [4. EVM Fundamentals](#4-evm-fundamentals)
  - [4.1 World State Model](#41-world-state-model)
  - [4.2 Accounts](#42-accounts)
  - [4.3 Transactions](#43-transactions)
  - [4.4 Messages](#44-messages)
  - [4.5 Gas Mechanics](#45-gas-mechanics)
- [5. Supported Forks](#5-supported-forks)
  - [5.1 Frontier (Genesis)](#51-frontier-genesis)
  - [5.2 Homestead (EIP-2)](#52-homestead-eip-2)
  - [5.3 Shanghai (EIP-3855, EIP-3860)](#53-shanghai-eip-3855-eip-3860)
- [6. Opcode Reference](#6-opcode-reference)
  - [6.1 Arithmetic Operations](#61-arithmetic-operations)
  - [6.2 Comparison Operations](#62-comparison-operations)
  - [6.3 Bitwise Operations](#63-bitwise-operations)
  - [6.4 SHA3](#64-sha3)
  - [6.5 Environmental Information](#65-environmental-information)
  - [6.6 Block Information](#66-block-information)
  - [6.7 Stack, Memory, Storage](#67-stack-memory-storage)
  - [6.8 Push Operations](#68-push-operations)
  - [6.9 Duplication Operations](#69-duplication-operations)
  - [6.10 Exchange Operations](#610-exchange-operations)
  - [6.11 Logging Operations](#611-logging-operations)
  - [6.12 System Operations](#612-system-operations)
  - [6.13 Control Flow](#613-control-flow)
- [7. Gas Schedule](#7-gas-schedule)
  - [7.1 Base Gas Costs](#71-base-gas-costs)
  - [7.2 Dynamic Gas Costs](#72-dynamic-gas-costs)
  - [7.3 Memory Expansion](#73-memory-expansion)
  - [7.4 Storage Costs](#74-storage-costs)

## Part III: Security Tools
- [8. MUTANT - Mutation Testing](#8-mutant---mutation-testing)
  - [8.1 What is Mutation Testing?](#81-what-is-mutation-testing)
  - [8.2 Mutation Operators](#82-mutation-operators)
  - [8.3 Running MUTANT](#83-running-mutant)
  - [8.4 Interpreting Results](#84-interpreting-results)
  - [8.5 Best Practices](#85-best-practices)
- [9. PHANTOM - Differential Fuzzing](#9-phantom---differential-fuzzing)
  - [9.1 What is Differential Fuzzing?](#91-what-is-differential-fuzzing)
  - [9.2 Bytecode Generation Strategies](#92-bytecode-generation-strategies)
  - [9.3 Running PHANTOM](#93-running-phantom)
  - [9.4 Divergence Types](#94-divergence-types)
  - [9.5 Delta Debugging](#95-delta-debugging)
- [10. ADVERSARY - Test Generation](#10-adversary---test-generation)
  - [10.1 Adversarial Testing](#101-adversarial-testing)
  - [10.2 Test Strategies](#102-test-strategies)
  - [10.3 Running ADVERSARY](#103-running-adversary)
  - [10.4 Output Formats](#104-output-formats)
  - [10.5 Known EIPs](#105-known-eips)

## Part IV: API Reference
- [11. Core Types API](#11-core-types-api)
  - [11.1 U256](#111-u256)
  - [11.2 Address](#112-address)
  - [11.3 Account](#113-account)
  - [11.4 State](#114-state)
  - [11.5 Transaction](#115-transaction)
  - [11.6 Environment](#116-environment)
  - [11.7 Message](#117-message)
  - [11.8 ExecutionResult](#118-executionresult)
- [12. EVM Execution API](#12-evm-execution-api)
  - [12.1 Interpreter](#121-interpreter)
  - [12.2 Stack](#122-stack)
  - [12.3 Memory](#123-memory)
  - [12.4 State Transition](#124-state-transition)
- [13. Security Tools API](#13-security-tools-api)
  - [13.1 MUTANT API](#131-mutant-api)
  - [13.2 PHANTOM API](#132-phantom-api)
  - [13.3 ADVERSARY API](#133-adversary-api)

## Part V: CLI Reference
- [14. Command Line Interface](#14-command-line-interface)
  - [14.1 Global Commands](#141-global-commands)
  - [14.2 MUTANT Commands](#142-mutant-commands)
  - [14.3 PHANTOM Commands](#143-phantom-commands)
  - [14.4 ADVERSARY Commands](#144-adversary-commands)

## Part VI: Advanced Topics
- [15. Security Analysis](#15-security-analysis)
  - [15.1 Threat Model](#151-threat-model)
  - [15.2 Attack Vectors](#152-attack-vectors)
  - [15.3 Defense Strategies](#153-defense-strategies)
- [16. Performance](#16-performance)
  - [16.1 Benchmarks](#161-benchmarks)
  - [16.2 Scalability](#162-scalability)
  - [16.3 Optimization Tips](#163-optimization-tips)
- [17. Project Structure](#17-project-structure)
  - [17.1 Directory Layout](#171-directory-layout)
  - [17.2 Code Statistics](#172-code-statistics)
- [18. Contributing](#18-contributing)
  - [18.1 Development Setup](#181-development-setup)
  - [18.2 Code Style](#182-code-style)
  - [18.3 Testing Guidelines](#183-testing-guidelines)
  - [18.4 Pull Request Process](#184-pull-request-process)

## Appendices
- [A. Formal Semantics](#appendix-a-formal-semantics)
- [B. EIP Reference](#appendix-b-eip-reference)
- [C. Bibliography](#appendix-c-bibliography)
- [D. Glossary](#appendix-d-glossary)

---

# Part I: Introduction

---

## 1. Overview

### 1.1 What is SPECTRE?

**SPECTRE** (Security Protocol for Ethereum Compliance Testing and Runtime Evaluation) is a comprehensive security assurance toolkit designed for testing and validating Ethereum Virtual Machine (EVM) implementations across multiple protocol forks.

SPECTRE provides four integrated components:

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **miniEELS** | Reference EVM implementation | 140+ opcodes, 3 forks, clean Python code |
| **MUTANT** | Mutation testing | 8 operators, test suite quality evaluation |
| **PHANTOM** | Differential fuzzing | 5 strategies, fork divergence detection |
| **ADVERSARY** | Test generation | 6 strategies, EIP-targeted test cases |

### 1.2 Motivation

The Ethereum Virtual Machine executes smart contracts that collectively secure billions of dollars in digital assets. Ensuring correctness across protocol upgrades is critical for:

1. **Network Consensus**: All clients must produce identical results
2. **Security**: Implementation bugs can lead to fund theft or DoS
3. **Compliance**: EIPs must be implemented precisely

**Historical Incidents:**

| Year | Incident | Impact |
|------|----------|--------|
| 2016 | Shanghai DoS Attacks | Network degradation from gas mispricing |
| 2016 | DAO Hack | $60M stolen due to reentrancy |
| 2020 | Berlin Fork Divergence | Brief chain split between clients |

SPECTRE addresses these challenges through systematic, automated testing.

### 1.3 Key Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  SPECTRE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          miniEELS Core                                  │ │
│  │                                                                         │ │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │ │
│  │   │   Frontier   │ ─► │  Homestead   │ ─► │   Shanghai   │             │ │
│  │   │   (Block 0)  │    │  (Block 1.1M)│    │ (Block 17M)  │             │ │
│  │   │              │    │              │    │              │             │ │
│  │   │  Base EVM    │    │   EIP-2      │    │  EIP-3855    │             │ │
│  │   │  140+ ops    │    │   CREATE     │    │  PUSH0       │             │ │
│  │   └──────────────┘    └──────────────┘    └──────────────┘             │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │      MUTANT      │  │     PHANTOM      │  │    ADVERSARY     │          │
│  │                  │  │                  │  │                  │          │
│  │  Mutation        │  │  Differential    │  │  Adversarial     │          │
│  │  Testing         │  │  Fuzzing         │  │  Test Gen        │          │
│  │                  │  │                  │  │                  │          │
│  │  • 8 operators   │  │  • 5 strategies  │  │  • 6 strategies  │          │
│  │  • Test quality  │  │  • Fork compare  │  │  • EIP coverage  │          │
│  │  • Kill analysis │  │  • Minimization  │  │  • EEST format   │          │
│  │                  │  │                  │  │                  │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Architecture

```
                              ┌──────────────────┐
                              │    User / CLI    │
                              └────────┬─────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
                 ▼                     ▼                     ▼
          ┌────────────┐        ┌────────────┐        ┌────────────┐
          │   MUTANT   │        │  PHANTOM   │        │ ADVERSARY  │
          │            │        │            │        │            │
          │ operators  │        │ generator  │        │ analyzer   │
          │ engine     │        │ executor   │        │ strategies │
          │ reporter   │        │ minimizer  │        │ generator  │
          └─────┬──────┘        └─────┬──────┘        └─────┬──────┘
                │                     │                     │
                └─────────────────────┼─────────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │     miniEELS Core      │
                         │                        │
                         │  ┌──────────────────┐  │
                         │  │    Interpreter   │  │
                         │  │  (opcode exec)   │  │
                         │  └──────────────────┘  │
                         │  ┌──────────────────┐  │
                         │  │      State       │  │
                         │  │ (accounts, stor) │  │
                         │  └──────────────────┘  │
                         │  ┌──────────────────┐  │
                         │  │       Gas        │  │
                         │  │   (schedule)     │  │
                         │  └──────────────────┘  │
                         │  ┌──────────────────┐  │
                         │  │   Stack/Memory   │  │
                         │  │   (execution)    │  │
                         │  └──────────────────┘  │
                         │                        │
                         └────────────────────────┘
```

[↑ Back to Table of Contents](#table-of-contents)

---

## 2. Installation

### 2.1 Prerequisites

| Requirement | Minimum Version | Recommended | Check Command |
|-------------|-----------------|-------------|---------------|
| Python | 3.11 | 3.12 | `python3 --version` |
| pip | 21.0 | Latest | `pip --version` |
| Git | 2.0 | Latest | `git --version` |
| OS | Linux/macOS/Windows | Ubuntu 22.04+ | - |

**System Requirements:**
- RAM: 4GB minimum, 8GB recommended
- Disk: 500MB for installation
- Network: Required for installation only

### 2.2 Step-by-Step Installation

#### Option A: Standard Installation (Recommended)

```bash
# Step 1: Navigate to project directory
cd spectre

# Step 2: Create a virtual environment
python3 -m venv .venv

# Step 3: Activate the virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Step 4: Install dependencies
pip install -r requirements.txt

# Step 5: Install SPECTRE in development mode
pip install -e .

# Step 6: Verify installation
spectre --help
```

#### Option B: Development Installation

```bash
cd spectre
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

#### Option C: Using uv (Fastest)

```bash
cd spectre
uv sync --all-extras
```

#### One-Line Installation (after entering project directory)

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install -e .
```

### 2.3 Verification

After installation, verify everything works:

```bash
# Check CLI
spectre --help

# Check version
spectre --version

# Run test suite
pytest tests/ -v

# Expected: 181 tests passed
```

**Expected Output:**
```
============================= test session starts ==============================
collected 181 items

tests/frontier/test_arithmetic.py ............................ [ 15%]
tests/frontier/test_control_flow.py .................. [ 25%]
...
============================= 181 passed in 0.30s ==============================
```

### 2.4 Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `command not found: python3` | Python not installed | Install from [python.org](https://python.org) |
| `externally-managed-environment` | System Python protection | Use virtual environment (venv) |
| `ModuleNotFoundError` | venv not activated | Run `source .venv/bin/activate` |
| `spectre: command not found` | Package not installed | Run `pip install -e .` |
| `Permission denied` | File permissions | Use `sudo` or check permissions |
| Import errors | Wrong Python version | Ensure Python 3.11+ |

[↑ Back to Table of Contents](#table-of-contents)

---

## 3. Quick Start

### 3.1 First Commands

```bash
# Display SPECTRE information
spectre info
```

**Output:**
```
╭─────────────────────────────── About SPECTRE ────────────────────────────────╮
│ SPECTRE - Security assurance toolkit for Ethereum EVM specifications         │
│                                                                              │
│ Components:                                                                  │
│   • miniEELS - Python EVM implementation (Frontier, Homestead, Shanghai)     │
│   • MUTANT - Mutation testing engine                                         │
│   • PHANTOM - Differential fuzzer                                            │
│   • ADVERSARY - Adversarial test generator                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

```bash
# List available EIPs
spectre adversary list-eips
```

**Output:**
```
                                Known EIPs
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ EIP  ┃ Title                                ┃ Category ┃ Opcodes       ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 2    │ Homestead Hard-fork Changes          │ CORE     │ CREATE        │
│ 3855 │ PUSH0 instruction                    │ CORE     │ PUSH0         │
│ 3860 │ Limit and meter initcode             │ CORE     │ -             │
└──────┴──────────────────────────────────────┴──────────┴───────────────┘
```

### 3.2 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/frontier/test_arithmetic.py -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run tests in parallel
pytest tests/ -n auto
```

### 3.3 Generating Test Cases

```bash
# Generate tests for EIP-3855 (PUSH0)
spectre adversary generate --eip 3855 --output fixtures/
```

**Output:**
```
╭──────────────────────────────────────────────────────────────────────────────╮
│ ADVERSARY - Test Generation (EIP-3855: PUSH0 instruction)                    │
╰──────────────────────────────────────────────────────────────────────────────╯

Generated 33 test cases:

 Strategy            │ Count
─────────────────────┼───────
 BOUNDARY            │ 19
 OPCODE_INTERACTION  │ 4
 CALL_CONTEXT        │ 4
 GAS_EXHAUSTION      │ 3
 FORK_BOUNDARY       │ 2
 STACK_DEPTH         │ 1

Saved to:
  • fixtures/eip3855_tests.json
  • fixtures/eip3855_tests_eest.json
```

[↑ Back to Table of Contents](#table-of-contents)

---

# Part II: miniEELS Core - EVM Implementation

---

## 4. EVM Fundamentals

### 4.1 World State Model

The Ethereum Virtual Machine operates on a **world state** (σ) - a mapping from 20-byte addresses to account states.

```
World State (σ)
│
├── Address 0x0000...0001
│   └── Account
│       ├── nonce: 5
│       ├── balance: 1000000000000000000 (1 ETH)
│       ├── codeHash: 0xc5d2...
│       └── storageRoot: 0x56e8...
│
├── Address 0x0000...0002
│   └── Account
│       ├── nonce: 0
│       ├── balance: 0
│       ├── codeHash: 0x6080...
│       └── storageRoot: 0x1234...
│
└── ...
```

**SPECTRE Implementation:**

```python
from ethereum.common.types import State, Account, Address

# Create empty state
state = State()

# Create an account
account = Account(
    nonce=0,
    balance=10**18,  # 1 ETH in wei
    code=b"",
    storage={}
)

# Add to state
address = Address(b"\x00" * 19 + b"\x01")
state.set_account(address, account)

# Query state
balance = state.get_balance(address)
nonce = state.get_nonce(address)
```

### 4.2 Accounts

**Two Types of Accounts:**

| Type | Code | Controlled By | Purpose |
|------|------|---------------|---------|
| EOA (Externally Owned Account) | Empty | Private key | User wallets |
| Contract Account | Non-empty | Code logic | Smart contracts |

**Account Structure:**

```python
@dataclass
class Account:
    nonce: int = 0          # Transaction count (EOA) or creation count (contract)
    balance: int = 0        # Wei balance
    code: bytes = b""       # Contract bytecode (empty for EOA)
    storage: dict = {}      # Key-value storage (contracts only)
```

### 4.3 Transactions

A transaction is a signed message that triggers state changes:

```python
@dataclass
class Transaction:
    sender: Address         # Who sends (recovered from signature)
    to: Address | None      # Recipient (None for contract creation)
    value: int              # Wei to transfer
    data: bytes             # Input data or init code
    gas: int                # Gas limit
    gas_price: int          # Wei per gas unit
    nonce: int              # Sender's transaction count
```

**Transaction Types:**

| Type | `to` | `data` | Purpose |
|------|------|--------|---------|
| Transfer | Address | Empty | Send ETH |
| Contract Call | Contract | Calldata | Execute function |
| Contract Creation | None | Bytecode | Deploy contract |

### 4.4 Messages

Internal calls create message frames:

```python
@dataclass
class Message:
    caller: Address         # Who called
    target: Address         # Call target
    value: int              # Wei sent
    data: bytes             # Input data
    gas: int                # Gas available
    depth: int              # Call depth (max 1024)
    code: bytes             # Code to execute
    is_create: bool = False # Contract creation flag
```

### 4.5 Gas Mechanics

Gas is the execution fuel that:
1. Prevents infinite loops
2. Compensates validators
3. Prices computational resources

```
Transaction Gas Flow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  tx.gas (limit)
      │
      ▼
  ┌─────────────────────────────────────────────────┐
  │ Intrinsic Gas                                   │
  │   • 21000 base cost                             │
  │   • 16 per non-zero data byte                   │
  │   • 4 per zero data byte                        │
  │   • 32000 for contract creation                 │
  └─────────────────────────────────────────────────┘
      │
      ▼
  ┌─────────────────────────────────────────────────┐
  │ Execution Gas                                   │
  │   • Opcode costs (see gas schedule)             │
  │   • Memory expansion                            │
  │   • Storage operations                          │
  └─────────────────────────────────────────────────┘
      │
      ▼
  ┌─────────────────────────────────────────────────┐
  │ Refund (capped at execution_gas / 2)            │
  │   • SSTORE clear (set to zero)                  │
  │   • SELFDESTRUCT                                │
  └─────────────────────────────────────────────────┘
      │
      ▼
  gas_used = intrinsic + execution - refund
  gas_refund = tx.gas - gas_used

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

[↑ Back to Table of Contents](#table-of-contents)

---

## 5. Supported Forks

### 5.1 Frontier (Genesis)

**Block:** 0 (July 30, 2015)

The original Ethereum specification:

```python
from ethereum.frontier.vm.interpreter import Interpreter
from ethereum.frontier.fork import state_transition

# Create interpreter
interpreter = Interpreter(state, env)
result = interpreter.execute(message)

# Or use state transition function
new_state, result = state_transition(state, tx, env)
```

**Characteristics:**
- Base EVM with ~140 opcodes
- Simple gas schedule
- No special edge cases

### 5.2 Homestead (EIP-2)

**Block:** 1,150,000 (March 14, 2016)

```python
from ethereum.homestead.vm.interpreter import HomesteadInterpreter
from ethereum.homestead.fork import state_transition
```

**EIP-2 Changes:**

| Aspect | Frontier | Homestead |
|--------|----------|-----------|
| CREATE gas | 21000 | 32000 |
| CREATE failure | Returns 0, preserves gas | Returns 0, consumes all gas |
| OOG in CREATE | Silently fails | Properly reverts |
| Signature s-value | Any | Must be low (≤ secp256k1n/2) |

### 5.3 Shanghai (EIP-3855, EIP-3860)

**Block:** 17,034,870 (April 12, 2023)

```python
from ethereum.shanghai.vm.interpreter import ShanghaiInterpreter
from ethereum.shanghai.fork import state_transition
```

**EIP-3855: PUSH0 Opcode**

| Before | After |
|--------|-------|
| `PUSH1 0x00` (2 bytes, 3 gas) | `PUSH0` (1 byte, 2 gas) |

```
PUSH0 (0x5F):
  Stack: [...] → [..., 0]
  Gas: 2
  Description: Push the constant 0 onto the stack
```

**EIP-3860: Initcode Limits**

| Aspect | Value |
|--------|-------|
| Max initcode size | 49152 bytes (2 × MAX_CODE_SIZE) |
| Initcode gas cost | 2 gas per 32-byte word |

[↑ Back to Table of Contents](#table-of-contents)

---

## 6. Opcode Reference

### 6.1 Arithmetic Operations

| Opcode | Hex | Gas | Stack [in] → [out] | Description |
|--------|-----|-----|-------------------|-------------|
| STOP | 0x00 | 0 | [] → [] | Halt execution |
| ADD | 0x01 | 3 | [a, b] → [a+b] | Addition mod 2²⁵⁶ |
| MUL | 0x02 | 5 | [a, b] → [a×b] | Multiplication mod 2²⁵⁶ |
| SUB | 0x03 | 3 | [a, b] → [a-b] | Subtraction mod 2²⁵⁶ |
| DIV | 0x04 | 5 | [a, b] → [a÷b] | Integer division (0 if b=0) |
| SDIV | 0x05 | 5 | [a, b] → [a÷b] | Signed integer division |
| MOD | 0x06 | 5 | [a, b] → [a%b] | Modulo (0 if b=0) |
| SMOD | 0x07 | 5 | [a, b] → [a%b] | Signed modulo |
| ADDMOD | 0x08 | 8 | [a, b, N] → [(a+b)%N] | Addition modulo N |
| MULMOD | 0x09 | 8 | [a, b, N] → [(a×b)%N] | Multiplication modulo N |
| EXP | 0x0A | 10* | [a, b] → [a^b] | Exponentiation |
| SIGNEXTEND | 0x0B | 5 | [b, x] → [y] | Sign extend x from (b+1) bytes |

*EXP gas: 10 + 50 × ceil(log256(exponent+1))

### 6.2 Comparison Operations

| Opcode | Hex | Gas | Stack [in] → [out] | Description |
|--------|-----|-----|-------------------|-------------|
| LT | 0x10 | 3 | [a, b] → [a<b] | Less than |
| GT | 0x11 | 3 | [a, b] → [a>b] | Greater than |
| SLT | 0x12 | 3 | [a, b] → [a<b] | Signed less than |
| SGT | 0x13 | 3 | [a, b] → [a>b] | Signed greater than |
| EQ | 0x14 | 3 | [a, b] → [a==b] | Equality |
| ISZERO | 0x15 | 3 | [a] → [a==0] | Is zero |

### 6.3 Bitwise Operations

| Opcode | Hex | Gas | Stack [in] → [out] | Description |
|--------|-----|-----|-------------------|-------------|
| AND | 0x16 | 3 | [a, b] → [a&b] | Bitwise AND |
| OR | 0x17 | 3 | [a, b] → [a\|b] | Bitwise OR |
| XOR | 0x18 | 3 | [a, b] → [a^b] | Bitwise XOR |
| NOT | 0x19 | 3 | [a] → [~a] | Bitwise NOT |
| BYTE | 0x1A | 3 | [i, x] → [y] | i-th byte of x |
| SHL | 0x1B | 3 | [shift, val] → [val<<shift] | Left shift |
| SHR | 0x1C | 3 | [shift, val] → [val>>shift] | Logical right shift |
| SAR | 0x1D | 3 | [shift, val] → [val>>shift] | Arithmetic right shift |

### 6.4 SHA3

| Opcode | Hex | Gas | Stack [in] → [out] | Description |
|--------|-----|-----|-------------------|-------------|
| SHA3 | 0x20 | 30* | [offset, size] → [hash] | Keccak-256 hash |

*SHA3 gas: 30 + 6 × ceil(size/32) + memory expansion

### 6.5 Environmental Information

| Opcode | Hex | Gas | Stack | Description |
|--------|-----|-----|-------|-------------|
| ADDRESS | 0x30 | 2 | [] → [addr] | Current contract address |
| BALANCE | 0x31 | 100 | [addr] → [bal] | Balance of address |
| ORIGIN | 0x32 | 2 | [] → [addr] | Transaction origin |
| CALLER | 0x33 | 2 | [] → [addr] | Message caller |
| CALLVALUE | 0x34 | 2 | [] → [val] | Message value |
| CALLDATALOAD | 0x35 | 3 | [i] → [data] | Load 32 bytes from calldata |
| CALLDATASIZE | 0x36 | 2 | [] → [size] | Calldata size |
| CALLDATACOPY | 0x37 | 3* | [dstOff, srcOff, len] → [] | Copy calldata to memory |
| CODESIZE | 0x38 | 2 | [] → [size] | Code size |
| CODECOPY | 0x39 | 3* | [dstOff, srcOff, len] → [] | Copy code to memory |
| GASPRICE | 0x3A | 2 | [] → [price] | Gas price |
| EXTCODESIZE | 0x3B | 100 | [addr] → [size] | External code size |
| EXTCODECOPY | 0x3C | 100* | [addr, dstOff, srcOff, len] → [] | Copy external code |
| RETURNDATASIZE | 0x3D | 2 | [] → [size] | Return data size |
| RETURNDATACOPY | 0x3E | 3* | [dstOff, srcOff, len] → [] | Copy return data |
| EXTCODEHASH | 0x3F | 100 | [addr] → [hash] | External code hash |

### 6.6 Block Information

| Opcode | Hex | Gas | Stack | Description |
|--------|-----|-----|-------|-------------|
| BLOCKHASH | 0x40 | 20 | [num] → [hash] | Block hash (last 256) |
| COINBASE | 0x41 | 2 | [] → [addr] | Block miner address |
| TIMESTAMP | 0x42 | 2 | [] → [time] | Block timestamp |
| NUMBER | 0x43 | 2 | [] → [num] | Block number |
| DIFFICULTY | 0x44 | 2 | [] → [diff] | Block difficulty |
| GASLIMIT | 0x45 | 2 | [] → [limit] | Block gas limit |
| CHAINID | 0x46 | 2 | [] → [id] | Chain ID |
| SELFBALANCE | 0x47 | 5 | [] → [bal] | Current contract balance |
| BASEFEE | 0x48 | 2 | [] → [fee] | Base fee |

### 6.7 Stack, Memory, Storage

| Opcode | Hex | Gas | Stack | Description |
|--------|-----|-----|-------|-------------|
| POP | 0x50 | 2 | [a] → [] | Remove top item |
| MLOAD | 0x51 | 3* | [off] → [val] | Load 32 bytes from memory |
| MSTORE | 0x52 | 3* | [off, val] → [] | Store 32 bytes to memory |
| MSTORE8 | 0x53 | 3* | [off, val] → [] | Store 1 byte to memory |
| SLOAD | 0x54 | 50 | [key] → [val] | Load from storage |
| SSTORE | 0x55 | ** | [key, val] → [] | Store to storage |
| JUMP | 0x56 | 8 | [dest] → [] | Jump to destination |
| JUMPI | 0x57 | 10 | [dest, cond] → [] | Conditional jump |
| PC | 0x58 | 2 | [] → [pc] | Program counter |
| MSIZE | 0x59 | 2 | [] → [size] | Memory size |
| GAS | 0x5A | 2 | [] → [gas] | Remaining gas |
| JUMPDEST | 0x5B | 1 | [] → [] | Jump destination marker |

*Plus memory expansion cost
**SSTORE: 5000-20000 depending on operation

### 6.8 Push Operations

| Opcode | Hex | Gas | Description |
|--------|-----|-----|-------------|
| PUSH0 | 0x5F | 2 | Push 0 (Shanghai only) |
| PUSH1 | 0x60 | 3 | Push 1-byte value |
| PUSH2 | 0x61 | 3 | Push 2-byte value |
| ... | ... | 3 | ... |
| PUSH32 | 0x7F | 3 | Push 32-byte value |

### 6.9 Duplication Operations

| Opcode | Hex | Gas | Description |
|--------|-----|-----|-------------|
| DUP1 | 0x80 | 3 | Duplicate 1st stack item |
| DUP2 | 0x81 | 3 | Duplicate 2nd stack item |
| ... | ... | 3 | ... |
| DUP16 | 0x8F | 3 | Duplicate 16th stack item |

### 6.10 Exchange Operations

| Opcode | Hex | Gas | Description |
|--------|-----|-----|-------------|
| SWAP1 | 0x90 | 3 | Swap 1st and 2nd items |
| SWAP2 | 0x91 | 3 | Swap 1st and 3rd items |
| ... | ... | 3 | ... |
| SWAP16 | 0x9F | 3 | Swap 1st and 17th items |

### 6.11 Logging Operations

| Opcode | Hex | Gas | Description |
|--------|-----|-----|-------------|
| LOG0 | 0xA0 | 375* | Log with 0 topics |
| LOG1 | 0xA1 | 750* | Log with 1 topic |
| LOG2 | 0xA2 | 1125* | Log with 2 topics |
| LOG3 | 0xA3 | 1500* | Log with 3 topics |
| LOG4 | 0xA4 | 1875* | Log with 4 topics |

*Plus 8 × data_size + memory expansion

### 6.12 System Operations

| Opcode | Hex | Gas | Description |
|--------|-----|-----|-------------|
| CREATE | 0xF0 | 32000 | Create contract |
| CALL | 0xF1 | 100* | Call contract |
| CALLCODE | 0xF2 | 100* | Call with own storage |
| RETURN | 0xF3 | 0** | Return data |
| DELEGATECALL | 0xF4 | 100* | Delegate call |
| CREATE2 | 0xF5 | 32000 | Create with salt |
| STATICCALL | 0xFA | 100* | Static call (read-only) |
| REVERT | 0xFD | 0** | Revert with data |
| INVALID | 0xFE | all | Invalid instruction |
| SELFDESTRUCT | 0xFF | 5000 | Destroy contract |

*Plus various dynamic costs
**Plus memory expansion

### 6.13 Control Flow

```
Control Flow Opcodes:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STOP (0x00)     - Halt successfully, no return data
JUMP (0x56)     - Unconditional jump to JUMPDEST
JUMPI (0x57)    - Conditional jump (if condition ≠ 0)
JUMPDEST (0x5B) - Valid jump destination marker
RETURN (0xF3)   - Halt and return data
REVERT (0xFD)   - Halt, revert state, return data
INVALID (0xFE)  - Consume all gas, revert

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

[↑ Back to Table of Contents](#table-of-contents)

---

## 7. Gas Schedule

### 7.1 Base Gas Costs

| Name | Value | Used By |
|------|-------|---------|
| G_zero | 0 | STOP, RETURN, REVERT |
| G_base | 2 | ADDRESS, ORIGIN, CALLER, CALLVALUE, CALLDATASIZE, CODESIZE, GASPRICE, COINBASE, TIMESTAMP, NUMBER, DIFFICULTY, GASLIMIT, CHAINID, RETURNDATASIZE, POP, PC, MSIZE, GAS, PUSH0 |
| G_verylow | 3 | ADD, SUB, NOT, LT, GT, SLT, SGT, EQ, ISZERO, AND, OR, XOR, BYTE, SHL, SHR, SAR, CALLDATALOAD, MLOAD, MSTORE, MSTORE8, PUSH*, DUP*, SWAP* |
| G_low | 5 | MUL, DIV, SDIV, MOD, SMOD, SIGNEXTEND, SELFBALANCE |
| G_mid | 8 | ADDMOD, MULMOD, JUMP |
| G_high | 10 | JUMPI |

### 7.2 Dynamic Gas Costs

| Operation | Formula |
|-----------|---------|
| EXP | 10 + 50 × byte_size(exponent) |
| SHA3 | 30 + 6 × ceil(size/32) + mem_expansion |
| CALLDATACOPY | 3 + 3 × ceil(size/32) + mem_expansion |
| CODECOPY | 3 + 3 × ceil(size/32) + mem_expansion |
| EXTCODECOPY | 100 + 3 × ceil(size/32) + mem_expansion |
| LOG{0-4} | 375 × (topics+1) + 8 × size + mem_expansion |

### 7.3 Memory Expansion

Memory expansion cost grows quadratically:

```
G_memory(size) = 3 × words + words² ÷ 512

where words = ceil(size / 32)
```

| Size | Words | Cost |
|------|-------|------|
| 32 | 1 | 3 |
| 64 | 2 | 6 |
| 256 | 8 | 24 |
| 1024 | 32 | 98 |
| 4096 | 128 | 416 |

### 7.4 Storage Costs

| Operation | Condition | Gas |
|-----------|-----------|-----|
| SLOAD | Any | 50 (100 cold) |
| SSTORE | Zero → Non-zero | 20000 |
| SSTORE | Non-zero → Non-zero | 5000 |
| SSTORE | Non-zero → Zero | 5000 (+ 15000 refund) |
| SSTORE | Zero → Zero | 5000 |

[↑ Back to Table of Contents](#table-of-contents)

---

# Part III: Security Tools

---

## 8. MUTANT - Mutation Testing

### 8.1 What is Mutation Testing?

Mutation testing evaluates **test suite quality** by:

1. Creating small changes (mutations) in source code
2. Running tests against each mutant
3. Measuring how many mutants are detected (killed)

```
Mutation Testing Flow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Original Code        Mutation           Test Result
  ─────────────        ────────           ───────────

  if a < b:      →    if a <= b:    →    KILLED ✓
                                          (test fails)

  x = a + b      →    x = a - b     →    KILLED ✓
                                          (test fails)

  MAX = 1024     →    MAX = 1023    →    SURVIVED ✗
                                          (tests pass!)
                                          ↓
                                    Missing test coverage!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Mutation Score:**
```
                    Killed Mutants
Mutation Score = ─────────────────── × 100%
                    Total Mutants
```

### 8.2 Mutation Operators

MUTANT provides 8 EVM-specific mutation operators:

| Operator | Description | Example |
|----------|-------------|---------|
| **arithmetic_swap** | Swap arithmetic operators | `a + b` → `a - b` |
| **comparison_swap** | Swap comparison operators | `a < b` → `a >= b` |
| **off_by_one** | Modify constants by ±1 | `1024` → `1023` |
| **gas_cost** | Double or halve gas costs | `G_SLOAD = 50` → `100` |
| **logic_negate** | Negate boolean conditions | `if x:` → `if not x:` |
| **return_value** | Change return values | `return True` → `False` |
| **boundary_change** | Modify boundary constants | `2**256 - 1` → `2**256 - 2` |
| **constant_change** | Change magic numbers | `32` → `31` |

**Operator Details:**

```
arithmetic_swap:
  + ↔ -
  * ↔ /
  % ↔ /

comparison_swap:
  <  ↔ >=
  >  ↔ <=
  == ↔ !=

off_by_one:
  n → n+1
  n → n-1

gas_cost:
  G = n → G = 2n
  G = n → G = n/2
```

### 8.3 Running MUTANT

```bash
# Basic mutation testing
spectre mutant run --fork frontier

# With options
spectre mutant run \
    --fork shanghai \
    --source-dir src/ethereum/shanghai \
    --max-mutants 100 \
    --output reports/mutation.json

# Quick mode (sampling)
spectre mutant run --fork frontier --quick

# List available operators
spectre mutant list-operators
```

### 8.4 Interpreting Results

**Score Ratings:**

| Score | Rating | Interpretation |
|-------|--------|----------------|
| 95%+ | Excellent | Comprehensive test coverage |
| 80-94% | Good | Minor gaps, address survivors |
| 60-79% | Moderate | Significant testing needed |
| <60% | Poor | Major test suite gaps |

**Survivor Analysis:**

When mutants survive, analyze why:

1. **Missing test**: No test covers this code path
2. **Weak assertion**: Test runs but doesn't check result
3. **Equivalent mutant**: Mutation doesn't change behavior

### 8.5 Best Practices

1. **Run regularly**: Include in CI/CD pipeline
2. **Address survivors**: Each survivor indicates a test gap
3. **Focus on critical code**: Prioritize security-sensitive modules
4. **Combine with coverage**: Use both metrics together

[↑ Back to Table of Contents](#table-of-contents)

---

## 9. PHANTOM - Differential Fuzzing

### 9.1 What is Differential Fuzzing?

Differential fuzzing detects bugs by comparing behavior across implementations:

```
Differential Fuzzing Flow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌──────────────┐
                    │  Bytecode    │
                    │  Generator   │
                    └──────┬───────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      ┌────────────┐              ┌────────────┐
      │  Frontier  │              │  Shanghai  │
      │    EVM     │              │    EVM     │
      └─────┬──────┘              └─────┬──────┘
            │                           │
            ▼                           ▼
      ┌────────────┐              ┌────────────┐
      │  Result A  │              │  Result B  │
      │            │              │            │
      │ success: T │              │ success: F │
      │ gas: 100   │              │ gas: 0     │
      └─────┬──────┘              └─────┬──────┘
            │                           │
            └───────────┬───────────────┘
                        │
                        ▼
                 ┌────────────┐
                 │  Compare   │
                 │            │
                 │ DIVERGENCE │ ← Potential bug!
                 └────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 9.2 Bytecode Generation Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **random** | Random byte sequences | Robustness, crash detection |
| **grammar** | Syntactically valid EVM | Valid execution paths |
| **boundary** | Boundary value testing | Edge cases |
| **opcode_focused** | Target specific opcodes | EIP-specific testing |
| **sequence** | Known opcode patterns | Regression testing |

**Grammar-Based Generation:**

```
Program    ::= Instruction* Terminator
Instruction ::= Push | Arithmetic | Memory | Storage | Control
Push       ::= PUSH1 byte | PUSH2 byte byte | ... | PUSH32 bytes
Arithmetic ::= ADD | SUB | MUL | DIV | MOD | EXP | ...
Memory     ::= MLOAD | MSTORE | MSTORE8
Storage    ::= SLOAD | SSTORE
Control    ::= JUMP | JUMPI | JUMPDEST
Terminator ::= STOP | RETURN | REVERT | INVALID
```

### 9.3 Running PHANTOM

```bash
# Basic differential fuzzing
spectre phantom run --fork-a frontier --fork-b shanghai --count 1000

# With specific strategy
spectre phantom run \
    --fork-a homestead \
    --fork-b shanghai \
    --strategy grammar \
    --count 5000 \
    --seed 42

# Minimize divergent input
spectre phantom minimize 5f00 --fork-a frontier --fork-b shanghai
```

### 9.4 Divergence Types

| Type | Severity | Description |
|------|----------|-------------|
| **SUCCESS_MISMATCH** | Critical | Different success/failure |
| **RETURN_DATA_MISMATCH** | High | Different return data |
| **GAS_USED_MISMATCH** | Medium | Different gas consumption |
| **LOGS_MISMATCH** | High | Different events emitted |
| **STATE_MISMATCH** | Critical | Different final state |

**Expected vs Unexpected:**

```
Expected Divergence:
  Bytecode: 0x5F00 (PUSH0, STOP)
  Frontier: FAIL (invalid opcode 0x5F)
  Shanghai: SUCCESS (PUSH0 is valid)
  Status: EXPECTED (EIP-3855 change)

Unexpected Divergence:
  Bytecode: 0x600160020100
  Frontier: Result = 3
  Shanghai: Result = 4  ← BUG!
  Status: UNEXPECTED
```

### 9.5 Delta Debugging

When a divergence is found, PHANTOM minimizes the input:

```
Delta Debugging (ddmin):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input: 5f 60 01 60 02 01 52 60 20 60 00 f3
       ↓ Split in half

Test 1: 5f 60 01 60 02 01  → Diverges? Yes
        ↓ Split again

Test 2: 5f 60 01           → Diverges? No
Test 3: 60 02 01           → Diverges? No

        ↓ Try complements

Test 4: 5f 60 02 01        → Diverges? Yes
        ↓ Continue...

Result: 5f 00              → Minimal diverging input!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

[↑ Back to Table of Contents](#table-of-contents)

---

## 10. ADVERSARY - Test Generation

### 10.1 Adversarial Testing

ADVERSARY generates comprehensive test cases targeting:

- Boundary conditions
- Edge cases
- Specification ambiguities
- Fork transitions

```
ADVERSARY Pipeline:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌────────────────┐
  │   EIP Spec     │  "PUSH0 pushes 0 to stack, costs 2 gas"
  └───────┬────────┘
          │
          ▼
  ┌────────────────┐
  │   Analyzer     │  Extract: opcodes, gas, values, contexts
  └───────┬────────┘
          │
          ▼
  ┌────────────────┐
  │   Strategies   │  Boundary, Interaction, Gas, Fork, Stack
  └───────┬────────┘
          │
          ▼
  ┌────────────────┐
  │   Generator    │  Create test cases for each strategy
  └───────┬────────┘
          │
          ▼
  ┌────────────────┐
  │   Test Suite   │  JSON / EEST format output
  └────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 10.2 Test Strategies

| Strategy | Focus | Test Cases Generated |
|----------|-------|---------------------|
| **BOUNDARY** | Input values | 0, 1, 255, 256, MAX-1, MAX |
| **OPCODE_INTERACTION** | Opcode combinations | PUSH0+ADD, PUSH0+MSTORE, etc. |
| **CALL_CONTEXT** | Call types | Direct, CALL, DELEGATECALL, STATICCALL |
| **GAS_EXHAUSTION** | Gas limits | Exact gas, insufficient, in loops |
| **FORK_BOUNDARY** | Fork transitions | Pre-fork fail, post-fork success |
| **STACK_DEPTH** | Stack limits | Near 1024 depth limit |

**Strategy Details:**

```
BOUNDARY Strategy:
  Values tested: 0, 1, 2, 255, 256, 32767, 32768, 65535, 65536,
                 2³²-1, 2³², 2⁶⁴-1, 2⁶⁴, 2¹²⁸-1, 2¹²⁸,
                 2²⁵⁵-1, 2²⁵⁵, 2²⁵⁶-1

OPCODE_INTERACTION Strategy:
  • Stack operations: DUP, SWAP after target opcode
  • Memory operations: MSTORE result
  • Control flow: JUMPI with result as condition
  • Arithmetic: Use result in calculations

GAS_EXHAUSTION Strategy:
  • Exact gas: Just enough to complete
  • Insufficient: One gas unit short
  • Loop: Repeat until out of gas
```

### 10.3 Running ADVERSARY

```bash
# List known EIPs
spectre adversary list-eips

# Generate for specific EIP
spectre adversary generate --eip 3855 --output fixtures/

# Generate with specific strategies
spectre adversary generate \
    --eip 3855 \
    --strategy boundary \
    --strategy gas \
    --output fixtures/

# Analyze EIP
spectre adversary analyze --eip 3855

# Generate for all EIPs
spectre adversary generate-all --output fixtures/
```

### 10.4 Output Formats

**JSON Format:**

```json
{
  "eip_number": 3855,
  "eip_title": "PUSH0 instruction",
  "generated_at": "2024-01-01T00:00:00Z",
  "test_cases": [
    {
      "name": "boundary_PUSH0_0",
      "strategy": "BOUNDARY",
      "bytecode": "5f00",
      "gas_limit": 1000000,
      "expected_success": true,
      "expected_gas_used": 2,
      "description": "Test PUSH0 with boundary value 0"
    }
  ]
}
```

**EEST Format (Ethereum Execution Spec Tests):**

```json
{
  "boundary_PUSH0_0": {
    "env": {
      "currentNumber": "0x1",
      "currentGasLimit": "0xf4240",
      "currentTimestamp": "0x1"
    },
    "pre": {
      "0x1000000000000000000000000000000000000001": {
        "balance": "0xf4240",
        "code": "0x5f00",
        "nonce": "0x0",
        "storage": {}
      }
    },
    "transaction": {
      "to": "0x1000000000000000000000000000000000000001",
      "gasLimit": "0xf4240",
      "data": "0x"
    }
  }
}
```

### 10.5 Known EIPs

| EIP | Title | Fork | Opcodes |
|-----|-------|------|---------|
| 2 | Homestead Hard-fork | Homestead | CREATE |
| 7 | DELEGATECALL | Homestead | DELEGATECALL |
| 211 | RETURNDATASIZE/COPY | Byzantium | RETURNDATASIZE, RETURNDATACOPY |
| 3855 | PUSH0 instruction | Shanghai | PUSH0 |
| 3860 | Limit and meter initcode | Shanghai | - |

[↑ Back to Table of Contents](#table-of-contents)

---

# Part IV: API Reference

---

## 11. Core Types API

### 11.1 U256

256-bit unsigned integer with modular arithmetic:

```python
from ethereum.common.types import U256, MAX_U256

# Creation
a = U256(100)
b = U256(2**256 - 1)  # Maximum value

# Arithmetic (mod 2^256)
c = a + b  # Wraps on overflow
d = a * b
e = a - b  # Wraps on underflow

# Comparison
a < b
a == b

# Constants
MAX_U256  # 2^256 - 1
```

### 11.2 Address

20-byte Ethereum address:

```python
from ethereum.common.types import Address, ZERO_ADDRESS

# Creation
addr = Address(b"\x00" * 19 + b"\x01")
addr = Address(bytes.fromhex("0000000000000000000000000000000000000001"))

# Constants
ZERO_ADDRESS  # 0x0000...0000
```

### 11.3 Account

Account state:

```python
from ethereum.common.types import Account

account = Account(
    nonce=0,
    balance=10**18,
    code=b"\x60\x01",
    storage={0: 100, 1: 200}
)

# Access
account.nonce
account.balance
account.code
account.storage
```

### 11.4 State

World state management:

```python
from ethereum.common.types import State

state = State()

# Account operations
state.set_account(address, account)
state.get_account(address)

# Balance
state.set_balance(address, amount)
state.get_balance(address)

# Nonce
state.increment_nonce(address)
state.get_nonce(address)

# Code
state.set_code(address, bytecode)
state.get_code(address)

# Storage
state.set_storage(address, key, value)
state.get_storage(address, key)

# Copy (for transaction isolation)
new_state = state.copy()
```

### 11.5 Transaction

```python
from ethereum.common.types import Transaction

tx = Transaction(
    sender=sender_address,
    to=recipient_address,      # None for contract creation
    value=1000000000,
    data=b"",
    gas=100000,
    gas_price=20000000000,
    nonce=0,
)
```

### 11.6 Environment

Block execution environment:

```python
from ethereum.common.types import Environment

env = Environment(
    caller=address,
    origin=address,
    block_hashes={},
    coinbase=miner_address,
    number=1000000,
    gas_limit=10000000,
    gas_price=20,
    timestamp=1600000000,
    difficulty=1000000,
    chain_id=1,
    base_fee=0,
)
```

### 11.7 Message

Internal call message:

```python
from ethereum.common.types import Message

message = Message(
    caller=caller_address,
    target=target_address,
    value=0,
    data=b"",
    gas=100000,
    depth=0,
    code=bytecode,
    is_create=False,
)
```

### 11.8 ExecutionResult

Execution outcome:

```python
from ethereum.common.types import ExecutionResult

result = ExecutionResult(
    success=True,
    gas_used=21000,
    gas_remaining=79000,
    return_data=b"",
    logs=[],
    error=None,
    created_address=None,
)

# Access
result.success
result.gas_used
result.return_data
result.logs
result.error
```

[↑ Back to Table of Contents](#table-of-contents)

---

## 12. EVM Execution API

### 12.1 Interpreter

```python
from ethereum.frontier.vm.interpreter import Interpreter
from ethereum.homestead.vm.interpreter import HomesteadInterpreter
from ethereum.shanghai.vm.interpreter import ShanghaiInterpreter

# Create interpreter
interpreter = ShanghaiInterpreter(state, env)

# Execute message
result = interpreter.execute(message)

# Check result
if result.success:
    print(f"Gas used: {result.gas_used}")
    print(f"Return: {result.return_data.hex()}")
else:
    print(f"Error: {result.error}")
```

### 12.2 Stack

```python
from ethereum.frontier.vm.stack import Stack

stack = Stack()

# Operations
stack.push(value)
value = stack.pop()
value = stack.peek(n)  # n-th from top
stack.dup(n)           # Duplicate n-th
stack.swap(n)          # Swap top with n-th

# Limits
Stack.MAX_DEPTH  # 1024
```

### 12.3 Memory

```python
from ethereum.frontier.vm.memory import Memory

memory = Memory()

# Operations
memory.store(offset, value)      # 32 bytes
memory.store8(offset, value)     # 1 byte
value = memory.load(offset)      # 32 bytes
data = memory.load_range(offset, size)

# Size
size = memory.size()

# Gas calculation
gas = memory.expansion_cost(new_size)
```

### 12.4 State Transition

```python
from ethereum.frontier.fork import state_transition
from ethereum.shanghai.fork import state_transition as shanghai_transition

# Execute transaction
new_state, result = state_transition(state, transaction, env)

# With Shanghai rules
new_state, result = shanghai_transition(state, transaction, env)
```

[↑ Back to Table of Contents](#table-of-contents)

---

## 13. Security Tools API

### 13.1 MUTANT API

```python
from spectre.mutant.operators import get_all_operators
from spectre.mutant.engine import MutationEngine

# List operators
operators = get_all_operators()
for op in operators:
    print(f"{op.name}: {op.description}")

# Generate mutations
for op in operators:
    mutations = op.generate(source_code)
    for mutation in mutations:
        print(f"Line {mutation.line}: {mutation.original} → {mutation.mutated}")

# Run mutation testing
engine = MutationEngine(
    source_dir="src/ethereum/frontier",
    test_command="pytest tests/frontier -x",
)

results = engine.run(max_mutants=100)
print(f"Score: {results.score:.1f}%")
```

### 13.2 PHANTOM API

```python
from spectre.phantom.generator import BytecodeGenerator
from spectre.phantom.executor import DifferentialExecutor, Fork

# Generate bytecode
generator = BytecodeGenerator()

# Single generation
bytecode = next(generator.generate(count=1))
print(f"Generated: {bytecode.code.hex()}")

# Batch generation
for bytecode in generator.generate(count=100):
    print(bytecode.code.hex())

# With specific strategy
for bytecode in generator.generate(count=100, strategy="grammar"):
    print(bytecode.code.hex())

# Differential execution
executor = DifferentialExecutor(Fork.FRONTIER, Fork.SHANGHAI)

# Single execution
trace = executor.execute_single(bytecode.code, Fork.SHANGHAI)
print(f"Success: {trace.result.success}")

# Differential comparison
divergences = executor.execute_differential(bytecode)
for div in divergences:
    print(f"Divergence: {div.description}")
    print(f"Expected: {div.is_expected()}")
```

### 13.3 ADVERSARY API

```python
from spectre.adversary.analyzer import EIPAnalyzer
from spectre.adversary.generator import TestGenerator
from pathlib import Path

# Analyze EIP
analyzer = EIPAnalyzer()
eip = analyzer.get_eip(3855)

print(f"EIP-{eip.number}: {eip.title}")
print(f"Opcodes: {eip.opcodes}")
print(f"Gas changes: {eip.gas_changes}")

# List all EIPs
for eip_num in analyzer.list_eips():
    eip = analyzer.get_eip(eip_num)
    print(f"EIP-{eip.number}: {eip.title}")

# Generate tests
generator = TestGenerator()
suite = generator.generate_for_eip(3855)

print(f"Generated {len(suite.test_cases)} tests")

# Save to file
generator.save_test_suite(suite, Path("fixtures/"), format="json")
generator.save_test_suite(suite, Path("fixtures/"), format="eest")

# Generate for all EIPs
all_suites = generator.generate_all()
for eip_num, suite in all_suites.items():
    print(f"EIP-{eip_num}: {len(suite.test_cases)} tests")
```

[↑ Back to Table of Contents](#table-of-contents)

---

# Part V: CLI Reference

---

## 14. Command Line Interface

### 14.1 Global Commands

```bash
spectre --help                    # Show help
spectre --version                 # Show version
spectre info                      # Show SPECTRE information
```

### 14.2 MUTANT Commands

```bash
# Run mutation testing
spectre mutant run [OPTIONS]

Options:
  --fork [frontier|homestead|shanghai]  Target fork (default: frontier)
  --source-dir PATH                     Source directory to mutate
  --test-dir PATH                       Test directory
  --max-mutants INT                     Maximum mutants to test
  --output PATH                         Output file for report
  --html                                Generate HTML report
  --quick                               Quick mode (sampling)

# Examples
spectre mutant run --fork frontier
spectre mutant run --fork shanghai --max-mutants 50 --output report.json
spectre mutant run --fork frontier --quick

# List operators
spectre mutant list-operators
```

### 14.3 PHANTOM Commands

```bash
# Run differential fuzzing
spectre phantom run [OPTIONS]

Options:
  --fork-a [frontier|homestead|shanghai]  First fork (default: frontier)
  --fork-b [frontier|homestead|shanghai]  Second fork (default: shanghai)
  --count INT                             Number of test cases (default: 100)
  --strategy [random|grammar|boundary|opcode_focused|sequence|all]
  --seed INT                              Random seed for reproducibility
  --output PATH                           Output file for results

# Examples
spectre phantom run --fork-a frontier --fork-b shanghai --count 1000
spectre phantom run --strategy grammar --count 500 --seed 42

# Minimize divergent input
spectre phantom minimize BYTECODE [OPTIONS]

Options:
  --fork-a, --fork-b                      Forks to compare

# Example
spectre phantom minimize 5f6001016000f3 --fork-a frontier --fork-b shanghai
```

### 14.4 ADVERSARY Commands

```bash
# List known EIPs
spectre adversary list-eips

# Analyze EIP
spectre adversary analyze --eip INT

# Generate test cases
spectre adversary generate [OPTIONS]

Options:
  --eip INT                               EIP number (required)
  --output PATH                           Output directory
  --format [json|eest|both]               Output format (default: both)
  --strategy [boundary|interaction|context|gas|fork|stack|all]

# Examples
spectre adversary generate --eip 3855 --output fixtures/
spectre adversary generate --eip 3855 --format eest --strategy boundary
spectre adversary analyze --eip 3855

# Generate for all EIPs
spectre adversary generate-all --output fixtures/
```

[↑ Back to Table of Contents](#table-of-contents)

---

# Part VI: Advanced Topics

---

## 15. Security Analysis

### 15.1 Threat Model

**Assets:**

| Asset | Value | Impact if Compromised |
|-------|-------|----------------------|
| User funds | Billions USD | Direct financial loss |
| Network consensus | Critical | Chain split, double-spend |
| Smart contract logic | Per-contract | Exploit, theft |
| Transaction privacy | Moderate | Front-running |

**Threat Actors:**

| Actor | Capability | Motivation | Target |
|-------|------------|------------|--------|
| Script kiddies | Low | Fame | Easy exploits |
| MEV searchers | Medium | Profit | Arbitrage |
| DeFi hackers | High | $$$$ | Protocol bugs |
| Nation states | Very high | Strategic | Infrastructure |

### 15.2 Attack Vectors

**1. Opcode Implementation Bugs**

```
Attack: Exploit incorrect opcode behavior
Example: ADDMOD overflow before modulo
Impact: Incorrect cryptographic operations
Defense: MUTANT arithmetic operators
```

**2. Gas Mispricing**

```
Attack: DoS via underpriced operations
Example: 2016 Shanghai attacks (EXTCODESIZE)
Impact: Network degradation
Defense: MUTANT gas cost operators
```

**3. Fork Boundary Exploits**

```
Attack: Exploit behavior changes at forks
Example: PUSH0 availability post-Shanghai
Impact: Unexpected contract behavior
Defense: PHANTOM differential fuzzing
```

**4. Specification Ambiguity**

```
Attack: Exploit different interpretations
Example: EIP-2 CREATE failure semantics
Impact: Client divergence
Defense: ADVERSARY edge case generation
```

### 15.3 Defense Strategies

**Defense-in-Depth:**

```
Layer 1: Unit Tests          (basic coverage)
    │
    ▼
Layer 2: MUTANT              (test quality)
    │
    ▼
Layer 3: PHANTOM             (divergence detection)
    │
    ▼
Layer 4: ADVERSARY           (edge cases)
    │
    ▼
Layer 5: Manual Audit        (expert review)
```

**SPECTRE Coverage Matrix:**

| Threat | MUTANT | PHANTOM | ADVERSARY |
|--------|--------|---------|-----------|
| Opcode bugs | ✓✓✓ | ✓ | ✓✓ |
| Gas errors | ✓✓✓ | ✓ | ✓ |
| Fork boundaries | ✓ | ✓✓✓ | ✓✓ |
| Edge cases | ✓ | ✓ | ✓✓✓ |
| Spec ambiguity | - | ✓✓ | ✓✓✓ |

[↑ Back to Table of Contents](#table-of-contents)

---

## 16. Performance

### 16.1 Benchmarks

**EVM Execution:**

| Metric | Value |
|--------|-------|
| Throughput | 13,424 tx/s |
| Per execution | 0.074 ms |
| Memory usage | ~5 MB |

**Differential Fuzzing:**

| Metric | Value |
|--------|-------|
| Throughput | 11,083 tests/s |
| Per iteration | 0.090 ms |
| Divergence detection | 100% |

**Test Generation:**

| Metric | Value |
|--------|-------|
| Throughput | 88,319 tests/s |
| Per EIP | 0.4 ms |
| Tests per EIP | 33 |

**Test Suite:**

| Metric | Value |
|--------|-------|
| Total tests | 181 |
| Execution time | 0.30 s |
| Coverage | 64% |

### 16.2 Scalability

| Fuzzing Iterations | Time | Memory |
|--------------------|------|--------|
| 100 | 0.009s | 5 MB |
| 1,000 | 0.090s | 8 MB |
| 10,000 | 0.900s | 15 MB |
| 100,000 | 9.0s | 20 MB |

### 16.3 Optimization Tips

1. **Use parallel execution:**
   ```bash
   pytest tests/ -n auto
   ```

2. **Quick mode for iteration:**
   ```bash
   spectre mutant run --quick
   ```

3. **Seed for reproducibility:**
   ```bash
   spectre phantom run --seed 42
   ```

4. **Focus on specific modules:**
   ```bash
   spectre mutant run --source-dir src/ethereum/shanghai
   ```

[↑ Back to Table of Contents](#table-of-contents)

---

## 17. Project Structure

### 17.1 Directory Layout

```
spectre/
├── src/
│   ├── ethereum/                    # miniEELS Core
│   │   ├── __init__.py
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   └── types.py             # Core types (2000+ lines)
│   │   ├── frontier/
│   │   │   ├── __init__.py
│   │   │   ├── fork.py              # State transition
│   │   │   └── vm/
│   │   │       ├── __init__.py
│   │   │       ├── stack.py         # Stack (1024 depth)
│   │   │       ├── memory.py        # Memory (expansion)
│   │   │       ├── gas.py           # Gas schedule
│   │   │       └── interpreter.py   # Opcodes (1100+ lines)
│   │   ├── homestead/
│   │   │   ├── __init__.py
│   │   │   ├── fork.py
│   │   │   └── vm/
│   │   │       ├── __init__.py
│   │   │       └── interpreter.py   # EIP-2 changes
│   │   └── shanghai/
│   │       ├── __init__.py
│   │       ├── fork.py
│   │       └── vm/
│   │           ├── __init__.py
│   │           └── interpreter.py   # EIP-3855 PUSH0
│   │
│   └── spectre/                     # Security Toolkit
│       ├── __init__.py
│       ├── cli.py                   # Click CLI (500+ lines)
│       ├── mutant/
│       │   ├── __init__.py
│       │   ├── operators.py         # 8 operators
│       │   ├── engine.py            # Mutation engine
│       │   └── report.py            # Reporting
│       ├── phantom/
│       │   ├── __init__.py
│       │   ├── generator.py         # 5 strategies
│       │   ├── executor.py          # Differential exec
│       │   └── minimizer.py         # Delta debugging
│       └── adversary/
│           ├── __init__.py
│           ├── analyzer.py          # EIP analysis
│           ├── strategies.py        # 6 strategies
│           └── generator.py         # Test generation
│
├── tests/
│   ├── conftest.py                  # Fixtures
│   ├── frontier/
│   │   ├── test_arithmetic.py       # 24 tests
│   │   ├── test_control_flow.py     # 18 tests
│   │   ├── test_gas.py              # 24 tests
│   │   ├── test_stack_ops.py        # 17 tests
│   │   ├── test_state_transition.py # 10 tests
│   │   └── test_storage.py          # 12 tests
│   ├── homestead/
│   │   └── test_eip2.py             # 11 tests
│   ├── shanghai/
│   │   └── test_eip3855_push0.py    # 14 tests
│   └── spectre/
│       ├── test_adversary.py        # 22 tests
│       ├── test_mutant.py           # 12 tests
│       └── test_phantom.py          # 17 tests
│
├── docs/
│   └── DOCUMENTATION.md             # This file
│
├── manuscript/
│   └── REFERENCES.md                # Bibliography
│
├── fixtures/                        # Generated test fixtures
├── reports/                         # Generated reports
│
├── pyproject.toml                   # Project configuration
├── requirements.txt                 # Dependencies
├── requirements-dev.txt             # Dev dependencies
├── .gitignore                       # Git ignore
├── LICENSE                          # MIT License
└── README.md                        # Main README
```

### 17.2 Code Statistics

| Component | Files | Lines |
|-----------|-------|-------|
| miniEELS Core | 15 | ~3,500 |
| MUTANT | 3 | ~400 |
| PHANTOM | 3 | ~500 |
| ADVERSARY | 3 | ~600 |
| CLI | 1 | ~500 |
| Tests | 11 | ~2,000 |
| **Total** | **36** | **~7,500** |

[↑ Back to Table of Contents](#table-of-contents)

---

## 18. Contributing

### 18.1 Development Setup

```bash
# Navigate to project directory
cd spectre

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Verify setup
pytest tests/ -v
ruff check src/
mypy src/
```

### 18.2 Code Style

- **Formatter:** Ruff
- **Linter:** Ruff
- **Type checker:** mypy (strict)
- **Line length:** 100 characters

```bash
# Format code
ruff format src/ tests/

# Check linting
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Type checking
mypy src/
```

### 18.3 Testing Guidelines

1. **Every feature needs tests**
2. **Aim for >80% coverage**
3. **Use descriptive test names**
4. **Test edge cases**

```python
class TestPush0Opcode:
    """Tests for EIP-3855 PUSH0 opcode."""

    def test_push0_pushes_zero_to_stack(self):
        """PUSH0 should push 0 onto the stack."""
        code = bytes([0x5F, 0x00])  # PUSH0, STOP
        result = execute(code)
        assert result.success
        assert result.gas_used == 2

    def test_push0_cheaper_than_push1_zero(self):
        """PUSH0 should cost less than PUSH1 0x00."""
        push0_gas = execute(bytes([0x5F, 0x00])).gas_used
        push1_gas = execute(bytes([0x60, 0x00, 0x00])).gas_used
        assert push0_gas < push1_gas
```

### 18.4 Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Run tests: `pytest tests/ -v`
5. Run linting: `ruff check src/`
6. Commit: `git commit -m "Add my feature"`
7. Push: `git push origin feature/my-feature`
8. Open Pull Request

[↑ Back to Table of Contents](#table-of-contents)

---

# Appendices

---

## Appendix A: Formal Semantics

### A.1 State Transition Function

```
Ξ: State × Transaction × Environment → State × Result

Given:
  σ = World state
  T = Transaction
  E = Environment

Then:
  (σ', R) = Ξ(σ, T, E)

Where:
  σ' = New world state
  R  = Execution result (gas used, logs, return data)
```

### A.2 Opcode Semantics

```
⟦ω⟧: MachineState → MachineState ∪ {⊥}

Where:
  MachineState = (stack, memory, gas, pc, ...)
  ⊥ = Exceptional halt

Example (ADD):
  ⟦ADD⟧(S, μ, g, pc) = {
    (S' ∪ {a + b mod 2²⁵⁶}, μ, g - 3, pc + 1)  if g ≥ 3 ∧ |S| ≥ 2
    ⊥                                            otherwise
  }
  where {a, b} ∪ S' = S

Example (PUSH0):
  ⟦PUSH0⟧(S, μ, g, pc) = {
    (S ∪ {0}, μ, g - 2, pc + 1)  if g ≥ 2 ∧ |S| < 1024
    ⊥                             otherwise
  }
```

### A.3 Gas Calculation

```
G(operation) = G_base(operation) + G_dynamic(operation, args)

Memory expansion:
  G_memory(size) = 3 × ⌈size/32⌉ + ⌊⌈size/32⌉² / 512⌋

Storage:
  G_sstore(current, new) = {
    20000  if current = 0 ∧ new ≠ 0
    5000   if current ≠ 0 ∧ new ≠ 0
    5000   if current ≠ 0 ∧ new = 0  (+ 15000 refund)
  }
```

[↑ Back to Table of Contents](#table-of-contents)

---

## Appendix B: EIP Reference

| EIP | Title | Fork | Status |
|-----|-------|------|--------|
| 2 | Homestead Hard-fork Changes | Homestead | Final |
| 7 | DELEGATECALL | Homestead | Final |
| 100 | Change difficulty adjustment | Homestead | Final |
| 140 | REVERT instruction | Byzantium | Final |
| 145 | Bitwise shifting | Constantinople | Final |
| 150 | Gas cost changes | Tangerine Whistle | Final |
| 155 | Simple replay attack protection | Spurious Dragon | Final |
| 211 | RETURNDATASIZE, RETURNDATACOPY | Byzantium | Final |
| 214 | STATICCALL | Byzantium | Final |
| 1014 | Skinny CREATE2 | Constantinople | Final |
| 1052 | EXTCODEHASH | Constantinople | Final |
| 1283 | Net gas metering for SSTORE | Istanbul | Final |
| 1344 | ChainID opcode | Istanbul | Final |
| 2200 | Structured definitions for SSTORE | Istanbul | Final |
| 2565 | ModExp gas cost | Berlin | Final |
| 2718 | Typed transaction envelope | Berlin | Final |
| 2929 | Gas cost increases | Berlin | Final |
| 2930 | Access lists | Berlin | Final |
| 3198 | BASEFEE opcode | London | Final |
| 3529 | Reduction in refunds | London | Final |
| 3541 | Reject new contracts starting with 0xEF | London | Final |
| 3607 | Reject txs from senders with deployed code | London | Final |
| 3855 | PUSH0 instruction | Shanghai | Final |
| 3860 | Limit and meter initcode | Shanghai | Final |

[↑ Back to Table of Contents](#table-of-contents)

---

## Appendix C: Bibliography

### Core References

1. **Wood, G.** (2014). "Ethereum: A Secure Decentralised Generalised Transaction Ledger." *Ethereum Yellow Paper*.

2. **Hildenbrandt, E., et al.** (2018). "KEVM: A Complete Formal Semantics of the Ethereum Virtual Machine." *IEEE CSF*.

3. **Luu, L., et al.** (2016). "Making Smart Contracts Smarter." *ACM CCS*.

4. **Jia, Y. and Harman, M.** (2011). "An Analysis and Survey of the Development of Mutation Testing." *IEEE TSE*.

5. **McKeeman, W.** (1998). "Differential Testing for Software." *Digital Technical Journal*.

6. **Zeller, A. and Hildebrandt, R.** (2002). "Simplifying and Isolating Failure-Inducing Input." *IEEE TSE*.

### Additional Resources

- Ethereum Foundation. *Execution Specification Tests*. https://github.com/ethereum/execution-spec-tests
- Ethereum Foundation. *Execution Specs*. https://github.com/ethereum/execution-specs
- Ethereum Improvement Proposals. https://eips.ethereum.org/

[↑ Back to Table of Contents](#table-of-contents)

---

## Appendix D: Glossary

| Term | Definition |
|------|------------|
| **Account** | An entity with balance, nonce, code, and storage |
| **Bytecode** | Compiled EVM instructions |
| **Calldata** | Input data sent with a transaction |
| **Contract** | Account with non-empty code |
| **EIP** | Ethereum Improvement Proposal |
| **EOA** | Externally Owned Account (controlled by private key) |
| **EVM** | Ethereum Virtual Machine |
| **Fork** | Protocol upgrade with rule changes |
| **Gas** | Unit measuring computational work |
| **Gwei** | 10⁹ wei (0.000000001 ETH) |
| **Mutation** | Small code change for testing |
| **Nonce** | Transaction counter for an account |
| **Opcode** | Single EVM instruction |
| **State** | All account data on the blockchain |
| **Storage** | Persistent key-value store for contracts |
| **Transaction** | Signed message triggering state change |
| **Wei** | Smallest ETH unit (10⁻¹⁸ ETH) |

[↑ Back to Table of Contents](#table-of-contents)

---

<p align="center">
<strong>SPECTRE Documentation</strong><br>
Version 1.0<br>
<br>
Anik Tahabilder<br>
PhD Candidate, Department of Computer Science<br>
Wayne State University<br>
<br>
MIT License
</p>
