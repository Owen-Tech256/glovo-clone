import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
TOKENS = (APP / "static/css/tokens.css").read_text()
BASE_CSS = (APP / "static/css/base.css").read_text()

EXPECTED_TOKENS = [
    "color-brand", "color-brand-hover", "color-brand-soft",
    "color-text", "color-text-muted", "color-surface", "color-page", "color-border",
    "color-success", "color-warning", "color-danger", "color-info",
    "font-body", "font-size-xs", "font-size-sm", "font-size-md", "font-size-lg", "font-size-xl", "font-size-display",
    "space-1", "space-2", "space-3", "space-4", "space-6", "space-8", "space-12",
    "radius-sm", "radius-md", "radius-lg", "radius-pill", "shadow-card",
    "content-max", "header-height",
]
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")


def token(name: str) -> str:
    return re.search(rf"--{name}:\s*(#[0-9A-Fa-f]{{6}})", TOKENS).group(1)


def luminance(hex_colour: str) -> float:
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(token(a)), luminance(token(b))), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# F-15
def test_base_layout_structure(client):
    html = client.get("/does-not-exist").get_data(as_text=True)
    assert '<html lang="en">' in html
    assert 'name="viewport"' in html
    assert 'class="skip-link" href="#main"' in html
    assert '<main id="main"' in html
    assert "<title>Page not found" in html


def test_flash_partial_labels_status_in_text(client):
    html = client.get("/_test/flash").get_data(as_text=True)
    assert "Success:" in html and "Saved it" in html
    assert "Warning:" in html and "Careful now" in html
    assert 'role="alert"' in html and 'role="status"' in html


# F-16
def test_tokens_are_served_and_complete(client):
    response = client.get("/static/css/tokens.css")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for name in EXPECTED_TOKENS:
        assert f"--{name}:" in body, f"missing token --{name}"


def test_base_css_uses_tokens_not_raw_colours():
    assert not re.search(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(", BASE_CSS)


# F-17
@pytest.mark.parametrize("path", sorted(p for p in APP.rglob("*") if p.suffix in {".html", ".css", ".js"}))
def test_no_gradients_or_emoji(path):
    text = path.read_text()
    assert "gradient(" not in text.lower()
    assert not EMOJI.search(text)


# F-18
@pytest.mark.parametrize(
    "foreground, background",
    [
        ("color-text", "color-surface"), ("color-text", "color-page"), ("color-text", "color-brand-soft"),
        ("color-text-muted", "color-surface"), ("color-text-muted", "color-page"),
        ("color-brand", "color-surface"), ("color-brand", "color-page"), ("color-brand", "color-brand-soft"),
        ("color-brand-hover", "color-surface"),
        ("color-surface", "color-brand"), ("color-surface", "color-brand-hover"),
        ("color-success", "color-surface"), ("color-success", "color-page"),
        ("color-warning", "color-surface"), ("color-warning", "color-page"),
        ("color-danger", "color-surface"), ("color-danger", "color-page"),
        ("color-info", "color-surface"), ("color-info", "color-page"),
    ],
)
def test_token_pairs_meet_wcag_aa_for_text(foreground, background):
    assert contrast(foreground, background) >= 4.5


# F-32
def test_focus_and_reduced_motion_rules_exist():
    assert ":focus-visible" in BASE_CSS
    assert "prefers-reduced-motion: reduce" in BASE_CSS


# F-33
@pytest.mark.parametrize("path", sorted((APP / "templates").rglob("*.html")))
def test_templates_have_no_inline_styles(path):
    assert not re.search(r"\sstyle\s*=", path.read_text(), re.IGNORECASE)
