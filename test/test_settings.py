# Copyright 2026 SURF, GÉANT.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the shell settings."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.shell.settings import Settings


def test_history_file_defaults_to_the_home_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default history file lives in the home directory and is expanded."""
    monkeypatch.delenv("ORCHESTRATOR_SHELL_HISTFILE", raising=False)

    settings = Settings(_env_file=None)

    assert settings.ORCHESTRATOR_SHELL_HISTFILE == Path("~/.orchestrator_shell_history").expanduser()
    assert "~" not in str(settings.ORCHESTRATOR_SHELL_HISTFILE)


def test_history_size_defaults_to_a_thousand(monkeypatch: pytest.MonkeyPatch) -> None:
    """The history keeps the last thousand commands by default."""
    monkeypatch.delenv("ORCHESTRATOR_SHELL_HISTFILE_SIZE", raising=False)

    assert Settings(_env_file=None).ORCHESTRATOR_SHELL_HISTFILE_SIZE == 1000


def test_environment_overrides_the_history_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Both settings can be set through their documented environment variables."""
    history_file = tmp_path / "other_history"
    monkeypatch.setenv("ORCHESTRATOR_SHELL_HISTFILE", str(history_file))
    monkeypatch.setenv("ORCHESTRATOR_SHELL_HISTFILE_SIZE", "42")

    settings = Settings(_env_file=None)

    assert settings.ORCHESTRATOR_SHELL_HISTFILE == history_file
    assert settings.ORCHESTRATOR_SHELL_HISTFILE_SIZE == 42


def test_an_invalid_history_size_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-numeric history size fails validation instead of being accepted silently."""
    monkeypatch.setenv("ORCHESTRATOR_SHELL_HISTFILE_SIZE", "many")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
