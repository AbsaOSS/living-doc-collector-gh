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
This module contains the `doc-source` collector, which mines User Story, Functionality and
Feature living documentation from locally checked-out repositories and writes a
`doc-source-v1.0.0` artifact. Parsing, status derivation and relation checks are
`living_doc_utilities.authoring`'s; this module only discovers files and assembles the result.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from living_doc_utilities.authoring.feature_header import parse_feature_header
from living_doc_utilities.authoring.framing import NO_FRAME
from living_doc_utilities.authoring.issue_body import ParsedEntity
from living_doc_utilities.authoring.normalize import SourceFormat, normalize_framed
from living_doc_utilities.authoring.page_object import PageObjectResult, parse_page_object
from living_doc_utilities.authoring.relations import check_relations
from living_doc_utilities.authoring.status import derive_statuses
from living_doc_utilities.contracts.codes import Code
from living_doc_utilities.contracts.common import DocType, SourceRef
from living_doc_utilities.contracts.doc_entities import Entity, PageRef
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import Cardinality, ContractWarning
from pydantic import ValidationError

from action_inputs import ActionInputs
from doc_source.model.config_repository import ConfigRepository
from utils.artifact import (
    SourceRepository,
    build_metadata,
    build_source_ref,
    collect_artifact,
    relative_path,
    with_path,
)
from utils.constants import DOC_SOURCE_OUTPUT_PATH
from utils.feature_file_discovery import discover_feature_files, discover_ts_files
from utils.utils import load_repository_configs

logger = logging.getLogger(__name__)

DOC_SOURCE_FILE_NAME = "doc-source.json"

# source_ref.native_type of each kind of source file.
FEATURE_FILE_NATIVE_TYPE = "feature-file"
PAGE_OBJECT_NATIVE_TYPE = "page-object"

# The banner title's fixed lead (`LIVING DOC — <id> · <title>`): a `.ts` file that never names it is code.
_LIVING_DOC_MARKER = "LIVING DOC"


@dataclass
class _Collected:
    """Everything parsed in one run, before status derivation: the entities with their source_ref and the
    path they were read from, the cross-reference pages waiting for their Feature, the warnings, and the
    count of skipped entities."""

    entities: list[ParsedEntity] = field(default_factory=list)
    sources: dict[str, tuple[SourceRef, str]] = field(default_factory=dict)
    cross_references: list[tuple[str, PageRef, str]] = field(default_factory=list)
    warnings: list[ContractWarning] = field(default_factory=list)
    entities_skipped: int = 0


def _has_living_doc_header(text: str) -> bool:
    """A TypeScript file is a PageObject header only when it has a header comment and names `LIVING DOC`. Any other
    file is code, even one opening with an eslint directive or a JSDoc block, which the PageObject frame (the file's
    first `/* ... */` comment) would otherwise read as a header. A misplaced banner still names `LIVING DOC`, so it
    is parsed and reported rather than skipped silently."""
    if _LIVING_DOC_MARKER not in text:
        return False
    _, frame = normalize_framed(text, SourceFormat.PAGE_OBJECT, "DocumentedFeature")
    return all(problem.kind != NO_FRAME for problem in frame.problems)


def _read(file_path: Path) -> Optional[str]:
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Could not read file `%s`: %s - skipping.", file_path, e)
        return None


