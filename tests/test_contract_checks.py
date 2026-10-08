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
R12 checks 1 and 2 over this repository's active code, and the guard against utilities' deleted legacy model.
`doc-issues` PLANNED after v0.1.0, kept aside unchanged for the port: `_KEPT_ASIDE` is left out of every check.
"""

import ast
import subprocess
import typing
from pathlib import Path

import pytest
from living_doc_utilities.contracts.check_no_vendored_schemas import find_vendored_schemas
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.ui_tests import UITestsResult

from doc_source.collector import GHDocSourceCollector
from ui_tests.collector import GHUITestsCollector

REPO_ROOT = Path(__file__).resolve().parents[1]

# `doc-issues` PLANNED after v0.1.0, kept aside unchanged for the port.
_KEPT_ASIDE = (
    "doc_issues/",
    "tests/doc_issues/",
    "utils/github_project_queries.py",
    "tests/utils/test_github_project_queries.py",
)

_LEGACY_MODULES = ("living_doc_utilities.model", "living_doc_utilities.factory", "living_doc_utilities.exporter")


def _active_python_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "*.py"], capture_output=True, check=True, text=True
    ).stdout.split()
    untracked = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "--others", "--exclude-standard", "*.py"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.split()
    return sorted(path for path in {*tracked, *untracked} if not path.startswith(_KEPT_ASIDE))


def _imported_modules(path: str) -> set[str]:
    tree = ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_no_contract_schema_is_committed():
    # R12 check 1. `doc-issues` PLANNED after v0.1.0, kept aside unchanged for the port: its schema is allowed.
    assert find_vendored_schemas(REPO_ROOT, allow=[Path("doc_issues")]) == []


def test_no_active_module_imports_the_legacy_model_or_kept_aside_code():
    # Act
    offenders = {
        path: sorted(
            module
            for module in _imported_modules(path)
            if module.startswith(_LEGACY_MODULES)
            or module.split(".")[0] == "doc_issues"
            or module == "utils.github_project_queries"
        )
        for path in _active_python_files()
    }

    # Assert
    assert {path: modules for path, modules in offenders.items() if modules} == {}


@pytest.mark.parametrize("package", ["doc_source", "ui_tests", "utils"])
def test_collector_code_reads_and_writes_no_json_itself(package):
    # R12 check 2: an artifact is written only via write_artifact; no collector module serialises JSON itself.
    # Any import of `json` counts, aliased (`import json as j`) or by name (`from json import dump`).
    # Act
    offenders = []
    for path in _active_python_files():
        if not path.startswith(f"{package}/"):
            continue
        for node in ast.walk(ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import) and any(alias.name.split(".")[0] == "json" for alias in node.names):
                offenders.append(f"{path}:{node.lineno} import json")
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "json":
                offenders.append(f"{path}:{node.lineno} from json import")

    # Assert
    assert offenders == []


@pytest.mark.parametrize(
    ("collector", "result_model"),
    [(GHDocSourceCollector, DocSourceResult), (GHUITestsCollector, UITestsResult)],
)
def test_entry_point_is_typed_on_the_contract_model(collector, result_model):
    # R12 check 2: each mode's entry point returns the shared contract model, never a dict.
    assert typing.get_type_hints(collector.build_result)["return"] is result_model
