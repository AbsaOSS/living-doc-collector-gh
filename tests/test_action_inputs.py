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
import json
import os

from action_inputs import ActionInputs

# Check Action Inputs default values


def test_doc_issues_mode_default(mocker):
    # Arrange
    mocker.patch.dict(os.environ, {}, clear=True)

    # Act
    actual = ActionInputs.is_doc_issues_mode_enabled()

    # Assert
    assert not actual


def test_doc_issues_mode_requested(mocker):
    # Arrange
    mocker.patch.dict(os.environ, {"INPUT_DOC_ISSUES": "true"})

    # Act & Assert
    assert ActionInputs.is_doc_issues_mode_enabled() is True


def test_report_page_default():
    # Act
    actual = os.getenv("INPUT_REPORT_PAGE", "true").lower() == "true"

    # Assert
    assert actual


def test_verbose_logging_default():
    # Act
    actual = os.getenv("INPUT_VERBOSE_LOGGING", "false").lower() == "true"

    # Assert
    assert not actual


# validate_user_configuration


def test_validate_user_configuration_correct_behaviour(mocker):
    # Arrange
    mock_log_info = mocker.patch("action_inputs.logger.info")
    mock_log_error = mocker.patch("action_inputs.logger.error")
    mocker.patch("action_inputs.ActionInputs.get_github_token", return_value="correct_token")
    mocker.patch("action_inputs.ActionInputs.is_doc_source_mode_enabled", return_value=True)
    mocker.patch("action_inputs.ActionInputs.get_doc_source_repositories", return_value=[{"x": 1}])
    fake_correct_response = mocker.Mock()
    fake_correct_response.status_code = 200
    mocker.patch("action_inputs.requests.get", return_value=fake_correct_response)

    # Act
    return_value = ActionInputs().validate_user_configuration()

    # Assert
    assert return_value is True
    mock_log_info.assert_has_calls(
        [
            mocker.call("User configuration validation successfully completed."),
            mocker.call("Mode: `doc-source`: %s.", "Enabled"),
        ],
        any_order=False,
    )
    mock_log_error.assert_not_called()


def test_validate_user_configuration_invalid_token(mocker):
    # Arrange
    mock_log_error = mocker.patch("action_inputs.logger.error")
    mocker.patch("action_inputs.ActionInputs.get_github_token", return_value="fake-token")
    mock_error_response = mocker.Mock()
    mock_error_response.status_code = 401
    mock_error_response.text = "Bad credentials"
    mocker.patch("action_inputs.requests.get", return_value=mock_error_response)

    # Act
    return_value = ActionInputs().validate_user_configuration()

    # Assert
    assert return_value is False
    mock_log_error.assert_called_with("User configuration validation failed.")


def test_validate_user_configuration_reads_no_doc_issues_input(mocker):
    # Arrange
    mocker.patch("action_inputs.ActionInputs.get_github_token", return_value="correct_token")
    fake_response = mocker.Mock()
    fake_response.status_code = 200
    mocker.patch("action_inputs.requests.get", return_value=fake_response)
    mock_get_input = mocker.patch("action_inputs.get_action_input", return_value="[]")

    # Act
    ActionInputs().validate_user_configuration()

    # Assert
    read_inputs = {call.args[0] for call in mock_get_input.call_args_list}
    assert not {name for name in read_inputs if name.startswith("DOC_ISSUES")}


# doc-source and ui-tests mode inputs


def test_is_doc_source_mode_enabled(mocker):
    # Arrange
    mocker.patch("action_inputs.get_action_input", return_value="true")

    # Act & Assert
    assert ActionInputs.is_doc_source_mode_enabled() is True


def test_get_doc_source_repositories(mocker):
    # Arrange
    repositories_json = [
        {
            "organization-name": "absa-group",
            "repository-name": "aul-ui",
            "local-path": "/path/to/aul-ui",
            "paths": ["features/**/*.feature"],
        }
    ]
    mocker.patch("action_inputs.get_action_input", return_value=json.dumps(repositories_json))

    # Act
    actual = ActionInputs.get_doc_source_repositories()

    # Assert
    assert actual == repositories_json


def test_is_ui_tests_mode_enabled(mocker):
    # Arrange
    mocker.patch("action_inputs.get_action_input", return_value="true")

    # Act & Assert
    assert ActionInputs.is_ui_tests_mode_enabled() is True


def test_get_ui_tests_repositories_default(mocker):
    # Arrange
    mocker.patch("action_inputs.get_action_input", return_value="[]")

    # Act
    actual = ActionInputs.get_ui_tests_repositories()

    # Assert
    assert actual == []


def test_validate_warns_when_source_modes_enabled_without_repositories(mocker):
    # Arrange
    mock_log_warning = mocker.patch("action_inputs.logger.warning")
    mocker.patch("action_inputs.ActionInputs.get_github_token", return_value="correct_token")
    mocker.patch("action_inputs.ActionInputs.is_doc_source_mode_enabled", return_value=True)
    mocker.patch("action_inputs.ActionInputs.get_doc_source_repositories", return_value=[])
    mocker.patch("action_inputs.ActionInputs.is_ui_tests_mode_enabled", return_value=True)
    mocker.patch("action_inputs.ActionInputs.get_ui_tests_repositories", return_value=[])
    fake_response = mocker.Mock()
    fake_response.status_code = 200
    mocker.patch("action_inputs.requests.get", return_value=fake_response)

    # Act
    ActionInputs().validate_user_configuration()

    # Assert
    mock_log_warning.assert_any_call("`doc-source` mode is enabled but `doc-source-repositories` is empty.")
    mock_log_warning.assert_any_call("`ui-tests` mode is enabled but `ui-tests-repositories` is empty.")
