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

import pytest
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.github.utils import get_action_input

from action_inputs import ActionInputs

VALID_DOC_SOURCE_ENTRY = {"organization-name": "absa-group", "repository-name": "aul-ui", "us-paths": ["/x/us"]}
VALID_UI_TESTS_ENTRY = {"organization-name": "absa-group", "repository-name": "aul-ui", "paths": ["/x/features"]}


def _logged(mock_log):
    """Each call of a mocked logger method, formatted as the log line it writes."""
    return [call.args[0] % call.args[1:] if len(call.args) > 1 else call.args[0] for call in mock_log.call_args_list]


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


# project-id


def test_get_project_id_returns_a_valid_id(monkeypatch):
    # Arrange
    monkeypatch.setenv("INPUT_PROJECT_ID", "aul-docs-7")

    # Act & Assert
    assert ActionInputs.get_project_id() == "aul-docs-7"


@pytest.mark.parametrize("value", [None, ""], ids=["unset", "empty"])
def test_get_project_id_missing_raises_invalid_configuration(monkeypatch, value):
    # Arrange
    if value is None:
        monkeypatch.delenv("INPUT_PROJECT_ID")
    else:
        monkeypatch.setenv("INPUT_PROJECT_ID", value)

    # Act
    with pytest.raises(ContractError) as error:
        ActionInputs.get_project_id()

    # Assert
    assert error.value.code == Code.INVALID_CONFIGURATION
    assert error.value.message == "`project-id` is required."


@pytest.mark.parametrize(
    "value",
    ["Not A Valid Id", "-leading-hyphen", "abc\n", "Upper-case", "under_score"],
    ids=["spaces-and-capitals", "leading-hyphen", "trailing-newline", "upper-case", "underscore"],
)
def test_get_project_id_malformed_raises_invalid_configuration(monkeypatch, value):
    # Arrange
    monkeypatch.setenv("INPUT_PROJECT_ID", value)

    # Act
    with pytest.raises(ContractError) as error:
        ActionInputs.get_project_id()

    # Assert
    assert error.value.code == Code.INVALID_CONFIGURATION
    assert error.value.message == f"`project-id` {value!r} does not match `^[a-z0-9][a-z0-9-]*$`."


# output-path


def test_get_output_path_default():
    # Act & Assert
    assert ActionInputs.get_output_path() == "./output/collector-gh"


def test_get_output_path_override(monkeypatch):
    # Arrange
    monkeypatch.setenv("INPUT_OUTPUT_PATH", "build/living-doc")

    # Act & Assert
    assert ActionInputs.get_output_path() == "build/living-doc"


# allow-partial


@pytest.mark.parametrize(
    "value, expected",
    [(None, False), ("true", True), ("TRUE", True), ("false", False), ("yes", False)],
    ids=["unset", "true", "upper-case-true", "false", "yes"],
)
def test_is_allow_partial_enabled(monkeypatch, value, expected):
    # Arrange
    if value is not None:
        monkeypatch.setenv("INPUT_ALLOW_PARTIAL", value)

    # Act & Assert
    assert ActionInputs.is_allow_partial_enabled() is expected


# github-server-url


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, "https://github.com"),
        ("https://ghe.example", "https://ghe.example"),
        ("https://ghe.example/", "https://ghe.example"),
    ],
    ids=["default", "override", "trailing-slash"],
)
def test_get_github_server_url(monkeypatch, value, expected):
    # Arrange
    if value is not None:
        monkeypatch.setenv("INPUT_GITHUB_SERVER_URL", value)

    # Act & Assert
    assert ActionInputs.get_github_server_url() == expected


def test_get_github_server_url_that_is_not_an_http_url_raises_invalid_configuration(monkeypatch):
    # Arrange
    monkeypatch.setenv("INPUT_GITHUB_SERVER_URL", "ghe.example")

    # Act
    with pytest.raises(ContractError) as error:
        ActionInputs.get_github_server_url()

    # Assert
    assert error.value.code == Code.INVALID_CONFIGURATION
    assert error.value.message == "`github-server-url` must be an http(s) URL, got 'ghe.example'."


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


_REPOSITORY_GETTERS = [
    ("INPUT_DOC_SOURCE_REPOSITORIES", ActionInputs.get_doc_source_repositories, "doc-source-repositories"),
    ("INPUT_UI_TESTS_REPOSITORIES", ActionInputs.get_ui_tests_repositories, "ui-tests-repositories"),
]


