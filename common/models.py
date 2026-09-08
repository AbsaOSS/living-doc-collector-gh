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
Shared Pydantic models for the file-level provenance metadata and the
compatibility-warning block that every collector output contract carries.

These shapes are identical across `doc-issues`, `doc-source`, and `ui-tests`, so
they live here once and are imported by each mode's `models.py`. Each mode's
`schema/*-v1.0.0-schema.json` is generated from those models by the mode's
`schema_export.py`, not hand-authored.
"""

from typing import Any, Optional

from pydantic import BaseModel

__all__ = [
    "AdapterMetadataProducer",
    "AdapterMetadataRun",
    "AdapterMetadataSource",
    "AdapterMetadata",
    "CompatibilityWarning",
]


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
