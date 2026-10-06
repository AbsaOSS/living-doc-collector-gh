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

import pytest
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import Source
from living_doc_utilities.contracts.io import read_artifact

from doc_source.collector import GHDocSourceCollector
from utils.artifact import build_metadata

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

FUNC_FEATURE_TEMPLATE = """# =============================================================================
# LIVING DOC — FUNC-{num} · Functionality {num}
# =============================================================================
# status:    active
# parent:    FEAT-{num}
# func_type: button_action
#
# acceptance_criteria:
#
#   AC:FUNC-{num}-01 (v1.0.0 - active)
#     - Criterion for functionality {num}.
# =============================================================================

@FUNC_ID:FUNC-{num}
Feature: Functionality {num}
"""

TS_PAGE_OBJECT_TEMPLATE = """/* =============================================================================
 * LIVING DOC — FEAT-{num} · Feature {num}
 * =============================================================================
 * surface_type:          UI
 * route:                 /feat-{num}
 * owners:                Test Team
 * purpose:               Purpose of feature {num}.
 * user_stories:          US-{num}
 * functionalities:       FUNC-{num}
 * external_dependencies: none
 * page-object:           Feature{num}Page.ts
 * ============================================================================= */

export class Feature{num}Page {{}}
"""

TS_CROSS_REFERENCE_TEMPLATE = """/* =============================================================================
 * LIVING DOC — FEAT-{num} · Feature {num} [cross-reference]
 * =============================================================================
 * parent-feat: FEAT-{num}
 * route:       /feat-{num}/details
 * owners:      Test Team
 * purpose:     Details of feature {num}.
 * page-object: Feature{num}DetailsPage.ts
 * ============================================================================= */
"""


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _configure(mocker, repo_dir):
    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "us-paths": [str(repo_dir / "us")],
                "func-paths": [str(repo_dir / "func")],
                "pages-paths": [str(repo_dir / "pages")],
            }
        ],
    )


def _write_entity_set(repo_dir, num=1):
    _write(repo_dir / "us" / f"story_{num}.feature", US_FEATURE_TEMPLATE.format(num=num))
    _write(repo_dir / "func" / f"func_{num}.feature", FUNC_FEATURE_TEMPLATE.format(num=num))
    _write(repo_dir / "pages" / f"Feature{num}Page.ts", TS_PAGE_OBJECT_TEMPLATE.format(num=num))


# build_result / collect


def test_build_result_returns_the_contract_model(tmp_path, mocker):
    # Arrange
    _write_entity_set(tmp_path / "repo")
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert isinstance(result, DocSourceResult)
    assert [e.entity_id for e in result.user_stories] == ["US-1"]
    assert [e.entity_id for e in result.functionalities] == ["FUNC-1"]
    assert [e.entity_id for e in result.features] == ["FEAT-1"]
    assert result.features[0].state == "active"
    assert result.features[0].state_origin == "derived"


def test_collect_writes_a_valid_artifact_read_back_as_the_contract_model(tmp_path, mocker):
    # Arrange
    _write_entity_set(tmp_path / "repo")
    _configure(mocker, tmp_path / "repo")
    output_dir = tmp_path / "output"

    # Act
    assert GHDocSourceCollector(str(output_dir)).collect() is True

    # Assert
    output_file = output_dir / "doc-source" / "doc-source.json"
    artifact = read_artifact(output_file, "doc-source")
    assert isinstance(artifact, DocSourceResult)
    data = artifact.model_dump(mode="json")
    assert data["schema_version"] == "doc-source-v1.0.0"
    assert set(data) == {"schema_version", "metadata", "warnings", "user_stories", "features", "functionalities"}
    assert data["metadata"]["source"]["project_id"] == "unset-project"
    assert data["metadata"]["source"]["repositories"] == ["absa-group/aul-ui"]
    assert data["metadata"]["stats"]["cardinality"]["entities"] == 3
    assert data["metadata"]["stats"]["cardinality"]["sources_configured"] == 1


