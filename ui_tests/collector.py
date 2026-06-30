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
This module contains the `ui-tests` collector, which mines UI test scenarios
from `.feature` file scenario blocks in locally checked-out repositories and
emits a test catalog JSON.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from action_inputs import ActionInputs
from ui_tests.model.config_repository import ConfigRepository
from ui_tests.scenario_parser import parse_scenarios
from utils.constants import UI_TESTS_OUTPUT_PATH, get_package_version
from utils.feature_file_discovery import discover_feature_files

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class GHUITestsCollector:
    """
    A class representing the `ui-tests` collector. It scans local `.feature`
    files for scenario blocks and exports the parsed test catalog as JSON.
    """

    def __init__(self, output_path: str):
        self.__output_path = os.path.join(output_path, UI_TESTS_OUTPUT_PATH)

    def collect(self) -> bool:
        """
        Collect `ui-tests` data from local `.feature` files and export the output.

        @return: True if collection completed, False only if the output cannot be written.
        """
        self._clean_output_directory()
        logger.debug("'ui-tests' mode output directory cleaned.")

        items: list[dict] = []
        for config in self._load_repositories():
            items.extend(self._collect_repository(config))

        return self._store_items(items)

    def _clean_output_directory(self) -> None:
        """Clean the output directory from the previous run."""
        if os.path.exists(self.__output_path):
            shutil.rmtree(self.__output_path)
        os.makedirs(self.__output_path)

    @staticmethod
    def _load_repositories() -> list[ConfigRepository]:
        """Load configured repositories from action inputs."""
        repositories: list[ConfigRepository] = []
        for repository_json in ActionInputs.get_ui_tests_repositories():
            config = ConfigRepository()
            if config.load_from_json(repository_json):
                repositories.append(config)
            else:
                logger.error("Failed to load ui-tests repository from JSON: %s.", repository_json)
        return repositories

    @staticmethod
    def _collect_repository(config: ConfigRepository) -> list[dict]:
        """Collect output items for a single configured repository."""
        if not os.path.exists(config.local_path):
            logger.error(
                "Local path `%s` for repository `%s/%s` does not exist - skipping.",
                config.local_path,
                config.organization_name,
                config.repository_name,
            )
            return []

        items: list[dict] = []
        for file_path in discover_feature_files(config.local_path, config.paths):
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except OSError as e:
                logger.warning("Could not read file `%s`: %s - skipping.", file_path, e)
                continue

            rel_path = file_path.relative_to(Path(config.local_path)).as_posix()
            items.extend(
                parse_scenarios(lines, config.organization_name, config.repository_name, rel_path)
            )

        return items

    def _store_items(self, items: list[dict]) -> bool:
        """Persist the collected items as JSON. Returns False on write failure."""
        output_file_path = os.path.join(self.__output_path, "ui-tests.json")
        logger.info("Exporting ui-tests items - exporting to `%s`.", output_file_path)

        output_data = {
            "items": items,
            "metadata": self._get_file_metadata(),
            "warnings": [],
        }

        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
        except OSError as e:
            logger.error("Failed to write ui-tests output to `%s`: %s.", output_file_path, e)
            return False

        return True

    @staticmethod
    def _get_file_metadata() -> dict:
        """Generate file-level metadata matching the AdapterMetadata structure."""
        repositories = GHUITestsCollector._load_repositories()
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
