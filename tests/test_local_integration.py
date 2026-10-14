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
The promises of `local-integration.sh`, a developer's run of the real collector outside any workflow, and of
`tools/local_integration.py`, its Python half: the repository list is the one a mode's `*-repositories` input
reads; every artifact is re-read with `read_artifact` and reported; the configuration is read as data and never
sourced; a misconfiguration fails with one actionable stderr line; no token reaches anything the script prints or
starts; and no workflow runs it.

The script itself runs here only as `--check`: a full run builds a venv from `requirements.txt`, which needs the
network.
"""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import ContractWarning
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_tests import UITestsResult

from action_inputs import ActionInputs
from doc_source.collector import GHDocSourceCollector
from doc_source.model.config_repository import ConfigRepository as DocSourceConfigRepository
from tools.local_integration import FIRST_OCCURRENCES, main, report, repositories_json, warnings_by_code
from ui_tests.collector import GHUITestsCollector
from ui_tests.model.config_repository import ConfigRepository as UITestsConfigRepository
from utils.utils import load_repository_configs

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "local-integration.sh"
EXAMPLE_CONFIG = REPO_ROOT / ".env.local.example"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
FULL_SAMPLE = Path(__file__).resolve().parent / "fixtures" / "full_sample"

ORGANIZATION = "AbsaOSS"
REPOSITORY = "living-doc-collector-gh"

# A token-shaped value no real credential has; the script must print it nowhere and hand it to no child.
TOKEN = "ghp_dummy_local_integration_token"


# --- repositories: the list a mode's `*-repositories` input reads ------------------------------------------------


def test_repositories_json_lists_one_entry_for_the_configured_checkout():
    # Act
    entries = json.loads(repositories_json("AbsaOSS", "living-doc-testbed", ["paths=/target/features"]))

    # Assert
    assert entries == [
        {"organization-name": "AbsaOSS", "repository-name": "living-doc-testbed", "paths": ["/target/features"]}
    ]


def test_a_key_given_twice_lists_both_directories_in_order():
    # Act
    entries = json.loads(
        repositories_json("org", "repo", ["us-paths=/t/us-b", "func-paths=/t/func", "us-paths=C:/t/us-a"])
    )

    # Assert: the order is the configured one, not a sorted one.
    assert entries == [
        {
            "organization-name": "org",
            "repository-name": "repo",
            "us-paths": ["/t/us-b", "C:/t/us-a"],
            "func-paths": ["/t/func"],
        }
    ]


def test_a_directory_keeps_everything_after_the_first_equals_sign():
    # Act & Assert
    assert json.loads(repositories_json("org", "repo", ["paths=/t/a=b"]))[0]["paths"] == ["/t/a=b"]


@pytest.mark.parametrize("pair", ["us-paths", "=C:/x", "us-paths="], ids=["no-separator", "no-key", "no-directory"])
def test_a_malformed_pair_is_rejected(pair):
    # Act & Assert: the pair is named, even after a valid one.
    with pytest.raises(ValueError, match=re.escape(f"not a <key>=<directory> pair: {pair!r}")):
        repositories_json("org", "repo", ["paths=/t/ok", pair])


def test_the_doc_source_list_loads_as_the_doc_source_repositories_input(monkeypatch):
    # Arrange
    monkeypatch.setenv(
        "INPUT_DOC_SOURCE_REPOSITORIES",
        repositories_json(
            "AbsaOSS",
            "living-doc-testbed",
            ["us-paths=/t/us-a", "func-paths=/t/func", "us-paths=/t/us-b", "pages-paths=/t/pages"],
        ),
    )

    # Act
    [config] = load_repository_configs(
        ActionInputs.get_doc_source_repositories(), DocSourceConfigRepository, "doc-source-repositories"
    )

    # Assert
    assert (config.organization_name, config.repository_name) == ("AbsaOSS", "living-doc-testbed")
    assert (config.paths, config.func_paths, config.pages_paths) == (["/t/us-a", "/t/us-b"], ["/t/func"], ["/t/pages"])


def test_the_ui_tests_list_loads_as_the_ui_tests_repositories_input(monkeypatch):
    # Arrange
    monkeypatch.setenv(
        "INPUT_UI_TESTS_REPOSITORIES", repositories_json("AbsaOSS", "living-doc-testbed", ["paths=/t/a", "paths=/t/b"])
    )

    # Act
    [config] = load_repository_configs(
        ActionInputs.get_ui_tests_repositories(), UITestsConfigRepository, "ui-tests-repositories"
    )

    # Assert
    assert (config.organization_name, config.repository_name) == ("AbsaOSS", "living-doc-testbed")
    assert config.paths == ["/t/a", "/t/b"]


def test_main_prints_the_repository_list_and_exits_zero(capsys):
    # Act
    code = main(["repositories", "AbsaOSS", "living-doc-testbed", "paths=/t/a", "paths=/t/b"])

    # Assert
    out, err = capsys.readouterr()
    assert code == 0
    assert err == ""
    assert json.loads(out) == [
        {"organization-name": "AbsaOSS", "repository-name": "living-doc-testbed", "paths": ["/t/a", "/t/b"]}
    ]


def test_main_rejects_a_malformed_pair_with_one_line_and_exits_one(capsys):
    # Act
    code = main(["repositories", "AbsaOSS", "living-doc-testbed", "us-paths"])

    # Assert
    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert err == "repositories: not a <key>=<directory> pair: 'us-paths'\n"


# --- warnings by code ----------------------------------------------------------------------------------------------


def _warning(message: str, code: str = "AC_UNLINKED", **where) -> ContractWarning:
    return ContractWarning(code=code, message=message, **where)


def test_no_warnings_is_the_header_alone():
    # Act & Assert
    assert warnings_by_code([]) == ["  warnings: 0"]


def test_warnings_are_grouped_by_sorted_code_each_in_artifact_order():
    # Arrange
    warnings = [
        _warning("z first", code="ZETA_CODE"),
        _warning("a only", code="ALPHA_CODE"),
        _warning("z second", code="ZETA_CODE"),
    ]

    # Act & Assert
    assert warnings_by_code(warnings) == [
        "  warnings: 3",
        "    ALPHA_CODE: 1",
        "      - a only",
        "    ZETA_CODE: 2",
        "      - z first",
        "      - z second",
    ]


def test_only_the_first_occurrences_of_a_code_are_listed_and_the_rest_counted():
    # Arrange
    warnings = [_warning(f"w{n}", code="MANY") for n in range(5)] + [_warning("one", code="FEW")]

    # Act & Assert: the code's count covers all five; the listing stops at `first`.
    assert warnings_by_code(warnings, first=2) == [
        "  warnings: 6",
        "    FEW: 1",
        "      - one",
        "    MANY: 5",
        "      - w0",
        "      - w1",
        "      ... and 3 more",
    ]


def test_a_code_with_exactly_first_occurrences_is_listed_whole():
    # Act & Assert
    assert warnings_by_code([_warning("a"), _warning("b")], first=2) == [
        "  warnings: 2",
        "    AC_UNLINKED: 2",
        "      - a",
        "      - b",
    ]


def test_ten_occurrences_of_a_code_are_listed_by_default():
    # Arrange
    warnings = [_warning(f"w{n:02d}") for n in range(12)]

    # Act & Assert
    assert FIRST_OCCURRENCES == 10
    assert warnings_by_code(warnings) == [
        "  warnings: 12",
        "    AC_UNLINKED: 12",
        *(f"      - w{n:02d}" for n in range(10)),
        "      ... and 2 more",
    ]


@pytest.mark.parametrize(
    ("where", "expected"),
    [
        (
            {"path": "us/loans.feature", "line_no": 12, "entity_id": "US-7", "ac_id": "US-7-02"},
            "us/loans.feature:12 US-7/US-7-02 msg",
        ),
        ({"path": "us/loans.feature", "context": "not shown when a path is known"}, "us/loans.feature msg"),
        ({"context": "entity_id='FEAT-902'", "entity_id": "FEAT-902"}, "entity_id='FEAT-902' FEAT-902 msg"),
        ({"context": "in a header", "line_no": 3}, "in a header:3 msg"),
        ({"line_no": 3}, "-:3 msg"),
        ({"ac_id": "FUNC-4-01"}, "- FUNC-4-01 msg"),
        ({"entity_id": "US-7"}, "- US-7 msg"),
        ({}, "- msg"),
    ],
    ids=["everything", "path-over-context", "context", "context-line", "line-only", "ac-only", "entity-only", "none"],
)
def test_an_occurrence_says_where_and_about_what(where, expected):
    # Act & Assert: `<path or context or ->[:line] <entity>/<ac> <message>`, empty parts dropped.
    assert warnings_by_code([_warning("msg", **where)]) == ["  warnings: 1", "    AC_UNLINKED: 1", f"      {expected}"]


# --- report: one artifact re-read with read_artifact ---------------------------------------------------------------


@pytest.fixture(name="collected")
def _collected(tmp_path, monkeypatch):
    """
    The real collector's output root after both modes ran over the full samples, configured through the
    repository lists `repositories_json` builds - the path the script takes, `INPUT_*` environment included.
    """
    root = tmp_path / "collector-gh"
    doc_source = FULL_SAMPLE / "doc_source"
    monkeypatch.setenv(
        "INPUT_DOC_SOURCE_REPOSITORIES",
        repositories_json(
            ORGANIZATION,
            REPOSITORY,
            [
                f"us-paths={doc_source / 'us'}",
                f"func-paths={doc_source / 'func'}",
                f"pages-paths={doc_source / 'pages'}",
            ],
        ),
    )
    monkeypatch.setenv(
        "INPUT_UI_TESTS_REPOSITORIES",
        repositories_json(ORGANIZATION, REPOSITORY, [f"paths={FULL_SAMPLE / 'ui_tests'}"]),
    )
    assert GHDocSourceCollector(str(root)).collect() is True
    assert GHUITestsCollector(str(root)).collect() is True
    return root


def test_the_report_describes_the_artifact_it_re_read(collected):
    # Arrange
    path = os.path.join(collected, "doc-source", "doc-source.json")
    artifact = read_artifact(path, "doc-source")
    assert isinstance(artifact, DocSourceResult)
    producer = artifact.metadata.producer
    stats = artifact.metadata.stats

    # Act
    lines = report(str(collected), "doc-source", 1234)

    # Assert: what was read, that it is valid, who wrote it, how long it took and how big it is.
    assert lines[:5] == [
        f"doc-source: {path}",
        f"  contract: {artifact.schema_version}, valid (read_artifact)",
        f"  producer: {producer.name} {producer.version}, living-doc-utilities {producer.utilities_version}",
        "  time: 1.23 s",
        f"  size: {os.path.getsize(path)} bytes",
    ]
    assert artifact.schema_version.startswith("doc-source-v")
    # Assert: every cardinality counter in the model's order, every occupancy path sorted, then the warnings.
    cardinality_at = lines.index("  stats.cardinality:")
    occupancy_at = lines.index("  stats.field_occupancy:")
    warnings_at = lines.index(f"  warnings: {len(artifact.warnings)}")
    assert cardinality_at == 5 < occupancy_at < warnings_at
    assert [line.split(":")[0].strip() for line in lines[cardinality_at + 1 : occupancy_at]] == list(
        stats.cardinality.model_dump()
    )
    assert lines[occupancy_at + 1 : warnings_at] == [
        f"    {field}: {count}" for field, count in sorted(stats.field_occupancy.items())
    ]
    assert lines[warnings_at:] == warnings_by_code(artifact.warnings)
    assert artifact.warnings, "the full sample is expected to carry a warning, so the section is not only a header"


def test_a_counter_reads_as_its_number_and_a_mapping_as_sorted_pairs(collected):
    # Arrange
    artifact = read_artifact(collected / "doc-source" / "doc-source.json", "doc-source")
    cardinality = artifact.metadata.stats.cardinality
    assert len(cardinality.entities_by_type) > 1, "one key cannot show the pairs are sorted"

    # Act
    lines = report(str(collected), "doc-source", 0)

    # Assert
    assert f"    entities: {cardinality.entities}" in lines
    pairs = ", ".join(f"{name}={count}" for name, count in sorted(cardinality.entities_by_type.items()))
    assert f"    entities_by_type: {pairs}" in lines


def test_an_empty_mapping_reads_as_a_dash_and_no_warnings_as_the_header_alone(collected):
    # Arrange
    artifact = read_artifact(collected / "ui-tests" / "ui-tests.json", "ui-tests")
    assert isinstance(artifact, UITestsResult)
    assert artifact.metadata.stats.cardinality.warnings_by_code == {}

    # Act
    lines = report(str(collected), "ui-tests", 0)

    # Assert
    assert lines[0] == f"ui-tests: {os.path.join(collected, 'ui-tests', 'ui-tests.json')}"
    assert lines[1] == f"  contract: {artifact.schema_version}, valid (read_artifact)"
    assert "    warnings_by_code: -" in lines
    assert lines[-1] == "  warnings: 0"


@pytest.mark.parametrize(("elapsed_ms", "shown"), [(0, "0.00"), (1234, "1.23"), (125600, "125.60")])
def test_the_time_is_shown_in_seconds_to_two_decimals(collected, elapsed_ms, shown):
    # Act & Assert
    assert report(str(collected), "ui-tests", elapsed_ms)[3] == f"  time: {shown} s"


def test_main_prints_the_report_and_exits_zero(collected, capsys):
    # Arrange
    capsys.readouterr()

    # Act
    code = main(["report", str(collected), "doc-source", "1234"])

    # Assert
    out, err = capsys.readouterr()
    assert code == 0
    assert err == ""
    assert out == "\n".join(report(str(collected), "doc-source", 1234)) + "\n"


def test_main_reports_a_missing_artifact_and_exits_one(tmp_path, capsys):
    # Act
    code = main(["report", str(tmp_path), "doc-source", "5"])

    # Assert: one line, naming the file it looked for.
    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert err.startswith("doc-source: the artifact is not valid: ")
    assert "doc-source.json" in err
    assert len(err.splitlines()) == 1


def test_main_reports_a_file_that_is_not_json_and_exits_one(tmp_path, capsys):
    # Arrange
    (tmp_path / "ui-tests").mkdir()
    (tmp_path / "ui-tests" / "ui-tests.json").write_text("{ not json", encoding="utf-8")

    # Act
    code = main(["report", str(tmp_path), "ui-tests", "5"])

    # Assert
    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert err.startswith("ui-tests: the artifact is not valid: ")
    assert len(err.splitlines()) == 1


def test_an_artifact_of_the_other_contract_fails_validation(collected, tmp_path, capsys):
    # Arrange: a valid `ui-tests` artifact where the `doc-source` one belongs.
    wrong_root = tmp_path / "wrong"
    (wrong_root / "doc-source").mkdir(parents=True)
    shutil.copyfile(collected / "ui-tests" / "ui-tests.json", wrong_root / "doc-source" / "doc-source.json")
    capsys.readouterr()

    # Act & Assert: `report` raises the contract's own error...
    with pytest.raises(ContractError) as raised:
        report(str(wrong_root), "doc-source", 5)
    assert raised.value.code is Code.CONTRACT_MISMATCH

    # ...and `main` turns it into one stderr line and exit 1.
    code = main(["report", str(wrong_root), "doc-source", "5"])
    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert err.startswith("doc-source: the artifact is not valid: [CONTRACT_MISMATCH]")
    assert len(err.splitlines()) == 1


def test_main_reports_only_the_two_collector_modes(tmp_path):
    # Act & Assert: `doc-issues` is PLANNED, so it has no artifact to report; argparse rejects it.
    with pytest.raises(SystemExit) as raised:
        main(["report", str(tmp_path), "doc-issues", "5"])
    assert raised.value.code == 2


# --- static promises over the script and its configuration --------------------------------------------------------


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", os.fspath(REPO_ROOT), *args], capture_output=True, check=False, text=True, timeout=60
    )


def _shell_code() -> list[str]:
    """The script's lines without comments: in bash a `#` that starts a word starts a comment."""
    return [re.sub(r"(?:^|\s)#.*", "", line).strip() for line in SCRIPT.read_text(encoding="utf-8").splitlines()]


