# Contributing to MasterBlaster

Thank you for helping build the Authorized Security Assessment Control Plane.

## Principles

1. Simulator-first until an explicit phase approves live capability.
2. Deny-by-default for unknown adapters, targets, and arguments.
3. The UI is never a trusted authorization boundary.
4. Every security-sensitive change needs tests and review per `docs/REVIEW_POLICY.md`.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
python main.py
```

## Branch Strategy

- `main` — stable integration
- `codex/*` — experimental control-plane work
- `feature/*` — focused feature branches (e.g. `feature/p0-continuation`)

## Pull Request Checklist

- [ ] `python -m pytest` passes
- [ ] `python scripts/validate_p0_registry.py` passes
- [ ] No live network transport or shell execution added without phase approval
- [ ] Security-sensitive paths documented in PR description
- [ ] Acceptance/phase tracker updated when criteria change

## Adding Adapters

1. Register a reviewed manifest in `masterblaster_control/runner_simulator.py`
2. Keep `network_access=False` until an approved phase
3. Add deterministic fixture or mock-transport behavior
4. Add tests in `tests/test_runner_simulator.py`

## Code Style

- Python 3.12+
- Prefer small, explicit modules over generic execution APIs
- Match existing naming and dataclass patterns in `masterblaster_control/`