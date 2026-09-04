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

from typing import Any, Optional

from pydantic import BaseModel


class AcceptanceCriterion(BaseModel):
    """A single acceptance-criterion row parsed from an issue body."""

    id: str
    state: str
    version: str
    description: str


class AdapterItemTimestamps(BaseModel):
    """Creation/update timestamps for an adapter item."""

    created: str
    updated: str


class AdapterMetadataProducer(BaseModel):
    """Identifies the tool that produced the output file."""

    name: str
    version: str
    # Required key, nullable value — always present, `null` when there is no CI build id.
    build: Optional[str]


class AdapterMetadataRun(BaseModel):
    """GitHub Actions workflow run information, when available."""

    run_id: Optional[str]
    run_attempt: Optional[str]
    actor: Optional[str]
    workflow: Optional[str]
    ref: Optional[str]
    sha: Optional[str]
    # All six keys are required (always present) but nullable — outside a GitHub Actions
    # run, every value is `null` rather than the key being omitted.


class AdapterMetadataSource(BaseModel):
    """Source system and repository information."""

    systems: list[str]
    repositories: list[str]
    organization: Optional[str]
    # Required key, nullable value — `enterprise` is not currently captured.
    enterprise: Optional[str]


class AdapterMetadata(BaseModel):
    """File-level provenance and audit metadata."""

    producer: AdapterMetadataProducer
    run: AdapterMetadataRun
    source: AdapterMetadataSource
    original_metadata: dict[str, Any]


class CompatibilityWarning(BaseModel):
    """A non-fatal compatibility warning surfaced to downstream consumers."""

    code: str
    message: str
    context: Optional[str] = None


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
    acceptance_criteria: Optional[list[AcceptanceCriterion]] = None


class AdapterResult(BaseModel):
    """Complete result from adapter parsing."""

    user_stories: list[AdapterItem]
    metadata: AdapterMetadata
    warnings: list[CompatibilityWarning]