# pylint: disable=too-few-public-methods
class GHDocSourceCollector:
    """
    A class representing the `doc-source` collector. It scans local `.feature` and `.ts` files for
    LIVING DOC header blocks and writes the parsed entities as a `doc-source-v1.0.0` artifact.
    """

    def __init__(self, output_path: str):
        self.__output_path = os.path.join(output_path, DOC_SOURCE_OUTPUT_PATH)

    def collect(self) -> bool:
        """
        Collect `doc-source` data from local files and write the artifact.

        @return: True if the artifact was written, False when it failed validation or could not be written.
        """
        return collect_artifact(self.build_result, self.__output_path, DOC_SOURCE_FILE_NAME, "doc-source")

    def build_result(self) -> DocSourceResult:
        """
        Parse every configured file and assemble the `doc-source-v1.0.0` result. Status derivation and
        relation checks run over every entity of the run the contract accepts.

        @return: The contract result; `write_artifact` fills its stats.
        """
        configs, sources_failed = self._load_repositories()
        collected = _Collected()
        for config in configs:
            repository = SourceRepository(config.organization_name, config.repository_name)
            for file_path in discover_feature_files(config.paths):
                self._collect_feature_file(collected, repository, file_path, config.paths, "DocumentedUserStory")
            for file_path in discover_feature_files(config.func_paths):
                self._collect_feature_file(
                    collected, repository, file_path, config.func_paths, "DocumentedFunctionality"
                )
            for file_path in discover_ts_files(config.pages_paths):
                self._collect_page_object(collected, repository, file_path, config.pages_paths)

        self._attach_cross_references(collected)
        derived, entities, status_warnings = self._derive_accepted(collected)
        relation_warnings = check_relations(derived)
        warnings = collected.warnings + status_warnings + relation_warnings

        roots: dict[DocType, list[Entity]] = {
            "DocumentedUserStory": [],
            "DocumentedFeature": [],
            "DocumentedFunctionality": [],
        }
        for entity in entities:
            roots[entity.type].append(entity)

        return DocSourceResult(
            metadata=build_metadata(
                [SourceRepository(c.organization_name, c.repository_name) for c in configs],
                Cardinality(
                    sources_configured=len(configs) + sources_failed,
                    sources_failed=sources_failed,
                    unresolved_refs=sum(1 for w in warnings if w.code == Code.UNRESOLVED_RELATION.name),
                    entities_skipped=collected.entities_skipped,
                ),
            ),
            warnings=warnings,
            user_stories=roots["DocumentedUserStory"],
            features=roots["DocumentedFeature"],
            functionalities=roots["DocumentedFunctionality"],
        )

    @staticmethod
    def _load_repositories() -> tuple[list[ConfigRepository], int]:
        """Load configured repositories from action inputs; return them with the count that failed to load."""
        return load_repository_configs(ActionInputs.get_doc_source_repositories(), ConfigRepository, "doc-source")

    @staticmethod
    def _derive_accepted(
        collected: _Collected,
    ) -> tuple[list[ParsedEntity], list[Entity], list[ContractWarning]]:
        """
        Derive statuses and build the contract entities. An entity the contract rejects (e.g. an AC id of another
        entity) is skipped with an `AUTHORING_ERROR` and counted in `entities_skipped`, so one bad header never
        fails the whole run; statuses are then derived again without it, so no other entity's state or relation
        check relies on it.

        @return: The derived entities the contract accepts, their contract entities, and the warnings of the run.
        """
        parsed_entities = collected.entities
        rejections: list[ContractWarning] = []
        while True:
            derived, status_warnings = derive_statuses(parsed_entities)
            entities: list[Entity] = []
            rejected: set[str] = set()
            for parsed in derived:
                source_ref, rel_path = collected.sources[parsed.entity_id]
                try:
                    entities.append(Entity(source_ref=source_ref, **parsed.model_dump()))
                except ValidationError as e:
                    reason = "; ".join(error["msg"] for error in e.errors())
                    rejections.append(
                        ContractWarning(
                            code=Code.AUTHORING_ERROR.name,
                            message=f"Entity fails contract validation and is skipped: {reason}",
                            context=f"path={rel_path!r} entity_id={parsed.entity_id!r}",
                        )
                    )
                    rejected.add(parsed.entity_id)
            if not rejected:
                return derived, entities, rejections + status_warnings
            collected.entities_skipped += len(rejected)
            parsed_entities = [e for e in parsed_entities if e.entity_id not in rejected]

    @staticmethod
    def _add_entity(
        collected: _Collected,
        entity: Optional[ParsedEntity],
        warnings: list[ContractWarning],
        source: tuple[SourceRepository, Path, list[str], str],
    ) -> None:
        """Record one file's parse result: its warnings with the file's path, and its entity with a source_ref -
        or, with no parseable entity id, a skip (the parser's `MISSING_ENTITY_ID` carries the title). An entity id
        already collected is skipped with an `AUTHORING_ERROR`: the first file read keeps it."""
        repository, file_path, scan_roots, native_type = source
        rel_path = relative_path(file_path, scan_roots)
        collected.warnings.extend(with_path(warnings, rel_path))
        if entity is None:
            collected.entities_skipped += 1
            return
        if entity.entity_id in collected.sources:
            first_ref, first_path = collected.sources[entity.entity_id]
            first_source = first_ref.url or first_path
            collected.warnings.append(
                ContractWarning(
                    code=Code.AUTHORING_ERROR.name,
                    message=f"Entity id is already collected from {first_source!r}; this file is skipped.",
                    context=f"path={rel_path!r} entity_id={entity.entity_id!r}",
                )
            )
            collected.entities_skipped += 1
            return
        source_ref, ref_warnings = build_source_ref(repository, file_path, scan_roots, native_type)
        collected.warnings.extend(ref_warnings)
        collected.entities.append(entity)
        collected.sources[entity.entity_id] = (source_ref, rel_path)

    def _collect_feature_file(
        self,
        collected: _Collected,
        repository: SourceRepository,
        file_path: Path,
        scan_roots: list[str],
        entity_type: DocType,
    ) -> None:
        """Parse one User Story or Functionality `.feature` file's header."""
        text = _read(file_path)
        if text is None:
            return
        entity, warnings = parse_feature_header(text, entity_type)
        self._add_entity(collected, entity, warnings, (repository, file_path, scan_roots, FEATURE_FILE_NATIVE_TYPE))

    def _collect_page_object(
        self, collected: _Collected, repository: SourceRepository, file_path: Path, scan_roots: list[str]
    ) -> None:
        """Parse one TypeScript PageObject file's header: a full header is a Feature, a cross-reference header
        is one more page of its parent Feature. A `.ts` file with no header comment is code, not documentation."""
        text = _read(file_path)
        if text is None:
            return
        if not _has_living_doc_header(text):
            logger.debug("No living-doc header in `%s` - not a PageObject header, skipping.", file_path)
            return
        result: Optional[PageObjectResult]
        result, warnings = parse_page_object(text)
        if result is not None and result.entity is None:
            rel_path = relative_path(file_path, scan_roots)
            collected.warnings.extend(with_path(warnings, rel_path))
            collected.cross_references.append((result.parent_feat or "", result.page_ref, rel_path))
            return
        entity = None if result is None else result.entity
        self._add_entity(collected, entity, warnings, (repository, file_path, scan_roots, PAGE_OBJECT_NATIVE_TYPE))

    @staticmethod
    def _attach_cross_references(collected: _Collected) -> None:
        """Append each cross-reference page to its parent Feature's `pages`; one with no such Feature in the run
        is reported `UNRESOLVED_RELATION` and dropped."""
        features = {entity.entity_id: entity for entity in collected.entities if entity.type == "DocumentedFeature"}
        for parent_feat, page_ref, rel_path in collected.cross_references:
            feature = features.get(parent_feat)
            if feature is None:
                collected.warnings.append(
                    ContractWarning(
                        code=Code.UNRESOLVED_RELATION.name,
                        message="'parent-feat' points outside the collected entity set; the page is dropped.",
                        context=f"path={rel_path!r} target={parent_feat!r}",
                    )
                )
                continue
            feature.pages.append(page_ref)
