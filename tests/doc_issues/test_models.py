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
Tests for the doc-issues.json Pydantic contract models (P1-CGH1).
"""

import pytest
from pydantic import ValidationError

from doc_issues.models import AdapterItem, AdapterMetadataProducer, AdapterResult

_VALID_ITEM = {
    "id": "org/repo#1",
    "title": "Title",
    "state": "open",
    "tags": [],
    "url": "https://example.com",
    "timestamps": {"created": "2025-01-01", "updated": "2025-01-02"},
}

_VALID_RESULT = {
    "user_stories": [_VALID_ITEM],
    "metadata": {
        "producer": {"name": "n", "version": "v", "build": None},
        "run": {"run_id": None, "run_attempt": None, "actor": None, "workflow": None, "ref": None, "sha": None},
        "source": {"systems": ["GitHub"], "repositories": [], "organization": None, "enterprise": None},
        "original_metadata": {"generated_at": "x", "schema_version": "1.0.0", "inputs": {}},
    },
    "warnings": [],
}


def test_adapter_result_accepts_valid_payload():
    result = AdapterResult.model_validate(_VALID_RESULT)

    assert result.user_stories[0].id == "org/repo#1"
    assert result.metadata.producer.name == "n"


def test_adapter_item_optional_fields_default_to_none():
    item = AdapterItem.model_validate(_VALID_ITEM)

    assert item.description is None
    assert item.business_value is None
    assert item.preconditions is None
    assert item.acceptance_criteria is None


def test_adapter_metadata_producer_requires_build_key_present():
    # `build` is required (must be present) even though its value is nullable.
    with pytest.raises(ValidationError):
        AdapterMetadataProducer.model_validate({"name": "n", "version": "v"})


def test_adapter_metadata_producer_accepts_null_build():
    producer = AdapterMetadataProducer.model_validate({"name": "n", "version": "v", "build": None})

    assert producer.build is None


def test_adapter_result_rejects_missing_required_top_level_key():
    payload = {k: v for k, v in _VALID_RESULT.items() if k != "warnings"}

    with pytest.raises(ValidationError):
        AdapterResult.model_validate(payload)
