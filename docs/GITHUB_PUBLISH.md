# GitHub Publish Guide

Target repository:

```text
https://github.com/EdgeAdaptics/BingoMate
```

The local `origin` remote should point to `https://github.com/EdgeAdaptics/BingoMate.git`. The remote repository exists and already has a `main` branch, so prefer a branch and pull request instead of force-pushing over existing history.

## Publish Branch

```powershell
git remote set-url origin https://github.com/EdgeAdaptics/BingoMate.git
git fetch origin main
git switch -c edgeadaptics/bingomate-product-scaffold origin/main
git checkout main -- .
git add .
git commit -m "Design BingoMate edge AI companion"
git push -u origin edgeadaptics/bingomate-product-scaffold
```

Then open a pull request into `main`.

## Direct Push

Use only when you intentionally want to update `main` directly:

```powershell
git remote set-url origin https://github.com/EdgeAdaptics/BingoMate.git
git push -u origin main
```

If Git rejects the push as non-fast-forward, do not force-push unless the existing remote history has been reviewed.

## Pre-Publish Checks

```powershell
python -m compileall bingomate edge_lab scripts
python scripts\self_test.py
python scripts\preflight_publish.py
```

The preflight should pass before publishing.
