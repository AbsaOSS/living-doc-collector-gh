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
Tests for the shared metadata / warning contract models in `common/models.py`.
"""

import pytest
from pydantic import ValidationError

from common.models import AdapterMetadata, CompatibilityWarning

_VALID_METADATA = {
    "producer": {"name": "n", "version": "v", "build": None},
    "run": {"run_id": None, "run_attempt": None, "actor": None, "workflow": None, "ref": None, "sha": None},
    "source": {"systems": ["GitHub"], "repositories": [], "organization": None, "enterprise": None},
    "original_metadata": {"generated_at": "x", "schema_version": "1.0.0", "inputs": {}},
}


def test_adapter_metadata_accepts_valid_payload():
    metadata = AdapterMetadata.model_validate(_VALID_METADATA)

    assert metadata.producer.name == "n"
    assert metadata.run.actor is None
    assert metadata.source.systems == ["GitHub"]


def test_adapter_metadata_requires_nullable_keys_present():
    payload = {**_VALID_METADATA, "producer": {"name": "n", "version": "v"}}

    with pytest.raises(ValidationError):
        AdapterMetadata.model_validate(payload)


def test_compatibility_warning_context_defaults_to_none():
    warning = CompatibilityWarning.model_validate({"code": "C1", "message": "m"})

    assert warning.context is None


def test_shared_models_are_the_same_objects_across_modes():
    import doc_issues.models as di
    import doc_source.models as ds
    import ui_tests.models as ut

    assert di.AdapterMetadata is ds.AdapterMetadata is ut.AdapterMetadata is AdapterMetadata
    assert di.CompatibilityWarning is ds.CompatibilityWarning is ut.CompatibilityWarning is CompatibilityWarning
