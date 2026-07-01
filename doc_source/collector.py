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
This module contains the `doc-source` collector, which mines User Story,
Functionality, and Feature living documentation from locally checked-out
repositories and emits JSON.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from action_inputs import ActionInputs
from doc_source.header_parser import parse_func_header, parse_header
from doc_source.model.config_repository import ConfigRepository
from doc_source.page_object_parser import parse_page_object_header
from utils.constants import DOC_SOURCE_OUTPUT_PATH, get_package_version
from utils.feature_file_discovery import discover_feature_files, discover_ts_files

logger = logging.getLogger(__name__)


def _find_repo_root(file_path: Path) -> Optional[Path]:
    """Walk up from file_path to find the Git repository root (.git directory)."""
    current = file_path.parent
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _build_file_url(org: str, repo: str, file_path: Path) -> Optional[str]:
    """Build a GitHub web URL pointing to the source file in the repository.

    Returns None when no Git root is found above the file.
    """
    root = _find_repo_root(file_path)
    if root is None:
        logger.warning(
            "No git root found for `%s` - cannot build file URL.",
            file_path.name,
        )
        return None
    rel = file_path.relative_to(root).as_posix()
    return f"https://github.com/{org}/{repo}/blob/main/{rel}"


# pylint: disable=too-few-public-methods
class GHDocSourceCollector:
    """
    A class representing the `doc-source` collector. It scans local `.feature`
    and `.ts` files for LIVING DOC header blocks and exports the parsed data as JSON.
    """

    def __init__(self, output_path: str):
        self.__output_path = os.path.join(output_path, DOC_SOURCE_OUTPUT_PATH)

    def collect(self) -> bool:
        """
        Collect `doc-source` data from local files and export the output.

        @return: True if collection completed, False only if the output cannot be written.
        """
        self._clean_output_directory()
        logger.debug("'doc-source' mode output directory cleaned.")

        user_stories: list[dict] = []
        functionalities: list[dict] = []
        features: list[dict] = []

        for config in self._load_repositories():
            user_stories.extend(self._collect_user_stories(config))
            functionalities.extend(self._collect_functionalities(config))
            features.extend(self._collect_features(config))

        return self._store_items(user_stories, functionalities, features)

    def _clean_output_directory(self) -> None:
        """Clean the output directory from the previous run."""
        if os.path.exists(self.__output_path):
            shutil.rmtree(self.__output_path)
        os.makedirs(self.__output_path)

    @staticmethod
    def _load_repositories() -> list[ConfigRepository]:
        """Load configured repositories from action inputs."""
        repositories: list[ConfigRepository] = []
        for repository_json in ActionInputs.get_doc_source_repositories():
            config = ConfigRepository()
            if config.load_from_json(repository_json):
                repositories.append(config)
            else:
                logger.error("Failed to load doc-source repository from JSON: %s.", repository_json)
        return repositories

    @staticmethod
    def _collect_user_stories(config: ConfigRepository) -> list[dict]:
        """Collect User Story items from US .feature files for a single configured repository."""
        items: list[dict] = []
        for file_path in discover_feature_files(config.paths):
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except OSError as e:
                logger.warning("Could not read file `%s`: %s - skipping.", file_path, e)
                continue

            parsed = parse_header(lines)
            if parsed is None:
                continue

            items.append(
                {
                    "id": f"{config.organization_name}/{config.repository_name}/{parsed['us_id']}",
                    "repository_name": config.repository_name,
                    "title": parsed["title"],
                    "state": parsed["state"],
                    "tags": [],
                    "url": _build_file_url(config.organization_name, config.repository_name, file_path),
                    "timestamps": None,
                    "description": parsed["description"],
                    "business_value": parsed["business_value"],
                    "preconditions": parsed["preconditions"],
                    "acceptance_criteria": parsed["acceptance_criteria"],
                }
            )

        return items

    @staticmethod
    def _collect_functionalities(config: ConfigRepository) -> list[dict]:
        """Collect Functionality items from FUNC .feature files for a single configured repository."""
        items: list[dict] = []
        for file_path in discover_feature_files(config.func_paths):
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except OSError as e:
                logger.warning("Could not read FUNC file `%s`: %s - skipping.", file_path, e)
                continue

            parsed = parse_func_header(lines)
            if parsed is None:
                continue

            items.append(
                {
                    "id": f"{config.organization_name}/{config.repository_name}/{parsed['func_id']}",
                    "repository_name": config.repository_name,
                    "title": parsed["title"],
                    "state": parsed["state"],
                    "parent": parsed["parent"],
                    "func_type": parsed["func_type"],
                    "acceptance_criteria": parsed["acceptance_criteria"],
                }
            )

        return items

    @staticmethod
    def _collect_features(config: ConfigRepository) -> list[dict]:
        """Collect Feature items from TypeScript page object files for a single configured repository."""
        items: list[dict] = []
        for file_path in discover_ts_files(config.pages_paths):
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except OSError as e:
                logger.warning("Could not read page object file `%s`: %s - skipping.", file_path, e)
                continue

            parsed = parse_page_object_header(lines)
            if parsed is None:
                continue

            items.append(
                {
                    "id": f"{config.organization_name}/{config.repository_name}/{parsed['feat_id']}",
                    "repository_name": config.repository_name,
                    "title": parsed["title"],
                    "state": parsed["state"],
                    "surface_type": parsed["surface_type"],
                    "route": parsed["route"],
                    "owners": parsed["owners"],
                    "purpose": parsed["purpose"],
                    "user_stories": parsed["user_stories"],
                    "functionalities": parsed["functionalities"],
                    "external_dependencies": parsed["external_dependencies"],
                    "page_object": parsed["page_object"],
                }
            )

        return items

    def _store_items(
        self,
        user_stories: list[dict],
        functionalities: list[dict],
        features: list[dict],
    ) -> bool:
        """Persist the collected items as JSON. Returns False on write failure."""
        output_file_path = os.path.join(self.__output_path, "doc-source.json")
        logger.info("Exporting doc-source items - exporting to `%s`.", output_file_path)

        output_data = {
            "user_stories": user_stories,
            "functionalities": functionalities,
            "features": features,
            "metadata": self._get_file_metadata(),
            "warnings": [],
        }

        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
        except OSError as e:
            logger.error("Failed to write doc-source output to `%s`: %s.", output_file_path, e)
            return False

        return True

    @staticmethod
    def _get_file_metadata() -> dict:
        """Generate file-level metadata matching the AdapterMetadata structure."""
        repositories = GHDocSourceCollector._load_repositories()
        repository_list = [f"{repo.organization_name}/{repo.repository_name}" for repo in repositories]

        return {
            "producer": {
                "name": "AbsaOSS/living-doc-collector-gh",
                "version": get_package_version(),
                "build": os.getenv("GITHUB_RUN_ID"),
            },
            "run": {
                "run_id": os.getenv("GITHUB_RUN_ID"),
                "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
                "actor": os.getenv("GITHUB_ACTOR"),
                "workflow": os.getenv("GITHUB_WORKFLOW"),
                "ref": os.getenv("GITHUB_REF"),
                "sha": os.getenv("GITHUB_SHA"),
            },
            "source": {
                "systems": ["GitHub"],
                "repositories": repository_list,
                "organization": repositories[0].organization_name if repositories else None,
                "enterprise": None,
            },
            "original_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "inputs": {},
            },
        }
