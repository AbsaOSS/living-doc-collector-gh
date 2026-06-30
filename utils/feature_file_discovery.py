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


def discover_feature_files(local_path: str, patterns: list[str]) -> list[Path]:
    """
    Resolve glob patterns under local_path and return matching .feature file paths.

    Parameters:
        local_path: Path to the checked-out repository root.
        patterns: Glob patterns relative to local_path.

    Returns:
        Sorted list of unique matching file paths. Empty list if local_path does
        not exist (caller is expected to log the error).
    """
    root = Path(local_path)
    if not root.exists():
        return []

    matched: set[Path] = set()
    for pattern in patterns:
        found = list(root.glob(pattern))
        if not found:
            logger.warning("No files match glob pattern `%s` under `%s`.", pattern, local_path)
            continue
        for path in found:
            if path.is_file():
                matched.add(path)

    return sorted(matched)
