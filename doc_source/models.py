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
Pydantic models for the `doc-source.json` output contract (the shape written by
`doc_source/collector.py`).

These models are the source of truth for the contract:
`doc_source/schema/doc-source-v1.0.0-schema.json` is generated from them by
`doc_source/schema_export.py` (`python -m doc_source.schema_export`), not
hand-authored. A downstream consumer vendors a pinned copy of the generated schema.
"""

# Pydantic model classes are declarative data containers with no public methods by design.
# pylint: disable=too-few-public-methods

from typing import Optional

from pydantic import BaseModel, Field

# Shared metadata / warning block — one definition for every collector output contract.
from common.models import AdapterMetadata, CompatibilityWarning  # noqa: F401  (re-export)


class AcceptanceCriterion(BaseModel):
    """A single acceptance-criterion row parsed from a `.feature` header block."""

    id: str
    state: str
    version: str
    description: str
    aspect: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    not_in_scope: list[str] = Field(default_factory=list)
    removal_planned: Optional[str] = None
    descoped_at: Optional[str] = None
    descoped_reason: Optional[str] = None
    future_release: Optional[str] = None


class UserStoryItem(BaseModel):
    """A User Story record mined from a `@US_ID:` `.feature` file header block."""

    id: str
    repository_name: str
    title: str
    state: Optional[str]
    tags: list[str]
    url: Optional[str]
    timestamps: None
    description: Optional[str] = None
    business_value: Optional[list[str]] = None
    preconditions: Optional[list[str]] = None
    not_in_scope: Optional[list[str]] = None
    deprecated_at: Optional[str] = None
    deprecation_reason: Optional[str] = None
    acceptance_criteria: Optional[list[AcceptanceCriterion]] = None


class FunctionalityItem(BaseModel):
    """A Functionality record mined from a `@FUNC_ID:` `.feature` file header block."""

    id: str
    repository_name: str
    title: str
    state: Optional[str] = None
    parent: Optional[str] = None
    func_type: Optional[str] = None
    not_in_scope: Optional[list[str]] = None
    deprecated_at: Optional[str] = None
    deprecation_reason: Optional[str] = None
    acceptance_criteria: Optional[list[AcceptanceCriterion]] = None


class FeatureItem(BaseModel):
    """A Feature record mined from a TypeScript page-object header block."""

    id: str
    repository_name: str
    title: str
    state: Optional[str] = None
    surface_type: Optional[str] = None
    route: Optional[str] = None
    owners: Optional[str] = None
    purpose: Optional[str] = None
    user_stories: list[str] = Field(default_factory=list)
    functionalities: list[str] = Field(default_factory=list)
    external_dependencies: Optional[str] = None
    page_object: Optional[str] = None
    not_in_scope: Optional[list[str]] = None
    deprecated_at: Optional[str] = None
    deprecation_reason: Optional[str] = None


class DocSourceResult(BaseModel):
    """Complete result from doc-source collector parsing."""

    user_stories: list[UserStoryItem]
    functionalities: list[FunctionalityItem]
    features: list[FeatureItem]
    metadata: AdapterMetadata
    warnings: list[CompatibilityWarning]
