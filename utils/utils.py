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
This module contains utility functions used across the project.
"""

import logging
import os
import re
from typing import Callable, Optional, Protocol, TypeVar

from living_doc_utilities.contracts.codes import Code, ContractError

from utils.exceptions import InvalidQueryFormatError

logger = logging.getLogger(__name__)


class LoadableConfig(Protocol):  # pylint: disable=too-few-public-methods
    """A mode's repository configuration, loaded from one entry of its `*-repositories` input."""

    def load_from_json(self, repository_json: dict) -> None:
        """Load the configuration from one JSON entry; raise ValueError naming the reason when it is malformed."""


ConfigT = TypeVar("ConfigT", bound=LoadableConfig)


def check_repository_names(repository_json: object) -> tuple[str, str]:
    """
    Check that a repository entry is a JSON object whose `organization-name` and `repository-name` are non-empty
    strings with no `/`; the artifact's `metadata.source` lists them (`<organization>/<repository>`).

    @param repository_json: One entry of a mode's `*-repositories` input.
    @return: The organization name and the repository name.
    @raise ValueError: When the entry is not an object, a name is missing, or a name is not such a string.
    """
    if not isinstance(repository_json, dict):
        raise ValueError(f"the entry must be a JSON object, got {repository_json!r}")
    names = []
    for key in ("organization-name", "repository-name"):
        if key not in repository_json:
            raise ValueError(f"missing key `{key}`")
        value = repository_json[key]
        if not isinstance(value, str) or not value or "/" in value:
            raise ValueError(f"`{key}` must be a non-empty string with no `/`, got {value!r}")
        names.append(value)
    return names[0], names[1]


def get_path_list(repository_json: dict, key: str, required: bool = True) -> list[str]:
    """
    Read one path list of a repository entry.

    @param repository_json: One entry of a mode's `*-repositories` input, already checked to be an object.
    @param key: The path list's key, e.g. `paths`.
    @param required: When False, a missing key reads as an empty list.
    @return: The configured paths.
    @raise ValueError: When a required key is missing, or the value is not a list of strings.
    """
    if key not in repository_json:
        if required:
            raise ValueError(f"missing key `{key}`")
        return []
    value = repository_json[key]
    if not isinstance(value, list) or not all(isinstance(path, str) for path in value):
        raise ValueError(f"`{key}` must be a list of path strings, got {value!r}")
    return value


def load_repository_configs(
    repository_jsons: list[dict], config_factory: Callable[[], ConfigT], input_name: str
) -> list[ConfigT]:
    """
    Load a mode's configured repositories. A malformed entry is a configuration error, so the run fails at start.

    @param repository_jsons: The entries of the mode's `*-repositories` input.
    @param config_factory: Creates an empty configuration of the mode.
    @param input_name: The mode's `*-repositories` input, for the error.
    @return: The loaded configurations, one per entry, in input order.
    @raise ContractError: `INVALID_CONFIGURATION` naming the input, the entry and the reason.
    """
    repositories: list[ConfigT] = []
    for index, repository_json in enumerate(repository_jsons):
        config = config_factory()
        try:
            config.load_from_json(repository_json)
        except ValueError as e:
            raise ContractError(Code.INVALID_CONFIGURATION, f"`{input_name}` entry {index} is malformed: {e}.") from e
        repositories.append(config)
    return repositories


def sanitize_filename(filename: str) -> str:
    """
    Sanitize the provided filename by removing invalid characters.

    @param filename: The filename to sanitize.
    @return: The sanitized filename
    """
    # Remove invalid characters for Windows filenames
    sanitized_name = re.sub(r'[<>:"/|?*#{}()`]', "", filename)
    # Reduce consecutive periods
    sanitized_name = re.sub(r"\.{2,}", ".", sanitized_name)
    # Reduce consecutive spaces to a single space
    sanitized_name = re.sub(r" {2,}", " ", sanitized_name)
    # Replace space with '_'
    sanitized_name = sanitized_name.replace(" ", "_")

    return sanitized_name


def make_absolute_path(path: str) -> str:
    """
    Convert the provided path to an absolute path.

    @param path: The path to convert.
    @return: The absolute path.
    """
    # If the path is already absolute, return it as is
    if os.path.isabs(path):
        return path
    # Otherwise, convert the relative path to an absolute path
    return os.path.abspath(path)


def validate_query_format(query_string, expected_placeholders) -> None:
    """
    Validate the placeholders in the query string.
    Check if all the expected placeholders are present in the query and exit if not.

    @param query_string: The query string to validate.
    @param expected_placeholders: The set of expected placeholders in the query.
    @return: None
    @raise InvalidQueryFormatError: When some placeholders are missing in the query.
    """
    actual_placeholders = set(re.findall(r"\{(\w+)\}", query_string))
    missing = expected_placeholders - actual_placeholders
    extra = actual_placeholders - expected_placeholders
    if missing or extra:
        missing_message = f"Missing placeholders: {missing}. " if missing else ""
        extra_message = f"Extra placeholders: {extra}." if extra else ""
        logger.error("%s%s\nFor the query: %s", missing_message, extra_message, query_string)
        raise InvalidQueryFormatError


def load_template(file_path: str, error_message: str) -> Optional[str]:
    """
    Load the content of the template file.

    @param file_path: The path to the template file.
    @param error_message: The error message to log if the file cannot be read.
    @return: The content of the template file or None if the file cannot be read.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        logger.error(error_message, exc_info=True)
        return None
