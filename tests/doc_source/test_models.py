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
Tests for the `doc-source.json` Pydantic contract models, including a parity
check that the collector's real dict output round-trips through the models
without divergence.
"""

import json
import os

import pytest
from pydantic import ValidationError

from doc_source.collector import GHDocSourceCollector
from doc_source.models import DocSourceResult

_METADATA = {
    "producer": {"name": "n", "version": "v", "build": None},
    "run": {"run_id": None, "run_attempt": None, "actor": None, "workflow": None, "ref": None, "sha": None},
    "source": {"systems": ["GitHub"], "repositories": [], "organization": None, "enterprise": None},
    "original_metadata": {"generated_at": "x", "schema_version": "1.0.0", "inputs": {}},
}

_FULL_RESULT = {
    "user_stories": [
        {
            "id": "org/repo/US-1",
            "repository_name": "repo",
            "title": "Story",
            "state": "active",
            "tags": [],
            "url": None,
            "timestamps": None,
            "description": "As a user I want a thing.",
            "business_value": ["Value."],
            "preconditions": ["Logged in."],
            "not_in_scope": [],
            "deprecated_at": None,
            "deprecation_reason": None,
            "acceptance_criteria": [
                {
                    "id": "US-1-01",
                    "state": "Active",
                    "version": "v1.0.0",
                    "description": "Does the thing.",
                    "aspect": [],
                    "preconditions": [],
                    "not_in_scope": [],
                    "removal_planned": None,
                    "descoped_at": None,
                    "descoped_reason": None,
                    "future_release": None,
                }
            ],
        }
    ],
    "functionalities": [],
    "features": [],
    "metadata": _METADATA,
    "warnings": [],
}


def test_doc_source_result_accepts_full_payload():
    result = DocSourceResult.model_validate(_FULL_RESULT)

    assert result.user_stories[0].id == "org/repo/US-1"
    assert result.user_stories[0].acceptance_criteria[0].version == "v1.0.0"


def test_doc_source_result_rejects_missing_required_item_key():
    payload = json.loads(json.dumps(_FULL_RESULT))
    del payload["user_stories"][0]["timestamps"]

    with pytest.raises(ValidationError):
        DocSourceResult.model_validate(payload)


_FEATURE = """# =============================================================================
# LIVING DOC — US-7 · Parity Story
# =============================================================================
# source:         https://github.com/org/repo/issues/7
# status:         active
# business_value:
#   - Keeps the schema honest.
# preconditions:
#   - The user has logged in.
# acceptance_criteria:
#   AC:US-7-01 (v1.0.0 - Active)
#     - The collector output matches the model.
# =============================================================================

@US_ID:US-7
Feature: Parity Story
As a maintainer, I want parity so that the schema cannot drift.
"""


def test_collector_output_round_trips_through_models(tmp_path, mocker):
    repo_dir = tmp_path / "repo"
    us_dir = repo_dir / "us"
    us_dir.mkdir(parents=True)
    (us_dir / "story.feature").write_text(_FEATURE, encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[{"organization-name": "org", "repository-name": "repo", "us-paths": [str(repo_dir)]}],
    )

    assert GHDocSourceCollector(str(output_dir)).collect() is True

    with open(os.path.join(str(output_dir), "doc-source", "doc-source.json"), "r", encoding="utf-8") as f:
        collector_output = json.load(f)

    assert DocSourceResult.model_validate(collector_output).model_dump(mode="json") == collector_output
