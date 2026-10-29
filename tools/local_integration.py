#
# Copyright 2026 ABSA Group Limited
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
The Python half of `local-integration.sh`: the repository list a mode's `*-repositories` input reads, and the
report on one artifact the collector wrote - re-read with `read_artifact`, then its `metadata.stats` counts, its
warnings by code, the time the run took and the file's size. Runs in the script's venv, which holds
`requirements.txt` alone, so it imports nothing the collector itself does not.
"""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from typing import Any, Optional

from living_doc_utilities.contracts.codes import ContractError
from living_doc_utilities.contracts.envelope import ContractWarning
from living_doc_utilities.contracts.io import read_artifact

from doc_source.collector import DOC_SOURCE_FILE_NAME
from ui_tests.collector import UI_TESTS_FILE_NAME
from utils.constants import DOC_SOURCE_OUTPUT_PATH, UI_TESTS_OUTPUT_PATH

# Each mode's artifact, relative to the output root, as the collector writes it. A mode's name is also the name of
# the contract its artifact carries.
ARTIFACTS = {
    "doc-source": os.path.join(DOC_SOURCE_OUTPUT_PATH, DOC_SOURCE_FILE_NAME),
    "ui-tests": os.path.join(UI_TESTS_OUTPUT_PATH, UI_TESTS_FILE_NAME),
}

# How many occurrences of each warning code the report lists; the count covers them all.
FIRST_OCCURRENCES = 10


def repositories_json(organization: str, repository: str, paths: Sequence[str]) -> str:
    """
    A mode's repository list for the one configured checkout, as its `*-repositories` input reads it.

    @param organization: The repository's `organization-name`.
    @param repository: The repository's `repository-name`.
    @param paths: `<key>=<directory>` pairs, e.g. `us-paths=/abs/dir`; a key given twice lists both directories.
    @return: The JSON array string.
    @raise ValueError: When a pair has no key or no directory.
    """
    directories: dict[str, list[str]] = {}
    for pair in paths:
        key, separator, directory = pair.partition("=")
        if not separator or not key or not directory:
            raise ValueError(f"not a <key>=<directory> pair: {pair!r}")
        directories.setdefault(key, []).append(directory)
    return json.dumps([{"organization-name": organization, "repository-name": repository, **directories}])


def _printable(line: str) -> str:
    """One printed line with its control characters spelled out (`\\n`, `\\x1b`), so a file cannot forge a line."""
    return "".join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in line)


def _counts(value: Any) -> str:
    """A `metadata.stats` value on one line: a number as it is, a mapping as sorted `key=count` pairs."""
    if isinstance(value, dict):
        return ", ".join(f"{key}={count}" for key, count in sorted(value.items())) or "-"
    return str(value)


def _occurrence(warning: ContractWarning) -> str:
    """Where one warning was raised and what it says: `<path>:<line> <entity>/<ac> <message>`."""
    where = warning.path or warning.context or "-"
    if warning.line_no is not None:
        where = f"{where}:{warning.line_no}"
    subject = "/".join(part for part in (warning.entity_id, warning.ac_id) if part)
    return " ".join(part for part in (where, subject, warning.message) if part)


def warnings_by_code(warnings: Sequence[ContractWarning], first: int = FIRST_OCCURRENCES) -> list[str]:
    """
    The warnings grouped by code, codes sorted: each code's count, then its first occurrences in artifact order.

    @param warnings: The artifact's warnings.
    @param first: How many occurrences of each code to list.
    @return: The report lines.
    """
    grouped: dict[str, list[ContractWarning]] = {}
    for warning in warnings:
        grouped.setdefault(warning.code, []).append(warning)
    lines = [f"  warnings: {len(warnings)}"]
    for code in sorted(grouped):
        occurrences = grouped[code]
        lines.append(f"    {code}: {len(occurrences)}")
        lines.extend(f"      {_occurrence(warning)}" for warning in occurrences[:first])
        if len(occurrences) > first:
            lines.append(f"      ... and {len(occurrences) - first} more")
    return lines


def report(output_root: str, mode: str, elapsed_ms: int) -> list[str]:
    """
    Re-read one mode's artifact with `read_artifact` and describe it.

    @param output_root: The collector's output root, the `output-path` it ran with.
    @param mode: `doc-source` or `ui-tests`.
    @param elapsed_ms: How long the collector's run of the mode took, in milliseconds.
    @return: The report lines.
    @raise ContractError: When the artifact fails its contract.
    @raise OSError: When the artifact cannot be read.
    @raise ValueError: When the artifact is not JSON.
    """
    path = os.path.join(output_root, ARTIFACTS[mode])
    result = read_artifact(path, mode)
    metadata = result.metadata
    return [
        f"{mode}: {path}",
        f"  contract: {result.schema_version}, valid (read_artifact)",
        f"  producer: {metadata.producer.name} {metadata.producer.version}, "
        f"living-doc-utilities {metadata.producer.utilities_version}",
        f"  time: {elapsed_ms / 1000:.2f} s",
        f"  size: {os.path.getsize(path)} bytes",
        "  stats.cardinality:",
        *(f"    {name}: {_counts(value)}" for name, value in metadata.stats.cardinality.model_dump().items()),
        "  stats.field_occupancy:",
        *(f"    {name}: {count}" for name, count in sorted(metadata.stats.field_occupancy.items())),
        *warnings_by_code(result.warnings),
    ]


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    The command line `local-integration.sh` calls: `repositories` prints a mode's repository list, `report` prints
    the report on one artifact.

    @param argv: The arguments; the process's own when None.
    @return: The process exit code: 0 on success, 1 when the artifact fails validation or the list cannot be built.
    """
    parser = argparse.ArgumentParser(prog="python -m tools.local_integration")
    commands = parser.add_subparsers(dest="command", required=True)
    repositories = commands.add_parser("repositories", help="print a mode's repository list as JSON")
    repositories.add_argument("organization")
    repositories.add_argument("repository")
    repositories.add_argument("paths", nargs="+", metavar="key=directory")
    artifact = commands.add_parser("report", help="validate one mode's artifact and print its report")
    artifact.add_argument("output_root")
    artifact.add_argument("mode", choices=sorted(ARTIFACTS))
    artifact.add_argument("elapsed_ms", type=int)
    args = parser.parse_args(argv)

    if args.command == "repositories":
        try:
            print(repositories_json(args.organization, args.repository, args.paths))
        except ValueError as e:
            print(_printable(f"repositories: {e}"), file=sys.stderr)
            return 1
        return 0

    try:
        lines = report(args.output_root, args.mode, args.elapsed_ms)
    except (ContractError, OSError, ValueError) as e:
        print(_printable(f"{args.mode}: the artifact is not valid: {e}"), file=sys.stderr)
        return 1
    print("\n".join(_printable(line) for line in lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
