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
from doc_source.header_parser import parse_header

FULL_HEADER = """# =============================================================================
# LIVING DOC — US-27 · Request Access to Domain
# =============================================================================
# source:         https://github.com/org/repo/issues/3
# status:         active
# business_value:
#   - Enables data consumers to gain access to domains they need.
#   - Provides a governed, auditable access-request workflow.
# preconditions:
#   - The user has logged in.
#   - At least one domain exists that the user does not own.
#
# acceptance_criteria:
#
#   AC:US-27-01 (v1.9.0 - Active)
#     - A user who is not the domain owner can open the Access tab
#       and see a "Request access" button.
#
#   AC:US-27-02 (v1.9.0 - Active)
#     - After submitting an access request, the user receives confirmation.
# =============================================================================

@US_ID:US-27
Feature: Request Access to Domain
As a data consumer, I want to request access to a domain I do not own
so that I can be granted the permissions needed to use its data.
"""


def test_full_header():
    # Act
    result = parse_header(FULL_HEADER.splitlines())

    # Assert
    assert result is not None
    assert result["us_id"] == "US-27"
    assert result["title"] == "Request Access to Domain"
    assert result["state"] == "active"
    assert result["url"] == "https://github.com/org/repo/issues/3"
    assert result["business_value"] == [
        "Enables data consumers to gain access to domains they need.",
        "Provides a governed, auditable access-request workflow.",
    ]
    assert result["preconditions"] == [
        "The user has logged in.",
        "At least one domain exists that the user does not own.",
    ]
    assert result["description"] == (
        "As a data consumer, I want to request access to a domain I do not own "
        "so that I can be granted the permissions needed to use its data."
    )
    assert result["acceptance_criteria"] == [
        {
            "id": "US-27-01",
            "state": "Active",
            "version": "v1.9.0",
            "description": 'A user who is not the domain owner can open the Access tab '
            'and see a "Request access" button.',
        },
        {
            "id": "US-27-02",
            "state": "Active",
            "version": "v1.9.0",
            "description": "After submitting an access request, the user receives confirmation.",
        },
    ]


def test_missing_optional_fields():
    # Arrange
    lines = [
        "# =============================================================================",
        "# LIVING DOC — US-5 · Minimal Story",
        "# =============================================================================",
        "",
        "@US_ID:US-5",
        "Feature: Minimal Story",
        "As a user, I want minimal so that simple.",
    ]

    # Act
    result = parse_header(lines)

    # Assert
    assert result is not None
    assert result["us_id"] == "US-5"
    assert result["title"] == "Minimal Story"
    assert result["state"] is None
    assert result["url"] is None
    assert result["business_value"] == []
    assert result["preconditions"] == []
    assert result["acceptance_criteria"] == []


def test_missing_required_fields_no_block():
    # Arrange
    lines = ["@US_ID:US-9", "Feature: No Header", "As a user."]

    # Act
    result = parse_header(lines)

    # Assert
    assert result is None


def test_missing_required_fields_no_title():
    # Arrange
    lines = [
        "# =============================================================================",
        "# Some random comment without the living doc marker",
        "# =============================================================================",
        "Feature: No Title",
    ]

    # Act
    result = parse_header(lines)

    # Assert
    assert result is None


def test_multi_line_ac_description():
    # Arrange
    lines = [
        "# =============================================================================",
        "# LIVING DOC — US-1 · Story",
        "# =============================================================================",
        "# acceptance_criteria:",
        "#   AC:US-1-01 (v1.0.0 - Active)",
        "#     - First sentence",
        "#       continues here.",
        "#     - Second sentence.",
        "# =============================================================================",
        "Feature: Story",
    ]

    # Act
    result = parse_header(lines)

    # Assert
    assert result is not None
    assert result["acceptance_criteria"] == [
        {
            "id": "US-1-01",
            "state": "Active",
            "version": "v1.0.0",
            "description": "First sentence continues here. Second sentence.",
        }
    ]


def test_malformed_ac_block(caplog):
    # Arrange
    lines = [
        "# =============================================================================",
        "# LIVING DOC — US-2 · Story",
        "# =============================================================================",
        "# acceptance_criteria:",
        "#   AC:US-2-01 (v1.0.0)",
        "#     - Malformed, missing state.",
        "#   AC:US-2-02 (v1.0.0 - Active)",
        "#     - Valid criterion.",
        "# =============================================================================",
        "Feature: Story",
    ]

    # Act
    result = parse_header(lines)

    # Assert
    assert result is not None
    assert result["acceptance_criteria"] == [
        {
            "id": "US-2-02",
            "state": "Active",
            "version": "v1.0.0",
            "description": "Valid criterion.",
        }
    ]


def test_us_id_tag_mismatch_uses_header(caplog):
    # Arrange
    lines = [
        "# =============================================================================",
        "# LIVING DOC — US-7 · Story",
        "# =============================================================================",
        "@US_ID:US-99",
        "Feature: Story",
    ]

    # Act
    result = parse_header(lines)

    # Assert
    assert result is not None
    assert result["us_id"] == "US-7"
    assert any("mismatches header ID" in message for message in caplog.messages)
