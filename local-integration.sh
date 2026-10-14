#!/usr/bin/env bash
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
# Run the real collector over a configured checkout, outside any workflow: `doc-source` and `ui-tests`, in a venv
# of its own built from `requirements.txt` alone, then re-read every artifact with `read_artifact` and print what
# ran and what came out. The configuration is `.env.local` (copy `.env.local.example`). See DEVELOPER.md
# § Local Integration Run.
#
#   ./local-integration.sh            # check, build the venv, run both modes, validate and report
#   ./local-integration.sh --check    # check Python, git, the configuration and every path; nothing else
#
# Runs in bash 3.2 or later: Linux, macOS, or Git Bash on Windows.

set -euo pipefail

ME="local-integration.sh"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

ENV_FILE=".env.local"
# The script's own venv, never the developer's `.venv`: it holds `requirements.txt` and nothing else, so a runtime
# requirement missing from that file fails here as it would on a runner.
VENV=".venv-local-integration"

# Every setting `.env.local` may hold; a line with any other key is ignored and reported by its number only.
KEYS="PROJECT_ID TARGET_CHECKOUT ORGANIZATION_NAME REPOSITORY_NAME DOC_SOURCE_US_PATHS DOC_SOURCE_FUNC_PATHS
DOC_SOURCE_PAGES_PATHS UI_TESTS_PATHS GITHUB_SERVER_URL OUT_DIR PYTHON"
REQUIRED="PROJECT_ID TARGET_CHECKOUT ORGANIZATION_NAME REPOSITORY_NAME DOC_SOURCE_US_PATHS UI_TESTS_PATHS"

die() { printf '%s: %s\n' "$ME" "$*" >&2; exit 1; }
note() { printf '%s: %s\n' "$ME" "$*" >&2; }
is_key() { local key; for key in $KEYS; do [ "$key" = "$1" ] && return 0; done; return 1; }

# Echo a command, each argument quoted where the shell would need it, then run it.
run() {
  local line="+" arg
  for arg in "$@"; do
    case "$arg" in
      "" | *[!A-Za-z0-9_./:=@,+-]*) line="$line '${arg//\'/\'\\\'\'}'" ;;
      *) line="$line $arg" ;;
    esac
  done
  printf '%s\n' "$line" >&2
  "$@"
}

usage() {
  cat <<EOF
usage: ./$ME [--check]

Runs doc-source and ui-tests over the checkout configured in $ENV_FILE (copy .env.local.example), validates
each artifact with read_artifact and prints a report.

  --check   verify Python, git, the configuration and every configured path; create no venv, run nothing
EOF
}

CHECK_ONLY=false
case "${1-}" in
  "") ;;
  --check) CHECK_ONLY=true ;;
  -h | --help) usage; exit 0 ;;
  *) die "unknown argument '$1'; usage: ./$ME [--check]" ;;
esac
[ $# -le 1 ] || die "too many arguments; usage: ./$ME [--check]"

# No mode reads a credential: both read local checkouts and call no API. Drop the token names an operator's shell
# may still carry from versions that needed one, so nothing this script starts can print or write one.
unset GITHUB_TOKEN GH_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN
# Every action input comes from `.env.local`; none is inherited from the shell (`INPUT_GITHUB_TOKEN` included).
for name in $(compgen -e); do
  case "$name" in INPUT_*) unset "$name" ;; esac
done

