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
import os

import requests
from living_doc_utilities.github.utils import get_action_input
from living_doc_utilities.inputs.action_inputs import BaseActionInputs

from utils.constants import (
    DOC_SOURCE_REPOSITORIES,
    UI_TESTS_REPOSITORIES,
    VERBOSE_LOGGING,
    Mode,
)

logger = logging.getLogger(__name__)


class ActionInputs(BaseActionInputs):
    """
    A class representing all the action inputs. It is responsible for loading, managing
    and validating the inputs required for running the GH Action.
    """

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
        """
        return json.loads(get_action_input(DOC_SOURCE_REPOSITORIES, "[]"))

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
        """
        return json.loads(get_action_input(UI_TESTS_REPOSITORIES, "[]"))

    @staticmethod
    def get_verbose_logging() -> bool:
        """
        Getter of the verbose logging switch. False by default.
        @return: True if verbose logging is enabled, False otherwise.
        """
        return get_action_input(VERBOSE_LOGGING, "false").lower() == "true"

    @staticmethod
    def get_ca_bundle() -> str | bool:
        """
        Get the CA bundle for HTTPS certificate verification.
        Reads from REQUESTS_CA_BUNDLE environment variable if set.

        @return: Path to CA bundle file, or True to use system default CA bundle.
        """
        ca_bundle: str | None = os.getenv("REQUESTS_CA_BUNDLE")
        return ca_bundle if ca_bundle else True

    def _validate(self) -> int:
        err_counter = 0

        # Warn (non-fatal) when a source mode is enabled without configured repositories
        if self.is_doc_source_mode_enabled() and not self.get_doc_source_repositories():
            logger.warning("`doc-source` mode is enabled but `doc-source-repositories` is empty.")
        if self.is_ui_tests_mode_enabled() and not self.get_ui_tests_repositories():
            logger.warning("`ui-tests` mode is enabled but `ui-tests-repositories` is empty.")

        github_token = self.get_github_token()
        headers = {"Authorization": f"token {github_token}"}
        verify_cert = self.get_ca_bundle()

        # Validate GitHub token
        response = requests.get("https://api.github.com/octocat", headers=headers, timeout=10, verify=verify_cert)
        if response.status_code != 200:
            logger.error(
                "Can not connect to GitHub. Possible cause: Invalid GitHub token. Status code: %s, Response: %s",
                response.status_code,
                response.text,
            )
            err_counter += 1

        if err_counter > 0:
            logger.error("User configuration validation failed.")
            return err_counter

        logger.info("User configuration validation successfully completed.")
        self.print_effective_configuration()

        return err_counter

    def _print_effective_configuration(self) -> None:
        """
        Print the effective configuration of the action inputs.
        """
        logger.info("Mode: `doc-source`: %s.", "Enabled" if ActionInputs.is_doc_source_mode_enabled() else "Disabled")
        logger.info("Mode(doc-source): `doc-source-repositories`: %s.", self.get_doc_source_repositories())
        logger.info("Mode: `ui-tests`: %s.", "Enabled" if ActionInputs.is_ui_tests_mode_enabled() else "Disabled")
        logger.info("Mode(ui-tests): `ui-tests-repositories`: %s.", self.get_ui_tests_repositories())
        logger.info("verbose logging: %s", self.get_verbose_logging())
