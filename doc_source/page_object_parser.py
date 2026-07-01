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
This module contains the parser for TypeScript PageObject LIVING DOC header
blocks (FEAT-NNN entities) used by the `doc-source` collector.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

_FEAT_TITLE_PATTERN = re.compile(r"FEAT-(\d+)\s*·\s*(.+?)\s*$")
_TS_KEY_PATTERN = re.compile(r"^([\w-]+)\s*:\s*(.*?)\s*$")
_TS_DELIMITER_PATTERN = re.compile(r"^=+\s*$")


def _strip_ts_comment_prefix(line: str) -> str:
    """Strip the leading ` * ` or ` *` from a TypeScript block comment line."""
    stripped = line.strip()
    if stripped.startswith("* "):
        return stripped[2:]
    if stripped == "*":
        return ""
    return stripped


def _extract_ts_header_block(lines: list[str]) -> Optional[list[str]]:
    """
    Extract the ``/* === ... === */`` LIVING DOC header block from a TypeScript file.

    Returns inner content lines with the comment prefix stripped, or None when no
    block is found.
    """
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("/*") and "=" in stripped:
            start_idx = i
        elif start_idx is not None and stripped.endswith("*/"):
            end_idx = i
            break

    if start_idx is None or end_idx is None:
        return None

    return [_strip_ts_comment_prefix(lines[i]) for i in range(start_idx + 1, end_idx)]


def _parse_id_list(value: str) -> list[str]:
    """Parse a comma-separated ID list (e.g. ``'FUNC-001, FUNC-002'``). Returns ``[]`` for ``'none'``."""
    if not value or value.lower() == "none":
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_page_object_header(lines: list[str]) -> Optional[dict]:
    """
    Parse a TypeScript PageObject LIVING DOC header block into a structured dict.

    Parameters:
        lines: All raw lines of the TypeScript file.

    Returns:
        A dict with keys: feat_id, title, state, surface_type, route, owners,
        purpose, user_stories, functionalities, external_dependencies,
        page_object. Returns None when required fields (FEAT ID, title) are missing.
    """
    block = _extract_ts_header_block(lines)
    if block is None:
        logger.warning("No LIVING DOC header block found in TypeScript file - skipping.")
        return None

    feat_id: Optional[str] = None
    title: Optional[str] = None
    current_key: Optional[str] = None
    fields: dict[str, str] = {}

    for content in block:
        # Skip delimiter lines (=====...)
        if _TS_DELIMITER_PATTERN.match(content):
            continue

        # Title line — search for FEAT-NNN · <title>
        if feat_id is None:
            m = _FEAT_TITLE_PATTERN.search(content)
            if m:
                feat_id = f"FEAT-{m.group(1)}"
                title = m.group(2).strip()
                current_key = None
                continue

        # Continuation line for multi-line values (leading whitespace after prefix strip)
        if content and content[0].isspace() and current_key is not None:
            fields[current_key] = f"{fields[current_key]} {content.strip()}"
            continue

        # Key-value line
        key_match = _TS_KEY_PATTERN.match(content)
        if key_match:
            raw_key = key_match.group(1).lower().replace("-", "_")
            current_key = raw_key
            fields[current_key] = key_match.group(2).strip()

    if feat_id is None or not title:
        logger.warning("Required FEAT header field missing (FEAT ID or title) - skipping file.")
        return None

    return {
        "feat_id": feat_id,
        "title": title,
        "state": fields.get("status", "").lower() or None,
        "surface_type": fields.get("surface_type") or None,
        "route": fields.get("route") or None,
        "owners": fields.get("owners") or None,
        "purpose": fields.get("purpose") or None,
        "user_stories": _parse_id_list(fields.get("user_stories", "")),
        "functionalities": _parse_id_list(fields.get("functionalities", "")),
        "external_dependencies": fields.get("external_dependencies") or None,
        "page_object": fields.get("page_object") or None,
    }
