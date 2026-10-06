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
import json
import logging
import os

import pytest
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_tests import UITestsResult

from main import run
from utils.constants import DEFAULT_OUTPUT_PATH

US_FEATURE_TEMPLATE = """# =============================================================================
# LIVING DOC — US-{num} · Story {num}
# =============================================================================
# status:         active
# business_value:
#   - Value for story {num}.
#
# acceptance_criteria:
#
#   AC:US-{num}-01 (v1.0.0 - active)
#     - Criterion for story {num}.
# =============================================================================

@US_ID:US-{num}
Feature: Story {num}
"""

UI_FEATURE_TEMPLATE = """Feature: Login {num}
    @AC:US-{num}-01
    Scenario: Login {num}
        Given a step
"""

# run


def test_run_with_zero_modes_enabled(mocker):
    # Arrange
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=True)

    mock_log_info = mocker.patch("logging.getLogger").return_value.info
    mocker.patch.dict(os.environ, {"INPUT_DOC_ISSUES": "false"})
    mock_doc_source_collector = mocker.patch("main.GHDocSourceCollector")
    expected_output_path = os.path.abspath(DEFAULT_OUTPUT_PATH)

    # Act
    run()

    # Assert
    mock_doc_source_collector.assert_not_called()
    mock_log_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - starting."),
            mocker.call("Liv-Doc collector for GitHub - `doc-source` mode disabled."),
            mocker.call("Liv-Doc collector for GitHub - `ui-tests` mode disabled."),
            mocker.call("Liv-Doc collector for GitHub - root output path set to `%s`.", expected_output_path),
            mocker.call("Liv-Doc collector for GitHub - ending."),
        ],
        any_order=False,
    )


def test_run_doc_issues_mode_fails_at_start_as_planned(mocker):
    # Arrange
    mocker.patch.dict(os.environ, {"INPUT_DOC_ISSUES": "true"})
    mock_logger = mocker.patch("logging.getLogger").return_value
    mock_validate = mocker.patch("action_inputs.ActionInputs.validate_user_configuration")
    mock_doc_source_collector = mocker.patch("main.GHDocSourceCollector")
    mock_ui_tests_collector = mocker.patch("main.GHUITestsCollector")

    # Act
    with pytest.raises(SystemExit) as exit_info:
        run()

    # Assert
    assert exit_info.value.code == 1
    mock_logger.error.assert_called_once()
    fmt, error = mock_logger.error.call_args.args
    assert fmt % error == (
        "[INVALID_CONFIGURATION] `doc-issues` mode is planned and not available in this version"
    )
    mock_validate.assert_not_called()
    mock_doc_source_collector.assert_not_called()
    mock_ui_tests_collector.assert_not_called()


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
            mocker.call("Liv-Doc collector for GitHub - `doc-source` mode disabled."),
            mocker.call("Liv-Doc collector for GitHub - `ui-tests` mode disabled."),
            mocker.call("Liv-Doc collector for GitHub - root output path set to `%s`.", "/unit/test/output/path"),
            mocker.call("Liv-Doc collector for GitHub - ending."),
        ],
        any_order=False,
    )

    mock_exit.assert_called_once_with(1)


def test_run_doc_source_and_ui_tests_modes_success(mocker):
    # Arrange
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=True)
    mocker.patch("main.ActionInputs.is_doc_issues_mode_enabled", return_value=False)
    mocker.patch("main.ActionInputs.is_doc_source_mode_enabled", return_value=True)
    mocker.patch("main.ActionInputs.is_ui_tests_mode_enabled", return_value=True)
    mocker.patch("main.GHDocSourceCollector.collect", return_value=True)
    mocker.patch("main.GHUITestsCollector.collect", return_value=True)
    mock_log_info = mocker.patch("logging.getLogger").return_value.info

    # Act
    run()

    # Assert
    mock_log_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - Starting the `doc-source` mode."),
            mocker.call("Liv-Doc collector for GitHub - `doc-source` mode completed successfully."),
            mocker.call("Liv-Doc collector for GitHub - Starting the `ui-tests` mode."),
            mocker.call("Liv-Doc collector for GitHub - `ui-tests` mode completed successfully."),
        ],
        any_order=False,
    )


