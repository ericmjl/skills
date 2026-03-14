#!/usr/bin/env bash
# Continuous Learning v3 - Project Detection Helper
#
# Shared logic for detecting current project context.
# Sourced by observe.sh and other scripts.
#
# Exports:
#   PROJECT_ID     - Short hash identifying the project (or "global")
#   PROJECT_NAME   - Human-readable project name
#   PROJECT_ROOT   - Absolute path to project root
#   PROJECT_DIR    - Project-scoped storage directory
#
# Detection priority:
#   1. AGENT_PROJECT_DIR env var (if set)
#   2. CLAUDE_PROJECT_DIR env var (backward compat, if set)
#   3. git remote URL (hashed for uniqueness across machines)
#   4. git repo root path (fallback, machine-specific)
#   5. "global" (no project context detected)

_ALV3_BASE_DIR="${AGENT_LEARNING_HOME:-${HOME}/.agent-learning}"
_ALV3_PROJECTS_DIR="${_ALV3_BASE_DIR}/projects"
_ALV3_REGISTRY_FILE="${_ALV3_BASE_DIR}/projects.json"

_alv3_resolve_python_cmd() {
  if [ -n "${AGENT_LEARNING_PYTHON:-}" ] && command -v "$AGENT_LEARNING_PYTHON" >/dev/null 2>&1; then
    printf '%s\n' "$AGENT_LEARNING_PYTHON"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    printf '%s\n' python
    return 0
  fi
  return 1
}

_ALV3_PYTHON_CMD="$(_alv3_resolve_python_cmd 2>/dev/null || true)"

_alv3_detect_project() {
  local project_root=""
  local project_name=""
  local project_id=""
  local source_hint=""

  if [ -n "$AGENT_PROJECT_DIR" ] && [ -d "$AGENT_PROJECT_DIR" ]; then
    project_root="$AGENT_PROJECT_DIR"
    source_hint="env"
  fi

  if [ -z "$project_root" ] && [ -n "$CLAUDE_PROJECT_DIR" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
    project_root="$CLAUDE_PROJECT_DIR"
    source_hint="env-legacy"
  fi

  if [ -z "$project_root" ] && command -v git &>/dev/null; then
    project_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [ -n "$project_root" ]; then
      source_hint="git"
    fi
  fi

  if [ -z "$project_root" ]; then
    PROJECT_ID="global"
    PROJECT_NAME="global"
    PROJECT_ROOT=""
    PROJECT_DIR="${_ALV3_BASE_DIR}"
    return 0
  fi

  project_name=$(basename "$project_root")

  local remote_url=""
  if command -v git &>/dev/null; then
    if [ "$source_hint" = "git" ] || [ -d "${project_root}/.git" ]; then
      remote_url=$(git -C "$project_root" remote get-url origin 2>/dev/null || true)
    fi
  fi

  if [ -n "$remote_url" ]; then
    remote_url=$(printf '%s' "$remote_url" | sed -E 's|://[^@]+@|://|')
  fi

  local hash_input="${remote_url:-$project_root}"
  
  if [ -n "$_ALV3_PYTHON_CMD" ]; then
    project_id=$(printf '%s' "$hash_input" | "$_ALV3_PYTHON_CMD" -c "import sys,hashlib; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest()[:12])" 2>/dev/null)
  fi

  if [ -z "$project_id" ]; then
    project_id=$(printf '%s' "$hash_input" | shasum -a 256 2>/dev/null | cut -c1-12 || \
                 printf '%s' "$hash_input" | sha256sum 2>/dev/null | cut -c1-12 || \
                 echo "fallback")
  fi

  PROJECT_ID="$project_id"
  PROJECT_NAME="$project_name"
  PROJECT_ROOT="$project_root"
  PROJECT_DIR="${_ALV3_PROJECTS_DIR}/${project_id}"

  mkdir -p "${PROJECT_DIR}/instincts/personal"
  mkdir -p "${PROJECT_DIR}/instincts/inherited"
  mkdir -p "${PROJECT_DIR}/observations.archive"
  mkdir -p "${PROJECT_DIR}/evolved/skills"
  mkdir -p "${PROJECT_DIR}/evolved/commands"
  mkdir -p "${PROJECT_DIR}/evolved/agents"

  _alv3_update_project_registry "$project_id" "$project_name" "$project_root" "$remote_url"
}

_alv3_update_project_registry() {
  local pid="$1"
  local pname="$2"
  local proot="$3"
  local premote="$4"

  mkdir -p "$(dirname "$_ALV3_REGISTRY_FILE")"

  if [ -z "$_ALV3_PYTHON_CMD" ]; then
    return 0
  fi

  _ALV3_REG_PID="$pid" \
  _ALV3_REG_PNAME="$pname" \
  _ALV3_REG_PROOT="$proot" \
  _ALV3_REG_PREMOTE="$premote" \
  _ALV3_REG_PDIR="$PROJECT_DIR" \
  _ALV3_REG_FILE="$_ALV3_REGISTRY_FILE" \
  "$_ALV3_PYTHON_CMD" -c '
import json, os, tempfile
from datetime import datetime, timezone

registry_path = os.environ["_ALV3_REG_FILE"]
project_dir = os.environ["_ALV3_REG_PDIR"]
project_file = os.path.join(project_dir, "project.json")

os.makedirs(project_dir, exist_ok=True)

def atomic_write_json(path, payload):
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{os.path.basename(path)}.tmp.",
        dir=os.path.dirname(path),
        text=True,
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

try:
    with open(registry_path) as f:
        registry = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    registry = {}

now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
entry = registry.get(os.environ["_ALV3_REG_PID"], {})

metadata = {
    "id": os.environ["_ALV3_REG_PID"],
    "name": os.environ["_ALV3_REG_PNAME"],
    "root": os.environ["_ALV3_REG_PROOT"],
    "remote": os.environ["_ALV3_REG_PREMOTE"],
    "created_at": entry.get("created_at", now),
    "last_seen": now,
}

registry[os.environ["_ALV3_REG_PID"]] = metadata

atomic_write_json(project_file, metadata)
atomic_write_json(registry_path, registry)
' 2>/dev/null || true
}

_alv3_detect_project

export PROJECT_ID PROJECT_NAME PROJECT_ROOT PROJECT_DIR
