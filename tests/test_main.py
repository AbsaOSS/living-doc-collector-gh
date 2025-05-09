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
import os

from main import run
from utils.constants import OUTPUT_PATH


# run


def test_run_correct_behaviour_with_all_regimes_enabled(mocker):
    # Arrange
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=True)

    expected_output_path = os.path.abspath(OUTPUT_PATH)
    mock_log_info = mocker.patch("logging.getLogger").return_value.info
    mocker.patch.dict(os.environ, {"INPUT_GITHUB_TOKEN": "fake_token",
                                   "INPUT_DOC_ISSUES": "true"})
    mock_doc_issues_collector = mocker.patch("main.GHDocIssuesCollector")
    mock_doc_issues_collector.generate = mocker.MagicMock(return_value=True)

    # Act
    run()

    # Assert
    # mock_doc_issues_collector.assert_called_once()
    mock_log_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - starting."),
            mocker.call("Liv-Doc collector for GitHub - Starting the `doc-issues` mode."),
            mocker.call("Liv-Doc collector for GitHub - `doc-issues` mode completed successfully."),
            mocker.call("Liv-Doc collector for GitHub - root output path set to `%s`.", expected_output_path),
            mocker.call("Liv-Doc collector for GitHub - ending."),
        ],
        any_order=False,
    )


def test_run_with_zero_modes_enabled(mocker):
    # Arrange
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=True)

    mock_log_info = mocker.patch("logging.getLogger").return_value.info
    mocker.patch.dict(os.environ, {"INPUT_GITHUB_TOKEN": "fake_token", "INPUT_DOC_ISSUES": "false"})
    mock_doc_issues_collector = mocker.patch("main.GHDocIssuesCollector")
    expected_output_path = os.path.abspath("./output")  # Adding the default value

    # Act
    run()

    # Assert
    mock_doc_issues_collector.assert_not_called()
    mock_log_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - starting."),
            mocker.call("Liv-Doc collector for GitHub - `doc-issues` mode disabled."),
            mocker.call("Liv-Doc collector for GitHub - root output path set to `%s`.", expected_output_path),
            mocker.call("Liv-Doc collector for GitHub - ending."),
        ],
        any_order=False,
    )


def test_run_doc_issues_mode_failed(mocker):
    mock_log_info = mocker.patch("logging.getLogger").return_value.info
    mock_exit = mocker.patch("sys.exit")
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=True)
    mocker.patch("action_inputs.ActionInputs.is_doc_issues_mode_enabled", return_value=True)
    mocker.patch("main.GHDocIssuesCollector.collect", return_value=False)
    expected_output_path = os.path.abspath("./output")  # Adding the default value

    mocker.patch.dict(
        os.environ,
        {
            "INPUT_GITHUB_TOKEN": "fake_token",
            "INPUT_DOC_ISSUES": "true",
            "INPUT_OUTPUT_PATH": "./user/output/path",
        },
    )

    run()

    mock_log_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - starting."),
            mocker.call("Liv-Doc collector for GitHub - Starting the `doc-issues` mode."),
            mocker.call("Liv-Doc collector for GitHub - `doc-issues` mode failed."),
            mocker.call("Liv-Doc collector for GitHub - root output path set to `%s`.", expected_output_path),
            mocker.call("Liv-Doc collector for GitHub - ending."),
        ],
        any_order=False,
    )
    mock_exit.assert_called_once_with(1)


def test_validate_user_configuration_failed(mocker):
    # Mock ActionInputs.validate_user_configuration to return False
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=False)
    mocker.patch("main.make_absolute_path", return_value="/unit/test/output/path")  # Mock make_absolute_path

    mock_logger_info = mocker.patch("logging.getLogger").return_value.info
    mock_exit = mocker.patch("sys.exit")

    # Run the function
    run()

    # Assert logger and sys.exit were called
    mock_logger_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - starting."),
            mocker.call("Liv-Doc collector for GitHub - user configuration validation failed."),
            mocker.call("Liv-Doc collector for GitHub - `doc-issues` mode disabled."),
            mocker.call("Liv-Doc collector for GitHub - root output path set to `%s`.", "/unit/test/output/path"),
            mocker.call("Liv-Doc collector for GitHub - ending."),

        ],
        any_order=False,
    )

    mock_exit.assert_called_once_with(1)


def test_validate_query_formats_failed(mocker):
    # Mock ActionInputs.validate_user_configuration to return True
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=True)
    mocker.patch("main.make_absolute_path", return_value="/unit/test/output/path")  # Mock make_absolute_path

    # Mock validate_query_formats to return False
    mocker.patch("main.validate_query_formats", return_value=False)
    mock_logger_info = mocker.patch("logging.getLogger").return_value.info
    mock_exit = mocker.patch("sys.exit")

    # Run the function
    run()

    # Assert logger and sys.exit were called
    mock_logger_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - starting."),
            mocker.call("Liv-Doc collector for GitHub - query format validation failed."),
            mocker.call("Liv-Doc collector for GitHub - `doc-issues` mode disabled."),
            mocker.call("Liv-Doc collector for GitHub - root output path set to `%s`.", "/unit/test/output/path"),
            mocker.call("Liv-Doc collector for GitHub - ending."),

        ],
        any_order=False,
    )

    mock_exit.assert_called_once_with(1)
