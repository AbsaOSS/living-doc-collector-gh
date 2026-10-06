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
from pathlib import Path

from living_doc_utilities.contracts.envelope import Source
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_tests import UITestsResult

from ui_tests.collector import GHUITestsCollector
from utils.artifact import build_metadata

FEATURE = """@US_ID:US-26
Feature: Create Domain
    As a user, I want to create domain.

    @AC:US-26-01
    Scenario: First scenario
        Given the user is logged in
        When the user acts
        Then a result happens

    @Regression
    Scenario: Second scenario
        Given another state
        Then another result

    @AC:US-26-02/aspect:owner
    Scenario: First scenario
        Given the same title again
"""

TUTORIAL_FEATURE = """@tutorial
@US_ID:US-26
Feature: Onboarding walkthrough
    @AC:US-26-01
    Scenario: Walkthrough step
        Given the user starts onboarding
        Then the tour begins
"""

MALFORMED_TAG_FEATURE = """Feature: Malformed
    @AC:not-an-id
    Scenario: Malformed tag
        Given a step
"""


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _configure(mocker, repo_dir):
    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[{"organization-name": "absa-group", "repository-name": "aul-ui", "paths": [str(repo_dir)]}],
    )


def test_build_result_returns_the_contract_model(tmp_path, mocker):
    # Arrange
    _write(tmp_path / "repo" / "features" / "create.feature", FEATURE)
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert isinstance(result, UITestsResult)
    assert [s.scenario_id for s in result.scenarios] == [
        "absa-group/aul-ui/features/create.feature/first-scenario",
        "absa-group/aul-ui/features/create.feature/second-scenario",
        "absa-group/aul-ui/features/create.feature/first-scenario-2",
    ]
    assert [(link.id, link.aspect) for link in result.scenarios[0].acceptance_criteria] == [("US-26-01", None)]
    assert [(link.id, link.aspect) for link in result.scenarios[2].acceptance_criteria] == [("US-26-02", "owner")]
    assert result.scenarios[1].tags == ["@Regression"]


def test_collect_writes_a_valid_artifact_read_back_as_the_contract_model(tmp_path, mocker):
    # Arrange
    _write(tmp_path / "repo" / "features" / "create.feature", FEATURE)
    _configure(mocker, tmp_path / "repo")
    output_dir = tmp_path / "output"

    # Act
    assert GHUITestsCollector(str(output_dir)).collect() is True

    # Assert
    output_file = output_dir / "ui-tests" / "ui-tests.json"
    artifact = read_artifact(output_file, "ui-tests")
    assert isinstance(artifact, UITestsResult)
    data = artifact.model_dump(mode="json")
    assert data["schema_version"] == "ui-tests-v1.0.0"
    assert set(data) == {"schema_version", "metadata", "warnings", "scenarios"}
    assert data["metadata"]["stats"]["cardinality"]["scenarios"] == 3


def test_collect_validation_failure_leaves_no_output_file(tmp_path, mocker):
    # Arrange
    _write(tmp_path / "repo" / "features" / "create.feature", FEATURE)
    _configure(mocker, tmp_path / "repo")
    stale = _write(tmp_path / "output" / "ui-tests" / "ui-tests.json", "{}")

    def invalid_metadata(repositories, cardinality):
        metadata = build_metadata(repositories, cardinality)
        # Bypasses model validation, so only write_artifact's own schema validation can catch it.
        metadata.source = Source.model_construct(project_id="Not A Valid Id", systems=["GitHub"])
        return metadata

    mocker.patch("ui_tests.collector.build_metadata", side_effect=invalid_metadata)
    mock_log_error = mocker.patch("utils.artifact.logger.error")

    # Act
    actual = GHUITestsCollector(str(tmp_path / "output")).collect()

    # Assert
    assert actual is False
    assert not stale.exists()
    assert not (tmp_path / "output" / "ui-tests").exists()
    mock_log_error.assert_called_once()
    assert "contract validation" in mock_log_error.call_args.args[0]


