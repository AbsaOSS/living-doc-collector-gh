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
`utilities`' golden scenario file (tests/fixtures/golden/gherkin/scenario-bodies.feature) run through the full
`ui-tests` collector: each scenario in `ui-tests.json` equals the parser's expected scenario, except the
`scenario_id` and `source_ref` the collector adds.
"""

import json
from pathlib import Path

import pytest
from living_doc_utilities.contracts.io import read_artifact

from ui_tests.collector import GHUITestsCollector

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "golden"


@pytest.fixture(name="head_sha")
def _head_sha(tmp_path, git_checkout):
    return git_checkout(tmp_path / "repo")


@pytest.fixture(name="ui_tests_artifact")
def _ui_tests_artifact(tmp_path, mocker, head_sha):
    # The golden `gherkin/` folder also holds the `doc-source` corpus, so the one scenario file is scanned on its own,
    # in a git checkout (`head_sha`) so that its `source_ref.url` resolves.
    scan_dir = tmp_path / "repo" / "features"
    scan_dir.mkdir()
    (scan_dir / "scenario-bodies.feature").write_text(
        (GOLDEN_DIR / "gherkin" / "scenario-bodies.feature").read_text(encoding="utf-8"), encoding="utf-8"
    )
    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[
            {"organization-name": "AbsaOSS", "repository-name": "living-doc-collector-gh", "paths": [str(scan_dir)]}
        ],
    )
    assert GHUITestsCollector(str(tmp_path / "output")).collect() is True
    return read_artifact(tmp_path / "output" / "ui-tests" / "ui-tests.json", "ui-tests")


def test_golden_scenarios_come_through_the_collector_unchanged_except_id_and_source_ref(ui_tests_artifact):
    # Arrange
    expected = json.loads((GOLDEN_DIR / "expected" / "scenario-bodies.json").read_text(encoding="utf-8"))

    # Act
    actual = [
        scenario.model_dump(mode="json", exclude={"scenario_id", "source_ref"})
        for scenario in ui_tests_artifact.scenarios
    ]

    # Assert: a `Rule:` with its own `Background:`, a DataTable, a DocString and a Scenario Outline with two
    # `Examples:` blocks, the tag line above one of them in neither the steps nor the tags.
    assert actual == expected
    assert ui_tests_artifact.warnings == []


def test_source_ref_url_still_points_at_the_file_and_line_locates_the_scenario(ui_tests_artifact, head_sha):
    # Arrange
    file_url = f"https://github.com/AbsaOSS/living-doc-collector-gh/blob/{head_sha}/features/scenario-bodies.feature"

    # Assert: every scenario of the file shares the file's permalink; a consumer links one as `<url>#L<line>`.
    assert [(s.source_ref.url, s.line) for s in ui_tests_artifact.scenarios] == [(file_url, 8), (file_url, 25)]