def test_run_doc_source_and_ui_tests_modes_failed(mocker):
    # Arrange
    mocker.patch("action_inputs.ActionInputs.validate_user_configuration", return_value=True)
    mocker.patch("main.ActionInputs.is_doc_issues_mode_enabled", return_value=False)
    mocker.patch("main.ActionInputs.is_doc_source_mode_enabled", return_value=True)
    mocker.patch("main.ActionInputs.is_ui_tests_mode_enabled", return_value=True)
    mocker.patch("main.GHDocSourceCollector.collect", return_value=False)
    mocker.patch("main.GHUITestsCollector.collect", return_value=False)
    mock_log_info = mocker.patch("logging.getLogger").return_value.info
    mock_exit = mocker.patch("sys.exit")

    # Act
    run()

    # Assert
    mock_log_info.assert_has_calls(
        [
            mocker.call("Liv-Doc collector for GitHub - Starting the `doc-source` mode."),
            mocker.call("Liv-Doc collector for GitHub - `doc-source` mode failed."),
            mocker.call("Liv-Doc collector for GitHub - Starting the `ui-tests` mode."),
            mocker.call("Liv-Doc collector for GitHub - `ui-tests` mode failed."),
        ],
        any_order=False,
    )
    mock_exit.assert_called_once_with(1)



# end to end: `run()` over local checkouts, every input set as the action sets it


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_story(directory, num):
    _write(directory / f"story_{num}.feature", US_FEATURE_TEMPLATE.format(num=num))


def _write_ui_feature(directory, num):
    _write(directory / f"login_{num}.feature", UI_FEATURE_TEMPLATE.format(num=num))


# Each source mode as `run()` reads it: its switch, its `*-repositories` input, the key of the paths it scans,
# how to author one record, its artifact, and the ids of the records an artifact holds.
_MODES = {
    "doc-source": {
        "switch": "INPUT_DOC_SOURCE",
        "repositories": "INPUT_DOC_SOURCE_REPOSITORIES",
        "paths_key": "us-paths",
        "write": _write_story,
        "artifact": ("doc-source", "doc-source.json"),
        "record_ids": lambda artifact: [e.entity_id for e in artifact.user_stories],
        "first_source_ids": ["US-1"],
    },
    "ui-tests": {
        "switch": "INPUT_UI_TESTS",
        "repositories": "INPUT_UI_TESTS_REPOSITORIES",
        "paths_key": "paths",
        "write": _write_ui_feature,
        "artifact": ("ui-tests", "ui-tests.json"),
        "record_ids": lambda artifact: [s.scenario_id for s in artifact.scenarios],
        "first_source_ids": ["absa-group/repo-a/login_1.feature/login-1"],
    },
}


def _entry(mode, repository_name, *paths):
    return {
        "organization-name": "absa-group",
        "repository-name": repository_name,
        _MODES[mode]["paths_key"]: [str(path) for path in paths],
    }


def _enable(monkeypatch, mode, entries):
    monkeypatch.setenv(_MODES[mode]["switch"], "true")
    monkeypatch.setenv(_MODES[mode]["repositories"], json.dumps(entries))


def _artifact_path(output_root, mode):
    return output_root.joinpath(*_MODES[mode]["artifact"])


def _read(output_root, mode):
    return read_artifact(_artifact_path(output_root, mode), mode)


def _files_under(directory):
    return sorted(p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file())


def _messages(caplog, level):
    return [record.getMessage() for record in caplog.records if record.levelno == level]


@pytest.fixture(name="e2e")
def _e2e(tmp_path, mocker, caplog):
    """`run()` end to end: the action's own logging setup is skipped, so `caplog` sees every record."""
    mocker.patch("main.setup_logging")
    caplog.set_level(logging.INFO)
    return tmp_path


def _enable_both_modes(monkeypatch, src):
    _write_story(src / "us", 1)
    _write_ui_feature(src / "ui", 1)
    _enable(monkeypatch, "doc-source", [_entry("doc-source", "aul-ui", src / "us")])
    _enable(monkeypatch, "ui-tests", [_entry("ui-tests", "aul-ui", src / "ui")])


# AC1: output layout


