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
Tests for the doc-issues schema-export utility (P1-CGH1): the generated schema must stay
in lockstep with the committed `doc-issues-v1.0.0-schema.json` file.
"""

import json
from pathlib import Path

from doc_issues.schema_export import _DEFAULT_SCHEMA_PATH, export_schema, write_schema


def test_export_schema_matches_committed_file():
    with open(_DEFAULT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        committed_schema = json.load(f)

    assert export_schema() == committed_schema


def test_export_schema_top_level_shape():
    schema = export_schema()

    assert schema["$schema_version"] == "1.0.0"
    assert schema["title"] == "AdapterResult"
    assert schema["type"] == "object"
    assert set(schema["properties"].keys()) == {"user_stories", "metadata", "warnings"}
    assert schema["required"] == ["user_stories", "metadata", "warnings"]
    assert set(schema["$defs"].keys()) == {
        "AcceptanceCriterion",
        "AdapterItemTimestamps",
        "AdapterMetadataProducer",
        "AdapterMetadataRun",
        "AdapterMetadataSource",
        "AdapterMetadata",
        "CompatibilityWarning",
        "AdapterItem",
    }


def test_write_schema_writes_generated_schema(tmp_path):
    output_path = tmp_path / "generated-schema.json"

    result_path = write_schema(output_path)

    assert result_path == output_path
    with open(output_path, "r", encoding="utf-8") as f:
        written_schema = json.load(f)
    assert written_schema == export_schema()


def test_write_schema_creates_parent_directories(tmp_path):
    output_path = tmp_path / "nested" / "dir" / "schema.json"

    write_schema(output_path)

    assert output_path.exists()


def test_default_schema_path_points_at_committed_schema():
    assert _DEFAULT_SCHEMA_PATH == Path(__file__).parent.parent.parent / "doc_issues" / "schema" / (
        "doc-issues-v1.0.0-schema.json"
    )
