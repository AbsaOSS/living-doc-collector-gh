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
This module generates `doc-issues-v1.0.0-schema.json` from the Pydantic models in
`doc_issues/models.py`. Run it directly (`python -m doc_issues.schema_export`) to
regenerate the committed schema file after changing a model.
"""

import json
import sys
from pathlib import Path
from typing import Any

from pydantic.json_schema import GenerateJsonSchema

from doc_issues.models import AdapterResult

SCHEMA_VERSION = "1.0.0"

# Key order in the generated document, matching the previously hand-authored file.
_DEFS_ORDER = [
    "AcceptanceCriterion",
    "AdapterItemTimestamps",
    "AdapterMetadataProducer",
    "AdapterMetadataRun",
    "AdapterMetadataSource",
    "AdapterMetadata",
    "CompatibilityWarning",
    "AdapterItem",
]

_DEFAULT_SCHEMA_PATH = Path(__file__).parent / "schema" / "doc-issues-v1.0.0-schema.json"


class _NoFieldTitlesGenerator(GenerateJsonSchema):
    """Suppresses Pydantic's default per-field `title` — this contract keeps titles at the object level only."""

    def field_title_should_be_set(self, schema: Any) -> bool:
        return False


def export_schema() -> dict[str, Any]:
    """
    Build the `doc-issues.json` output-contract schema from `doc_issues/models.py`.

    @return: The schema document, ready to serialize as `doc-issues-v1.0.0-schema.json`.
    """
    raw_schema = AdapterResult.model_json_schema(schema_generator=_NoFieldTitlesGenerator)

    defs = raw_schema.pop("$defs", {})
    ordered_defs = {name: defs[name] for name in _DEFS_ORDER if name in defs}
    # Preserve any future def not covered by the fixed ordering above.
    ordered_defs.update({name: schema for name, schema in defs.items() if name not in ordered_defs})

    return {
        "$schema_version": SCHEMA_VERSION,
        "$defs": ordered_defs,
        "title": raw_schema.get("title", AdapterResult.__name__),
        "description": raw_schema.get("description", ""),
        "type": raw_schema.get("type", "object"),
        "properties": raw_schema.get("properties", {}),
        "required": raw_schema.get("required", []),
    }


def write_schema(output_path: Path = _DEFAULT_SCHEMA_PATH) -> Path:
    """
    Generate the schema and write it to `output_path`.

    @param output_path: Destination file path (defaults to the committed schema location).
    @return: The path the schema was written to.
    """
    schema = export_schema()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        f.write("\n")
    return output_path


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_SCHEMA_PATH
    written_path = write_schema(target)
    print(f"Wrote schema to {written_path}")
