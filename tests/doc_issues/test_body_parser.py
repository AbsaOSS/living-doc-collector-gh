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

"""Tests for doc_issues.body_parser module."""

import pytest

from doc_issues.body_parser import (
    _extract_section,
    _extract_subsection,
    _parse_ac_table,
    _parse_bullet_list,
    _remove_subsections,
    parse_body,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_BODY = (
    "# User Story\n\n"
    "## Description\n\n"
    "As a user, I want to view the details of a selected domain.\n\n"
    "### Business Value\n"
    "- Streamlines domain details visibility for authorized users.\n\n"
    "## Preconditions\n\n"
    "- The user has logged in.\n"
    "- User can see at least one domain.\n\n"
    "## Acceptance Criteria\n\n"
    "| Criteria ID | State | Version | Description |\n"
    "|:------:|:------:|:-------|:------------|\n"
    "| `GH-28-01` | Active | v1.5.0 | User can access the domain details. |\n"
    "| `GH-28-02` | Active | v1.5.0 | Domain card details on dashboard. |\n\n"
    "## Connections\n\n"
    "### Related User stories\n"
    "- #2 \n\n"
    "## Change Log\n\n"
    "| Version | Date | Comment | Author |\n"
    "|---------|------|---------|--------|\n"
    "| v1 | 2025-10-28 | Updated by | Rinah Gololo |\n"
)

BODY_WITH_RATIONALE = (
    "# User Story\n\n"
    "## Description\n\n"
    "As a user, I want to receive on-screen notifications.\n\n"
    "## Rationale\n\n"
    "User wants to stay informed about changes.\n\n"
    "### Business Value\n\n"
    "- Streamlines notifications for authorized users.\n\n"
    "## Preconditions\n\n"
    "- The user logged in.\n"
    "- User has necessary permissions.\n\n"
    "## Acceptance Criteria\n\n"
    "| Criteria ID | State | Version | Description |\n"
    "|:------:|:------:|:-------|:------------|\n"
    "| `GH-17-01` | Active | v1.4.2 | An on-screen notification is displayed. |\n"
)

BODY_MULTIPLE_BV = (
    "## Description\n\n"
    "As a user, I want to search among all domains.\n\n"
    "### Business Value\n\n"
    "- Saves time for users managing numerous domains.\n"
    "- Improves navigation and clarity.\n\n"
    "## Preconditions\n\n"
    "- User logged in.\n"
)

# ---------------------------------------------------------------------------
# _extract_section
# ---------------------------------------------------------------------------


def test_extract_section_finds_existing_heading():
    result = _extract_section(FULL_BODY, "Preconditions")
    assert result == "- The user has logged in.\n- User can see at least one domain."


def test_extract_section_returns_none_for_missing_heading():
    result = _extract_section(FULL_BODY, "Nonexistent Section")
    assert result is None


def test_extract_section_stops_at_next_section():
    result = _extract_section(FULL_BODY, "Description")
    assert "## Preconditions" not in result
    assert "As a user" in result


# ---------------------------------------------------------------------------
# _extract_subsection
# ---------------------------------------------------------------------------


def test_extract_subsection_finds_business_value_under_description():
    result = _extract_subsection(FULL_BODY, "Business Value")
    assert result == "- Streamlines domain details visibility for authorized users."


def test_extract_subsection_finds_business_value_under_rationale():
    result = _extract_subsection(BODY_WITH_RATIONALE, "Business Value")
    assert result == "- Streamlines notifications for authorized users."


def test_extract_subsection_stops_before_next_section():
    result = _extract_subsection(FULL_BODY, "Business Value")
    assert "## Preconditions" not in result


def test_extract_subsection_returns_none_for_missing_heading():
    result = _extract_subsection(FULL_BODY, "Nonexistent Sub")
    assert result is None


# ---------------------------------------------------------------------------
# _remove_subsections
# ---------------------------------------------------------------------------


def test_remove_subsections_strips_business_value():
    text = (
        "As a user, I want to view the details of a selected domain.\n\n"
        "### Business Value\n"
        "- Streamlines domain details visibility for authorized users.\n"
    )
    result = _remove_subsections(text)
    assert result == "As a user, I want to view the details of a selected domain."


def test_remove_subsections_returns_text_unchanged_when_no_subsection():
    text = "As a user, I want to view the details of a selected domain."
    assert _remove_subsections(text) == text


# ---------------------------------------------------------------------------
# _parse_bullet_list
# ---------------------------------------------------------------------------


def test_parse_bullet_list_returns_items():
    text = "- The user has logged in.\n- User can see at least one domain."
    result = _parse_bullet_list(text)
    assert result == ["The user has logged in.", "User can see at least one domain."]


def test_parse_bullet_list_ignores_non_bullet_lines():
    text = "Some header\n- Item one\nNot a bullet\n- Item two"
    result = _parse_bullet_list(text)
    assert result == ["Item one", "Item two"]


def test_parse_bullet_list_empty_text_returns_empty_list():
    assert _parse_bullet_list("") == []


# ---------------------------------------------------------------------------
# _parse_ac_table
# ---------------------------------------------------------------------------


AC_TABLE = (
    "| Criteria ID | State | Version | Description |\n"
    "|:------:|:------:|:-------|:------------|\n"
    "| `GH-28-01` | Active | v1.5.0 | User can access the domain details. |\n"
    "| `GH-28-02` | Active | v1.5.0 | Domain card details on dashboard. |\n"
)


def test_parse_ac_table_returns_list_of_dicts():
    result = _parse_ac_table(AC_TABLE)
    assert len(result) == 2


def test_parse_ac_table_strips_backticks_from_id():
    result = _parse_ac_table(AC_TABLE)
    assert result[0]["id"] == "GH-28-01"
    assert result[1]["id"] == "GH-28-02"


def test_parse_ac_table_captures_all_fields():
    result = _parse_ac_table(AC_TABLE)
    assert result[0] == {
        "id": "GH-28-01",
        "state": "Active",
        "version": "v1.5.0",
        "description": "User can access the domain details.",
    }


def test_parse_ac_table_empty_text_returns_empty_list():
    assert _parse_ac_table("") == []


def test_parse_ac_table_skips_separator_row():
    result = _parse_ac_table(AC_TABLE)
    # separator row must not appear as a data row
    for row in result:
        assert "---" not in row["id"]


# ---------------------------------------------------------------------------
# parse_body
# ---------------------------------------------------------------------------


def test_parse_body_none_returns_all_none():
    result = parse_body(None)
    assert result == {
        "description": None,
        "business_value": None,
        "preconditions": None,
        "acceptance_criteria": None,
    }


def test_parse_body_empty_string_returns_all_none():
    result = parse_body("")
    assert result == {
        "description": None,
        "business_value": None,
        "preconditions": None,
        "acceptance_criteria": None,
    }


def test_parse_body_full_body_description():
    result = parse_body(FULL_BODY)
    assert result["description"] == "As a user, I want to view the details of a selected domain."


def test_parse_body_full_body_business_value():
    result = parse_body(FULL_BODY)
    assert result["business_value"] == ["Streamlines domain details visibility for authorized users."]


def test_parse_body_full_body_preconditions():
    result = parse_body(FULL_BODY)
    assert result["preconditions"] == ["The user has logged in.", "User can see at least one domain."]


def test_parse_body_full_body_acceptance_criteria():
    result = parse_body(FULL_BODY)
    assert result["acceptance_criteria"] == [
        {
            "id": "GH-28-01",
            "state": "Active",
            "version": "v1.5.0",
            "description": "User can access the domain details.",
        },
        {
            "id": "GH-28-02",
            "state": "Active",
            "version": "v1.5.0",
            "description": "Domain card details on dashboard.",
        },
    ]


def test_parse_body_business_value_under_rationale():
    result = parse_body(BODY_WITH_RATIONALE)
    assert result["description"] == "As a user, I want to receive on-screen notifications."
    assert result["business_value"] == ["Streamlines notifications for authorized users."]


def test_parse_body_multiple_business_value_items():
    result = parse_body(BODY_MULTIPLE_BV)
    assert result["business_value"] == [
        "Saves time for users managing numerous domains.",
        "Improves navigation and clarity.",
    ]


def test_parse_body_missing_acceptance_criteria_returns_none():
    body = "## Description\n\nSome description.\n\n## Preconditions\n\n- Logged in.\n"
    result = parse_body(body)
    assert result["acceptance_criteria"] is None


def test_parse_body_missing_preconditions_returns_none():
    body = "## Description\n\nSome description.\n"
    result = parse_body(body)
    assert result["preconditions"] is None


def test_parse_body_missing_business_value_returns_none():
    body = "## Description\n\nSome description.\n\n## Preconditions\n\n- Logged in.\n"
    result = parse_body(body)
    assert result["business_value"] is None


def test_parse_body_change_log_not_included_in_any_field():
    result = parse_body(FULL_BODY)
    # Change Log table rows must not bleed into acceptance_criteria
    ac_ids = [ac["id"] for ac in result["acceptance_criteria"]]
    assert "v1" not in ac_ids