def _script_list(name: str) -> list[str]:
    """A whitespace-separated list the script assigns in double quotes, e.g. `KEYS`; it may span lines."""
    match = re.search(rf'^{name}="([^"]*)"', SCRIPT.read_text(encoding="utf-8"), re.MULTILINE)
    assert match, f"{name} is not assigned in {SCRIPT.name}"
    return match.group(1).split()


def _example_settings() -> dict[str, str]:
    settings = {}
    for line in EXAMPLE_CONFIG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, separator, value = line.partition("=")
            assert separator, f"not a KEY=value line in {EXAMPLE_CONFIG.name}: {line!r}"
            settings[key] = value
    return settings


def test_the_script_is_committed_executable():
    # Assert: `./local-integration.sh` runs on a fresh clone with no `chmod`.
    entry = _git("ls-files", "-s", SCRIPT.name).stdout
    assert entry.startswith("100755 "), f"{SCRIPT.name} is not committed with mode 100755: {entry!r}"


def test_the_script_keeps_lf_line_ends_on_every_checkout():
    # Assert: bash, Git Bash on Windows included, fails on a CRLF line.
    assert _git("check-attr", "eol", "--", SCRIPT.name).stdout.strip() == f"{SCRIPT.name}: eol: lf"
    assert b"\r" not in SCRIPT.read_bytes()