def test_default_run_writes_each_mode_under_output_collector_gh(e2e, monkeypatch):
    # Arrange: no `output-path`, so the default `./output/collector-gh` resolves against the working directory.
    monkeypatch.chdir(e2e)
    monkeypatch.setenv("INPUT_PROJECT_ID", "aul-docs")
    _enable_both_modes(monkeypatch, e2e / "src")
    output_root = e2e / "output" / "collector-gh"

    # Act
    run()

    # Assert
    assert _files_under(e2e / "output") == [
        "collector-gh/doc-source/doc-source.json",
        "collector-gh/ui-tests/ui-tests.json",
    ]
    assert (e2e / "github_output.txt").read_text(encoding="utf-8") == f"output-path={output_root}\n"
    doc_source = _read(output_root, "doc-source")
    ui_tests = _read(output_root, "ui-tests")
    assert isinstance(doc_source, DocSourceResult)
    assert isinstance(ui_tests, UITestsResult)
    # AC2: every written output carries the configured project-id.
    assert doc_source.metadata.source.project_id == "aul-docs"
    assert ui_tests.metadata.source.project_id == "aul-docs"


def test_two_runs_with_different_output_paths_do_not_touch_each_other(e2e, monkeypatch):
    # Arrange: relative `output-path`s, resolved against the working directory.
    monkeypatch.chdir(e2e)
    _enable_both_modes(monkeypatch, e2e / "src")
    root_a = e2e / "output" / "a"
    root_b = e2e / "output" / "b"

    # Act: run A, then run B.
    monkeypatch.setenv("INPUT_OUTPUT_PATH", "output/a")
    run()
    files_a = {path: path.read_bytes() for path in root_a.rglob("*") if path.is_file()}
    monkeypatch.setenv("INPUT_OUTPUT_PATH", "output/b")
    run()

    # Assert: A's files are untouched by B.
    assert sorted(path.relative_to(root_a).as_posix() for path in files_a) == [
        "doc-source/doc-source.json",
        "ui-tests/ui-tests.json",
    ]
    assert {path: path.read_bytes() for path in root_a.rglob("*") if path.is_file()} == files_a
    assert _files_under(root_b) == ["doc-source/doc-source.json", "ui-tests/ui-tests.json"]

    # Arrange: a stale file in B's mode directory, and an unrelated file beside it.
    stale = _write(root_b / "doc-source" / "stale.txt", "stale")
    unrelated = _write(root_b / "notes.txt", "keep")

    # Act: run B again.
    run()

    # Assert: the re-run clears only B's own `<mode>/` directories.
    assert not stale.exists()
    assert unrelated.read_text(encoding="utf-8") == "keep"
    assert _files_under(root_b) == ["doc-source/doc-source.json", "notes.txt", "ui-tests/ui-tests.json"]
    assert {path: path.read_bytes() for path in root_a.rglob("*") if path.is_file()} == files_a
    assert (e2e / "github_output.txt").read_text(encoding="utf-8").splitlines() == [
        f"output-path={root_a}",
        f"output-path={root_b}",
        f"output-path={root_b}",
    ]


# AC2: required, validated inputs


@pytest.mark.parametrize(
    "project_id, expected_error",
    [
        (None, "[INVALID_CONFIGURATION] `project-id` is required."),
        (
            "Not A Valid Id",
            "[INVALID_CONFIGURATION] `project-id` 'Not A Valid Id' does not match `^[a-z0-9][a-z0-9-]*$`.",
        ),
        (
            "-leading-hyphen",
            "[INVALID_CONFIGURATION] `project-id` '-leading-hyphen' does not match `^[a-z0-9][a-z0-9-]*$`.",
        ),
    ],
    ids=["missing", "spaces-and-capitals", "leading-hyphen"],
)
def test_invalid_project_id_fails_the_run_and_no_mode_writes(e2e, monkeypatch, caplog, project_id, expected_error):
    # Arrange
    _enable_both_modes(monkeypatch, e2e / "src")
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(e2e / "output"))
    if project_id is None:
        monkeypatch.delenv("INPUT_PROJECT_ID")
    else:
        monkeypatch.setenv("INPUT_PROJECT_ID", project_id)

    # Act
    with pytest.raises(SystemExit) as exit_info:
        run()

    # Assert
    assert exit_info.value.code == 1
    assert _messages(caplog, logging.ERROR) == [expected_error, "User configuration validation failed."]
    assert not (e2e / "output").exists()


