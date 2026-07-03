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
This module contains a data container for the doc-source Config Repository,
which holds all the essential logic.
"""

import logging

logger = logging.getLogger(__name__)


class ConfigRepository:
    """
    A class representing the doc-source configuration from which to scan local
    `.feature` files. The class provides loading logic and properties to access
    all the details.
    """

    def __init__(self):
        self.__organization_name: str = ""
        self.__repository_name: str = ""
        self.__paths: list[str] = []
        self.__func_paths: list[str] = []
        self.__pages_paths: list[str] = []

    @property
    def organization_name(self) -> str:
        """Getter of the repository organization name."""
        return self.__organization_name

    @property
    def repository_name(self) -> str:
        """Getter of the repository name."""
        return self.__repository_name

    @property
    def paths(self) -> list[str]:
        """Getter of absolute paths to scan for User Story .feature files."""
        return self.__paths

    @property
    def func_paths(self) -> list[str]:
        """Getter of absolute paths to scan for Functionality .feature files."""
        return self.__func_paths

    @property
    def pages_paths(self) -> list[str]:
        """Getter of absolute paths to scan for TypeScript page object files."""
        return self.__pages_paths

    def load_from_json(self, repository_json: dict) -> bool:
        """
        Load the configuration from a JSON object.

        @param repository_json: The JSON object containing the repository configuration.
        @return: bool
        """
        try:
            self.__organization_name = repository_json["organization-name"]
            self.__repository_name = repository_json["repository-name"]
            # "us-paths" is canonical; "paths" is accepted for backward compatibility.
            if "us-paths" in repository_json:
                self.__paths = repository_json["us-paths"]
            else:
                self.__paths = repository_json["paths"]
            self.__func_paths = repository_json.get("func-paths", [])
            self.__pages_paths = repository_json.get("pages-paths", [])
            return True
        except KeyError as e:
            logger.error("The key is not found in the repository JSON input: %s.", e, exc_info=True)
        except TypeError as e:
            logger.error("The repository JSON input does not have a dictionary structure: %s.", e, exc_info=True)
        return False

    def __repr__(self):
        return (
            f"ConfigRepository(organization_name={self.organization_name}, repository_name={self.repository_name}, "
            f"paths={self.paths}, func_paths={self.func_paths}, pages_paths={self.pages_paths})"
        )
