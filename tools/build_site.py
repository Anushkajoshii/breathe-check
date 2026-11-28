"""Assemble the report website from the write-ups and docs, then build it with MkDocs.

    uv run --group site python tools/build_site.py          # build into site_build/
    uv run --group site python tools/build_site.py --serve  # preview at http://127.0.0.1:8000

The write-ups (reports/) and docs (docs/, reference/) stay where they are in the
repo. This script copies them into .site_src/ with a site layout:

    index.md                 home page (tools/site_home.md)
    findings/                the five write-ups and their charts
    about/                   data card, cleaning rules, calendar, daily update, ADRs

Links between pages are rewritten for the new layout. Links to anything that isn't
on the site (code, CSV files) point to the file on GitHub instead.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".site_src"
GITHUB = "https://github.com/Anushkajoshii/breathe-check/blob/main/"

# repo path -> site path
PAGES = {
    "tools/site_home.md": "index.md",
    "reports/01-first-look.md": "findings/01-first-look.md",
    "reports/02-weather-adjusted.md": "findings/02-weather-adjusted.md",
    "reports/03-did-grap-work.md": "findings/03-did-grap-work.md",
    "reports/04-indore.md": "findings/04-indore.md",
    "reports/05-run-window.md": "findings/05-run-window.md",
    "docs/data-card.md": "about/data-card.md",
    "docs/cleaning-rules.md": "about/cleaning-rules.md",
    "reference/README.md": "about/reference-dates.md",
    "docs/calendar.md": "about/calendar.md",
    "docs/daily-update.md": "about/daily-update.md",
    "docs/deploy-web.md": "about/deploy-web.md",
}
for adr in sorted((ROOT / "docs" / "adr").glob("*.md")):
    PAGES[f"docs/adr/{adr.name}"] = f"about/adr/{adr.name}"

LINK = re.compile(r"(!?\[[^\]]*\])\(([^)\s]+)\)")


def rewrite(text: str, repo_path: str, site_path: str) -> str:
    here = (ROOT / repo_path).parent
    site_here = (SRC / site_path).parent

    def fix(match: re.Match) -> str:
        label, target = match.group(1), match.group(2)
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            return match.group(0)  # full URLs and same-page anchors stay
        path, _, anchor = target.partition("#")
        resolved = (here / path).resolve()
        try:
            rel_repo = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            return match.group(0)
        if rel_repo in PAGES:
            new = Path(PAGES[rel_repo])
            out = Path(_relpath(SRC / new, site_here))
        elif rel_repo.startswith("reports/figures/"):
            out = Path(_relpath(SRC / "findings" / "figures" / resolved.name, site_here))
        else:
            kind = "tree" if resolved.is_dir() else "blob"
            return f"{label}({GITHUB.replace('/blob/', f'/{kind}/')}{rel_repo})"
        return f"{label}({out.as_posix()}{'#' + anchor if anchor else ''})"

    return LINK.sub(fix, text)


LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s")


def markdown_for_mkdocs(text: str) -> str:
    """GitHub is forgiving about lists; MkDocs's Markdown is not. Two fixes, site only:
    - a list needs a blank line before it when it follows a sentence
    - nested list items need 4 spaces per level, not 2
    Code blocks are left alone."""
    out, in_code = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code:
            m = LIST_ITEM.match(line)
            if m:
                indent = len(m.group(1))
                if indent:
                    line = " " * (indent * 2) + line.lstrip()
                prev = out[-1] if out else ""
                if prev.strip() and not LIST_ITEM.match(prev) and not prev.startswith(" "):
                    out.append("")
        out.append(line)
    return "\n".join(out)


def _relpath(target: Path, start: Path) -> str:
    import os

    return os.path.relpath(target, start)


def assemble() -> None:
    if SRC.exists():
        shutil.rmtree(SRC)
    for repo_path, site_path in PAGES.items():
        text = (ROOT / repo_path).read_text()
        out = SRC / site_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown_for_mkdocs(rewrite(text, repo_path, site_path)))
    shutil.copytree(ROOT / "reports" / "figures", SRC / "findings" / "figures")
    shutil.copy(ROOT / "web" / "public" / "icon.svg", SRC / "icon.svg")
    demo = ROOT / "reports" / "demo.gif"
    if demo.exists():
        shutil.copy(demo, SRC / "demo.gif")


def main() -> None:
    assemble()
    cmd = ["mkdocs", "serve"] if "--serve" in sys.argv else ["mkdocs", "build", "--strict"]
    sys.exit(subprocess.call(cmd, cwd=ROOT))


if __name__ == "__main__":
    main()
