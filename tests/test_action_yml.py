#
# Copyright 2025 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
The `action.yml` promises a caller relies on: the action brings its own venv, writes nothing into the
caller's environment, and rejects an unsupported Python with one actionable error.

The integration workflow can prove the version check *fails*, but a composite action's step log is not
readable from a later workflow step, so the message itself is pinned here - otherwise a refactor to a bare
`exit 1` would regress the only guidance a caller gets, with every job still green.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_YML = REPO_ROOT / "action.yml"

PYTHON_FLOOR_ERROR = (
    "::error::living-doc-collector-gh needs Python >= 3.10 on PATH. Add actions/setup-python before this step."
)


def test_an_unsupported_python_fails_with_the_documented_one_line_error():
    # Assert: the exact string README's Prerequisites section promises.
    assert PYTHON_FLOOR_ERROR in ACTION_YML.read_text(encoding="utf-8")


def test_the_version_floor_matches_the_one_the_project_requires():
    # Assert: the guard tests the same floor `pyproject.toml` declares, so the docs name one number.
    assert "sys.version_info >= (3, 10)" in ACTION_YML.read_text(encoding="utf-8")
    assert 'requires-python = ">=3.10"' in (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")


@pytest.mark.parametrize("leak", ["GITHUB_ENV", "GITHUB_PATH"])
def test_the_action_writes_nothing_into_the_callers_environment(leak):
    # Assert: every input is passed in the run step's own `env:`; nothing is exported to the job.
    code = [
        line.split("#", 1)[0] for line in ACTION_YML.read_text(encoding="utf-8").splitlines()
    ]
    assert not [line for line in code if leak in line]


def test_the_action_installs_into_its_own_venv_and_never_the_runners_interpreter():
    # Assert: pip is always the venv's own, so no install reaches whatever interpreter the caller had.
    code = [line.split("#", 1)[0].strip() for line in ACTION_YML.read_text(encoding="utf-8").splitlines()]
    installs = [line for line in code if "pip" in line and "install" in line]
    assert installs == ['"$VENV/bin/pip" install -r "${{ github.action_path }}/requirements.txt"']
