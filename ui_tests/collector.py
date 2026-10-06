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
This module contains the `ui-tests` collector, which mines UI test scenarios from `.feature`
files in locally checked-out repositories and writes a `ui-tests-v1.0.0` artifact. Scenario
parsing is `living_doc_utilities.authoring`'s; this module only discovers files, gives each
scenario its id and source_ref, and assembles the result.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

from living_doc_utilities.authoring.scenario import parse_scenarios
from living_doc_utilities.contracts.codes import Code
from living_doc_utilities.contracts.common import DocType, SourceRef
from living_doc_utilities.contracts.envelope import Cardinality, ContractWarning
from living_doc_utilities.contracts.ui_tests import Scenario, UITestsResult

from action_inputs import ActionInputs
from ui_tests.model.config_repository import ConfigRepository
from utils.artifact import (
    SourceRepository,
    build_metadata,
    build_source_ref,
    collect_artifact,
    relative_path,
    with_path,
)
from utils.constants import UI_TESTS_OUTPUT_PATH
from utils.feature_file_discovery import discover_feature_files
from utils.utils import load_repository_configs

logger = logging.getLogger(__name__)

UI_TESTS_FILE_NAME = "ui-tests.json"

# source_ref.native_type of a scenario.
SCENARIO_NATIVE_TYPE = "scenario"

# A tutorial walkthrough is not an AC-linked test: a scenario, or a whole file, tagged with it is not mined.
_TUTORIAL_TAG = "@tutorial"
_FEATURE_LINE_RE = re.compile(r"^\s*Feature:")
_SLUG_INVALID_RE = re.compile(r"[^a-z0-9\-]")
# The slug of a title with no ASCII letter or digit, so a scenario_id never ends in `/`.
_FALLBACK_SLUG = "scenario"

# Scenario-file framing does not depend on the entity type; any one selects the normaliser's profile.
_SCENARIO_ENTITY_TYPE: DocType = "DocumentedUserStory"


def _is_tutorial_file(text: str) -> bool:
    """True when a tag line above `Feature:` carries `@tutorial`."""
    for line in text.splitlines():
        if _FEATURE_LINE_RE.match(line):
            return False
        stripped = line.strip()
        if stripped.startswith("@") and _TUTORIAL_TAG in stripped.split():
            return True
    return False


def _slugify(title: str, used_slugs: dict[str, int]) -> str:
    """A collision-safe slug of a scenario title, unique within one file (`-2`, `-3`, ... on collision). A suffixed
    slug is recorded too, so a later title that slugs to it (`Login 2` after two `Login`s) is suffixed in turn."""
    base = _SLUG_INVALID_RE.sub("", title.lower().replace(" ", "-"))[:80]
    if not base.strip("-"):
        base = _FALLBACK_SLUG
    slug = base
    while slug in used_slugs:
        used_slugs[base] += 1
        slug = f"{base}-{used_slugs[base]}"
    used_slugs[slug] = 1
    return slug


# pylint: disable=too-few-public-methods
class GHUITestsCollector:
    """
    A class representing the `ui-tests` collector. It scans local `.feature` files for scenario
    blocks and writes them as a `ui-tests-v1.0.0` artifact.
    """

    def __init__(self, output_path: str):
        self.__output_path = os.path.join(output_path, UI_TESTS_OUTPUT_PATH)

    def collect(self) -> bool:
        """
        Collect `ui-tests` data from local `.feature` files and write the artifact.

        @return: True if the artifact was written, False when it failed validation or could not be written.
        """
        return collect_artifact(self.build_result, self.__output_path, UI_TESTS_FILE_NAME, "ui-tests")

    def build_result(self) -> UITestsResult:
        """
        Parse every configured `.feature` file's scenarios and assemble the `ui-tests-v1.0.0` result.

        @return: The contract result; `write_artifact` fills its stats.
        """
        configs, sources_failed = self._load_repositories()
        scenarios: dict[str, Scenario] = {}
        warnings: list[ContractWarning] = []
        for config in configs:
            repository = SourceRepository(config.organization_name, config.repository_name)
            for file_path in discover_feature_files(config.paths):
                self._collect_file(repository, file_path, config.paths, scenarios, warnings)

        return UITestsResult(
            metadata=build_metadata(
                [SourceRepository(c.organization_name, c.repository_name) for c in configs],
                Cardinality(sources_configured=len(configs) + sources_failed, sources_failed=sources_failed),
            ),
            warnings=warnings,
            scenarios=list(scenarios.values()),
        )

    @staticmethod
    def _load_repositories() -> tuple[list[ConfigRepository], int]:
        """Load configured repositories from action inputs; return them with the count that failed to load."""
        return load_repository_configs(ActionInputs.get_ui_tests_repositories(), ConfigRepository, "ui-tests")

    @staticmethod
    def _collect_file(
        repository: SourceRepository,
        file_path: Path,
        scan_roots: list[str],
        scenarios: dict[str, Scenario],
        warnings: list[ContractWarning],
    ) -> None:
        """Parse one `.feature` file's scenarios into `scenarios`, keyed by id: `<org>/<repo>/<source_ref.native_id>/
        <title slug>`. An id already collected from another file (e.g. one file reached through two scan roots) is
        skipped with an `AUTHORING_ERROR`: the first file read keeps it."""
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Could not read file `%s`: %s - skipping.", file_path, e)
            return
        rel_path = relative_path(file_path, scan_roots)
        if _is_tutorial_file(text):
            logger.debug("Skipping `@tutorial` feature file `%s` - walkthroughs are not mined.", rel_path)
            return

        parsed_scenarios, parse_warnings = parse_scenarios(text, _SCENARIO_ENTITY_TYPE)
        warnings.extend(with_path(parse_warnings, rel_path))

        # Built once the file keeps a scenario, so a file with none raises no `NO_SOURCE_URL`.
        source_ref: Optional[SourceRef] = None
        used_slugs: dict[str, int] = {}
        for parsed in parsed_scenarios:
            if _TUTORIAL_TAG in parsed.tags:
                logger.debug("Skipping `@tutorial` scenario `%s` - walkthroughs are not mined.", parsed.title)
                continue
            if source_ref is None:
                source_ref, ref_warnings = build_source_ref(repository, file_path, scan_roots, SCENARIO_NATIVE_TYPE)
                warnings.extend(ref_warnings)
            scenario_id = f"{repository.full_name}/{source_ref.native_id}/{_slugify(parsed.title, used_slugs)}"
            if scenario_id in scenarios:
                warnings.append(
                    ContractWarning(
                        code=Code.AUTHORING_ERROR.name,
                        message="Scenario id is already collected from another file; this scenario is skipped.",
                        context=f"path={rel_path!r} scenario_id={scenario_id!r}",
                    )
                )
                continue
            scenarios[scenario_id] = Scenario(
                scenario_id=scenario_id,
                title=parsed.title,
                source_ref=source_ref,
                tags=parsed.tags,
                acceptance_criteria=parsed.acceptance_criteria,
            )