def test_no_workflow_runs_the_script():
    # Arrange
    workflows = [path for path in WORKFLOWS.rglob("*") if path.is_file()]

    # Assert: the script is a developer's tool; CI keeps its own integration workflow.
    assert workflows
    assert [
        path.name for path in workflows if re.search(r"local[-_]integration", path.read_text(encoding="utf-8"))
    ] == []


def test_the_example_sets_only_settings_the_script_reads():
    # Arrange
    keys = _script_list("KEYS")

    # Assert: `KEYS` is read across both its lines, and the example names nothing outside it - no token.
    assert {"PROJECT_ID", "UI_TESTS_PATHS", "DOC_SOURCE_PAGES_PATHS", "PYTHON"} <= set(keys)
    assert set(_example_settings()) <= set(keys)


def test_the_example_documents_every_setting():
    # Assert: a setting added to the script is added to the example the operator copies.
    assert set(_example_settings()) == set(_script_list("KEYS"))


def test_the_example_fills_every_required_setting():
    # Arrange
    required = _script_list("REQUIRED")
    example = _example_settings()

    # Assert: a copied example passes the required-key check as it is.
    assert required
    assert set(required) <= set(_script_list("KEYS"))
    assert [key for key in required if not example.get(key)] == []


def test_the_only_install_is_the_runtime_requirements_into_the_scripts_venv():
    # Assert: pip is always the venv's own, and installs `requirements.txt` alone - what the action installs.
    installs = [line for line in _shell_code() if re.search(r"\bpip\b", line) and re.search(r"\binstall\b", line)]
    assert installs == ['run "$VPY" -m pip install --disable-pip-version-check -r requirements.txt']
    assert "requirements-dev" not in SCRIPT.read_text(encoding="utf-8")


