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
Pydantic models for the `ui-tests.json` output contract (the shape written by
`ui_tests/collector.py`).

These models are the source of truth for the contract:
`ui_tests/schema/ui-tests-v1.0.0-schema.json` is generated from them by
`ui_tests/schema_export.py` (`python -m ui_tests.schema_export`), not
hand-authored. A downstream consumer vendors a pinned copy of the generated schema.
"""

# Pydantic model classes are declarative data containers with no public methods by design.
# pylint: disable=too-few-public-methods

from typing import Optional

from pydantic import BaseModel, Field

# Shared metadata / warning block — one definition for every collector output contract.
from common.models import AdapterMetadata, CompatibilityWarning  # noqa: F401  (re-export)


class Step(BaseModel):
    """A single Gherkin step within a scenario."""

    keyword: str
    text: str


class AcLink(BaseModel):
    """A scenario-to-AC link, carrying the optional aspect the scenario covers."""

    id: str
    aspect: Optional[str]


class ScenarioSource(BaseModel):
    """Source identity of a scenario."""

    org: str
    repo: str
    file: str
    line: int


class UITestItem(BaseModel):
    """Represents a single UI test scenario from the collector output."""

    id: str
    us_id: Optional[str]
    func_id: Optional[str]
    ac_ids: list[str]
    ac_links: list[AcLink] = Field(default_factory=list)
    scenario_name: str
    scenario_type: str
    tags: list[str]
    steps: list[Step]
    source: ScenarioSource


class UITestsResult(BaseModel):
    """Complete UI test catalog result from the ui-tests collector."""

    items: list[UITestItem]
    metadata: AdapterMetadata
    warnings: list[CompatibilityWarning]
