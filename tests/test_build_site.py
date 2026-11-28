import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "build_site", Path(__file__).resolve().parents[1] / "tools" / "build_site.py"
)
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)


def test_lists_get_a_blank_line_and_nested_items_get_four_spaces():
    text = "So:\n- one\n  - nested\n- two\n\n```\n- not a list\n```"
    out = build_site.markdown_for_mkdocs(text)
    assert out == "So:\n\n- one\n    - nested\n- two\n\n```\n- not a list\n```"


def test_links_between_pages_follow_the_site_layout():
    text = "[report](../reports/05-run-window.md) and [code](../src/breathe_check/daily.py)"
    out = build_site.rewrite(text, "docs/calendar.md", "about/calendar.md")
    assert "(../findings/05-run-window.md)" in out
    assert (
        "(https://github.com/Anushkajoshii/breathe-check/blob/main/src/breathe_check/daily.py)"
        in out
    )


def test_chart_links_point_into_the_findings_folder():
    out = build_site.rewrite(
        "![c](figures/10_grap_three_steps.png)",
        "reports/03-did-grap-work.md",
        "findings/03-did-grap-work.md",
    )
    assert out == "![c](figures/10_grap_three_steps.png)"
