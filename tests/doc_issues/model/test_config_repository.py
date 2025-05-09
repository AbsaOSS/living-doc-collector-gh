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
from doc_issues.model.config_repository import ConfigRepository


def test_load_from_json_with_valid_input_loads_correctly():
    # Arrange
    config_repository = ConfigRepository()
    organization_name = "organizationABC"
    repository_name = "repositoryABC"
    projects_title_filter = ["project1"]
    other_value = "other-value"
    repository_json = {
        "organization-name": organization_name,
        "repository-name": repository_name,
        "projects-title-filter": projects_title_filter,
        "other-field": other_value,
    }

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual
    assert organization_name == config_repository.organization_name
    assert repository_name == config_repository.repository_name
    assert projects_title_filter == config_repository.projects_title_filter


def test_load_from_json_with_valid_input_check_default_values():
    # Arrange
    config_repository = ConfigRepository()
    organization_name = "organizationABC"
    repository_name = "repositoryABC"
    repository_json = {"organization-name": organization_name, "repository-name": repository_name}

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual
    assert organization_name == config_repository.organization_name
    assert repository_name == config_repository.repository_name
    assert [] == config_repository.projects_title_filter


def test_load_from_json_with_missing_key_logs_error(mocker):
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {"non-existent-key": "value"}
    mock_log_error = mocker.patch("doc_issues.model.config_repository.logger.error")

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual is False
    mock_log_error.assert_called_once_with(
        "The key is not found in the repository JSON input: %s.", mocker.ANY, exc_info=True
    )


def test_load_from_json_with_wrong_structure_input_logs_error(mocker):
    # Arrange
    config_repository = ConfigRepository()
    repository_json = "not a dictionary"
    mock_log_error = mocker.patch("doc_issues.model.config_repository.logger.error")

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual is False
    mock_log_error.assert_called_once_with(
        "The repository JSON input does not have a dictionary structure: %s.", mocker.ANY, exc_info=True
    )


# __repr__


def test_repr():
    # Arrange
    organization_name = "organizationABC"
    repository_name = "repositoryABC"
    projects_title_filter = ["project1"]
    repository_json = {"organization-name": organization_name, "repository-name": repository_name,
                       "projects-title-filter": projects_title_filter}
    config_repository = ConfigRepository()
    config_repository.load_from_json(repository_json)

    # Act
    actual = repr(config_repository)

    # Assert
    assert actual == f"ConfigRepository(organization_name={organization_name}, repository_name={repository_name}, projects_title_filter={projects_title_filter})"
