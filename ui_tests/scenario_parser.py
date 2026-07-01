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
This module contains the pure-function parser for `.feature` file scenario
blocks used by the `ui-tests` collector. It takes raw file lines plus source
identity and returns a list of structured scenario dicts.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

_STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")
_SLUG_INVALID_PATTERN = re.compile(r"[^a-z0-9\-]")
_AC_TAG_PREFIX = "@AC:"
_US_ID_TAG_PREFIX = "@US_ID:"
_FUNC_ID_TAG_PREFIX = "@FUNC_ID:"


def _slugify(name: str, used_slugs: dict[str, int]) -> str:
    """Build a collision-safe slug from a scenario name within a single file."""
    slug = name.lower().replace(" ", "-")
    slug = _SLUG_INVALID_PATTERN.sub("", slug)
    slug = slug[:80]

    if slug in used_slugs:
        used_slugs[slug] += 1
        collision_slug = f"{slug}-{used_slugs[slug]}"
        logger.debug("Scenario slug collision for `%s` - using `%s`.", slug, collision_slug)
        return collision_slug

    used_slugs[slug] = 1
    return slug


def _split_scenario_tags(pending_tags: list[str]) -> tuple[list[str], list[str]]:
    """Split scenario-level tags into ac_ids and plain tags."""
    ac_ids: list[str] = []
    tags: list[str] = []
    for tag in pending_tags:
        if tag.startswith(_AC_TAG_PREFIX):
            ac_ids.append(tag[len(_AC_TAG_PREFIX) :])
        elif tag.startswith(_US_ID_TAG_PREFIX):
            logger.warning("`@US_ID:` tag on a scenario-level tag block is invalid - ignoring `%s`.", tag)
        elif tag.startswith(_FUNC_ID_TAG_PREFIX):
            logger.warning("`@FUNC_ID:` tag on a scenario-level tag block is invalid - ignoring `%s`.", tag)
        else:
            tags.append(tag.lstrip("@"))
    return ac_ids, tags


def parse_scenarios(lines: list[str], org: str, repo: str, rel_path: str) -> list[dict]:
    """
    Parse `.feature` file scenario blocks into a list of structured dicts.

    Parameters:
        lines: All raw lines of the `.feature` file.
        org: Organization name used in the scenario `id` and `source`.
        repo: Repository name used in the scenario `id` and `source`.
        rel_path: File path relative to the repository root (using `/` separators).

    Returns:
        A list of scenario dicts.
    """
    scenarios: list[dict] = []
    pending_tags: list[str] = []
    used_slugs: dict[str, int] = {}
    file_us_id: Optional[str] = None
    file_func_id: Optional[str] = None
    current: Optional[dict] = None

    for line_idx, raw in enumerate(lines):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("@"):
            pending_tags.extend(line.split())
            continue

        if line.startswith("Feature:"):
            for tag in pending_tags:
                if tag.startswith(_US_ID_TAG_PREFIX):
                    file_us_id = tag[len(_US_ID_TAG_PREFIX) :]
                elif tag.startswith(_FUNC_ID_TAG_PREFIX):
                    file_func_id = tag[len(_FUNC_ID_TAG_PREFIX) :]
            pending_tags = []
            continue

        if line.startswith("Scenario Outline:") or line.startswith("Scenario:"):
            if current is not None:
                scenarios.append(current)
            is_outline = line.startswith("Scenario Outline:")
            name = line.split(":", 1)[1].strip()
            ac_ids, tags = _split_scenario_tags(pending_tags)
            pending_tags = []
            slug = _slugify(name, used_slugs)
            current = {
                "id": f"{org}/{repo}/{rel_path}/{slug}",
                "us_id": file_us_id,
                "func_id": file_func_id,
                "ac_ids": ac_ids,
                "scenario_name": name,
                "scenario_type": "Scenario Outline" if is_outline else "Scenario",
                "tags": tags,
                "steps": [],
                "source": {"org": org, "repo": repo, "file": rel_path, "line": line_idx + 1},
            }
            continue

        if line.startswith(("Background:", "Rule:")):
            if current is not None:
                scenarios.append(current)
                current = None
            pending_tags = []
            continue

        if current is not None:
            for keyword in _STEP_KEYWORDS:
                if line.startswith(keyword + " "):
                    current["steps"].append({"keyword": keyword, "text": line[len(keyword) :].strip()})
                    break

        pending_tags = []

    if current is not None:
        scenarios.append(current)

    return scenarios
