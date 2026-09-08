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
from utils.feature_file_discovery import discover_feature_files, discover_ts_files


def test_matching_glob(tmp_path):
    # Arrange
    features = tmp_path / "features"
    features.mkdir()
    file_a = features / "a.feature"
    file_b = features / "b.feature"
    file_a.write_text("Feature: A", encoding="utf-8")
    file_b.write_text("Feature: B", encoding="utf-8")
    (features / "ignore.txt").write_text("nope", encoding="utf-8")

    # Act
    result = discover_feature_files([str(tmp_path)])

    # Assert
    assert result == [file_a, file_b]


def test_no_match(tmp_path, caplog):
    # Act
    result = discover_feature_files([str(tmp_path)])

    # Assert
    assert result == []
    assert any("No .feature files found under" in message for message in caplog.messages)


def test_missing_local_path(tmp_path):
    # Act
    result = discover_feature_files([str(tmp_path / "missing")])

    # Assert
    assert result == []


def test_tutorial_directories_excluded(tmp_path):
    # Arrange
    living = tmp_path / "liv_doc_us"
    living.mkdir()
    kept = living / "us.feature"
    kept.write_text("Feature: US", encoding="utf-8")
    for tutorial_dir in ("tutorials", "tutorial_onboarding"):
        directory = tmp_path / tutorial_dir
        directory.mkdir()
        (directory / "walkthrough.feature").write_text("Feature: T", encoding="utf-8")

    # Act
    result = discover_feature_files([str(tmp_path)])

    # Assert
    assert result == [kept]


def test_tutorial_directories_kept_when_opted_in(tmp_path):
    # Arrange
    directory = tmp_path / "tutorials"
    directory.mkdir()
    walkthrough = directory / "walkthrough.feature"
    walkthrough.write_text("Feature: T", encoding="utf-8")

    # Act
    result = discover_feature_files([str(tmp_path)], exclude_tutorials=False)

    # Assert
    assert result == [walkthrough]


def test_tutorial_root_path_excluded(tmp_path):
    # Arrange: When the configured root path itself is a tutorial directory
    tutorial_root = tmp_path / "tutorials"
    tutorial_root.mkdir()
    walkthrough = tutorial_root / "walkthrough.feature"
    walkthrough.write_text("Feature: T", encoding="utf-8")

    # Act: Pass the tutorial directory directly as the root path
    result = discover_feature_files([str(tutorial_root)])

    # Assert: Should be excluded by default
    assert result == []

    # Act: With exclude_tutorials=False
    result_included = discover_feature_files([str(tutorial_root)], exclude_tutorials=False)

    # Assert: Should be included when opted in
    assert result_included == [walkthrough]


def test_tutorial_root_path_with_variant_name(tmp_path):
    # Arrange: Test with tutorial_<group> variant naming
    tutorial_root = tmp_path / "tutorial_onboarding"
    tutorial_root.mkdir()
    walkthrough = tutorial_root / "walkthrough.feature"
    walkthrough.write_text("Feature: T", encoding="utf-8")

    # Act: Pass the tutorial directory directly as the root path
    result = discover_feature_files([str(tutorial_root)])

    # Assert: Should be excluded
    assert result == []


def test_directory_match_excluded(tmp_path):
    # Arrange
    nested = tmp_path / "features.feature"
    nested.mkdir()

    # Act
    result = discover_feature_files([str(tmp_path)])

    # Assert
    assert result == []


# ---------------------------------------------------------------------------
# discover_ts_files tests
# ---------------------------------------------------------------------------


def test_ts_matching_files(tmp_path):
    # Arrange
    pages = tmp_path / "pages"
    pages.mkdir()
    file_a = pages / "LoginPage.ts"
    file_b = pages / "DashboardPage.ts"
    file_a.write_text("export class LoginPage {}", encoding="utf-8")
    file_b.write_text("export class DashboardPage {}", encoding="utf-8")
    (pages / "ignore.js").write_text("nope", encoding="utf-8")

    # Act
    result = discover_ts_files([str(tmp_path)])

    # Assert
    assert result == [file_b, file_a]


def test_ts_no_match(tmp_path, caplog):
    # Act
    result = discover_ts_files([str(tmp_path)])

    # Assert
    assert result == []
    assert any("No .ts files found under" in message for message in caplog.messages)


def test_ts_missing_local_path(tmp_path):
    # Act
    result = discover_ts_files([str(tmp_path / "missing")])

    # Assert
    assert result == []


def test_ts_directory_match_excluded(tmp_path):
    # Arrange
    nested = tmp_path / "page.ts"
    nested.mkdir()

    # Act
    result = discover_ts_files([str(tmp_path)])

    # Assert
    assert result == []