def test_the_script_never_sources_or_evaluates_a_file():
    # Arrange: the first word of every command, a line split at `;`, `&&` and `||`.
    commands = [
        segment.split()[0] for line in _shell_code() for segment in re.split(r";|&&|\|\|", line) if segment.split()
    ]

    # Assert: `.env.local` is read as data; a sourced file runs whatever it holds and exports any token in it.
    assert commands
    assert {"source", ".", "eval"} & set(commands) == set()


@pytest.mark.parametrize(
    "path", [".env.local", ".venv-local-integration/x", "output/collector-gh/x"], ids=["config", "venv", "output"]
)
def test_what_the_script_reads_and_writes_locally_is_git_ignored(path):
    # Assert
    assert _git("check-ignore", "-q", path).returncode == 0, f"{path} is not git-ignored"


def test_the_example_config_is_not_git_ignored():
    # Assert: the pattern for `.env.local` does not swallow the committed example.
    assert _git("check-ignore", "-q", "--no-index", EXAMPLE_CONFIG.name).returncode == 1


# --- the script's behaviour: `--check`, run with bash in a copy ----------------------------------------------------


def _bash() -> Optional[str]:
    """bash to run the script with: Git Bash on Windows, never `System32\\bash.exe`, the WSL launcher."""
    bash = shutil.which("bash")
    if bash and sys.platform == "win32" and "system32" in (part.lower() for part in Path(bash).parts):
        return None
    return bash


