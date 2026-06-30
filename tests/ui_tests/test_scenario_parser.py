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
from ui_tests.scenario_parser import parse_scenarios

ORG = "absa-group"
REPO = "aul-ui"
REL = "playwright/features/domain_create.feature"

SINGLE_SCENARIO = """@US_ID:US-26
@domain_create
Feature: Create Domain
    As a user, I want to create domain
    so that I can make it available for data consumers.

    # AC:US-26-01 (v1.4.2 - Active) — description comment (ignored)
    @AC:US-26-01
    @Regression
    Scenario: User can complete the Create Domain wizard and create a new domain
        Given the user "1" is logged in
        And the user is on the Create Domain wizard About screen
        When the user fills in the domain name "<unique>"
        Then the user is on the Create Domain wizard Owner screen
"""


def test_single_scenario():
    # Act
    result = parse_scenarios(SINGLE_SCENARIO.splitlines(), ORG, REPO, REL)

    # Assert
    assert len(result) == 1
    scenario = result[0]
    assert scenario["us_id"] == "US-26"
    assert scenario["ac_ids"] == ["US-26-01"]
    assert scenario["scenario_type"] == "Scenario"
    assert scenario["tags"] == ["Regression"]
    assert scenario["scenario_name"] == (
        "User can complete the Create Domain wizard and create a new domain"
    )
    assert scenario["source"] == {"org": ORG, "repo": REPO, "file": REL}
    assert scenario["id"] == (
        f"{ORG}/{REPO}/{REL}/user-can-complete-the-create-domain-wizard-and-create-a-new-domain"
    )
    assert scenario["steps"] == [
        {"keyword": "Given", "text": 'the user "1" is logged in'},
        {"keyword": "And", "text": "the user is on the Create Domain wizard About screen"},
        {"keyword": "When", "text": 'the user fills in the domain name "<unique>"'},
        {"keyword": "Then", "text": "the user is on the Create Domain wizard Owner screen"},
    ]


def test_multiple_ac_tags():
    # Arrange
    lines = [
        "@US_ID:US-1",
        "Feature: F",
        "    @AC:US-1-01",
        "    @AC:US-1-02",
        "    Scenario: Multi AC",
        "        Given a",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert result[0]["ac_ids"] == ["US-1-01", "US-1-02"]


def test_scenario_outline():
    # Arrange
    lines = [
        "@US_ID:US-1",
        "Feature: F",
        "    Scenario Outline: An outline",
        "        Given <value>",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert result[0]["scenario_type"] == "Scenario Outline"


def test_no_us_id():
    # Arrange
    lines = [
        "Feature: F",
        "    Scenario: No US",
        "        Given a",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert result[0]["us_id"] is None


def test_no_ac_tags():
    # Arrange
    lines = [
        "@US_ID:US-1",
        "Feature: F",
        "    @Smoke",
        "    Scenario: No AC",
        "        Given a",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert result[0]["ac_ids"] == []
    assert result[0]["tags"] == ["Smoke"]


def test_slug_collision():
    # Arrange
    lines = [
        "@US_ID:US-1",
        "Feature: F",
        "    Scenario: Same Name",
        "        Given a",
        "    Scenario: Same Name",
        "        Given b",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert result[0]["id"].endswith("/same-name")
    assert result[1]["id"].endswith("/same-name-2")


def test_background_ignored():
    # Arrange
    lines = [
        "@US_ID:US-1",
        "Feature: F",
        "    Background:",
        "        Given a precondition",
        "    Scenario: Real",
        "        Given a",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert len(result) == 1
    assert result[0]["scenario_name"] == "Real"


def test_us_id_on_scenario_tag_is_ignored(caplog):
    # Arrange
    lines = [
        "@US_ID:US-1",
        "Feature: F",
        "    @US_ID:US-99",
        "    Scenario: With invalid tag",
        "        Given a",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert result[0]["us_id"] == "US-1"
    assert result[0]["tags"] == []
    assert any("scenario-level tag block is invalid" in message for message in caplog.messages)


def test_rule_closes_scenario():
    # Arrange
    lines = [
        "@US_ID:US-1",
        "Feature: F",
        "    Scenario: First",
        "        Given a",
        "    Rule: A rule",
        "    Scenario: Second",
        "        Given b",
    ]

    # Act
    result = parse_scenarios(lines, ORG, REPO, REL)

    # Assert
    assert [s["scenario_name"] for s in result] == ["First", "Second"]
