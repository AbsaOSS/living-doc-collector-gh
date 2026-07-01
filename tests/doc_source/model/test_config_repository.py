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


def test_load_from_json_with_us_paths_key_loads_correctly():
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "us-paths": ["/path/to/checkout/aul-ui/playwright/features/liv_doc_us"],
        "func-paths": ["/path/to/checkout/aul-ui/playwright/features/liv_doc_func"],
        "pages-paths": ["/path/to/checkout/aul-ui/playwright/pages"],
    }

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual
    assert config_repository.organization_name == "absa-group"
    assert config_repository.repository_name == "aul-ui"
    assert config_repository.paths == ["/path/to/checkout/aul-ui/playwright/features/liv_doc_us"]
    assert config_repository.func_paths == ["/path/to/checkout/aul-ui/playwright/features/liv_doc_func"]
    assert config_repository.pages_paths == ["/path/to/checkout/aul-ui/playwright/pages"]
    assert "aul-ui" in repr(config_repository)


def test_load_from_json_with_legacy_paths_key_loads_correctly():
    """'paths' is accepted as a backward-compatible alias for 'us-paths'."""
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "paths": ["/path/to/checkout/aul-ui/playwright/features/**/*.feature"],
    }

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual
    assert config_repository.paths == ["/path/to/checkout/aul-ui/playwright/features/**/*.feature"]
    assert config_repository.func_paths == []
    assert config_repository.pages_paths == []


def test_load_from_json_optional_paths_default_to_empty():
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "us-paths": ["/path/to/us"],
    }

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual
    assert config_repository.paths == ["/path/to/us"]
    assert config_repository.func_paths == []
    assert config_repository.pages_paths == []


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
