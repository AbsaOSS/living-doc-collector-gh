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

"""
This module contains functions for parsing raw markdown issue body strings
into structured JSON-ready data.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_SECTION_PATTERN = re.compile(r"^## (.+?)[ \t]*$", re.MULTILINE)
_SUBSECTION_PATTERN = re.compile(r"^### (.+?)[ \t]*$", re.MULTILINE)
_SEPARATOR_ROW_PATTERN = re.compile(r"^\|[-|:\s]+\|$")


def _extract_section(body: str, heading: str) -> Optional[str]:
    """
    Extract the content of a ## heading section from the body.

    Parameters:
        body: Raw markdown body string.
        heading: The heading text to look for (without the ## prefix).

    Returns:
        Section content string, or None if heading not found.
    """
    matches = list(_SECTION_PATTERN.finditer(body))
    for i, m in enumerate(matches):
        if m.group(1).strip() == heading:
            content_start = m.end()
            content_end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            return body[content_start:content_end].strip()
    return None


def _extract_subsection(body: str, heading: str) -> Optional[str]:
    """
    Extract the content of a ### heading sub-section, searching anywhere in the body.

    Parameters:
        body: Raw markdown body string.
        heading: The sub-heading text to look for (without the ### prefix).

    Returns:
        Sub-section content string, or None if heading not found.
    """
    sub_matches = list(_SUBSECTION_PATTERN.finditer(body))
    section_starts = [m.start() for m in _SECTION_PATTERN.finditer(body)]

    for i, m in enumerate(sub_matches):
        if m.group(1).strip() == heading:
            content_start = m.end()
            # End at the next ### sub-section or the next ## section, whichever comes first
            next_subsection = sub_matches[i + 1].start() if i + 1 < len(sub_matches) else len(body)
            next_section = next(
                (boundary for boundary in section_starts if boundary > m.start()), len(body)
            )
            content_end = min(next_subsection, next_section)
            return body[content_start:content_end].strip()
    return None


def _remove_subsections(text: str) -> str:
    """
    Remove all ### sub-sections from text, returning only the content before the first one.

    Parameters:
        text: Section content that may contain ### sub-headings.

    Returns:
        Text with sub-sections stripped.
    """
    m = _SUBSECTION_PATTERN.search(text)
    if m:
        return text[: m.start()].strip()
    return text.strip()


def _parse_bullet_list(text: str) -> list[str]:
    """
    Parse a markdown bullet list into a list of plain strings.

    Parameters:
        text: Markdown text containing '- item' lines.

    Returns:
        List of item strings (leading '- ' stripped).
    """
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def _parse_ac_table(text: str) -> list[dict]:
    """
    Parse a markdown table into a list of acceptance criterion dicts.

    Parameters:
        text: Markdown text containing a table with columns:
              Criteria ID | State | Version | Description

    Returns:
        List of dicts with keys: id, state, version, description.
    """
    result = []
    header_seen = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if _SEPARATOR_ROW_PATTERN.match(stripped):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        cells = [c for c in cells if c]
        if not header_seen:
            header_seen = True
            continue
        if len(cells) >= 4:
            result.append(
                {
                    "id": cells[0].strip("`").strip(),
                    "state": cells[1],
                    "version": cells[2],
                    "description": cells[3],
                }
            )
    return result


def parse_body(body: Optional[str]) -> dict:
    """
    Parse a raw markdown GitHub issue body into structured fields.

    Extracts:
    - description: plain narrative from ## Description (before any ### sub-sections)
    - business_value: bullet list from ### Business Value (anywhere in body)
    - preconditions: bullet list from ## Preconditions
    - acceptance_criteria: table rows from ## Acceptance Criteria

    Parameters:
        body: Raw markdown string from a GitHub issue body, or None.

    Returns:
        Dictionary with keys: description, business_value, preconditions, acceptance_criteria.
        Each value is either a structured type or None when the section is absent or empty.
    """
    result: dict = {
        "description": None,
        "business_value": None,
        "preconditions": None,
        "acceptance_criteria": None,
    }

    if not body:
        return result

    desc_section = _extract_section(body, "Description")
    if desc_section is not None:
        narrative = _remove_subsections(desc_section)
        result["description"] = narrative or None

    bv_section = _extract_subsection(body, "Business Value")
    if bv_section is not None:
        bv_items = _parse_bullet_list(bv_section)
        result["business_value"] = bv_items if bv_items else None

    precond_section = _extract_section(body, "Preconditions")
    if precond_section is not None:
        precond_items = _parse_bullet_list(precond_section)
        result["preconditions"] = precond_items if precond_items else None

    ac_section = _extract_section(body, "Acceptance Criteria")
    if ac_section is not None:
        ac_items = _parse_ac_table(ac_section)
        result["acceptance_criteria"] = ac_items if ac_items else None

    return result