@pytest.mark.parametrize("env_name, getter, input_name", _REPOSITORY_GETTERS, ids=["doc-source", "ui-tests"])
def test_repositories_input_that_is_not_json_raises_invalid_configuration(monkeypatch, env_name, getter, input_name):
    # Arrange
    monkeypatch.setenv(env_name, "[{not json")

    # Act
    with pytest.raises(ContractError) as error:
        getter()

    # Assert
    assert error.value.code == Code.INVALID_CONFIGURATION
    assert error.value.message.startswith(f"`{input_name}` is not valid JSON: ")


@pytest.mark.parametrize(
    "value", ['{"organization-name": "absa-group"}', '"a string"', "7"], ids=["object", "string", "number"]
)
@pytest.mark.parametrize("env_name, getter, input_name", _REPOSITORY_GETTERS, ids=["doc-source", "ui-tests"])
def test_repositories_input_that_is_not_an_array_raises_invalid_configuration(
    monkeypatch, env_name, getter, input_name, value
):
    # Arrange
    monkeypatch.setenv(env_name, value)

    # Act
    with pytest.raises(ContractError) as error:
        getter()

    # Assert
    assert error.value.code == Code.INVALID_CONFIGURATION
    assert error.value.message == f"`{input_name}` must be a JSON array of repository entries."


# validate_user_configuration


def test_validate_user_configuration_correct_behaviour(mocker, monkeypatch):
    # Arrange
    monkeypatch.setenv("INPUT_DOC_SOURCE", "true")
    monkeypatch.setenv("INPUT_DOC_SOURCE_REPOSITORIES", json.dumps([VALID_DOC_SOURCE_ENTRY]))
    mock_log_info = mocker.patch("action_inputs.logger.info")
    mock_log_error = mocker.patch("action_inputs.logger.error")

    # Act
    return_value = ActionInputs().validate_user_configuration()

    # Assert
    assert return_value is True
    mock_log_info.assert_has_calls(
        [
            mocker.call("User configuration validation successfully completed."),
            mocker.call("Mode: `doc-source`: %s.", "Enabled"),
            mocker.call("Mode(doc-source): `doc-source-repositories`: %s.", [VALID_DOC_SOURCE_ENTRY]),
            # A disabled mode's repositories are not read, so not printed.
            mocker.call("Mode: `ui-tests`: %s.", "Disabled"),
            mocker.call("verbose logging: %s", False),
            mocker.call("project-id: %s", "test-project"),
            mocker.call("output-path: %s", "./output/collector-gh"),
            mocker.call("allow-partial: %s", False),
            mocker.call("github-server-url: %s", "https://github.com"),
        ],
        any_order=False,
    )
    mock_log_error.assert_not_called()


def test_validate_user_configuration_reads_no_doc_issues_input(mocker):
    # Arrange
    mock_get_input = mocker.patch("action_inputs.get_action_input", wraps=get_action_input)

    # Act
    assert ActionInputs().validate_user_configuration() is True

    # Assert
    read_inputs = {call.args[0] for call in mock_get_input.call_args_list}
    assert not {name for name in read_inputs if name.startswith("DOC_ISSUES")}


def test_validate_makes_no_network_request(mocker, monkeypatch):
    # Arrange: `github-token` is not read, and any socket connection fails the test.
    monkeypatch.setenv("INPUT_DOC_SOURCE", "true")
    monkeypatch.setenv("INPUT_DOC_SOURCE_REPOSITORIES", json.dumps([VALID_DOC_SOURCE_ENTRY]))
    mocker.patch("socket.socket.connect", side_effect=AssertionError("network access"))
    mocker.patch("socket.socket.connect_ex", side_effect=AssertionError("network access"))

    # Act & Assert
    assert ActionInputs().validate_user_configuration() is True


def test_validate_warns_when_source_modes_enabled_without_repositories(mocker, monkeypatch):
    # Arrange
    monkeypatch.setenv("INPUT_DOC_SOURCE", "true")
    monkeypatch.setenv("INPUT_UI_TESTS", "true")
    mock_log_warning = mocker.patch("action_inputs.logger.warning")

    # Act
    assert ActionInputs().validate_user_configuration() is True

    # Assert
    mock_log_warning.assert_any_call(
        "`%s` is empty; the mode writes an artifact with no records.", "doc-source-repositories"
    )
    mock_log_warning.assert_any_call(
        "`%s` is empty; the mode writes an artifact with no records.", "ui-tests-repositories"
    )


