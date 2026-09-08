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
Round-trip stability for every generated output-contract schema: exporting the
schema from the models must reproduce the committed file exactly, for
`doc-issues`, `doc-source`, and `ui-tests` alike.
"""

import json

import pytest

from doc_issues import schema_export as doc_issues_export
from doc_source import schema_export as doc_source_export
from ui_tests import schema_export as ui_tests_export

_EXPORTERS = [
    pytest.param(doc_issues_export, id="doc-issues"),
    pytest.param(doc_source_export, id="doc-source"),
    pytest.param(ui_tests_export, id="ui-tests"),
]


@pytest.mark.parametrize("exporter", _EXPORTERS)
def test_export_schema_matches_committed_file(exporter):
    with open(exporter._DEFAULT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        committed_schema = json.load(f)

    assert exporter.export_schema() == committed_schema


@pytest.mark.parametrize("exporter", _EXPORTERS)
def test_write_schema_reproduces_export(exporter, tmp_path):
    output_path = tmp_path / "schema.json"

    result_path = exporter.write_schema(output_path)

    assert result_path == output_path
    with open(output_path, "r", encoding="utf-8") as f:
        assert json.load(f) == exporter.export_schema()


@pytest.mark.parametrize("exporter", _EXPORTERS)
def test_schema_top_level_shape(exporter):
    schema = exporter.export_schema()

    assert schema["$schema_version"] == "1.0.0"
    assert schema["type"] == "object"
    assert set(schema["properties"].keys()) == set(schema["required"])
