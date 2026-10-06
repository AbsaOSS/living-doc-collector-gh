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
R12 check 3 for `doc-source`: the collector runs over a fully authored fixture, and every contract field
has non-zero occupancy except those in `NOT_PRODUCED`, each with the reason GitHub source files cannot fill it.
"""

from pathlib import Path

import pytest
from living_doc_utilities.contracts.doc_source import RECORD_ROOTS, DocSourceResult
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.schema_export import field_occupancy_paths

from doc_source.collector import GHDocSourceCollector

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "full_sample" / "doc_source"

_NO_AZURE_DEVOPS = "Azure DevOps classification node; a GitHub source file has none"
_NO_LABELS = "the .feature-header and PageObject formats carry no labels; tags come from an issue's labels"
_NO_TIMESTAMPS = "a source file carries no created/updated/closed time; git history is not mined"
_NOT_A_FEATURE_FIELD = "a Feature-only field (PageObject header); this record type never carries it"
_NOT_A_FUNCTIONALITY_FIELD = "a Functionality-only field; this record type never carries it"
_NOT_A_US_FIELD = "a User Story-only field; this record type never carries it"
_NO_CRITERIA_ON_FEATURE = "a Feature owns no acceptance criteria and has no preconditions/not_in_scope keys"
_NO_DESCRIPTION_KEY = "the canon .feature header has no description key; the parser leaves `narrative` unset"

# Field (relative to the record, prefix match) -> reason, per record root.
_COMMON = {
    "source_ref.area_path": _NO_AZURE_DEVOPS,
    "source_ref.iteration_path": _NO_AZURE_DEVOPS,
    "tags[]": _NO_LABELS,
    "timestamps.": _NO_TIMESTAMPS,
}
_FEATURE_ONLY = {
    field: _NOT_A_FEATURE_FIELD
    for field in (
        "purpose",
        "surface_type",
        "owners[]",
        "user_stories[]",
        "functionalities[]",
        "external_dependencies[]",
        "feature_dependencies[]",
        "stub_reason",
        "wizard_steps[]",
        "pages[].",
    )
}
_NOT_PRODUCED_BY_ROOT = {
    "user_stories": {
        **_COMMON,
        **_FEATURE_ONLY,
        "narrative": _NO_DESCRIPTION_KEY,
        **{field: _NOT_A_FUNCTIONALITY_FIELD for field in ("parent", "func_type", "rationale")},
    },
    "functionalities": {
        **_COMMON,
        **_FEATURE_ONLY,
        "narrative": _NO_DESCRIPTION_KEY,
        "business_value[]": _NOT_A_US_FIELD,
    },
    "features": {
        **_COMMON,
        "narrative": "a Feature's description is `purpose`",
        "source": "the PageObject header has no `source:` key",
        "deprecated_at": "the PageObject header has no `deprecated_at:` key; a Feature's state is derived",
        "business_value[]": _NOT_A_US_FIELD,
        "acceptance_criteria[].": _NO_CRITERIA_ON_FEATURE,
        "preconditions[]": _NO_CRITERIA_ON_FEATURE,
        "not_in_scope[]": _NO_CRITERIA_ON_FEATURE,
        **{field: _NOT_A_FUNCTIONALITY_FIELD for field in ("parent", "func_type", "rationale")},
    },
}

# Envelope fields outside metadata.stats.field_occupancy that GitHub source files cannot fill.
NOT_PRODUCED_ENVELOPE = {
    "metadata.source.extraction_mode": "`markdown`/`field-map` is Azure DevOps' extraction mode; null for GitHub",
    "metadata.source_inputs": "a collector output carries no source inputs (R7); only a transform's does",
}


def _not_produced() -> dict[str, str]:
    """Every record path of the contract the fixture leaves empty on purpose, with its reason."""
    not_produced = {}
    for path in field_occupancy_paths(RECORD_ROOTS):
        root, field = path.split("[].", 1)
        for prefix, reason in _NOT_PRODUCED_BY_ROOT[root].items():
            if field == prefix or (prefix.endswith((".", "[].")) and field.startswith(prefix)):
                not_produced[path] = reason
    return not_produced


NOT_PRODUCED = _not_produced()


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
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "AbsaOSS",
                "repository-name": "living-doc-collector-gh",
                "us-paths": [str(FIXTURE_DIR / "us")],
                "func-paths": [str(FIXTURE_DIR / "func")],
                "pages-paths": [str(FIXTURE_DIR / "pages")],
            }
        ],
    )
    assert GHDocSourceCollector(str(tmp_path)).collect() is True
    return read_artifact(tmp_path / "doc-source" / "doc-source.json", "doc-source")


def test_every_contract_field_outside_not_produced_is_occupied(artifact):
    # Arrange
    assert isinstance(artifact, DocSourceResult)
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
    assert NOT_PRODUCED_ENVELOPE.keys() >= {"metadata.source.extraction_mode"}
    assert {"user_stories[].source_ref.area_path", "user_stories[].source_ref.iteration_path"} <= NOT_PRODUCED.keys()
    assert all(reason.strip() for reason in [*NOT_PRODUCED.values(), *NOT_PRODUCED_ENVELOPE.values()])


def test_full_sample_derives_state_and_resolves_every_relation(artifact):
    # Arrange
    by_id = {e.entity_id: e for e in [*artifact.user_stories, *artifact.features, *artifact.functionalities]}

    # Assert
    assert by_id["FEAT-901"].state == "active"
    assert by_id["FEAT-901"].state_origin == "derived"
    assert by_id["FEAT-901"].stub_reason == "Template carries no test-id attributes yet."
    assert [page.is_primary for page in by_id["FEAT-901"].pages] == [True, False]
    assert by_id["US-901"].acceptance_criteria[1].state == "active"  # authored with a non-canonical dash
    assert [(w.code, w.context) for w in artifact.warnings] == [
        ("FEATURE_WITHOUT_FUNCTIONALITY", "entity_id='FEAT-902'")
    ]
