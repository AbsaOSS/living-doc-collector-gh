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
This module contains the helpers the `doc-source` and `ui-tests` collectors share to build a
contract artifact: the metadata envelope, a source file's `source_ref`, warning location context,
and running a mode: clearing its output directory, then building and writing its result through the one
write path (`write_artifact`).
"""

import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.common import SourceRef
from living_doc_utilities.contracts.compat import installed_utilities_version
from living_doc_utilities.contracts.envelope import (
    Cardinality,
    ContractWarning,
    Metadata,
    Producer,
    Run,
    Source,
    Stats,
)
from living_doc_utilities.contracts.io import write_artifact
from living_doc_utilities.contracts.registry import ContractResult
from pydantic import ValidationError

from utils.constants import get_package_version

logger = logging.getLogger(__name__)

PRODUCER_NAME = "AbsaOSS/living-doc-collector-gh"

# TODO(project-id input): the follow-up collector-gh issue adds the `project-id` action input; until then every
# artifact carries this internal default.
DEFAULT_PROJECT_ID = "unset-project"

# A committed source file has no tracker; its provenance state is that it is committed to the repository.
SOURCE_FILE_TRACKER_STATE = "committed"


@dataclass(frozen=True)
class SourceRepository:
    """One configured repository: its GitHub organization and name."""

    organization_name: str
    repository_name: str

    @property
    def full_name(self) -> str:
        """`<organization>/<repository>`, the form `metadata.source.repositories` lists."""
        return f"{self.organization_name}/{self.repository_name}"


def find_repo_root(file_path: Path) -> Optional[Path]:
    """
    Walk up from the file to the Git repository root (the directory holding `.git`).

    @param file_path: The source file.
    @return: The repository root, or None when the file is outside a git checkout.
    """
    current = file_path.resolve().parent
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def relative_path(file_path: Path, scan_roots: list[str]) -> str:
    """
    The file's path relative to the first configured scan root that contains it, `/`-separated.

    @param file_path: The source file.
    @param scan_roots: The configured directories the file was discovered under.
    @return: The relative path, or the file name when no root contains the file.
    """
    for root in scan_roots:
        try:
            return file_path.relative_to(root).as_posix()
        except ValueError:
            continue
    return file_path.name


def build_source_ref(
    repository: SourceRepository, file_path: Path, scan_roots: list[str], native_type: str
) -> tuple[SourceRef, list[ContractWarning]]:
    """
    Build the provenance pointer of a record mined from a committed source file.

    `native_id` is the file's path from the repository root and `url` its GitHub blob URL on the default
    branch. A file outside a git checkout gets an empty `url`, a scan-root-relative `native_id` and a
    `NO_SOURCE_URL` warning.

    @param repository: The configured repository the file belongs to.
    @param file_path: The source file.
    @param scan_roots: The configured directories the file was discovered under.
    @param native_type: The kind of source file, e.g. `feature-file` or `page-object`.
    @return: The source_ref and any warning raised while building it.
    """
    root = find_repo_root(file_path)
    warnings: list[ContractWarning] = []
    if root is None:
        native_id = relative_path(file_path, scan_roots)
        url = ""
        warnings.append(
            ContractWarning(
                code=Code.NO_SOURCE_URL.name,
                message="Source file is outside a git checkout, so no URL can be derived.",
                context=f"path={native_id!r}",
            )
        )
    else:
        native_id = file_path.resolve().relative_to(root).as_posix()
        url = f"https://github.com/{repository.full_name}/blob/HEAD/{native_id}"

    source_ref = SourceRef(
        system="GitHub",
        native_id=native_id,
        native_type=native_type,
        url=url,
        tracker_state=SOURCE_FILE_TRACKER_STATE,
    )
    return source_ref, warnings


def with_path(warnings: list[ContractWarning], path: str) -> list[ContractWarning]:
    """
    Prefix each warning's context with the source file it was raised for.

    @param warnings: Warnings a parser returned for one file.
    @param path: The file's path relative to its scan root.
    @return: The warnings, each with `path=...` leading its context.
    """
    located = []
    for warning in warnings:
        context = f"path={path!r}" if not warning.context else f"path={path!r} {warning.context}"
        located.append(warning.model_copy(update={"context": context}))
    return located


def build_metadata(repositories: list[SourceRepository], cardinality: Cardinality) -> Metadata:
    """
    Build the metadata envelope of a collector artifact. `write_artifact` recomputes `stats` from the
    records, keeping only the caller-owned counters of `cardinality`.

    @param repositories: The configured repositories the artifact documents.
    @param cardinality: The caller-owned counters: sources configured/failed, unresolved refs, skipped entities.
    @return: The metadata envelope.
    """
    return Metadata(
        producer=Producer(
            name=PRODUCER_NAME,
            version=get_package_version(),
            build=os.getenv("GITHUB_RUN_ID"),
            utilities_version=installed_utilities_version(),
        ),
        run=Run(
            run_id=os.getenv("GITHUB_RUN_ID"),
            run_attempt=os.getenv("GITHUB_RUN_ATTEMPT"),
            actor=os.getenv("GITHUB_ACTOR"),
            workflow=os.getenv("GITHUB_WORKFLOW"),
            ref=os.getenv("GITHUB_REF"),
            sha=os.getenv("GITHUB_SHA"),
        ),
        source=Source(
            project_id=DEFAULT_PROJECT_ID,
            systems=["GitHub"],
            organizations=sorted({repository.organization_name for repository in repositories}),
            repositories=sorted({repository.full_name for repository in repositories}),
        ),
        generated_at=datetime.now(timezone.utc),
        stats=Stats(cardinality=cardinality),
    )


def clear_output_dir(output_dir: str) -> bool:
    """
    Remove the mode's output directory, so a run that fails before or during the write leaves no output file -
    not even a previous run's.

    @param output_dir: The mode's output directory.
    @return: True when the directory is gone, False when it could not be removed.
    """
    try:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
    except OSError as e:
        logger.error("Failed to remove the previous output `%s`: %s.", output_dir, e)
        return False
    return True


def store_artifact(result: ContractResult, output_dir: str, file_name: str) -> bool:
    """
    Write the artifact into the mode's output directory via `write_artifact` (validated before the write,
    atomic rename). A failed validation leaves no output file.

    @param result: The contract result to write.
    @param output_dir: The mode's output directory, already cleared by `clear_output_dir`.
    @param file_name: The artifact's file name.
    @return: True when the artifact was written, False on a validation or write failure.
    """
    output_file_path = os.path.join(output_dir, file_name)
    logger.info("Exporting `%s` - exporting to `%s`.", result.schema_version, output_file_path)
    try:
        write_artifact(result, output_file_path)
    except ContractError as e:
        logger.error("Output failed contract validation, nothing written to `%s`: %s", output_file_path, e)
        return False
    except OSError as e:
        logger.error("Failed to write output to `%s`: %s.", output_file_path, e)
        return False
    return True


def collect_artifact(build_result: Callable[[], ContractResult], output_dir: str, file_name: str, mode: str) -> bool:
    """
    Run one mode: clear its output directory, build its contract result and write it. A result that fails
    contract validation, while being built or in `write_artifact`, leaves no output file - not even a previous
    run's.

    @param build_result: The mode collector's entry point.
    @param output_dir: The mode's output directory.
    @param file_name: The artifact's file name.
    @param mode: The mode's name, for the log.
    @return: True when the artifact was written, False on a validation or write failure.
    """
    if not clear_output_dir(output_dir):
        return False
    try:
        result = build_result()
    except ValidationError as e:
        logger.error("The `%s` result fails contract validation, nothing written: %s", mode, e)
        return False
    return store_artifact(result, output_dir, file_name)