BASH = _bash()
needs_bash = pytest.mark.skipif(BASH is None, reason="no bash to run local-integration.sh with (Git Bash on Windows)")

# Process start-up is slow on Git Bash for Windows; a `--check` there takes seconds, elsewhere milliseconds.
TIMEOUT = 120

# A configuration the `workspace` fixture satisfies: the target is `../target`, relative to the script's copy.
VALID_CONFIG = {
    "PROJECT_ID": "local-integration-test",
    "TARGET_CHECKOUT": "../target",
    "ORGANIZATION_NAME": ORGANIZATION,
    "REPOSITORY_NAME": "living-doc-testbed",
    "DOC_SOURCE_US_PATHS": "features/us",
    "DOC_SOURCE_FUNC_PATHS": "features/func",
    "DOC_SOURCE_PAGES_PATHS": "pages",
    "UI_TESTS_PATHS": "features/us, features/func",
    "OUT_DIR": "./output",
    "PYTHON": Path(sys.executable).as_posix(),
}


@pytest.fixture(name="workspace")
def _workspace(tmp_path, git_checkout):
    """A copy of the script in a directory of its own, beside a target checkout holding every configured path."""
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copyfile(SCRIPT, repo / SCRIPT.name)
    target = tmp_path / "target"
    git_checkout(target)
    for directory in ("features/us", "features/func", "pages"):
        (target / directory).mkdir(parents=True)
    return repo