def test_collect_returns_false_when_the_result_fails_contract_validation(tmp_path, mocker):
    # Arrange: building the result itself fails validation, and a previous run's artifact is still in place.
    mocker.patch("ui_tests.collector.ActionInputs.get_ui_tests_repositories", return_value=[])
    stale = _write(tmp_path / "ui-tests" / "ui-tests.json", "{}")
    mocker.patch(
        "ui_tests.collector.build_metadata",
        side_effect=lambda *_: Source(project_id="Not A Valid Id", systems=["GitHub"]),
    )
    mock_log_error = mocker.patch("utils.artifact.logger.error")

    # Act
    actual = GHUITestsCollector(str(tmp_path)).collect()

    # Assert
    assert actual is False
    assert not stale.exists()
    assert not (tmp_path / "ui-tests").exists()
    mock_log_error.assert_called_once()
    assert "contract validation" in mock_log_error.call_args.args[0]


def test_collect_returns_false_when_the_previous_output_cannot_be_removed(tmp_path, mocker):
    # Arrange
    mocker.patch("ui_tests.collector.ActionInputs.get_ui_tests_repositories", return_value=[])
    _write(tmp_path / "ui-tests" / "ui-tests.json", "{}")
    mocker.patch("utils.artifact.shutil.rmtree", side_effect=OSError("access denied"))
    mock_build_result = mocker.patch.object(GHUITestsCollector, "build_result")

    # Act & Assert
    assert GHUITestsCollector(str(tmp_path)).collect() is False
    mock_build_result.assert_not_called()


def test_source_ref_points_at_the_feature_file(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    (repo_dir / ".git").mkdir(parents=True)
    _write(repo_dir / "features" / "create.feature", FEATURE)
    _configure(mocker, repo_dir)

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    source_ref = result.scenarios[0].source_ref
    assert source_ref.native_id == "features/create.feature"
    assert source_ref.native_type == "scenario"
    assert source_ref.url == "https://github.com/absa-group/aul-ui/blob/HEAD/features/create.feature"
    assert result.warnings == []


def test_tutorial_file_and_tutorial_scenario_are_not_mined(tmp_path, mocker):
    # Arrange
    _write(tmp_path / "repo" / "onboarding.feature", TUTORIAL_FEATURE)
    _write(
        tmp_path / "repo" / "mixed.feature",
        "Feature: Mixed\n    @tutorial\n    Scenario: Walkthrough\n        Given x\n\n"
        "    Scenario: Real test\n        Given y\n",
    )
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert [s.title for s in result.scenarios] == ["Real test"]


def test_malformed_ac_tag_is_reported_with_the_file_path(tmp_path, mocker):
    # Arrange
    _write(tmp_path / "repo" / "malformed.feature", MALFORMED_TAG_FEATURE)
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    malformed = [w for w in result.warnings if w.code == "MALFORMED_AC"]
    assert len(malformed) == 1
    assert malformed[0].context.startswith("path='malformed.feature' ")


def test_unreadable_file_is_skipped(tmp_path, mocker):
    # Arrange
    _write(tmp_path / "repo" / "create.feature", FEATURE)
    _configure(mocker, tmp_path / "repo")
    original_read_text = Path.read_text

    def deny_feature_files(path, *args, **kwargs):
        if path.suffix == ".feature":
            raise OSError("denied")
        return original_read_text(path, *args, **kwargs)

    mocker.patch("pathlib.Path.read_text", autospec=True, side_effect=deny_feature_files)

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.scenarios == []


def test_non_utf8_file_is_skipped(tmp_path, mocker):
    # Arrange
    (tmp_path / "repo").mkdir()
    (tmp_path / "repo" / "latin1.feature").write_bytes("Feature: Café\n".encode("latin-1"))
    _configure(mocker, tmp_path / "repo")
    mock_log_warning = mocker.patch("ui_tests.collector.logger.warning")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.scenarios == []
    assert mock_log_warning.call_args.args[0] == "Could not read file `%s`: %s - skipping."


def test_invalid_repository_configuration_is_logged_and_skipped(tmp_path, mocker):
    # Arrange
    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[{"organization-name": "absa-group"}],
    )
    mock_log_error = mocker.patch("utils.utils.logger.error")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.scenarios == []
    assert result.metadata.stats.cardinality.sources_configured == 1
    assert result.metadata.stats.cardinality.sources_failed == 1
    mock_log_error.assert_called_once()


