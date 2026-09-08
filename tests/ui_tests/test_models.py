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
Tests for the `ui-tests.json` Pydantic contract models, including a parity check
that the collector's real dict output round-trips through the models.
"""

import json
import os

import pytest
from pydantic import ValidationError

from ui_tests.collector import GHUITestsCollector
from ui_tests.models import UITestsResult

_METADATA = {
    "producer": {"name": "n", "version": "v", "build": None},
    "run": {"run_id": None, "run_attempt": None, "actor": None, "workflow": None, "ref": None, "sha": None},
    "source": {"systems": ["GitHub"], "repositories": [], "organization": None, "enterprise": None},
    "original_metadata": {"generated_at": "x", "schema_version": "1.0.0", "inputs": {}},
}

_FULL_RESULT = {
    "items": [
        {
            "id": "org/repo/features/x.feature/first-scenario",
            "us_id": "US-26",
            "func_id": None,
            "ac_ids": ["US-26-01"],
            "ac_links": [{"id": "US-26-01", "aspect": None}],
            "scenario_name": "First scenario",
            "scenario_type": "Scenario",
            "tags": ["Regression"],
            "steps": [{"keyword": "Given", "text": "the user is logged in"}],
            "source": {"org": "org", "repo": "repo", "file": "features/x.feature", "line": 5},
        }
    ],
    "metadata": _METADATA,
    "warnings": [],
}


def test_ui_tests_result_accepts_full_payload():
    result = UITestsResult.model_validate(_FULL_RESULT)

    assert result.items[0].ac_links[0].id == "US-26-01"
    assert result.items[0].source.line == 5


def test_ui_tests_result_rejects_missing_required_item_key():
    payload = json.loads(json.dumps(_FULL_RESULT))
    del payload["items"][0]["func_id"]

    with pytest.raises(ValidationError):
        UITestsResult.model_validate(payload)


_FEATURE = """@US_ID:US-26
Feature: Create Domain
    As a user, I want to create domain.

    @AC:US-26-01
    Scenario: First scenario
        Given the user is logged in
        When the user acts
        Then a result happens
"""


def test_collector_output_round_trips_through_models(tmp_path, mocker):
    repo_dir = tmp_path / "repo"
    features_dir = repo_dir / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "create.feature").write_text(_FEATURE, encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[{"organization-name": "org", "repository-name": "repo", "paths": [str(repo_dir)]}],
    )

    assert GHUITestsCollector(str(output_dir)).collect() is True

    with open(os.path.join(str(output_dir), "ui-tests", "ui-tests.json"), "r", encoding="utf-8") as f:
        collector_output = json.load(f)

    assert UITestsResult.model_validate(collector_output).model_dump(mode="json") == collector_output
