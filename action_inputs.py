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
This module contains an Action Inputs class methods,
which are essential for running the GH action.
"""

import json
import logging
import re
from typing import Callable

from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.envelope import PROJECT_ID_PATTERN
from living_doc_utilities.github.utils import get_action_input
from living_doc_utilities.inputs.action_inputs import BaseActionInputs

from doc_source.model.config_repository import ConfigRepository as DocSourceConfigRepository
from ui_tests.model.config_repository import ConfigRepository as UITestsConfigRepository
from utils.constants import (
    ALLOW_PARTIAL,
    DEFAULT_OUTPUT_PATH,
    DOC_SOURCE_REPOSITORIES,
    GITHUB_SERVER_URL,
    OUTPUT_PATH,
    PROJECT_ID,
    UI_TESTS_REPOSITORIES,
    VERBOSE_LOGGING,
    Mode,
    input_name,
)
from utils.github_urls import server_url
from utils.utils import LoadableConfig, load_repository_configs

logger = logging.getLogger(__name__)


def _get_repositories(key: str) -> list:
    """
    Read a mode's `*-repositories` input: a JSON array of repository entries.

    @param key: The input's key, e.g. `DOC_SOURCE_REPOSITORIES`.
    @return: The entries, not yet loaded.
    @raise ContractError: `INVALID_CONFIGURATION` when the input is not a JSON array.
    """
    try:
        repositories = json.loads(get_action_input(key, "[]"))
    except json.JSONDecodeError as e:
        raise ContractError(Code.INVALID_CONFIGURATION, f"`{input_name(key)}` is not valid JSON: {e}.") from e
    if not isinstance(repositories, list):
        raise ContractError(
            Code.INVALID_CONFIGURATION, f"`{input_name(key)}` must be a JSON array of repository entries."
        )
    return repositories


def _check_repositories(key: str, config_factory: Callable[[], LoadableConfig]) -> None:
    """
    Load every entry of an enabled mode's `*-repositories` input, so a malformed one fails the run at start.

    @param key: The input's key, e.g. `DOC_SOURCE_REPOSITORIES`.
    @param config_factory: Creates an empty configuration of the mode.
    @raise ContractError: `INVALID_CONFIGURATION` naming the input, the entry and the reason.
    """
    repositories = _get_repositories(key)
    load_repository_configs(repositories, config_factory, input_name(key))
    if not repositories:
        logger.warning("`%s` is empty; the mode writes an artifact with no records.", input_name(key))


class ActionInputs(BaseActionInputs):
    """
    A class representing all the action inputs. It is responsible for loading, managing
    and validating the inputs required for running the GH Action. The `doc-source` and `ui-tests` modes read
    local checkouts only, so no input needs the network and `github-token` is not read.
    """

    @staticmethod
    def get_project_id() -> str:
        """
        Getter of the required project id, written to every artifact's `metadata.source.project_id`.
        @return: The project id.
        @raise ContractError: `INVALID_CONFIGURATION` when it is missing or does not match `PROJECT_ID_PATTERN`.
        """
        project_id = get_action_input(PROJECT_ID, "")
        if not project_id:
            raise ContractError(Code.INVALID_CONFIGURATION, "`project-id` is required.")
        if not re.fullmatch(PROJECT_ID_PATTERN, project_id):
            raise ContractError(
                Code.INVALID_CONFIGURATION, f"`project-id` {project_id!r} does not match `{PROJECT_ID_PATTERN}`."
            )
        return project_id

    @staticmethod
    def get_output_path() -> str:
        """
        Getter of the output root; each mode writes `<output-path>/<mode>/<artifact>.json`.
        @return: The output root, `./output/collector-gh` by default.
        """
        return get_action_input(OUTPUT_PATH, "") or DEFAULT_OUTPUT_PATH

    @staticmethod
    def is_allow_partial_enabled() -> bool:
        """
        Getter of the partial-mode switch: a failed source is a warning instead of failing the mode. False by default.
        @return: True if partial mode is enabled, False otherwise.
        """
        return get_action_input(ALLOW_PARTIAL, "false").lower() == "true"

    @staticmethod
    def get_github_server_url() -> str:
        """
        Getter of the GitHub server the configured repositories live on, for each `source_ref.url`.
        @return: The server URL, `utils.github_urls.DEFAULT_SERVER_URL` by default.
        @raise ContractError: `INVALID_CONFIGURATION` when it is not an http(s) URL.
        """
        try:
            return server_url(get_action_input(GITHUB_SERVER_URL, ""))
        except ValueError as e:
            raise ContractError(Code.INVALID_CONFIGURATION, f"`github-server-url` {e}.") from e

    @staticmethod
    def is_doc_issues_mode_enabled() -> bool:
        """
        Getter of the doc-issues mode switch. The mode is PLANNED: enabling it fails the run at start,
        and no other doc-issues input is read.
        @return: True if doc-issues mode is requested, False otherwise.
        """
        return get_action_input(Mode.DOC_ISSUES.value, "false").lower() == "true"

    @staticmethod
    def is_doc_source_mode_enabled() -> bool:
        """
        Getter of the doc-source mode switch.
        @return: True if doc-source mode is enabled, False otherwise.
        """
        return get_action_input(Mode.DOC_SOURCE.value, "false").lower() == "true"

    @staticmethod
    def get_doc_source_repositories() -> list[dict]:
        """
        Getter of the doc-source repositories configuration.
        @return: A list of repository configuration dictionaries.
        @raise ContractError: `INVALID_CONFIGURATION` when the input is not a JSON array.
        """
        return _get_repositories(DOC_SOURCE_REPOSITORIES)

    @staticmethod
    def is_ui_tests_mode_enabled() -> bool:
        """
        Getter of the ui-tests mode switch.
        @return: True if ui-tests mode is enabled, False otherwise.
        """
        return get_action_input(Mode.UI_TESTS.value, "false").lower() == "true"

    @staticmethod
    def get_ui_tests_repositories() -> list[dict]:
        """
        Getter of the ui-tests repositories configuration.
        @return: A list of repository configuration dictionaries.
        @raise ContractError: `INVALID_CONFIGURATION` when the input is not a JSON array.
        """
        return _get_repositories(UI_TESTS_REPOSITORIES)

    @staticmethod
    def get_verbose_logging() -> bool:
        """
        Getter of the verbose logging switch. False by default.
        @return: True if verbose logging is enabled, False otherwise.
        """
        return get_action_input(VERBOSE_LOGGING, "false").lower() == "true"

    def _validate(self) -> int:
        """
        Validate every input before any work (R13): a missing or malformed `project-id`, `github-server-url` or
        repository entry of an enabled mode is an `INVALID_CONFIGURATION` naming the input and the reason. No
        network request is made.

        @return: The count of configuration errors.
        """
        checks: list[Callable[[], object]] = [self.get_project_id, self.get_github_server_url]
        # A disabled mode's repositories are never read.
        if self.is_doc_source_mode_enabled():
            checks.append(lambda: _check_repositories(DOC_SOURCE_REPOSITORIES, DocSourceConfigRepository))
        if self.is_ui_tests_mode_enabled():
            checks.append(lambda: _check_repositories(UI_TESTS_REPOSITORIES, UITestsConfigRepository))

        errors: list[ContractError] = []
        for check in checks:
            try:
                check()
            except ContractError as e:
                errors.append(e)
        for error in errors:
            logger.error("%s", error)
        if errors:
            logger.error("User configuration validation failed.")
            return len(errors)

        logger.info("User configuration validation successfully completed.")
        # Not the base `print_effective_configuration()`: its token line would suggest `github-token` is read.
        self._print_effective_configuration()
        return 0

    def _print_effective_configuration(self) -> None:
        """
        Print the effective configuration of the action inputs.
        """
        # A disabled mode's repositories are never read, so a malformed one cannot fail the run.
        logger.info("Mode: `doc-source`: %s.", "Enabled" if ActionInputs.is_doc_source_mode_enabled() else "Disabled")
        if ActionInputs.is_doc_source_mode_enabled():
            logger.info("Mode(doc-source): `doc-source-repositories`: %s.", self.get_doc_source_repositories())
        logger.info("Mode: `ui-tests`: %s.", "Enabled" if ActionInputs.is_ui_tests_mode_enabled() else "Disabled")
        if ActionInputs.is_ui_tests_mode_enabled():
            logger.info("Mode(ui-tests): `ui-tests-repositories`: %s.", self.get_ui_tests_repositories())
        logger.info("verbose logging: %s", self.get_verbose_logging())
        logger.info("project-id: %s", self.get_project_id())
        logger.info("output-path: %s", self.get_output_path())
        logger.info("allow-partial: %s", self.is_allow_partial_enabled())
        logger.info("github-server-url: %s", self.get_github_server_url())
