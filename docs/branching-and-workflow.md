# Branching and Team Workflow

This document describes how the PriorityPulse-AI team should divide work and keep the repository organized.

## Team Responsibilities
- **Gaurav**: Backend and database ownership
  - Improve FastAPI routes
  - Stabilize SQLAlchemy models and persistence
  - Add validation and error handling

- **Ichcha**: AI/NLP ownership
  - Enhance the NLP preprocessing pipeline
  - Improve rule-based analysis and scoring
  - Refine explainability output

- **BK**: Frontend, testing, and documentation ownership
  - Improve `dashboard.html`
  - Add meaningful tests and validation cases
  - Update `README.md`, `CONTRIBUTING.md`, and workflow docs

## Branch Strategy
Use these branches as the primary active work zones:
- `main`
- `feature/gaurav-backend`
- `feature/ichcha-ai`
- `feature/bk-frontend`

### Branch rules
- Do not commit directly to `main`.
- Keep each feature branch focused on one scope.
- Rebase or merge from `main` before opening a PR.

## Feature Branch Life Cycle
1. Create branch from `main`
2. Implement a single coherent feature or improvement
3. Commit frequently with clean messages
4. Push to remote
5. Open a PR into `main`
6. Request review from at least one teammate
7. Squash merge after approval

## Merge Order Recommendation
1. Backend work first (`feature/gaurav-backend`)
2. AI and scoring work second (`feature/ichcha-ai`)
3. Dashboard/tests/docs last (`feature/bk-frontend`)

## Evaluation Optimization
Before merging into `main`, ensure:
- All three contributors have visible work in separate PRs
- `README.md` and `CONTRIBUTING.md` are updated
- Tests pass locally
- Commit messages are descriptive and consistent
- The resulting `main` branch is clean and easy to read
