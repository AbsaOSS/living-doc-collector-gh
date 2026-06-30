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
from doc_source.model.config_repository import ConfigRepository


def test_load_from_json_with_valid_input_loads_correctly():
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "local-path": "/path/to/checkout/aul-ui",
        "paths": ["playwright/features/**/*.feature"],
    }

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual
    assert config_repository.organization_name == "absa-group"
    assert config_repository.repository_name == "aul-ui"
    assert config_repository.local_path == "/path/to/checkout/aul-ui"
    assert config_repository.paths == ["playwright/features/**/*.feature"]
    assert "aul-ui" in repr(config_repository)


def test_load_from_json_with_missing_key_logs_error(mocker):
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {"organization-name": "absa-group"}
    mock_log_error = mocker.patch("doc_source.model.config_repository.logger.error")

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
    mock_log_error = mocker.patch("doc_source.model.config_repository.logger.error")

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual is False
    mock_log_error.assert_called_once_with(
        "The repository JSON input does not have a dictionary structure: %s.", mocker.ANY, exc_info=True
    )
