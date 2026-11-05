# Contributing to VarhadAgro

Thanks for helping improve VarhadAgro, a crop-yield prediction model and web app for Vidarbha, Maharashtra. This document covers setup, conventions, and pull-request expectations.

## Code of Conduct

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report unacceptable behavior to ishan.vaidya01@gmail.com.

## Getting Started

1. Fork the repository and clone your fork.
2. Follow the setup instructions in [README.md](README.md#quick-start) (Python 3.10+, Flask, scikit-learn).
3. Create a branch from `main`:

   ```bash
   git checkout -b feat/season-feature-expansion
   # or
   git checkout -b fix/prediction-rounding
   ```

## Development Checks

Run these before opening a pull request:

```bash
pip install -r requirements.txt
python model.py   # trains, evaluates, and prints sample predictions
python train.py   # evaluation and testing script
python app.py     # start the Flask app and exercise / and /predict
```

- Include the printed Train/Test R², MAE, and RMSE in your PR if the model or data changed.
- The dataset contains 2,035 records covering 8 districts, 7 crops, and Kharif/Rabi seasons; preserve the CSV schema when appending data.

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat: add heatwave-day trend feature
fix: validate area input range before prediction
refactor: move feature engineering into model.py
docs: document the /predict response schema
chore: pin pandas version range
```

The subject should be in the imperative mood and under ~72 characters.

## Coding Guidelines

- Keep `model.py` framework-light (pure Python + scikit-learn) so it stays testable without the web app.
- Validate all numeric inputs in `/predict` before inference.
- Scale model behavior changes with evidence: rerun evaluation and quote both old and new metrics.
- Never commit `.env`, credentials, or generated model artifacts unless they are part of the design.

## Pull Request Checklist

- [ ] The change is focused on one problem.
- [ ] `python model.py` and `python train.py` run cleanly.
- [ ] Metrics are quoted before/after for model or data changes.
- [ ] `/predict` input validation covers the new code path.
- [ ] No secrets or large generated files are included.
- [ ] The PR description explains the change, motivation, and results.

## Reporting Bugs and Requesting Features

Use the GitHub issue templates. Include steps to reproduce, expected vs. actual yield outputs, and the exact input payload.

## Security

Do not open public issues for security problems. Follow [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the project's [MIT License](LICENSE).