def _write_config(repo: Path, config: dict, extra_lines: tuple = ()) -> None:
    lines = [*(f"{key}={value}" for key, value in config.items()), *extra_lines]
    (repo / ".env.local").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _executable(path: Path, body: str) -> str:
    """A `/bin/sh` script at `path`, executable; its path as `.env.local`'s `PYTHON` takes it."""
    path.write_text(f"#!/bin/sh\n{body}", encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path.as_posix()


def _run(repo: Path, *args: str, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    assert BASH is not None
    return subprocess.run(
        [BASH, f"./{SCRIPT.name}", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT,
        check=False,
    )


@needs_bash
def test_check_passes_on_a_valid_configuration_and_builds_nothing(workspace):
    # Arrange
    _write_config(workspace, VALID_CONFIG)

    # Act
    result = _run(workspace, "--check")

    # Assert: one line naming the Python found; no venv, no output directory, nothing else written.
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.startswith(f"local-integration.sh: check passed - Python {platform.python_version()} ")
    assert len(result.stdout.splitlines()) == 1
    assert sorted(path.name for path in workspace.iterdir()) == [".env.local", SCRIPT.name]


@needs_bash
def test_the_config_reads_comments_blank_lines_export_quotes_and_crlf(workspace):
    # Arrange: `.env.local` as an editor on Windows may leave it - CRLF line ends and no final one.
    lines = [
        "# a comment",
        "",
        *(f"{key}={value}" for key, value in VALID_CONFIG.items() if key not in ("PROJECT_ID", "TARGET_CHECKOUT")),
        'export PROJECT_ID="local-integration-test"',
        "  TARGET_CHECKOUT='../target'   ",
    ]
    (workspace / ".env.local").write_bytes("\r\n".join(lines).encode("utf-8"))

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "check passed" in result.stdout


@needs_bash
@pytest.mark.parametrize(("key", "value"), [("PROJECT_ID", None), ("TARGET_CHECKOUT", "")], ids=["absent", "empty"])
def test_a_required_setting_left_out_fails_with_one_line_naming_it(workspace, key, value):
    # Arrange
    config = {name: setting for name, setting in VALID_CONFIG.items() if name != key}
    if value is not None:
        config[key] = value
    _write_config(workspace, config)

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 1
    assert result.stderr.splitlines() == [f"local-integration.sh: {key} is not set in .env.local"]


@needs_bash
def test_a_mode_path_entry_not_in_the_checkout_fails_with_one_line_naming_it(workspace):
    # Arrange: the second of two comma-separated entries is missing.
    _write_config(workspace, {**VALID_CONFIG, "UI_TESTS_PATHS": "features/us, features/missing"})

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 1
    [line] = result.stderr.splitlines()
    assert line.startswith("local-integration.sh: UI_TESTS_PATHS entry 'features/missing' not found in TARGET_CHECKOUT")


@needs_bash
@pytest.mark.parametrize(("python", "says"), [("missing", "does not run"), ("3.9", "is 3.9.18")])
def test_a_python_that_does_not_run_or_is_older_than_3_10_fails_with_one_line(workspace, tmp_path, python, says):
    # Arrange: no file at all, or a Python 3.9 - it prints its version when asked and fails every other check.
    if python == "missing":
        interpreter = (tmp_path / "no-such-python").as_posix()
    else:
        interpreter = _executable(
            tmp_path / "python3.9", 'case "$2" in\n  *print*) echo 3.9.18 ;;\n  *) exit 1 ;;\nesac\n'
        )
    _write_config(workspace, {**VALID_CONFIG, "PYTHON": interpreter})

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 1
    assert result.stderr.splitlines() == [
        f"local-integration.sh: needs Python >= 3.10, and '{interpreter}' {says}; set PYTHON in .env.local"
    ]


@needs_bash
@pytest.mark.parametrize("passes", [True, False], ids=["check-passes", "check-fails"])
def test_a_token_in_the_shell_or_the_config_reaches_no_output_and_no_child(workspace, tmp_path, passes):
    # Arrange: the token everywhere an operator's may be - the shell, an action input and `.env.local` - and a
    # `PYTHON` that records the environment the script starts it with.
    record = tmp_path / "child-environment.txt"
    recording_python = _executable(
        tmp_path / "recording-python", f'env >> "{record.as_posix()}"\nexec "{Path(sys.executable).as_posix()}" "$@"\n'
    )
    config = {**VALID_CONFIG, "PYTHON": recording_python}
    if not passes:
        config["UI_TESTS_PATHS"] = "features/missing"
    _write_config(workspace, config, (f"GITHUB_TOKEN={TOKEN}",))
    env = {**os.environ, "GITHUB_TOKEN": TOKEN, "GH_TOKEN": TOKEN, "INPUT_GITHUB_TOKEN": TOKEN}

    # Act
    result = _run(workspace, "--check", env=env)

    # Assert: the `.env.local` line was read and reported by its number - neither its key nor its value is shown.
    assert result.returncode == (0 if passes else 1), result.stderr
    assert f".env.local:{len(config) + 1}: ignored, not a setting of this script" in result.stderr
    assert TOKEN not in result.stdout
    assert TOKEN not in result.stderr
    # Assert: what the script starts inherits neither the token nor any action input from the shell.
    child_environment = record.read_text(encoding="utf-8", errors="replace")
    assert "PATH=" in child_environment
    assert TOKEN not in child_environment
    assert [line for line in child_environment.splitlines() if line.startswith("INPUT_")] == []


@needs_bash
def test_a_line_that_is_no_setting_is_reported_by_its_number_alone(workspace):
    # Arrange: a pasted secret, no `=` in it.
    _write_config(workspace, VALID_CONFIG, (TOKEN,))

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 1
    assert result.stderr.splitlines() == [
        f"local-integration.sh: .env.local:{len(VALID_CONFIG) + 1}: not a KEY=value line"
    ]
    assert TOKEN not in result.stdout + result.stderr


@needs_bash
def test_a_pasted_secret_that_reads_as_a_key_is_reported_by_its_number_alone(workspace):
    # Arrange: a base64 secret's `=` padding makes the line read as `<key>=` - a key no setting has.
    secret = "c2VjcmV0X3Bhc3RlZF9ieV9taXN0YWtl"
    _write_config(workspace, VALID_CONFIG, (f"{secret}=",))

    # Act
    result = _run(workspace, "--check")

    # Assert: the line is ignored and named by its number; nothing of its text reaches the output.
    assert result.returncode == 0, result.stderr
    assert result.stderr.splitlines() == [
        f"local-integration.sh: .env.local:{len(VALID_CONFIG) + 1}: ignored, not a setting of this script"
    ]
    assert secret not in result.stdout + result.stderr


@needs_bash
@pytest.mark.parametrize(
    ("args", "message"),
    [(["--bogus"], "unknown argument '--bogus'"), (["--check", "--check"], "too many arguments")],
    ids=["unknown", "too-many"],
)
def test_an_unknown_argument_fails_with_one_line_of_usage(workspace, args, message):
    # Act
    result = _run(workspace, *args)

    # Assert
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.splitlines() == [f"local-integration.sh: {message}; usage: ./local-integration.sh [--check]"]


@needs_bash
def test_help_prints_the_usage_and_reads_no_config(workspace):
    # Act: the workspace has no `.env.local`, so a help that read it would fail.
    result = _run(workspace, "--help")

    # Assert
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.startswith("usage: ./local-integration.sh [--check]\n")