def test_collect_with_no_repositories_writes_empty_lists(tmp_path, mocker):
    # Arrange
    mocker.patch("doc_source.collector.ActionInputs.get_doc_source_repositories", return_value=[])

    # Act
    assert GHDocSourceCollector(str(tmp_path)).collect() is True

    # Assert
    artifact = read_artifact(tmp_path / "doc-source" / "doc-source.json", "doc-source")
    assert artifact.user_stories == artifact.features == artifact.functionalities == []


def test_collect_validation_failure_leaves_no_output_file(tmp_path, mocker):
    # Arrange
    _write_entity_set(tmp_path / "repo")
    _configure(mocker, tmp_path / "repo")
    stale = _write(tmp_path / "output" / "doc-source" / "doc-source.json", "{}")

    def invalid_metadata(repositories, cardinality):
        metadata = build_metadata(repositories, cardinality)
        # Bypasses model validation, so only write_artifact's own schema validation can catch it.
        metadata.source = Source.model_construct(project_id="Not A Valid Id", systems=["GitHub"])
        return metadata

    mocker.patch("doc_source.collector.build_metadata", side_effect=invalid_metadata)
    mock_log_error = mocker.patch("utils.artifact.logger.error")

    # Act
    actual = GHDocSourceCollector(str(tmp_path / "output")).collect()

    # Assert
    assert actual is False
    assert not stale.exists()
    assert not (tmp_path / "output" / "doc-source").exists()
    mock_log_error.assert_called_once()
    assert "contract validation" in mock_log_error.call_args.args[0]


def test_collect_write_failure_returns_false(tmp_path, mocker):
    # Arrange
    mocker.patch("doc_source.collector.ActionInputs.get_doc_source_repositories", return_value=[])
    mocker.patch("utils.artifact.write_artifact", side_effect=OSError("disk full"))

    # Act & Assert
    assert GHDocSourceCollector(str(tmp_path)).collect() is False


def test_collect_returns_false_when_the_previous_output_cannot_be_removed(tmp_path, mocker):
    # Arrange
    mocker.patch("doc_source.collector.ActionInputs.get_doc_source_repositories", return_value=[])
    _write(tmp_path / "doc-source" / "doc-source.json", "{}")
    mocker.patch("utils.artifact.shutil.rmtree", side_effect=OSError("access denied"))

    # Act & Assert
    assert GHDocSourceCollector(str(tmp_path)).collect() is False


def test_collect_returns_false_when_the_result_fails_contract_validation(tmp_path, mocker):
    # Arrange: building the result itself fails validation, and a previous run's artifact is still in place.
    mocker.patch("doc_source.collector.ActionInputs.get_doc_source_repositories", return_value=[])
    stale = _write(tmp_path / "doc-source" / "doc-source.json", "{}")
    mocker.patch(
        "doc_source.collector.build_metadata",
        side_effect=lambda *_: Source(project_id="Not A Valid Id", systems=["GitHub"]),
    )
    mock_log_error = mocker.patch("utils.artifact.logger.error")

    # Act
    actual = GHDocSourceCollector(str(tmp_path)).collect()

    # Assert
    assert actual is False
    assert not stale.exists()
    assert not (tmp_path / "doc-source").exists()
    mock_log_error.assert_called_once()
    assert "contract validation" in mock_log_error.call_args.args[0]


# identity


