#
# Copyright 2024 ABSA Group Limited
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
import requests

from doc_issues.model.config_repository import ConfigRepository
from utils.constants import GITHUB_TOKEN, Mode, DOC_ISSUES_PROJECT_STATE_MINING, DOC_ISSUES_REPOSITORIES
from utils.exceptions import FetchRepositoriesException
from utils.utils import get_action_input

logger = logging.getLogger(__name__)


class ActionInputs:
    """
    A class representing all the action inputs. It is responsible for loading, managing
    and validating the inputs required for running the GH Action.
    """

    @staticmethod
    def get_github_token() -> str:
        """
        Getter of the GitHub authorization token.
        @return: The GitHub authorization token.
        """
        return get_action_input(GITHUB_TOKEN)

    @staticmethod
    def is_doc_issues_mode_enabled() -> bool:
        """
        Getter of the LivDoc mode switch.
        @return: True if LivDoc mode is enabled, False otherwise.
        """
        mode: str = Mode.DOC_ISSUES.value
        return get_action_input(mode, "false").lower() == "true"

    @staticmethod
    def is_project_state_mining_enabled() -> bool:
        """
        Getter of the project state mining switch.
        @return: True if project state mining is enabled, False otherwise.
        """
        return get_action_input(DOC_ISSUES_PROJECT_STATE_MINING, "false").lower() == "true"

    @staticmethod
    def get_repositories() -> list[ConfigRepository]:
        """
        Getter and parser of the Config Repositories.

        @return: A list of Config Repositories
        @raise FetchRepositoriesException: When parsing JSON string to dictionary fails.
        """
        repositories = []
        action_input = get_action_input(DOC_ISSUES_REPOSITORIES, "[]")
        try:
            # Parse repositories json string into json dictionary format
            repositories_json = json.loads(action_input)

            # Load repositories into ConfigRepository object from JSON
            for repository_json in repositories_json:
                config_repository = ConfigRepository()
                if config_repository.load_from_json(repository_json):
                    repositories.append(config_repository)
                else:
                    logger.error("Failed to load repository from JSON: %s.", repository_json)

        except json.JSONDecodeError as e:
            logger.error("Error parsing JSON repositories: %s.", e, exc_info=True)
            raise FetchRepositoriesException from e

        except TypeError as e:
            logger.error("Type error parsing input JSON repositories: %s.", action_input)
            raise FetchRepositoriesException from e

        return repositories

    def validate_user_configuration(self) -> bool:
        """
        Checks that all the user configurations defined are correct.
        @return: True if configuration is correct, False otherwise.
        """
        logger.debug("User configuration validation started")

        # validate repositories configuration
        try:
            repositories = self.get_repositories()
        except FetchRepositoriesException:
            return False

        github_token = self.get_github_token()
        headers = {"Authorization": f"token {github_token}"}

        # Validate GitHub token
        response = requests.get("https://api.github.com/octocat", headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(
                "Can not connect to GitHub. Possible cause: Invalid GitHub token. Status code: %s, Response: %s",
                response.status_code,
                response.text,
            )
            return False

        repository_error_count = 0
        for repository in repositories:
            org_name = repository.organization_name
            repo_name = repository.repository_name
            github_repo_url = f"https://api.github.com/repos/{org_name}/{repo_name}"

            response = requests.get(github_repo_url, headers=headers, timeout=10)

            if response.status_code == 404:
                logger.error(
                    "Repository '%s/%s' could not be found on GitHub. Please verify that the repository "
                    "exists and that your authorization token is correct.",
                    org_name,
                    repo_name,
                )
                repository_error_count += 1
            elif response.status_code != 200:
                logger.error(
                    "An error occurred while validating the repository '%s/%s'. "
                    "The response status code is %s. Response: %s",
                    org_name,
                    repo_name,
                    response.status_code,
                    response.text,
                )
                repository_error_count += 1
        if repository_error_count > 0:
            return False

        # log user configuration
        logger.debug("User configuration validation successfully completed.")

        # log mode: enabled/disabled
        logger.debug("Mode: `doc-issues`: %s.", "Enabled" if ActionInputs.is_doc_issues_mode_enabled() else "Disabled")

        # log doc-issues mode user inputs
        if ActionInputs.is_doc_issues_mode_enabled():
            logger.debug("Mode(doc-issues): `doc-issues-repositories`: %s.", repositories)
            logger.debug(
                "Mode(doc-issues): `doc-issues-project-state-mining`: %s.",
                ActionInputs.is_project_state_mining_enabled(),
            )

        return True
