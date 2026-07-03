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
from doc_source.page_object_parser import parse_page_object_header

FULL_PO_HEADER = """\
/* =============================================================================
 * LIVING DOC — FEAT-001 · Authentication Screen
 * =============================================================================
 * surface_type:          UI
 * route:                 /
 * owners:                Unify Team
 * status:                active
 * purpose:               Authentication screen where users enter credentials to gain
 *                        access to the application.
 * user_stories:          US-1
 * functionalities:       FUNC-001, FUNC-002, FUNC-003
 * external_dependencies: none
 * page-object:           LoginPage.ts
 * ============================================================================= */

import type { Page } from '@playwright/test';

export class LoginPage {}
"""

FUNCTIONALITIES_NONE_HEADER = """\
/* =============================================================================
 * LIVING DOC — FEAT-003 · Dashboard
 * =============================================================================
 * surface_type:          UI
 * route:                 /auth/dashboard
 * owners:                Unify Team
 * status:                active
 * purpose:               Home screen for authenticated users.
 * user_stories:          US-2, US-16
 * functionalities:       none
 * external_dependencies: none
 * page-object:           DashboardPage.ts
 * ============================================================================= */

export class DashboardPage {}
"""


def test_full_po_header():
    # Act
    result = parse_page_object_header(FULL_PO_HEADER.splitlines())

    # Assert
    assert result is not None
    assert result["feat_id"] == "FEAT-001"
    assert result["title"] == "Authentication Screen"
    assert result["state"] == "active"
    assert result["surface_type"] == "UI"
    assert result["route"] == "/"
    assert result["owners"] == "Unify Team"
    assert result["purpose"] == "Authentication screen where users enter credentials to gain access to the application."
    assert result["user_stories"] == ["US-1"]
    assert result["functionalities"] == ["FUNC-001", "FUNC-002", "FUNC-003"]
    assert result["external_dependencies"] == "none"
    assert result["page_object"] == "LoginPage.ts"


def test_functionalities_none_parsed_as_empty_list():
    # Act
    result = parse_page_object_header(FUNCTIONALITIES_NONE_HEADER.splitlines())

    # Assert
    assert result is not None
    assert result["feat_id"] == "FEAT-003"
    assert result["functionalities"] == []
    assert result["user_stories"] == ["US-2", "US-16"]


def test_missing_header_block_returns_none():
    # Arrange
    lines = [
        "import type { Page } from '@playwright/test';",
        "export class NoHeaderPage {}",
    ]

    # Act
    result = parse_page_object_header(lines)

    # Assert
    assert result is None


def test_header_without_feat_id_returns_none():
    # Arrange
    lines = [
        "/* =============================================================================",
        " * Some comment without FEAT ID",
        " * ============================================================================= */",
        "export class SomePage {}",
    ]

    # Act
    result = parse_page_object_header(lines)

    # Assert
    assert result is None


def test_multi_line_purpose_joined():
    # Arrange — purpose spans two comment lines
    lines = [
        "/* =============================================================================",
        " * LIVING DOC — FEAT-005 · Domain Detail",
        " * =============================================================================",
        " * surface_type:          UI",
        " * route:                 /auth/all-domains/{domainId}/{version}/about",
        " * owners:                Unify Team",
        " * status:                active",
        " * purpose:               Domain detail page with nine sub-tabs: About, Schema,",
        " *                        Run history, Data feed.",
        " * user_stories:          US-6",
        " * functionalities:       none",
        " * external_dependencies: none",
        " * page-object:           DomainDetailPage.ts",
        " * ============================================================================= */",
        "export class DomainDetailPage {}",
    ]

    # Act
    result = parse_page_object_header(lines)

    # Assert
    assert result is not None
    assert result["purpose"] == "Domain detail page with nine sub-tabs: About, Schema, Run history, Data feed."
