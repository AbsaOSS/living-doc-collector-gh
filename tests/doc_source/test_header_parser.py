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
from doc_source.header_parser import parse_func_header, parse_header


def _ac(**overrides):
    """Build an expected acceptance-criterion dict with the additive fields defaulted."""
    base = {
        "aspect": [],
        "preconditions": [],
        "not_in_scope": [],
        "removal_planned": None,
        "descoped_at": None,
        "descoped_reason": None,
        "future_release": None,
    }
    base.update(overrides)
    return base

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
        _ac(
            id="US-27-01",
            state="Active",
            version="v1.9.0",
            description='A user who is not the domain owner can open the Access tab '
            'and see a "Request access" button.',
            preconditions=[
                "The user has logged in.",
                "At least one domain exists that the user does not own.",
            ],
        ),
        _ac(
            id="US-27-02",
            state="Active",
            version="v1.9.0",
            description="After submitting an access request, the user receives confirmation.",
            preconditions=[
                "The user has logged in.",
                "At least one domain exists that the user does not own.",
            ],
        ),
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
        _ac(
            id="US-1-01",
            state="Active",
            version="v1.0.0",
            description="First sentence continues here. Second sentence.",
        )
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
        _ac(id="US-2-02", state="Active", version="v1.0.0", description="Valid criterion.")
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


# ---------------------------------------------------------------------------
# parse_func_header tests
# ---------------------------------------------------------------------------

FULL_FUNC_HEADER = """# =============================================================================
# LIVING DOC — FUNC-001 · Authentication Screen — Credential-based Login
# =============================================================================
# status:    active
# parent:    FEAT-001
# func_type: button_action
#
# acceptance_criteria:
#
#   AC:FUNC-001-01 (v1.0.0 - Active)
#     - Submitting valid credentials navigates to the dashboard.
#
#   AC:FUNC-001-02 (v1.0.0 - Active)
#     - A user with an active session is automatically redirected.
# =============================================================================

@FUNC_ID:FUNC-001
Feature: Authentication Screen — Credential-based Login
Outcome of triggering the login button.
"""


def test_func_full_header():
    # Act
    result = parse_func_header(FULL_FUNC_HEADER.splitlines())

    # Assert
    assert result is not None
    assert result["func_id"] == "FUNC-001"
    assert result["title"] == "Authentication Screen — Credential-based Login"
    assert result["state"] == "active"
    assert result["parent"] == "FEAT-001"
    assert result["func_type"] == "button_action"
    assert result["acceptance_criteria"] == [
        _ac(
            id="FUNC-001-01",
            state="Active",
            version="v1.0.0",
            description="Submitting valid credentials navigates to the dashboard.",
        ),
        _ac(
            id="FUNC-001-02",
            state="Active",
            version="v1.0.0",
            description="A user with an active session is automatically redirected.",
        ),
    ]


def test_func_missing_optional_fields():
    # Arrange
    lines = [
        "# =============================================================================",
        "# LIVING DOC — FUNC-005 · Minimal Functionality",
        "# =============================================================================",
        "@FUNC_ID:FUNC-005",
        "Feature: Minimal Functionality",
        "Description.",
    ]

    # Act
    result = parse_func_header(lines)

    # Assert
    assert result is not None
    assert result["func_id"] == "FUNC-005"
    assert result["title"] == "Minimal Functionality"
    assert result["state"] is None
    assert result["parent"] is None
    assert result["func_type"] is None
    assert result["acceptance_criteria"] == []


def test_func_missing_header_block_returns_none():
    # Arrange
    lines = ["@FUNC_ID:FUNC-9", "Feature: No Header"]

    # Act
    result = parse_func_header(lines)

    # Assert
    assert result is None


