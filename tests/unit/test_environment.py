import subprocess
import sys
from pathlib import Path

from app.config import ENV_VARS

ROOT = Path(__file__).resolve().parents[2]


# F-27
def test_pip_check_reports_no_broken_requirements():
    result = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def _example_variables() -> dict[str, str]:
    values = {}
    for line in (ROOT / ".env.example").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key] = value
    return values


# F-28
def test_env_example_lists_every_variable_the_config_reads():
    assert set(_example_variables()) == set(ENV_VARS)


def test_env_example_contains_placeholders_only():
    text = (ROOT / ".env.example").read_text()
    assert "dev-only-local" not in text
    assert "USER:PASSWORD" in text


def test_real_env_file_is_git_ignored():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()


def test_requirements_are_pinned():
    for name in ("requirements.txt", "requirements-dev.txt"):
        for line in (ROOT / name).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith(("#", "-r")):
                assert "==" in line, f"{name}: {line} is not pinned"
