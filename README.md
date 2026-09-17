# Auto'd (`autod`)

> Autonomous repository synthesizer powered by frontier LLMs that invents, develops, verifies, and publishes a brand-new, production-ready open-source project every 2 days.

[![Synthesize Schedule](https://github.com/Raj123-0/autod/actions/workflows/synthesize.yml/badge.svg)](https://github.com/Raj123-0/autod/actions/workflows/synthesize.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

---

## What is Auto'd?

**Auto'd** is an autonomous engineering bot designed to continuously expand the user's open-source portfolio. Every 48 hours, Auto'd:

1. **Brainstorms** a novel, mathematically rigorous or systems-level project concept tailored to the user's domain interests (Aerospace, Orbital Mechanics, Hamiltonian Physics, Computational Math, Systems/Compilers, and Cryptography).
2. **Cross-references** all existing repositories under the user's profile (`Raj123-0`) to ensure 0 duplicates.
3. **Synthesizes** full multi-file codebases with type hints, modular architecture, mathematical foundations, and comprehensive `pytest` test suites (no stubs or placeholders).
4. **Verifies** in a local sandbox: AST parsing + automated unit tests with self-healing iterations.
5. **Provisions** the repository via GitHub API, commits all files to `main`, adds topic tags, and logs the new project to [`SHOWCASE.md`](SHOWCASE.md).

---

## Architectural Workflow

```
[Every 2 Days (cron)] ──▶ [Ideator (Checks 60+ Repos)] 
                                  │
                                  ▼
                    [Synthesizer (Gemini 2.5 Flash)]
                     • Core Algorithms (src/)
                     • Pytest Test Suite (tests/)
                     • LaTeX Math Documentation (README.md)
                     • CI Configuration (.github/workflows/)
                                  │
                                  ▼
                    [Sandbox Verifier]
                     • AST Syntax Tree Check
                     • Isolated Pytest Execution
                     • Self-Healing Debug Loop (if any test fails)
                                  │
                                  ▼ (100% Passing)
                    [GitHub Publisher]
                     • Creates https://github.com/Raj123-0/<repo>
                     • Pushes Verified Commit
                     • Updates SHOWCASE.md & created_repos.json
```

---

## Target Technical Domains

- **Aerospace & Orbital Mechanics**: Keplerian state propagation, Lambert trajectory targeting, coordinate frame transformations.
- **Computational Physics & Simulation**: Symplectic phase-space preserving integrators, N-body gravitational solvers, lattice Boltzmann fluids.
- **Computational Mathematics**: Continued fraction expansions, lattice reduction, high-precision root finding, Diophantine solvers.
- **Systems & Compilers**: Stack-based virtual machines, bytecode interpreters, instruction set simulators.
- **Cryptographic Primitives**: Shamir threshold secret sharing, verifiable delay functions, lattice cryptography.

---

## Local CLI Usage

### Dry-Run Simulation
Simulates full ideation, multi-file code synthesis, and sandboxed AST/pytest verification without publishing:
```bash
python main.py --dry-run
```

### Target a Specific Domain
```bash
python main.py --domain aerospace_orbital --dry-run
```

### Export Generated Project Locally
```bash
python main.py --dry-run --output-dir ./generated_projects
```

---

## Configuration

Model settings and domain topics are managed in [`config.json`](config.json):
- **Primary Model**: Google Gemini 2.5 Flash (`gemini-2.5-flash`) via `LLM_API_KEY` (1,000,000 TPM limit, 15 RPM, 1M context window).
- **Fallback Models**: Groq Llama 3.3 70B, Mistral Codestral, and Kilo AI keyless zero-auth fallback.

---

## License

MIT License © 2026 [Raj123-0](https://github.com/Raj123-0).
