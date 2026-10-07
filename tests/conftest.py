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
import os
import subprocess

import pytest

from utils.artifact import head_commit

# The `project-id` every test runs with, unless it sets or removes `INPUT_PROJECT_ID` itself.
TEST_PROJECT_ID = "test-project"


@pytest.fixture(autouse=True)
def _set_github_output_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_OUTPUT", os.fspath(tmp_path / "github_output.txt"))


@pytest.fixture(autouse=True)
def _set_project_id_env(monkeypatch):
    # No action input leaks in from the shell, so every input a test does not set reads as its default.
    for name in [name for name in os.environ if name.startswith("INPUT_")]:
        monkeypatch.delenv(name)
    # `project-id` is required: every collector reads it to build `metadata.source.project_id`.
    monkeypatch.setenv("INPUT_PROJECT_ID", TEST_PROJECT_ID)


@pytest.fixture(autouse=True)
def _clear_head_commit_cache():
    # `head_commit` caches each checkout's HEAD for the run; a test must not see another test's checkout.
    head_commit.cache_clear()


def _git(directory, *args) -> str:
    return subprocess.run(
        ["git", "-C", os.fspath(directory), *args], capture_output=True, check=True, text=True
    ).stdout.strip()


@pytest.fixture(name="git_checkout")
def _git_checkout():
    """Turn a directory into a real git checkout with one commit, and return its HEAD sha."""

    def make(directory) -> str:
        directory.mkdir(parents=True, exist_ok=True)
        _git(directory, "init", "-q")
        _git(
            directory,
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "--no-verify",
            "--allow-empty",
            "-m",
            "init",
        )
        return _git(directory, "rev-parse", "HEAD")

    return make
