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

from utils.exceptions import InvalidQueryFormatError

logger = logging.getLogger(__name__)


class LoadableConfig(Protocol):  # pylint: disable=too-few-public-methods
    """A mode's repository configuration, loaded from one entry of its `*-repositories` input."""

    def load_from_json(self, repository_json: dict) -> bool:
        """Load the configuration from one JSON entry; False when the entry is invalid."""


ConfigT = TypeVar("ConfigT", bound=LoadableConfig)


def has_string_names(repository_json: dict) -> bool:
    """
    Check that a repository entry's `organization-name` and `repository-name` are non-empty strings with no `/`;
    the artifact's `metadata.source` lists them (`<organization>/<repository>`), so any other value would fail the
    whole run.

    @param repository_json: One entry of a mode's `*-repositories` input.
    @return: True when both names are non-empty strings with no `/`; otherwise the entry is logged as invalid.
    """
    for key in ("organization-name", "repository-name"):
        value = repository_json[key]
        if not isinstance(value, str) or not value or "/" in value:
            logger.error("The repository JSON input `%s` must be a non-empty string with no `/`, got %r.", key, value)
            return False
    return True


def load_repository_configs(
    repository_jsons: list[dict], config_factory: Callable[[], ConfigT], mode: str
) -> tuple[list[ConfigT], int]:
    """
    Load a mode's configured repositories; an entry that fails to load is logged and skipped.

    @param repository_jsons: The entries of the mode's `*-repositories` input.
    @param config_factory: Creates an empty configuration of the mode.
    @param mode: The mode's name, for the log.
    @return: The loaded configurations and the count of entries that failed to load.
    """
    repositories: list[ConfigT] = []
    for repository_json in repository_jsons:
        config = config_factory()
        if config.load_from_json(repository_json):
            repositories.append(config)
        else:
            logger.error("Failed to load %s repository from JSON: %s.", mode, repository_json)
    return repositories, len(repository_jsons) - len(repositories)


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