@pytest.mark.parametrize(
    "env, expected_error",
    [
        ({"INPUT_PROJECT_ID": None}, "[INVALID_CONFIGURATION] `project-id` is required."),
        (
            {"INPUT_PROJECT_ID": "Not A Valid Id"},
            "[INVALID_CONFIGURATION] `project-id` 'Not A Valid Id' does not match `^[a-z0-9][a-z0-9-]*$`.",
        ),
        (
            {"INPUT_GITHUB_SERVER_URL": "ghe.example"},
            "[INVALID_CONFIGURATION] `github-server-url` must be an http(s) URL, got 'ghe.example'.",
        ),
        (
            {"INPUT_DOC_SOURCE": "true", "INPUT_DOC_SOURCE_REPOSITORIES": '[{"organization-name": "absa-group"}]'},
            "[INVALID_CONFIGURATION] `doc-source-repositories` entry 0 is malformed: missing key `repository-name`.",
        ),
        (
            {"INPUT_UI_TESTS": "true", "INPUT_UI_TESTS_REPOSITORIES": json.dumps([VALID_UI_TESTS_ENTRY, {"x": 1}])},
            "[INVALID_CONFIGURATION] `ui-tests-repositories` entry 1 is malformed: missing key `organization-name`.",
        ),
    ],
    ids=["missing-project-id", "malformed-project-id", "invalid-server-url", "doc-source-entry", "ui-tests-entry"],
)
def test_validate_fails_on_an_invalid_input(mocker, monkeypatch, env, expected_error):
    # Arrange
    for name, value in env.items():
        if value is None:
            monkeypatch.delenv(name)
        else:
            monkeypatch.setenv(name, value)
    mock_log_error = mocker.patch("action_inputs.logger.error")
    mock_log_info = mocker.patch("action_inputs.logger.info")

    # Act
    return_value = ActionInputs().validate_user_configuration()

    # Assert
    assert return_value is False
    assert _logged(mock_log_error) == [expected_error, "User configuration validation failed."]
    mock_log_info.assert_not_called()  # no effective configuration is printed


def test_validate_reports_every_error_at_once(mocker, monkeypatch):
    # Arrange: four invalid inputs - each must be reported, not just the first.
    monkeypatch.delenv("INPUT_PROJECT_ID")
    monkeypatch.setenv("INPUT_GITHUB_SERVER_URL", "ghe.example")
    monkeypatch.setenv("INPUT_DOC_SOURCE", "true")
    monkeypatch.setenv("INPUT_DOC_SOURCE_REPOSITORIES", "[{not json")
    monkeypatch.setenv("INPUT_UI_TESTS", "true")
    monkeypatch.setenv("INPUT_UI_TESTS_REPOSITORIES", '[{"organization-name": "absa-group"}]')
    mock_log_error = mocker.patch("action_inputs.logger.error")

    # Act
    error_count = ActionInputs()._validate()

    # Assert
    assert error_count == 4
    logged = _logged(mock_log_error)
    assert logged[0] == "[INVALID_CONFIGURATION] `project-id` is required."
    assert logged[1] == "[INVALID_CONFIGURATION] `github-server-url` must be an http(s) URL, got 'ghe.example'."
    assert logged[2].startswith("[INVALID_CONFIGURATION] `doc-source-repositories` is not valid JSON: ")
    assert logged[3] == (
        "[INVALID_CONFIGURATION] `ui-tests-repositories` entry 0 is malformed: missing key `repository-name`."
    )
    assert logged[4:] == ["User configuration validation failed."]


def test_validate_does_not_check_a_disabled_mode_s_malformed_entries(mocker, monkeypatch):
    # Arrange: both modes disabled; their entries are malformed, but a disabled mode's repositories are never read.
    monkeypatch.setenv("INPUT_DOC_SOURCE_REPOSITORIES", '[{"organization-name": "absa-group"}]')
    monkeypatch.setenv("INPUT_UI_TESTS_REPOSITORIES", '[{"repository-name": "aul-ui"}]')
    mock_log_error = mocker.patch("action_inputs.logger.error")

    # Act & Assert
    assert ActionInputs().validate_user_configuration() is True
    mock_log_error.assert_not_called()


@pytest.mark.parametrize(
    "env_name, value",
    [("INPUT_DOC_SOURCE_REPOSITORIES", "[{not json"), ("INPUT_UI_TESTS_REPOSITORIES", '{"organization-name": "x"}')],
    ids=["doc-source-not-json", "ui-tests-not-an-array"],
)
def test_validate_does_not_read_a_disabled_mode_s_invalid_repositories_input(mocker, monkeypatch, env_name, value):
    # Arrange: both modes disabled; one's repositories input cannot even be parsed.
    monkeypatch.setenv(env_name, value)
    mock_log_error = mocker.patch("action_inputs.logger.error")

    # Act & Assert
    assert ActionInputs().validate_user_configuration() is True
    mock_log_error.assert_not_called()
