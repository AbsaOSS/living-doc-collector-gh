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
This module contains the `doc-check` mode: `living-doc-utilities`' authored-input check over the files the
`doc-source` mode reads, its report printed, and whether the findings fail.
"""

import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

from living_doc_utilities.check.engine import AuthoredFile, Finding, check
from living_doc_utilities.check.report import fails, format_line, github_report, job_summary
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.policy import POLICY_FILE, Policy, load_policy

from action_inputs import ActionInputs
from doc_source.collector import read_source_files
from doc_source.model.config_repository import ConfigRepository
from utils.artifact import find_repo_root, relative_path, repository_path
from utils.constants import DOC_SOURCE_REPOSITORIES, input_name
from utils.utils import load_repository_configs

logger = logging.getLogger(__name__)


def _corpus() -> tuple[list[AuthoredFile], dict[str, Optional[Path]]]:
    """
    Read every authored file of `doc-source-repositories`, each named by its path from its repository root, as
    `git diff --name-only` prints it; a file outside a git checkout is named from its scan root.

    @return: The files, and each file's repository root by its path; None outside a git checkout.
    @raise ContractError: `INVALID_CONFIGURATION` when two files share a path, `SOURCE_UNAVAILABLE` when a
        configured path is missing.
    """
    configs = load_repository_configs(
        ActionInputs.get_doc_source_repositories(), ConfigRepository, input_name(DOC_SOURCE_REPOSITORIES)
    )
    files: list[AuthoredFile] = []
    roots: dict[str, Optional[Path]] = {}
    for config in configs:
        for source_file in read_source_files(config):
            root = find_repo_root(source_file.path)
            if root is None:
                path = relative_path(source_file.path, source_file.scan_roots)
            else:
                path = repository_path(source_file.path, root)
            files.append(AuthoredFile(path, source_file.entity_type, source_file.text))
            roots[path] = root
    twice = sorted(path for path, count in Counter(file.path for file in files).items() if count > 1)
    if twice:
        raise ContractError(
            Code.INVALID_CONFIGURATION,
            f"`{input_name(DOC_SOURCE_REPOSITORIES)}` reaches more than one file at {', '.join(twice)}; "
            "findings name a file by its path from its repository root, so each path must be one file.",
        )
    return files, roots


def _policy(root: Optional[Path]) -> Policy:
    """
    The policy file at a repository's root; the default policy without one, or outside a git checkout.

    @raise ContractError: `INVALID_CONFIGURATION` naming the file when it can't be read or the policy model rejects it.
    """
    if root is None or not (root / POLICY_FILE).exists():
        return Policy()
    path = root / POLICY_FILE
    try:
        return load_policy(path)
    # `load_policy` raises `OSError`, `pydantic.ValidationError` and PyYAML's `YAMLError`. PyYAML is no direct
    # dependency of this action (`requirements.txt`), so the loader's errors are caught whole, around this one call.
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise ContractError(Code.INVALID_CONFIGURATION, f"`{path}` is not a valid policy file: {e}") from e


def _by_repository(
    findings: list[Finding], roots: dict[str, Optional[Path]], policies: dict[Optional[Path], Policy]
) -> list[tuple[list[Finding], frozenset[str]]]:
    """The findings of each repository, in the order their files come, with the codes that fail there."""
    groups: dict[Optional[Path], list[Finding]] = {}
    for finding in findings:
        groups.setdefault(roots[finding.path], []).append(finding)
    return [(group, policies[root].check.fail_codes) for root, group in groups.items()]


def _report(groups: list[tuple[list[Finding], frozenset[str]]]) -> None:
    """
    Print the findings: inside GitHub Actions the check's GitHub report, each repository's under its own policy, and
    the job summary; outside it, one plain line per finding. Written to stdout, not logged: a workflow command must
    start its line.
    """
    if not ActionInputs.is_github_actions():
        for group, _ in groups:
            sys.stdout.write("".join(f"{format_line(finding)}\n" for finding in group))
        return
    summary = ""
    for group, fail_codes in groups:
        sys.stdout.write(github_report(group, fail_codes))
        summary += job_summary(group, fail_codes)
    summary_path = ActionInputs.get_step_summary_path()
    if summary and summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(summary)
        except OSError as e:
            logger.warning("Could not write the job summary to `%s`: %s.", summary_path, e)


# pylint: disable=too-few-public-methods
class GHDocChecker:
    """
    A class representing the `doc-check` mode. It runs `living-doc-utilities`' authored-input check over the files
    the `doc-source` mode reads, for the paths a pull request changed, and writes no artifact.
    """

    def check(self) -> bool:
        """
        Check the changed living-doc files and print the report.

        @return: True when no finding fails, False when one does or the mode failed.
        """
        try:
            return self._check()
        except ContractError as e:
            logger.error("The `doc-check` mode failed: %s", e)
            return False

    @staticmethod
    def _check() -> bool:
        files, roots = _corpus()
        changed_paths = ActionInputs.get_doc_check_changed_paths()
        changed = [path for path in changed_paths if path in roots]
        logger.info("`doc-check`: %d of %d changed paths are living-doc files.", len(changed), len(changed_paths))
        if not changed:
            return True
        # Every repository's policy, so an invalid one fails the step whether or not its files have findings.
        policies = {root: _policy(root) for root in roots.values()}
        groups = _by_repository(check(files, changed), roots, policies)
        _report(groups)
        failed = any(fails(group, fail_codes) for group, fail_codes in groups)
        findings = sum(len(group) for group, _ in groups)
        logger.info("`doc-check`: %d findings; %s.", findings, "they fail" if failed else "none fails")
        return not failed
