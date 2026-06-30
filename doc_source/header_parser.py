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
This module contains the pure-function parser for `.feature` file header blocks
used by the `doc-source` collector. It takes raw file lines and returns a
structured dict ready for JSON serialization.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

_DELIMITER_PATTERN = re.compile(r"^#\s*=+\s*$")
_TITLE_PATTERN = re.compile(r"US-(\d+)\s*·\s*(.+?)\s*$")
_US_ID_TAG_PATTERN = re.compile(r"^@US_ID:\s*US-(\d+)")
_KEY_PATTERN = re.compile(r"^(\w+):\s*(.*)$")
_AC_HEADER_PATTERN = re.compile(r"^AC:(\S+)\s*\(([^)]*)\)")


def _strip_comment_prefix(line: str) -> str:
    """Strip a single leading `#` and one following space from a header line."""
    content = line[1:] if line.startswith("#") else line
    if content.startswith(" "):
        content = content[1:]
    return content


def _extract_header_block(lines: list[str]) -> Optional[list[str]]:
    """
    Extract the contiguous comment header block delimited by `# ===` lines that
    appears before the first `@` tag or `Feature:` keyword.

    Returns the inner content lines (delimiters excluded, `# ` prefix stripped),
    or None if no header block is found.
    """
    boundary = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("@") or stripped.startswith("Feature:"):
            boundary = i
            break

    delimiter_indices = [i for i in range(boundary) if _DELIMITER_PATTERN.match(lines[i])]
    if len(delimiter_indices) < 2:
        return None

    start, end = delimiter_indices[0], delimiter_indices[-1]
    return [_strip_comment_prefix(lines[i]) for i in range(start + 1, end)]


def _parse_bullet_section(section_lines: list[str]) -> list[str]:
    """Parse `- item` lines with continuations into a list of strings."""
    items: list[str] = []
    for raw in section_lines:
        text = raw.strip()
        if not text:
            continue
        if text.startswith("- "):
            items.append(text[2:].strip())
        elif items:
            items[-1] = f"{items[-1]} {text}".strip()
    return items


def _parse_acceptance_criteria(section_lines: list[str]) -> list[dict]:
    """Parse AC blocks into a list of acceptance criterion dicts."""
    criteria: list[dict] = []
    current: Optional[dict] = None
    description_parts: list[str] = []

    def _flush() -> None:
        if current is not None:
            current["description"] = " ".join(description_parts).strip()
            criteria.append(current)

    for raw in section_lines:
        text = raw.strip()
        if not text:
            continue

        header_match = _AC_HEADER_PATTERN.match(text)
        if header_match:
            _flush()
            paren_parts = header_match.group(2).split(" - ")
            version = paren_parts[0].strip() if paren_parts else ""
            state = paren_parts[1].strip() if len(paren_parts) > 1 else ""
            if not version or not state:
                logger.warning("Malformed AC block header `%s` - skipping.", text)
                current = None
                description_parts = []
                continue
            current = {"id": header_match.group(1), "state": state, "version": version, "description": ""}
            description_parts = []
        elif current is not None:
            if text.startswith("- "):
                description_parts.append(text[2:].strip())
            elif description_parts:
                description_parts[-1] = f"{description_parts[-1]} {text}".strip()

    _flush()
    return criteria


def _extract_feature_description(lines: list[str], title: str) -> str:
    """
    Extract the User Story narrative that follows the `Feature:` line, up to the
    first blank line or `Scenario`/`Background` keyword.
    """
    narrative: list[str] = []
    in_feature = False
    for line in lines:
        stripped = line.strip()
        if not in_feature:
            if stripped.startswith("Feature:"):
                in_feature = True
            continue
        if not stripped or stripped.startswith(("Scenario", "Background", "Rule:", "@")):
            break
        narrative.append(stripped)
    _ = title  # title is parsed from the header block, narrative is independent
    return " ".join(narrative).strip()


def parse_header(lines: list[str]) -> Optional[dict]:
    """
    Parse a `.feature` file header block into a structured dict.

    Parameters:
        lines: All raw lines of the `.feature` file.

    Returns:
        A dict with keys: us_id, title, state, url, description, business_value,
        preconditions, acceptance_criteria. Returns None when required fields
        (US ID, title) are missing.
    """
    block = _extract_header_block(lines)
    if block is None:
        logger.warning("Header block missing from file - skipping.")
        return None

    title_id: Optional[str] = None
    title: Optional[str] = None
    sections: dict[str, list[str]] = {}
    current_section: Optional[str] = None
    url: Optional[str] = None
    state: Optional[str] = None

    for content in block:
        if title_id is None:
            title_match = _TITLE_PATTERN.search(content)
            if title_match:
                title_id = f"US-{title_match.group(1)}"
                title = title_match.group(2).strip()
                continue

        if not content.startswith(" "):
            key_match = _KEY_PATTERN.match(content)
            if key_match:
                key, value = key_match.group(1).lower(), key_match.group(2).strip()
                if key == "source":
                    url = value or None
                    current_section = None
                elif key == "status":
                    state = value.lower() or None
                    current_section = None
                elif key in ("business_value", "preconditions", "acceptance_criteria"):
                    current_section = key
                    sections[key] = []
                else:
                    current_section = None
                continue

        if current_section is not None:
            sections[current_section].append(content)

    if title_id is None or not title:
        logger.warning("Required header field missing (US ID or title) - skipping file.")
        return None

    tag_id = _find_us_id_tag(lines)
    if tag_id is not None and tag_id != title_id:
        logger.warning("`@US_ID` tag `%s` mismatches header ID `%s` - using header ID.", tag_id, title_id)

    return {
        "us_id": title_id,
        "title": title,
        "state": state,
        "url": url,
        "description": _extract_feature_description(lines, title),
        "business_value": _parse_bullet_section(sections.get("business_value", [])),
        "preconditions": _parse_bullet_section(sections.get("preconditions", [])),
        "acceptance_criteria": _parse_acceptance_criteria(sections.get("acceptance_criteria", [])),
    }


def _find_us_id_tag(lines: list[str]) -> Optional[str]:
    """Find the `@US_ID:US-{id}` tag value in the file lines, if present."""
    for line in lines:
        match = _US_ID_TAG_PATTERN.match(line.strip())
        if match:
            return f"US-{match.group(1)}"
    return None
