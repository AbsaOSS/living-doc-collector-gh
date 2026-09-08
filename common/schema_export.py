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
Shared helpers for generating a mode's `*-v1.0.0-schema.json` file from its
Pydantic output-contract models. Each mode's `schema_export.py` wraps
`build_schema` / `write_schema` with its own model and `$defs` ordering.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema

SCHEMA_VERSION = "1.0.0"


class NoFieldTitlesGenerator(GenerateJsonSchema):
    """Suppresses Pydantic's default per-field `title` — these contracts keep titles at the object level only."""

    def field_title_should_be_set(self, schema: Any) -> bool:
        return False


def build_schema(model: type[BaseModel], defs_order: list[str]) -> dict[str, Any]:
    """
    Build a mode's output-contract schema document from its top-level Pydantic model.

    @param model: The top-level result model (e.g. `AdapterResult`, `DocSourceResult`).
    @param defs_order: The `$defs` key order to emit, matching the committed file. Any
        def not named here is appended in Pydantic's own order.
    @return: The schema document, ready to serialize.
    """
    raw_schema = model.model_json_schema(schema_generator=NoFieldTitlesGenerator)

    defs = raw_schema.pop("$defs", {})
    ordered_defs = {name: defs[name] for name in defs_order if name in defs}
    # Preserve any future def not covered by the fixed ordering above.
    ordered_defs.update({name: schema for name, schema in defs.items() if name not in ordered_defs})

    return {
        "$schema_version": SCHEMA_VERSION,
        "$defs": ordered_defs,
        "title": raw_schema.get("title", model.__name__),
        "description": raw_schema.get("description", ""),
        "type": raw_schema.get("type", "object"),
        "properties": raw_schema.get("properties", {}),
        "required": raw_schema.get("required", []),
    }


def write_schema(schema: dict[str, Any], output_path: Path) -> Path:
    """
    Serialize a schema document to `output_path` (creating parent directories).

    @param schema: The schema document from `build_schema`.
    @param output_path: Destination file path.
    @return: The path the schema was written to.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        f.write("\n")
    return output_path
