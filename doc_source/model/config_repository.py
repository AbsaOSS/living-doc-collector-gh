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

from utils.utils import check_repository_names, get_path_list


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

    def load_from_json(self, repository_json: dict) -> None:
        """
        Load the configuration from a JSON object.

        @param repository_json: The JSON object containing the repository configuration.
        @return: None
        @raise ValueError: When the entry is malformed; the message names the missing key or the invalid value.
        """
        self.__organization_name, self.__repository_name = check_repository_names(repository_json)
        # "us-paths" is canonical; "paths" is accepted for backward compatibility.
        us_paths_key = "paths" if "paths" in repository_json and "us-paths" not in repository_json else "us-paths"
        self.__paths = get_path_list(repository_json, us_paths_key)
        self.__func_paths = get_path_list(repository_json, "func-paths", required=False)
        self.__pages_paths = get_path_list(repository_json, "pages-paths", required=False)

    def __repr__(self):
        return (
            f"ConfigRepository(organization_name={self.organization_name}, repository_name={self.repository_name}, "
            f"paths={self.paths}, func_paths={self.func_paths}, pages_paths={self.pages_paths})"
        )