def test_entity_without_parseable_id_is_skipped_and_reported(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    _write(
        repo_dir / "us" / "no_id.feature",
        US_FEATURE_TEMPLATE.format(num=1).replace("US-1 · Story 1", "Story without an id"),
    )
    _configure(mocker, repo_dir)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.user_stories == []
    assert result.metadata.stats.cardinality.entities_skipped == 1
    missing = [w for w in result.warnings if w.code == "MISSING_ENTITY_ID"]
    assert len(missing) == 1
    assert missing[0].context.startswith("path='no_id.feature' ")
    assert "title='Story without an id'" in missing[0].context


# source_ref


def test_source_ref_points_at_the_file_in_its_repository(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    (repo_dir / ".git").mkdir(parents=True)
    _write_entity_set(repo_dir)
    _configure(mocker, repo_dir)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    story_ref = result.user_stories[0].source_ref
    assert story_ref.system == "GitHub"
    assert story_ref.native_id == "us/story_1.feature"
    assert story_ref.native_type == "feature-file"
    assert story_ref.url == "https://github.com/absa-group/aul-ui/blob/HEAD/us/story_1.feature"
    assert story_ref.tracker_state == "committed"
    assert result.features[0].source_ref.native_type == "page-object"
    assert not [w for w in result.warnings if w.code == "NO_SOURCE_URL"]


def test_source_ref_outside_a_git_checkout_reports_no_source_url(tmp_path, mocker):
    # Arrange
    _write_entity_set(tmp_path / "repo")
    _configure(mocker, tmp_path / "repo")
    mocker.patch("utils.artifact.find_repo_root", return_value=None)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.user_stories[0].source_ref.url == ""
    assert result.user_stories[0].source_ref.native_id == "story_1.feature"
    assert len([w for w in result.warnings if w.code == "NO_SOURCE_URL"]) == 3


# PageObject files


def test_cross_reference_page_is_attached_to_its_feature(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    _write_entity_set(repo_dir)
    _write(repo_dir / "pages" / "Feature1DetailsPage.ts", TS_CROSS_REFERENCE_TEMPLATE.format(num=1))
    _configure(mocker, repo_dir)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    pages = result.features[0].pages
    assert [(p.route, p.is_primary) for p in pages] == [("/feat-1", True), ("/feat-1/details", False)]


def test_cross_reference_page_without_its_feature_is_reported(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    _write(repo_dir / "pages" / "Feature7DetailsPage.ts", TS_CROSS_REFERENCE_TEMPLATE.format(num=7))
    _configure(mocker, repo_dir)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.features == []
    unresolved = [w for w in result.warnings if w.code == "UNRESOLVED_RELATION"]
    assert [w.context for w in unresolved] == ["path='Feature7DetailsPage.ts' target='FEAT-7'"]
    assert result.metadata.stats.cardinality.unresolved_refs == 1


def test_typescript_file_without_header_is_ignored(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    _write(repo_dir / "pages" / "helpers.ts", "export const noop = (): void => undefined;\n")
    _configure(mocker, repo_dir)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.features == []
    assert result.warnings == []
    assert result.metadata.stats.cardinality.entities_skipped == 0


@pytest.mark.parametrize(
    "text",
    [
        "/* eslint-disable no-console */\nexport const log = (message: string): void => console.log(message);\n",
        "/**\n * Shared selectors for every page.\n */\nexport const ROOT = '#app';\n",
    ],
    ids=["eslint-directive", "jsdoc"],
)
def test_typescript_file_whose_first_comment_is_not_a_header_is_ignored(tmp_path, mocker, text):
    # Arrange
    repo_dir = tmp_path / "repo"
    _write(repo_dir / "pages" / "helpers.ts", text)
    _configure(mocker, repo_dir)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.features == []
    assert result.warnings == []
    assert result.metadata.stats.cardinality.entities_skipped == 0


def test_living_doc_banner_after_another_comment_is_reported_not_skipped_silently(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    _write(repo_dir / "pages" / "Feature1Page.ts", "/* eslint-disable */\n" + TS_PAGE_OBJECT_TEMPLATE.format(num=1))
    _configure(mocker, repo_dir)

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.features == []
    assert result.warnings != []
    assert all("path='Feature1Page.ts'" in (w.context or "") for w in result.warnings)
    assert result.metadata.stats.cardinality.entities_skipped == 1


# file and configuration errors


def test_unreadable_file_is_skipped(tmp_path, mocker):
    # Arrange
    _write_entity_set(tmp_path / "repo")
    _configure(mocker, tmp_path / "repo")
    original_read_text = Path.read_text

    def deny_source_files(path, *args, **kwargs):
        if path.suffix in (".feature", ".ts"):
            raise OSError("denied")
        return original_read_text(path, *args, **kwargs)

    mocker.patch("pathlib.Path.read_text", autospec=True, side_effect=deny_source_files)
    mock_log_warning = mocker.patch("doc_source.collector.logger.warning")

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.user_stories == result.functionalities == result.features == []
    assert mock_log_warning.call_count == 3


def test_non_utf8_file_is_skipped(tmp_path, mocker):
    # Arrange
    (tmp_path / "repo" / "us").mkdir(parents=True)
    (tmp_path / "repo" / "us" / "latin1.feature").write_bytes("# LIVING DOC café\n".encode("latin-1"))
    _configure(mocker, tmp_path / "repo")
    mock_log_warning = mocker.patch("doc_source.collector.logger.warning")

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.user_stories == result.functionalities == result.features == []
    assert mock_log_warning.call_args.args[0] == "Could not read file `%s`: %s - skipping."


def test_invalid_repository_configuration_is_logged_and_skipped(tmp_path, mocker):
    # Arrange
    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[{"organization-name": "absa-group"}],
    )
    mock_log_error = mocker.patch("utils.utils.logger.error")

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.metadata.stats.cardinality.sources_configured == 1
    assert result.metadata.stats.cardinality.sources_failed == 1
    mock_log_error.assert_called_once()


def test_entity_the_contract_rejects_is_skipped_and_the_run_continues(tmp_path, mocker):
    # Arrange
    _write_entity_set(tmp_path / "repo")
    foreign_ac = US_FEATURE_TEMPLATE.format(num=2).replace("AC:US-2-01", "AC:US-9-01")
    _write(tmp_path / "repo" / "us" / "story_2.feature", foreign_ac)
    _configure(mocker, tmp_path / "repo")

    # Act
    actual = GHDocSourceCollector(str(tmp_path / "output")).collect()

    # Assert
    assert actual is True
    artifact = read_artifact(tmp_path / "output" / "doc-source" / "doc-source.json", "doc-source")
    assert [e.entity_id for e in artifact.user_stories] == ["US-1"]
    assert artifact.metadata.stats.cardinality.entities_skipped == 1
    rejected = [w for w in artifact.warnings if w.code == "AUTHORING_ERROR"]
    assert len(rejected) == 1
    assert rejected[0].context == "path='story_2.feature' entity_id='US-2'"
    assert "US-9-01" in rejected[0].message


def test_duplicate_entity_id_keeps_the_first_file_and_reports_the_second(tmp_path, mocker):
    # Arrange
    _write(tmp_path / "repo" / "us" / "a_story.feature", US_FEATURE_TEMPLATE.format(num=1))
    duplicate = US_FEATURE_TEMPLATE.format(num=1).replace("Story 1", "Another story 1")
    _write(tmp_path / "repo" / "us" / "b_story.feature", duplicate)
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert [(e.entity_id, e.source_ref.native_id) for e in result.user_stories] == [("US-1", "a_story.feature")]
    assert result.metadata.stats.cardinality.entities_skipped == 1
    duplicates = [w for w in result.warnings if w.code == "AUTHORING_ERROR"]
    assert [w.context for w in duplicates] == ["path='b_story.feature' entity_id='US-1'"]
    assert "'a_story.feature'" in duplicates[0].message


def test_reference_to_a_rejected_entity_is_reported_unresolved(tmp_path, mocker):
    # Arrange: FEAT-1 lists US-1, whose foreign AC id makes the contract reject it.
    _write_entity_set(tmp_path / "repo")
    foreign_ac = US_FEATURE_TEMPLATE.format(num=1).replace("AC:US-1-01", "AC:US-9-01")
    _write(tmp_path / "repo" / "us" / "story_1.feature", foreign_ac)
    _configure(mocker, tmp_path / "repo")

    # Act
    result = GHDocSourceCollector(str(tmp_path / "output")).build_result()

    # Assert
    assert result.user_stories == []
    assert [e.entity_id for e in result.features] == ["FEAT-1"]
    unresolved = [w.context for w in result.warnings if w.code == "UNRESOLVED_RELATION"]
    assert "entity_id='FEAT-1' target='US-1'" in unresolved
    assert result.metadata.stats.cardinality.unresolved_refs == len(unresolved)
    assert result.metadata.stats.cardinality.entities_skipped == 1
