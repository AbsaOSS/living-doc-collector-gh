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
`utilities`' golden source-code entities (tests/fixtures/golden/, copied at v0.5.0) run through the full
`doc-source` collector come out unchanged except `source_ref`: each entity in `doc-source.json` equals what
the canonical parsers plus `derive_statuses` produce for the same files.
"""

import json
from pathlib import Path

import pytest
from living_doc_utilities.authoring.feature_header import parse_feature_header
from living_doc_utilities.authoring.page_object import parse_page_object
from living_doc_utilities.authoring.status import derive_statuses
from living_doc_utilities.contracts.common import SourceRef
from living_doc_utilities.contracts.doc_entities import Entity
from living_doc_utilities.contracts.io import read_artifact

from doc_source.collector import GHDocSourceCollector

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "golden"

# Same shape as utilities' golden helper: a placeholder source_ref, dropped before comparing.
_DUMMY_SOURCE_REF = SourceRef(system="GitHub", native_id="1", native_type="dummy", url="", tracker_state="open")


def _read(*parts):
    return GOLDEN_DIR.joinpath(*parts).read_text(encoding="utf-8")


def _expected_entities() -> dict[str, dict]:
    """The golden entities as the canonical parsers alone produce them, as contract entities without source_ref."""
    parsed = [
        parse_feature_header(_read("gherkin", "liv_doc_us", "us-001-customer-login.feature"), "DocumentedUserStory")[0],
        parse_feature_header(
            _read("gherkin", "liv_doc_func", "func-001-validate-password-strength.feature"), "DocumentedFunctionality"
        )[0],
        parse_feature_header(
            _read("gherkin", "liv_doc_func", "func-002-reject-breached-password.feature"), "DocumentedFunctionality"
        )[0],
        parse_page_object(_read("pageobject", "LoginPage.ts"))[0].entity,
        parse_page_object(_read("pageobject", "RegistrationPage.ts"))[0].entity,
    ]
    derived, _warnings = derive_statuses(parsed)
    expected = {}
    for entity in derived:
        dumped = Entity(source_ref=_DUMMY_SOURCE_REF, **entity.model_dump()).model_dump(mode="json")
        del dumped["source_ref"]
        expected[entity.entity_id] = dumped
    return expected


@pytest.fixture(name="doc_source_json")
def _doc_source_json(tmp_path, mocker):
    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "AbsaOSS",
                "repository-name": "living-doc-collector-gh",
                "us-paths": [str(GOLDEN_DIR / "gherkin" / "liv_doc_us")],
                "func-paths": [str(GOLDEN_DIR / "gherkin" / "liv_doc_func")],
                "pages-paths": [str(GOLDEN_DIR / "pageobject")],
            }
        ],
    )
    assert GHDocSourceCollector(str(tmp_path)).collect() is True
    return read_artifact(tmp_path / "doc-source" / "doc-source.json", "doc-source").model_dump(mode="json")


def test_golden_entities_come_through_the_collector_unchanged_except_source_ref(doc_source_json):
    # Arrange
    expected = _expected_entities()

    # Act
    actual = {}
    for root in ("user_stories", "features", "functionalities"):
        for entity in doc_source_json[root]:
            source_ref = entity.pop("source_ref")
            assert source_ref["native_type"] in ("feature-file", "page-object")
            actual[entity["entity_id"]] = entity

    # Assert
    assert actual == expected
    assert sorted(actual) == ["FEAT-001", "FEAT-003", "FUNC-001", "FUNC-002", "US-001"]


def test_feat_001_has_derived_state(doc_source_json):
    # Arrange
    feat_001 = next(e for e in doc_source_json["features"] if e["entity_id"] == "FEAT-001")

    # Assert
    assert feat_001["state"] == "active"
    assert feat_001["state_origin"] == "derived"


def test_golden_run_reports_only_the_canon_s_expected_warnings(doc_source_json):
    # Assert: FEAT-003 depends on the API Feature FEAT-002, which a source-code project cannot document yet.
    assert [(w["code"], w["context"]) for w in doc_source_json["warnings"]] == [
        ("FEATURE_WITHOUT_FUNCTIONALITY", "entity_id='FEAT-003'"),
        ("UNRESOLVED_RELATION", "entity_id='FEAT-003' target='FEAT-002'"),
    ]


@pytest.mark.parametrize(
    "expected_name",
    [
        "us-001-customer-login.json",
        "feat-001-login-page.json",
        "feat-003-registration-page.json",
        "func-001-validate-password-strength.json",
        "func-002-reject-breached-password.json",
    ],
)
def test_identity_and_state_match_the_hand_written_golden_entity(doc_source_json, expected_name):
    # Arrange
    expected = json.loads((GOLDEN_DIR / "expected" / expected_name).read_text(encoding="utf-8"))
    entities = [*doc_source_json["user_stories"], *doc_source_json["features"], *doc_source_json["functionalities"]]

    # Act
    actual = next(e for e in entities if e["entity_id"] == expected["entity_id"])

    # Assert
    for key in ("type", "title", "state", "state_origin"):
        assert actual[key] == expected[key], key
