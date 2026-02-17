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

"""
Tests for toolkit adapter fixture files to ensure they remain valid as the codebase evolves.
"""

import json
import os
from pathlib import Path

import pytest


# Get the fixtures directory path
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "toolkit_adapter"


def get_fixture_files():
    """
    Get all doc-issues.json fixture files from the toolkit_adapter directory.

    @return: List of tuples (version_dir, file_path)
    """
    fixture_files = []
    if FIXTURES_DIR.exists():
        for version_dir in FIXTURES_DIR.iterdir():
            if version_dir.is_dir():
                fixture_file = version_dir / "doc-issues.json"
                if fixture_file.exists():
                    fixture_files.append((version_dir.name, fixture_file))
    return fixture_files


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_top_level_structure(version, fixture_path):
    """
    Test that fixture has the correct top-level structure.

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate top-level keys
    assert "metadata" in data, f"{version}: Missing 'metadata' section"
    assert "issues" in data, f"{version}: Missing 'issues' section"
    assert isinstance(data["metadata"], dict), f"{version}: metadata must be a dictionary"
    assert isinstance(data["issues"], dict), f"{version}: issues must be a dictionary"


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_metadata_structure(version, fixture_path):
    """
    Test that fixture metadata has required fields.

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data["metadata"]

    # Validate required metadata fields
    assert "generated_at" in metadata, f"{version}: Missing 'generated_at' in metadata"
    assert "schema_version" in metadata, f"{version}: Missing 'schema_version' in metadata"
    assert "generator" in metadata, f"{version}: Missing 'generator' in metadata"

    # Validate generator structure
    generator = metadata["generator"]
    assert "name" in generator, f"{version}: Missing 'name' in generator"
    assert generator["name"] == "AbsaOSS/living-doc-collector-gh", f"{version}: Incorrect generator name"
    assert "version" in generator, f"{version}: Missing 'version' in generator"


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_schema_version(version, fixture_path):
    """
    Test that fixture has the correct schema_version.

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data["metadata"]
    assert metadata["schema_version"] == "1.0", f"{version}: Incorrect schema_version, expected '1.0'"


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_has_issues(version, fixture_path):
    """
    Test that fixture has at least one issue with required fields.

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    issues = data["issues"]
    assert len(issues) > 0, f"{version}: Fixture must have at least one issue"

    # Validate the first issue has required base fields
    first_issue_key = list(issues.keys())[0]
    first_issue = issues[first_issue_key]

    required_fields = ["type", "repository_id", "title", "issue_number", "state"]
    for field in required_fields:
        assert field in first_issue, f"{version}: Issue {first_issue_key} missing required field: {field}"


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_issue_types(version, fixture_path):
    """
    Test that fixture issues have valid types.

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    valid_types = ["Issue", "UserStoryIssue", "FeatureIssue", "FunctionalityIssue"]

    for issue_key, issue in data["issues"].items():
        assert "type" in issue, f"{version}: Issue {issue_key} missing 'type' field"
        assert issue["type"] in valid_types, f"{version}: Issue {issue_key} has invalid type: {issue['type']}"


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_issue_states(version, fixture_path):
    """
    Test that fixture issues have valid states.

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    valid_states = ["open", "closed"]

    for issue_key, issue in data["issues"].items():
        assert "state" in issue, f"{version}: Issue {issue_key} missing 'state' field"
        assert issue["state"] in valid_states, f"{version}: Issue {issue_key} has invalid state: {issue['state']}"


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_issue_key_format(version, fixture_path):
    """
    Test that fixture issue keys follow the correct format (org/repo#number).

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    import re

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Pattern: org/repo#number
    key_pattern = re.compile(r"^[^/]+/[^/#]+#\d+$")

    for issue_key in data["issues"].keys():
        assert key_pattern.match(issue_key), f"{version}: Issue key '{issue_key}' does not match format 'org/repo#number'"


@pytest.mark.parametrize("version,fixture_path", get_fixture_files())
def test_fixture_json_validity(version, fixture_path):
    """
    Test that fixture is valid JSON.

    @param version: Version directory name (e.g., 'v1.0.0')
    @param fixture_path: Path to the fixture file
    @return: None
    """
    # This test will pass if the file can be loaded as JSON
    # If JSON is invalid, json.load will raise an exception
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data is not None, f"{version}: Failed to load fixture as JSON"
