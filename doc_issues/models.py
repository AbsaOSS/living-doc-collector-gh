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
This module contains the Pydantic models for the `doc-issues.json` output contract
(the `AdapterResult` shape written by `doc_issues/collector.py`).

`collector-gh` is the data producer for this contract, and these models are the
source of truth for it: `doc_issues/schema/doc-issues-v1.0.0-schema.json` is generated
from them by `doc_issues/schema_export.py`, not hand-authored. `living-doc-toolkit`
vendors a pinned copy of the generated schema for its `collector_gh` adapter.
"""

from typing import Optional

from pydantic import BaseModel

# The metadata / warning block is identical across every collector output contract and
# is defined once in `common/models.py`. Re-exported here so existing
# `from doc_issues.models import ...` imports keep working.
from common.models import (
    AdapterMetadata,
    AdapterMetadataProducer,
    AdapterMetadataRun,
    AdapterMetadataSource,
    CompatibilityWarning,
)

__all__ = [
    "AdapterMetadata",
    "AdapterMetadataProducer",
    "AdapterMetadataRun",
    "AdapterMetadataSource",
    "CompatibilityWarning",
    "AcceptanceCriterion",
    "AdapterItemTimestamps",
    "AdapterItem",
    "AdapterResult",
]


class AcceptanceCriterion(BaseModel):
    """A single acceptance-criterion row parsed from an issue body."""

    id: str
    state: str
    version: str
    description: str
    # Additive fields from the canonical authoring format. GitHub issue bodies do
    # not currently express these, so they stay at their defaults for `doc-issues`
    # output; they exist on the shared contract for `.feature`-sourced records.
    aspect: Optional[list[str]] = None
    preconditions: Optional[list[str]] = None
    not_in_scope: Optional[list[str]] = None
    removal_planned: Optional[str] = None
    descoped_at: Optional[str] = None
    descoped_reason: Optional[str] = None
    future_release: Optional[str] = None


class AdapterItemTimestamps(BaseModel):
    """Creation/update timestamps for an adapter item."""

    created: str
    updated: str


class AdapterItem(BaseModel):
    """A single consolidated issue enriched with parsed body sections."""

    id: str
    title: str
    state: str
    tags: list[str]
    url: str
    timestamps: AdapterItemTimestamps
    description: Optional[str] = None
    business_value: Optional[list[str]] = None
    preconditions: Optional[list[str]] = None
    not_in_scope: Optional[list[str]] = None
    deprecated_at: Optional[str] = None
    deprecation_reason: Optional[str] = None
    acceptance_criteria: Optional[list[AcceptanceCriterion]] = None


class AdapterResult(BaseModel):
    """Complete result from adapter parsing."""

    # `items` holds every collected documentation record regardless of source system
    # (GitHub issue, Azure DevOps work item, `.feature` header) or documentation type — there
    # is no per-type grouping and no `type` field on the item; the type is carried by the
    # `DocumentedUserStory` / `DocumentedFeature` / `DocumentedFunctionality` label in
    # `AdapterItem.tags`.
    items: list[AdapterItem]
    metadata: AdapterMetadata
    warnings: list[CompatibilityWarning]