def test_malformed_repository_entry_fails_the_run_and_no_mode_writes(e2e, monkeypatch, caplog):
    # Arrange: the ui-tests configuration is valid; the doc-source entry has no `repository-name`.
    _enable_both_modes(monkeypatch, e2e / "src")
    monkeypatch.setenv(
        "INPUT_DOC_SOURCE_REPOSITORIES",
        json.dumps([{"organization-name": "absa-group", "us-paths": [str(e2e / "src" / "us")]}]),
    )
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(e2e / "output"))

    # Act
    with pytest.raises(SystemExit) as exit_info:
        run()

    # Assert
    assert exit_info.value.code == 1
    assert _messages(caplog, logging.ERROR) == [
        "[INVALID_CONFIGURATION] `doc-source-repositories` entry 0 is malformed: missing key `repository-name`.",
        "User configuration validation failed.",
    ]
    assert not (e2e / "output").exists()


# AC3: local paths only - no token, no network


def test_run_over_local_paths_needs_no_token_and_no_network(e2e, monkeypatch, mocker):
    # Arrange
    monkeypatch.delenv("INPUT_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    mock_connect = mocker.patch("socket.socket.connect", side_effect=OSError("network blocked"))
    mock_connect_ex = mocker.patch("socket.socket.connect_ex", side_effect=OSError("network blocked"))
    _enable_both_modes(monkeypatch, e2e / "src")
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(e2e / "output"))
    mock_exit = mocker.patch("sys.exit")

    # Act
    run()

    # Assert
    mock_exit.assert_not_called()
    mock_connect.assert_not_called()
    mock_connect_ex.assert_not_called()
    assert isinstance(_read(e2e / "output", "doc-source"), DocSourceResult)
    assert isinstance(_read(e2e / "output", "ui-tests"), UITestsResult)


# AC4: github-server-url


def test_invalid_github_server_url_fails_the_run_and_no_mode_writes(e2e, monkeypatch, caplog):
    # Arrange
    _enable_both_modes(monkeypatch, e2e / "src")
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(e2e / "output"))
    monkeypatch.setenv("INPUT_GITHUB_SERVER_URL", "ghe.example")

    # Act
    with pytest.raises(SystemExit) as exit_info:
        run()

    # Assert
    assert exit_info.value.code == 1
    assert _messages(caplog, logging.ERROR) == [
        "[INVALID_CONFIGURATION] `github-server-url` must be an http(s) URL, got 'ghe.example'.",
        "User configuration validation failed.",
    ]
    assert not (e2e / "output").exists()


# AC5: per-source failures (R13)


def _two_sources_second_missing(monkeypatch, src, mode):
    """Entry 0 answers with one record; entry 1 authors a record too, but one of its paths is missing."""
    _MODES[mode]["write"](src / "a", 1)
    _MODES[mode]["write"](src / "b", 2)
    missing = src / "b_missing"
    _enable(monkeypatch, mode, [_entry(mode, "repo-a", src / "a"), _entry(mode, "repo-b", src / "b", missing)])
    return missing


@pytest.mark.parametrize("mode", ["doc-source", "ui-tests"])
def test_a_failed_source_fails_the_run_and_its_mode_writes_nothing(e2e, monkeypatch, caplog, mode):
    # Arrange
    missing = _two_sources_second_missing(monkeypatch, e2e / "src", mode)
    output_root = e2e / "output"
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(output_root))

    # Act
    with pytest.raises(SystemExit) as exit_info:
        run()

    # Assert
    assert exit_info.value.code == 1
    assert _messages(caplog, logging.ERROR) == [
        f"[SOURCE_UNAVAILABLE] Configured path `{missing}` does not exist or is not a directory. "
        f"(input='{mode}-repositories' entry=1 repository='absa-group/repo-b')",
        f"The `{mode}` mode failed, nothing written: [SOURCE_UNAVAILABLE] 1 of 2 configured sources failed.",
    ]
    assert f"Liv-Doc collector for GitHub - `{mode}` mode failed." in _messages(caplog, logging.INFO)
    assert not output_root.joinpath(_MODES[mode]["artifact"][0]).exists()


