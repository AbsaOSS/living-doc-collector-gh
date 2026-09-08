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
This module generates `ui-tests-v1.0.0-schema.json` from the Pydantic models in
`ui_tests/models.py`. Run it directly (`python -m ui_tests.schema_export`) to
regenerate the committed schema file after changing a model.
"""

import logging
from pathlib import Path
from typing import Any

from living_doc_utilities.logging_config import setup_logging

from common.schema_export import build_schema
from common.schema_export import write_schema as write_schema_file
from ui_tests.models import UITestsResult

logger = logging.getLogger(__name__)

# Key order in the generated document.
_DEFS_ORDER = [
    "Step",
    "AcLink",
    "ScenarioSource",
    "UITestItem",
    "AdapterMetadataProducer",
    "AdapterMetadataRun",
    "AdapterMetadataSource",
    "AdapterMetadata",
    "CompatibilityWarning",
]

_DEFAULT_SCHEMA_PATH = Path(__file__).parent / "schema" / "ui-tests-v1.0.0-schema.json"


def export_schema() -> dict[str, Any]:
    """
    Build the `ui-tests.json` output-contract schema from `ui_tests/models.py`.

    @return: The schema document, ready to serialize as `ui-tests-v1.0.0-schema.json`.
    """
    return build_schema(UITestsResult, _DEFS_ORDER)


def write_schema(output_path: Path = _DEFAULT_SCHEMA_PATH) -> Path:
    """
    Generate the schema and write it to `output_path`.

    @param output_path: Destination file path. Defaults to — and in normal use is
        only ever — the committed schema location; the parameter exists so tests
        can redirect the write to a temporary path.
    @return: The path the schema was written to.
    """
    return write_schema_file(export_schema(), output_path)


if __name__ == "__main__":
    setup_logging()
    written_path = write_schema()
    logger.info("Wrote schema to %s", written_path)
