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
This module contains the shared feature file discovery utility used by the
`doc-source` and `ui-tests` collectors.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _is_under_tutorial_dir(file_path: Path, root: Path) -> bool:
    """Return True when any directory between `root` and the file is a `tutorial*` directory."""
    try:
        relative_parts = file_path.relative_to(root).parts
    except ValueError:
        relative_parts = file_path.parts
    return root.name.lower().startswith("tutorial") or any(
        part.lower().startswith("tutorial") for part in relative_parts[:-1]
    )


def discover_feature_files(paths: list[str], exclude_tutorials: bool = True) -> list[Path]:
    """
    Recursively scan each absolute directory path for .feature files.

    Parameters:
        paths: Absolute directory paths to scan.
        exclude_tutorials: When True (default), files under `tutorial*` /
            `tutorial_<group>` directories are skipped - tutorial walkthroughs are
            not living documentation and no collector mode mines them.

    Returns:
        Sorted list of unique matching file paths.
    """
    matched: set[Path] = set()
    for path in paths:
        root = Path(path)
        if not root.exists():
            logger.warning("Path `%s` does not exist - skipping.", path)
            continue
        found = [p for p in root.rglob("*.feature") if p.is_file()]
        excluded_count = 0
        if exclude_tutorials:
            kept = [p for p in found if not _is_under_tutorial_dir(p, root)]
            excluded_count = len(found) - len(kept)
            if excluded_count > 0:
                logger.debug("Excluded %d tutorial `.feature` file(s) under `%s`.", excluded_count, path)
            found = kept
        if not found:
            if excluded_count > 0:
                logger.debug("All .feature files under `%s` are tutorials (excluded %d).", path, excluded_count)
            else:
                logger.warning("No .feature files found under `%s`.", path)
            continue
        matched.update(found)

    return sorted(matched)


def discover_ts_files(paths: list[str]) -> list[Path]:
    """
    Recursively scan each absolute directory path for .ts files.

    Parameters:
        paths: Absolute directory paths to scan.

    Returns:
        Sorted list of unique matching file paths.
    """
    matched: set[Path] = set()
    for path in paths:
        root = Path(path)
        if not root.exists():
            logger.warning("Path `%s` does not exist - skipping.", path)
            continue
        found = [p for p in root.rglob("*.ts") if p.is_file()]
        if not found:
            logger.warning("No .ts files found under `%s`.", path)
            continue
        matched.update(found)

    return sorted(matched)
