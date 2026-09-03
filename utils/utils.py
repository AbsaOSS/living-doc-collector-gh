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

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import jsonschema

from utils.exceptions import InvalidQueryFormatError

logger = logging.getLogger(__name__)


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


def validate_against_schema(data: dict, schema_path: Path) -> bool:
    """
    Validate data against a JSON schema file.

    Parameters:
        data: The data dict to validate.
        schema_path: Absolute path to the JSON schema file.

    Returns:
        True when validation passes, False when it fails (errors are logged).
    """
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not load schema `%s`: %s", schema_path.name, e)
        return False

    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        logger.warning("Output does not conform to schema `%s`: %s", schema_path.name, e.message)
        return False
    except jsonschema.SchemaError as e:
        logger.warning("Schema `%s` is invalid: %s", schema_path.name, e.message)
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Unexpected schema validation error for `%s`: %s", schema_path.name, e)
        return False


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