# --- Configuration -------------------------------------------------------------------------------------------
# Read as data, never sourced: a sourced file runs whatever it holds and would put any token it carries into the
# environment of every command below.
for key in $KEYS; do printf -v "CFG_$key" '%s' ""; done
[ -f "$ENV_FILE" ] || die "$ENV_FILE not found; copy .env.local.example to $ENV_FILE and set TARGET_CHECKOUT"
line_no=0
while IFS= read -r line || [ -n "$line" ]; do
  line_no=$((line_no + 1))
  line="${line%$'\r'}"
  line="${line#"${line%%[![:space:]]*}"}"
  case "$line" in "" | "#"*) continue ;; esac
  line="${line#export }"
  key="${line%%=*}"
  # A line is reported by its number only, never by its text: it may be a pasted secret, and a base64 one ending in
  # `=` padding reads as a key.
  [[ "$line" == *=* && "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || die "$ENV_FILE:$line_no: not a KEY=value line"
  value="${line#*=}"
  value="${value%"${value##*[![:space:]]}"}"
  case "$value" in
    \"*\") value="${value#\"}"; value="${value%\"}" ;;
    \'*\') value="${value#\'}"; value="${value%\'}" ;;
  esac
  if is_key "$key"; then
    printf -v "CFG_$key" '%s' "$value"
  else
    note "$ENV_FILE:$line_no: ignored, not a setting of this script"
  fi
done < "$ENV_FILE"

for key in $REQUIRED; do
  var="CFG_$key"
  [ -n "${!var}" ] || die "$key is not set in $ENV_FILE"
done
# Mirrors living_doc_utilities.contracts.envelope.PROJECT_ID_PATTERN, so a bad PROJECT_ID fails here - at --check -
# rather than later, as the collector's own ContractError. Matched with LC_ALL=C: under some locales, bash's
# bracket ranges collate case-insensitively, so `[a-z]` can otherwise match an uppercase letter too.
(LC_ALL=C; [[ "$CFG_PROJECT_ID" =~ ^[a-z0-9][a-z0-9-]*$ ]]) \
  || die "PROJECT_ID '$CFG_PROJECT_ID' does not match ^[a-z0-9][a-z0-9-]*\$ (lowercase alphanumeric and hyphen, starting alphanumeric)"
CFG_OUT_DIR="${CFG_OUT_DIR:-./output}"

# A configured path: `~/` is the home directory, and a relative one resolves against this repository's root.
resolve() {
  case "$1" in
    "~/"*) printf '%s\n' "$HOME/${1#"~/"}" ;;
    /* | [A-Za-z]:[/\\]*) printf '%s\n' "$1" ;;
    *) printf '%s\n' "$ROOT/${1#./}" ;;
  esac
}

# An existing directory's absolute path in the form the venv's Python reads. Git Bash's `pwd -W` gives `C:/...`;
# elsewhere `-W` is an error, and plain `pwd` is already right.
native_dir() { (cd "$1" && { pwd -W 2>/dev/null || pwd; }); }

# --- Checks (also the whole of --check) ----------------------------------------------------------------------
# The interpreter: `PYTHON` when set, else `python3`, else `python` - the order `action.yml` resolves it in.
PY="${CFG_PYTHON:-$(command -v python3 || command -v python || true)}"
[ -n "$PY" ] || die "needs Python >= 3.10, and neither python3 nor python is on PATH; set PYTHON in $ENV_FILE"
PY_VERSION="$("$PY" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null | tr -d '\r')" \
  || die "needs Python >= 3.10, and '$PY' does not run; set PYTHON in $ENV_FILE"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || die "needs Python >= 3.10, and '$PY' is $PY_VERSION; set PYTHON in $ENV_FILE"

command -v git >/dev/null 2>&1 || die "git is not on PATH"

TARGET="$(resolve "$CFG_TARGET_CHECKOUT")"
[ -d "$TARGET" ] || die "TARGET_CHECKOUT not found: $TARGET"
TARGET="$(cd "$TARGET" && pwd)"
git -C "$TARGET" rev-parse --verify --quiet HEAD >/dev/null || die "TARGET_CHECKOUT is not a git checkout: $TARGET"
# Resolved once, symlinks and all, so a mode path entry's own resolved directory can be checked against it below -
# a `../` or a symlinked subdirectory must not be able to point collection outside the checkout.
TARGET_REAL="$(cd "$TARGET" && pwd -P)"

# One `<repository key>=<absolute directory>` line per comma-separated entry of a mode path setting, each entry
# relative to the checkout; the form `tools.local_integration repositories` reads. Prints nothing when unset.
mode_paths() {  # mode_paths CONFIG_KEY REPOSITORY_KEY
  local var="CFG_$1" entries entry resolved
  [ -n "${!var}" ] || return 0
  IFS=',' read -r -a entries <<< "${!var}"
  for entry in "${entries[@]}"; do
    entry="${entry#"${entry%%[![:space:]]*}"}"
    entry="${entry%"${entry##*[![:space:]]}"}"
    [ -n "$entry" ] || die "$1 has an empty entry"
    [ -d "$TARGET/$entry" ] || die "$1 entry '$entry' not found in TARGET_CHECKOUT: $TARGET/$entry"
    # A `../` entry or a symlinked subdirectory can point at a real directory outside TARGET_CHECKOUT even though
    # the `-d` check above passed; resolve it and reject anything that lands outside.
    resolved="$(cd "$TARGET/$entry" && pwd -P)"
    case "$resolved" in
      "$TARGET_REAL" | "$TARGET_REAL"/*) ;;
      *) die "$1 entry '$entry' resolves outside TARGET_CHECKOUT: $resolved" ;;
    esac
    printf '%s=%s\n' "$2" "$(native_dir "$TARGET/$entry")"
  done
}
DOC_SOURCE_PATHS="$(
  mode_paths DOC_SOURCE_US_PATHS us-paths
  mode_paths DOC_SOURCE_FUNC_PATHS func-paths
  mode_paths DOC_SOURCE_PAGES_PATHS pages-paths
)"
UI_TESTS_PATHS="$(mode_paths UI_TESTS_PATHS paths)"

OUT="$(resolve "$CFG_OUT_DIR")"
[ ! -e "$OUT" ] || [ -d "$OUT" ] || die "OUT_DIR is not a directory: $OUT"

if [ "$CHECK_ONLY" = true ]; then
  printf '%s: check passed - Python %s (%s), git, %s, TARGET_CHECKOUT %s\n' \
    "$ME" "$PY_VERSION" "$PY" "$ENV_FILE" "$TARGET"
  exit 0
fi

# --- The venv, as `action.yml` builds its own --------------------------------------------------------------------
# The install must land in the venv and nowhere else: these redirect pip's target or prepend to `sys.path`.
# Unset, not set empty: pip reads its own variables as configuration values.
unset PIP_TARGET PIP_PREFIX PIP_USER PYTHONPATH

venv_python() {
  if [ -x "$VENV/bin/python" ]; then
    printf '%s\n' "$VENV/bin/python"
  elif [ -x "$VENV/Scripts/python.exe" ]; then
    printf '%s\n' "$VENV/Scripts/python.exe"
  else
    return 1
  fi
}

# Reuse the venv only when the interpreter now configured built it, from the `requirements.txt` now in the tree.
# A requirement dropped from the file would otherwise stay installed, and the run would hide what it should show.
IDENTITY='import sys; print(sys.base_prefix, sys.version_info[:3])'
WANT="$("$PY" -c "$IDENTITY")"
HAVE=""
if VPY="$(venv_python)" && cmp -s requirements.txt "$VENV/requirements.txt"; then
  HAVE="$("$VPY" -c "$IDENTITY" 2>/dev/null || true)"
fi
if [ "$HAVE" != "$WANT" ]; then
  run rm -rf "$VENV"
  run "$PY" -m venv "$VENV" || die "'$PY -m venv' failed; install the venv module"
  VPY="$(venv_python)" || die "'$PY -m venv' made no interpreter under $VENV/bin or $VENV/Scripts"
fi
run "$VPY" -m pip install --disable-pip-version-check -r requirements.txt
# pip's own config files can still redirect the install while pip exits 0; one import through the venv's
# interpreter reports it here, where it happened.
run "$VPY" -E -c 'import living_doc_utilities, pydantic' \
  || die "the requirements did not land in $VENV; check pip's configuration for a 'target' or 'prefix' setting"
run cp requirements.txt "$VENV/requirements.txt"

# --- What runs ---------------------------------------------------------------------------------------------------
commit_of() {  # commit_of DIR: its HEAD, marked when tracked files differ from it
  local sha
  sha="$(git -C "$1" rev-parse HEAD 2>/dev/null)" || { echo "unknown (not a git checkout)"; return 0; }
  if [ -n "$(git -C "$1" status --porcelain --untracked-files=no 2>/dev/null)" ]; then
    sha="$sha (uncommitted changes)"
  fi
  printf '%s\n' "$sha"
}

UTILITIES_VERSION="$("$VPY" -E -c 'from importlib.metadata import version; print(version("living-doc-utilities"))' \
  | tr -d '\r')"
VENV_PY_VERSION="$("$VPY" -E -c 'import platform; print(platform.python_version())' | tr -d '\r')"
run mkdir -p "$OUT"
OUTPUT_PATH="$(native_dir "$OUT")/collector-gh"
# Each mode clears only its own directory, so a run that stops at `doc-source` would leave the previous run's
# `ui-tests` artifact beside it. Clear both first: the output holds this run's artifacts and nothing older.
run rm -rf "$OUT/collector-gh/doc-source" "$OUT/collector-gh/ui-tests"

cat <<EOF
== $ME
collector:             $(commit_of "$ROOT")
living-doc-utilities:  $UTILITIES_VERSION
python:                $VENV_PY_VERSION ($VPY)
target:                $(commit_of "$TARGET") ($TARGET)
project id:            $CFG_PROJECT_ID
output:                $OUTPUT_PATH
EOF

# `main.py` writes the `output-path` action output to `$GITHUB_OUTPUT`, which only a runner provides.
GITHUB_OUTPUT_FILE="$VENV/github-output.txt"

now_ms() { "$VPY" -E -c 'import time; print(int(time.time() * 1000))' | tr -d '\r'; }

# Run one mode as the action does - `-E`, every input in the command's own environment - then validate and report
# its artifact.
collect() {  # collect MODE DOC_SOURCE_SWITCH UI_TESTS_SWITCH REPOSITORIES_INPUT PATHS
  local mode="$1" paths path repositories started finished status=0
  paths=()
  while IFS= read -r path; do paths+=("$path"); done <<< "$5"
  echo
  echo "== $mode"
  repositories="$(run "$VPY" -E -X utf8 -m tools.local_integration repositories \
    "$CFG_ORGANIZATION_NAME" "$CFG_REPOSITORY_NAME" "${paths[@]}")" \
    || die "could not build the '$mode' repository list"
  : > "$GITHUB_OUTPUT_FILE"
  started="$(now_ms)"
  run env GITHUB_OUTPUT="$GITHUB_OUTPUT_FILE" \
    INPUT_PROJECT_ID="$CFG_PROJECT_ID" INPUT_OUTPUT_PATH="$OUTPUT_PATH" \
    INPUT_GITHUB_SERVER_URL="$CFG_GITHUB_SERVER_URL" \
    INPUT_DOC_SOURCE="$2" INPUT_UI_TESTS="$3" "$4=$repositories" \
    "$VPY" -E main.py || status=$?
  finished="$(now_ms)"
  [ "$status" -eq 0 ] || die "the collector failed in '$mode' (exit $status); its log is above"
  run "$VPY" -E -X utf8 -m tools.local_integration report "$OUTPUT_PATH" "$mode" "$((finished - started))" \
    || die "the '$mode' artifact failed validation"
}

collect doc-source true false INPUT_DOC_SOURCE_REPOSITORIES "$DOC_SOURCE_PATHS"
collect ui-tests false true INPUT_UI_TESTS_REPOSITORIES "$UI_TESTS_PATHS"

echo
echo "$ME: both artifacts written and valid under $OUTPUT_PATH"
