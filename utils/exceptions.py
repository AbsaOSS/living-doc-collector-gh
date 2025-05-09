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
This module contains custom exceptions for this project
"""


# class LivingDocumentationGeneratorException(Exception):
class LivingDocumentationCollectorException(Exception):
    """Base class for exceptions in this project."""


class FetchRepositoriesException(LivingDocumentationCollectorException):
    """Raised when fetching repositories fails in get_repositories()."""


class InvalidQueryFormatError(LivingDocumentationCollectorException):
    """Raised when a query string is missing or has unexpected placeholders."""
