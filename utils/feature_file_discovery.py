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


def discover_feature_files(paths: list[str]) -> list[Path]:
    """
    Recursively scan each absolute directory path for .feature files.

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
        found = [p for p in root.rglob("*.feature") if p.is_file()]
        if not found:
            logger.warning("No .feature files found under `%s`.", path)
            continue
        matched.update(found)

    return sorted(matched)
