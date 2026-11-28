# ADR-006: Build the report site with MkDocs Material, not Quarto

**Status:** Accepted, November 2026

## Context

The plan was a Quarto website on GitHub Pages, holding the full write-up with charts. By the time we got here:
- the five write-ups were already plain Markdown files in `reports/`
- the charts were already PNG images made by the analysis code
- Quarto isn't a Python package: it's a separate program to install on every machine and in CI

## Decision

Use **MkDocs Material**:
- **It's a normal Python package,** so `uv sync --group site` installs it, locally and in CI, with no extra installer.
- **It reads the existing Markdown as it is.** `tools/build_site.py` copies the write-ups and docs into a site layout and fixes the links between them. Links to code point to GitHub.
- **It comes with search, light and dark themes, and diagrams.**
- **It builds with `--strict`,** so a broken link fails the build instead of shipping.
- **It's published by a GitHub Actions workflow** to GitHub Pages, on every push to `main` that changes the reports or docs. There's no `gh-pages` branch and no bot commits.

## What we give up

Quarto can run code inside the pages. We don't need that: the analysis scripts (`make figures`, `make grap`, ...) already produce the charts and numbers, and keeping the analysis out of the site keeps the site build fast and simple.

## Note for later

Material for MkDocs says it reaches end of life on 5 May 2027, with security fixes until then. Its makers' successor, Zensical, reads the same `mkdocs.yml`, so moving over later should be a small change.
