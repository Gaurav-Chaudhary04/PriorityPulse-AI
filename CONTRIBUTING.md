# Contributing to PriorityPulse-AI

This repository is organized for collaborative development across three contributors.
Use this guide to keep contributions consistent, traceable, and review-ready.

## Branch Naming
- `main` - production-ready code only.
- `feature/gaurav-backend` - backend and database work.
- `feature/ichcha-ai` - AI, NLP, scoring, and explainability.
- `feature/bk-frontend` - dashboard, tests, and documentation.

## Workflow
1. Sync `main` locally before starting work:
   ```bash
git switch main
git pull origin main
```
2. Create a feature branch:
   ```bash
git switch -c feature/<owner>-<scope>
```
3. Work on one feature or issue at a time.
4. Write clear commits and push frequently.
5. Open a pull request to `main` when ready.

## Commit Message Guidelines
Use Conventional Commits to keep history readable:
- `feat:` - new feature
- `fix:` - bug fix
- `docs:` - documentation only changes
- `test:` - adding or fixing tests
- `refactor:` - code changes that do not add features or fix bugs
- `style:` - formatting, no logic change

Example:
```bash
git commit -m "feat(api): add complaint analysis endpoint"
```

## Pull Request Requirements
- Target branch: `main`
- One or more reviewers from the team
- Include a short description of the change
- Reference the issue or task if available
- Confirm tests were run locally
- Prefer squash merging into `main`

## Testing
Run the included test script before creating a PR:
```bash
python test_api.py
```

## Documentation
- Add README updates for feature changes that affect setup or usage.
- Keep the `docs/` folder up to date with workflow decisions and architecture notes.
- If you change API behavior, update the endpoint documentation in `README.md`.

## Collaboration Tips
- Keep branches small and focused.
- If you need help, open an issue or tag a teammate.
- Review teammates' PRs promptly.
- Use comments to explain non-obvious logic.
