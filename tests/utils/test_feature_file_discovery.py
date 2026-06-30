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
from utils.feature_file_discovery import discover_feature_files


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


def test_directory_match_excluded(tmp_path):
    # Arrange
    nested = tmp_path / "features.feature"
    nested.mkdir()

    # Act
    result = discover_feature_files([str(tmp_path)])

    # Assert
    assert result == []