@pytest.mark.parametrize("mode", ["doc-source", "ui-tests"])
def test_allow_partial_writes_the_sources_that_answered_and_succeeds(e2e, monkeypatch, caplog, mode):
    # Arrange
    missing = _two_sources_second_missing(monkeypatch, e2e / "src", mode)
    output_root = e2e / "output"
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(output_root))
    monkeypatch.setenv("INPUT_ALLOW_PARTIAL", "true")
    context = f"input='{mode}-repositories' entry=1 repository='absa-group/repo-b'"

    # Act
    run()

    # Assert
    artifact = _read(output_root, mode)
    assert _MODES[mode]["record_ids"](artifact) == _MODES[mode]["first_source_ids"]
    unavailable = [w for w in artifact.warnings if w.code == "SOURCE_UNAVAILABLE"]
    assert [(w.context, w.message) for w in unavailable] == [
        (context, f"Configured path `{missing}` does not exist or is not a directory.")
    ]
    assert artifact.warnings[0] == unavailable[0]
    assert artifact.metadata.stats.cardinality.sources_configured == 2
    assert artifact.metadata.stats.cardinality.sources_failed == 1
    assert f"[SOURCE_UNAVAILABLE] Configured path `{missing}` does not exist or is not a directory. ({context})" in (
        _messages(caplog, logging.WARNING)
    )
    assert _messages(caplog, logging.ERROR) == []


def test_allow_partial_still_fails_the_run_when_every_source_failed(e2e, monkeypatch, caplog):
    # Arrange
    src = e2e / "src"
    _enable(
        monkeypatch,
        "doc-source",
        [_entry("doc-source", "repo-a", src / "missing_a"), _entry("doc-source", "repo-b", src / "missing_b")],
    )
    output_root = e2e / "output"
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(output_root))
    monkeypatch.setenv("INPUT_ALLOW_PARTIAL", "true")

    # Act
    with pytest.raises(SystemExit) as exit_info:
        run()

    # Assert
    assert exit_info.value.code == 1
    assert [m for m in _messages(caplog, logging.WARNING) if m.startswith("[SOURCE_UNAVAILABLE]")] == [
        f"[SOURCE_UNAVAILABLE] Configured path `{src / 'missing_a'}` does not exist or is not a directory. "
        "(input='doc-source-repositories' entry=0 repository='absa-group/repo-a')",
        f"[SOURCE_UNAVAILABLE] Configured path `{src / 'missing_b'}` does not exist or is not a directory. "
        "(input='doc-source-repositories' entry=1 repository='absa-group/repo-b')",
    ]
    assert _messages(caplog, logging.ERROR) == [
        "The `doc-source` mode failed, nothing written: [SOURCE_UNAVAILABLE] 2 of 2 configured sources failed."
    ]
    assert not (output_root / "doc-source").exists()


@pytest.mark.parametrize("mode", ["doc-source", "ui-tests"])
def test_existing_but_empty_source_is_an_empty_source_warning_and_the_run_succeeds(e2e, monkeypatch, mocker, mode):
    # Arrange: entry 0 answers; entry 1's directory exists but holds no source file.
    src = e2e / "src"
    _MODES[mode]["write"](src / "a", 1)
    (src / "empty").mkdir()
    _enable(monkeypatch, mode, [_entry(mode, "repo-a", src / "a"), _entry(mode, "repo-empty", src / "empty")])
    output_root = e2e / "output"
    monkeypatch.setenv("INPUT_OUTPUT_PATH", str(output_root))
    mock_exit = mocker.patch("sys.exit")

    # Act
    run()

    # Assert
    mock_exit.assert_not_called()
    artifact = _read(output_root, mode)
    assert _MODES[mode]["record_ids"](artifact) == _MODES[mode]["first_source_ids"]
    assert [(w.code, w.context) for w in artifact.warnings if w.code == "EMPTY_SOURCE"] == [
        ("EMPTY_SOURCE", f"input='{mode}-repositories' entry=1 repository='absa-group/repo-empty'")
    ]
    assert artifact.metadata.stats.cardinality.sources_failed == 0
