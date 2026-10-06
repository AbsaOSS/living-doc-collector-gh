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
R12 check 3 for `ui-tests`: the collector runs over a fully authored fixture, and every contract field
has non-zero occupancy except those in `NOT_PRODUCED`, each with the reason GitHub source files cannot fill it.
"""

from pathlib import Path

import pytest
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.schema_export import field_occupancy_paths
from living_doc_utilities.contracts.ui_tests import RECORD_ROOTS, UITestsResult

from ui_tests.collector import GHUITestsCollector

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "full_sample" / "ui_tests"

_NO_AZURE_DEVOPS = "Azure DevOps classification node; a GitHub source file has none"

NOT_PRODUCED = {
    "scenarios[].source_ref.area_path": _NO_AZURE_DEVOPS,
    "scenarios[].source_ref.iteration_path": _NO_AZURE_DEVOPS,
}

# Envelope fields outside metadata.stats.field_occupancy that GitHub source files cannot fill.
NOT_PRODUCED_ENVELOPE = {
    "metadata.source.extraction_mode": "`markdown`/`field-map` is Azure DevOps' extraction mode; null for GitHub",
    "metadata.source_inputs": "a collector output carries no source inputs (R7); only a transform's does",
}


def _get(obj, dotted):
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


@pytest.fixture(name="artifact")
def _artifact(tmp_path, mocker, monkeypatch):
    for name, value in {
        "GITHUB_RUN_ID": "101",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_ACTOR": "octocat",
        "GITHUB_WORKFLOW": "living-doc",
        "GITHUB_REF": "refs/heads/master",
        "GITHUB_SHA": "0" * 40,
    }.items():
        monkeypatch.setenv(name, value)
    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[
            {
                "organization-name": "AbsaOSS",
                "repository-name": "living-doc-collector-gh",
                "paths": [str(FIXTURE_DIR)],
            }
        ],
    )
    assert GHUITestsCollector(str(tmp_path)).collect() is True
    return read_artifact(tmp_path / "ui-tests" / "ui-tests.json", "ui-tests")


def test_every_contract_field_outside_not_produced_is_occupied(artifact):
    # Arrange
    assert isinstance(artifact, UITestsResult)
    occupancy = artifact.metadata.stats.field_occupancy

    # Act
    empty = {path for path, count in occupancy.items() if count == 0}

    # Assert
    assert set(occupancy) == set(field_occupancy_paths(RECORD_ROOTS))
    assert empty - set(NOT_PRODUCED) == set(), "field loss: occupancy 0 on a field the fixture authors"
    assert set(NOT_PRODUCED) - empty == set(), "NOT_PRODUCED lists a field the collector does produce"


def test_every_envelope_field_outside_not_produced_is_set(artifact):
    # Arrange
    envelope_paths = [
        "metadata.producer.name",
        "metadata.producer.version",
        "metadata.producer.build",
        "metadata.producer.utilities_version",
        *(f"metadata.run.{field}" for field in ("run_id", "run_attempt", "actor", "workflow", "ref", "sha")),
        "metadata.source.project_id",
        "metadata.source.systems",
        "metadata.source.organizations",
        "metadata.source.repositories",
        "metadata.generated_at",
    ]

    # Act
    unset = [path for path in envelope_paths if _get(artifact, path) in (None, "", [])]

    # Assert
    assert unset == []
    assert all(_get(artifact, path) in (None, []) for path in NOT_PRODUCED_ENVELOPE)


def test_every_not_produced_entry_has_a_reason():
    # Assert
    assert {"scenarios[].source_ref.area_path", "scenarios[].source_ref.iteration_path"} <= NOT_PRODUCED.keys()
    assert "metadata.source.extraction_mode" in NOT_PRODUCED_ENVELOPE
    assert all(reason.strip() for reason in [*NOT_PRODUCED.values(), *NOT_PRODUCED_ENVELOPE.values()])


def test_full_sample_scenarios(artifact):
    # Assert: the `@tutorial` scenario is not mined; a Scenario Outline is.
    assert [s.title for s in artifact.scenarios] == [
        "Every extension is read on desktop",
        "Every extension is read on <device>",
    ]
    assert [(link.id, link.aspect) for link in artifact.scenarios[0].acceptance_criteria] == [
        ("US-901-01", "desktop"),
        ("US-901-02", None),
    ]
    assert artifact.warnings == []