def test_func_id_tag_mismatch_uses_header(caplog):
    # Arrange
    lines = [
        "# =============================================================================",
        "# LIVING DOC — FUNC-003 · Something",
        "# =============================================================================",
        "@FUNC_ID:FUNC-099",
        "Feature: Something",
    ]

    # Act
    result = parse_func_header(lines)

    # Assert
    assert result is not None
    assert result["func_id"] == "FUNC-003"
    assert any("mismatches header ID" in message for message in caplog.messages)


# ---------------------------------------------------------------------------
# Canonical authoring format: not_in_scope, deprecation, and full AC grammar
# ---------------------------------------------------------------------------

FULL_FORMAT_HEADER = """# =============================================================================
# LIVING DOC — US-40 · Full Format Story
# =============================================================================
# status:          deprecated
# deprecated_at:   2026-05-01
# deprecation_reason: Superseded by the new access flow.
# preconditions:
#   - The user has logged in.
# not_in_scope:
#   - Bulk access requests.
#
# acceptance_criteria:
#
#   AC:US-40-01 (v1.0.0 - active)
#     - The login screen displays the required field.
#     - Aspect: username input, password input
#     preconditions:
#       - The feature flag is enabled.
#     not_in_scope:
#       - Mobile browsers.
#
#   AC:US-40-02 (v2.1.0 - deprecated - removal planned v3.0.0)
#     - A "Remember me" checkbox retains the session.
#
#   AC:US-40-03 (v1.0.0 - planned)
#     - A deferred criterion.
#     - descoped_at: 2026-04-10
#     - descoped_reason: Deferred to next sprint.
#     - future_release: sprint-12
# =============================================================================

@US_ID:US-40
Feature: Full Format Story
As a user, I want the full format so that nothing is dropped.
"""


def test_entity_not_in_scope_and_deprecation_parsed():
    # Act
    result = parse_header(FULL_FORMAT_HEADER.splitlines())

    # Assert
    assert result is not None
    assert result["not_in_scope"] == ["Bulk access requests."]
    assert result["deprecated_at"] == "2026-05-01"
    assert result["deprecation_reason"] == "Superseded by the new access flow."


def test_ac_full_grammar_parsed():
    # Act
    result = parse_header(FULL_FORMAT_HEADER.splitlines())

    # Assert
    assert result is not None
    criteria = {ac["id"]: ac for ac in result["acceptance_criteria"]}

    assert criteria["US-40-01"]["aspect"] == ["username input", "password input"]
    assert criteria["US-40-01"]["preconditions"] == [
        "The user has logged in.",
        "The feature flag is enabled.",
    ]
    assert criteria["US-40-01"]["not_in_scope"] == [
        "Bulk access requests.",
        "Mobile browsers.",
    ]

    assert criteria["US-40-02"]["state"] == "deprecated"
    assert criteria["US-40-02"]["removal_planned"] == "v3.0.0"

    assert criteria["US-40-03"]["state"] == "planned"
    assert criteria["US-40-03"]["descoped_at"] == "2026-04-10"
    assert criteria["US-40-03"]["descoped_reason"] == "Deferred to next sprint."
    assert criteria["US-40-03"]["future_release"] == "sprint-12"
    assert criteria["US-40-03"]["description"] == "A deferred criterion."


def test_func_header_not_in_scope_and_deprecation():
    # Arrange
    lines = [
        "# =============================================================================",
        "# LIVING DOC — FUNC-010 · Deprecated Functionality",
        "# =============================================================================",
        "# status:    deprecated",
        "# deprecated_at: 2026-06-01",
        "# deprecation_reason: Merged into FUNC-011.",
        "# not_in_scope:",
        "#   - Legacy keyboard shortcuts.",
        "# =============================================================================",
        "@FUNC_ID:FUNC-010",
        "Feature: Deprecated Functionality",
    ]

    # Act
    result = parse_func_header(lines)

    # Assert
    assert result is not None
    assert result["not_in_scope"] == ["Legacy keyboard shortcuts."]
    assert result["deprecated_at"] == "2026-06-01"
    assert result["deprecation_reason"] == "Merged into FUNC-011."