def test_file_without_a_kept_scenario_raises_no_source_url_warning(tmp_path, mocker):
    # Arrange: a file outside a git checkout with only a `@tutorial` scenario, and one with no scenario at all.
    _write(tmp_path / "repo" / "tour.feature", "Feature: Tour\n    @tutorial\n    Scenario: Step\n        Given a step\n")
    _write(tmp_path / "repo" / "empty.feature", "Feature: Empty\n")
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.scenarios == []
    assert result.warnings == []


def test_title_without_ascii_letters_gets_the_fallback_slug(tmp_path, mocker):
    # Arrange
    feature = (
        "Feature: Unicode\n"
        "    Scenario: ∑∑\n        Given a step\n"
        "    Scenario: ∆\n        Given a step\n"
        "    Scenario: 日本 語\n        Given a step\n"
    )
    _write(tmp_path / "repo" / "unicode.feature", feature)
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert [s.scenario_id for s in result.scenarios] == [
        "absa-group/aul-ui/unicode.feature/scenario",
        "absa-group/aul-ui/unicode.feature/scenario-2",
        "absa-group/aul-ui/unicode.feature/scenario-3",
    ]


def test_colliding_slugs_never_repeat_a_scenario_id(tmp_path, mocker):
    # Arrange: two `Login`s take `login` and `login-2`, so `Login 2` must not take `login-2` again.
    feature = (
        "Feature: Login\n"
        "    Scenario: Login\n        Given a step\n"
        "    Scenario: Login\n        Given a step\n"
        "    Scenario: Login 2\n        Given a step\n"
    )
    _write(tmp_path / "repo" / "login.feature", feature)
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert [s.scenario_id for s in result.scenarios] == [
        "absa-group/aul-ui/login.feature/login",
        "absa-group/aul-ui/login.feature/login-2",
        "absa-group/aul-ui/login.feature/login-2-2",
    ]


def test_same_file_name_under_two_scan_roots_gets_two_scenario_ids(tmp_path, mocker):
    # Arrange: inside one git checkout, the id carries the path from the repository root, not from the scan root.
    repo_dir = tmp_path / "repo"
    (repo_dir / ".git").mkdir(parents=True)
    login = "Feature: Login\n    Scenario: Login\n        Given a step\n"
    _write(repo_dir / "smoke" / "login.feature", login)
    _write(repo_dir / "regression" / "login.feature", login)
    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "paths": [str(repo_dir / "smoke"), str(repo_dir / "regression")],
            }
        ],
    )

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert sorted(s.scenario_id for s in result.scenarios) == [
        "absa-group/aul-ui/regression/login.feature/login",
        "absa-group/aul-ui/smoke/login.feature/login",
    ]
    assert result.warnings == []


def test_file_reached_through_two_repository_entries_keeps_its_scenarios_once(tmp_path, mocker):
    # Arrange: two entries for the same repository with overlapping scan roots discover the same file twice.
    repo_dir = tmp_path / "repo"
    (repo_dir / ".git").mkdir(parents=True)
    _write(repo_dir / "features" / "login.feature", "Feature: Login\n    Scenario: Login\n        Given a step\n")
    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[
            {"organization-name": "absa-group", "repository-name": "aul-ui", "paths": [str(repo_dir)]},
            {"organization-name": "absa-group", "repository-name": "aul-ui", "paths": [str(repo_dir / "features")]},
        ],
    )

    # Act
    result = GHUITestsCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert [s.scenario_id for s in result.scenarios] == ["absa-group/aul-ui/features/login.feature/login"]
    assert [(w.code, w.context) for w in result.warnings] == [
        ("AUTHORING_ERROR", "path='login.feature' scenario_id='absa-group/aul-ui/features/login.feature/login'")
    ]
