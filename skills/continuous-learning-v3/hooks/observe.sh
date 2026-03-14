#!/usr/bin/env bash
# Continuous Learning v3 - Observation Hook (Agent-Agnostic)
#
# Captures tool use events for pattern analysis.
# Supports multiple agent formats via adapters.
#
# Usage:
#   ./observe.sh [--format <format>] [pre|post]
#   echo '{"tool":"Edit",...}' | ./observe.sh --format generic
#
# Environment:
#   AGENT_LEARNING_HOME    - Base directory (default: ~/.agent-learning)
#   AGENT_PROJECT_DIR      - Override project detection
#   AGENT_LEARNING_DISABLED - Set to 1 to disable
#   AGENT_LEARNING_PYTHON  - Python interpreter (default: python3)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

HOOK_PHASE="post"
HOOK_FORMAT=""

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --format)
        HOOK_FORMAT="$2"
        shift 2
        ;;
      pre|post)
        HOOK_PHASE="$1"
        shift
        ;;
      *)
        shift
        ;;
    esac
  done
}

parse_args "$@"

if [ "${AGENT_LEARNING_DISABLED:-}" = "1" ]; then
  exit 0
fi

resolve_python_cmd() {
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

PYTHON_CMD="$(resolve_python_cmd 2>/dev/null || true)"
if [ -z "$PYTHON_CMD" ]; then
  echo "[observe] No python interpreter found, skipping observation" >&2
  exit 0
fi

INPUT_JSON=$(cat)

if [ -z "$INPUT_JSON" ]; then
  exit 0
fi

detect_hook_format() {
  local input="$1"
  
  if echo "$input" | "$PYTHON_CMD" -c '
import json, sys
data = json.load(sys.stdin)
exit(0 if "tool_name" in data or "tool" in data else 1)
' 2>/dev/null; then
    echo "generic"
  else
    echo "generic"
  fi
}

FORMAT="${HOOK_FORMAT:-$(detect_hook_format "$INPUT_JSON")}"

source "${SKILL_ROOT}/scripts/detect-project.sh"

BASE_DIR="${AGENT_LEARNING_HOME:-${HOME}/.agent-learning}"
OBSERVATIONS_FILE="${PROJECT_DIR}/observations.jsonl"
MAX_FILE_SIZE_MB=10

if [ -f "${BASE_DIR}/disabled" ]; then
  exit 0
fi

PURGE_MARKER="${PROJECT_DIR}/.last-purge"
if [ ! -f "$PURGE_MARKER" ] || [ "$(find "$PURGE_MARKER" -mtime +1 2>/dev/null)" ]; then
  find "${PROJECT_DIR}" -name "observations-*.jsonl" -mtime +30 -delete 2>/dev/null || true
  touch "$PURGE_MARKER" 2>/dev/null || true
fi

ADAPTER_SCRIPT="${SCRIPT_DIR}/adapters/${FORMAT}.sh"
if [ -f "$ADAPTER_SCRIPT" ]; then
  NORMALIZED_INPUT=$("$ADAPTER_SCRIPT" "$INPUT_JSON" "$HOOK_PHASE" 2>/dev/null || echo "$INPUT_JSON")
else
  NORMALIZED_INPUT="$INPUT_JSON"
fi

PARSED=$(echo "$NORMALIZED_INPUT" | HOOK_PHASE="$HOOK_PHASE" "$PYTHON_CMD" -c '
import json
import sys
import os

try:
    data = json.load(sys.stdin)
    hook_phase = os.environ.get("HOOK_PHASE", "post")
    event = "tool_start" if hook_phase == "pre" else "tool_complete"

    tool_name = data.get("tool_name", data.get("tool", "unknown"))
    tool_input = data.get("tool_input", data.get("input", {}))
    tool_output = data.get("tool_response", data.get("tool_output", data.get("output", "")))
    session_id = data.get("session_id", data.get("session", "unknown"))
    tool_use_id = data.get("tool_use_id", data.get("id", ""))
    cwd = data.get("cwd", data.get("working_directory", ""))
    agent = data.get("agent", os.environ.get("AGENT_NAME", "unknown"))

    if isinstance(tool_input, dict):
        tool_input_str = json.dumps(tool_input)[:5000]
    else:
        tool_input_str = str(tool_input)[:5000]

    if isinstance(tool_output, dict):
        tool_response_str = json.dumps(tool_output)[:5000]
    else:
        tool_response_str = str(tool_output)[:5000]

    print(json.dumps({
        "parsed": True,
        "event": event,
        "tool": tool_name,
        "input": tool_input_str if event == "tool_start" else None,
        "output": tool_response_str if event == "tool_complete" else None,
        "session": session_id,
        "tool_use_id": tool_use_id,
        "cwd": cwd,
        "agent": agent
    }))
except Exception as e:
    print(json.dumps({"parsed": False, "error": str(e)}))
')

PARSED_OK=$(echo "$PARSED" | "$PYTHON_CMD" -c "import json,sys; print(json.load(sys.stdin).get('parsed', False))" 2>/dev/null || echo "False")

if [ "$PARSED_OK" != "True" ]; then
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  export TIMESTAMP="$timestamp"
  echo "$INPUT_JSON" | "$PYTHON_CMD" -c '
import json, sys, os, re

_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'"'"'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)

raw = sys.stdin.read()[:2000]
raw = _SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]", raw)
print(json.dumps({"timestamp": os.environ["TIMESTAMP"], "event": "parse_error", "raw": raw}))
' >> "$OBSERVATIONS_FILE"
  exit 0
fi

if [ -f "$OBSERVATIONS_FILE" ]; then
  file_size_mb=$(du -m "$OBSERVATIONS_FILE" 2>/dev/null | cut -f1)
  if [ "${file_size_mb:-0}" -ge "$MAX_FILE_SIZE_MB" ]; then
    archive_dir="${PROJECT_DIR}/observations.archive"
    mkdir -p "$archive_dir"
    mv "$OBSERVATIONS_FILE" "$archive_dir/observations-$(date +%Y%m%d-%H%M%S)-$$.jsonl" 2>/dev/null || true
  fi
fi

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

export PROJECT_ID_ENV="$PROJECT_ID"
export PROJECT_NAME_ENV="$PROJECT_NAME"
export TIMESTAMP="$timestamp"
export BASE_DIR_ENV="$BASE_DIR"

echo "$PARSED" | "$PYTHON_CMD" -c '
import json, sys, os, re

parsed = json.load(sys.stdin)
observation = {
    "timestamp": os.environ["TIMESTAMP"],
    "event": parsed["event"],
    "tool": parsed["tool"],
    "session": parsed["session"],
    "agent": parsed.get("agent", "unknown"),
    "project_id": os.environ.get("PROJECT_ID_ENV", "global"),
    "project_name": os.environ.get("PROJECT_NAME_ENV", "global")
}

_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'"'"'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)

def scrub(val):
    if val is None:
        return None
    return _SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]", str(val))

if parsed["input"]:
    observation["input"] = scrub(parsed["input"])
if parsed["output"] is not None:
    observation["output"] = scrub(parsed["output"])

print(json.dumps(observation))
' >> "$OBSERVATIONS_FILE"

for pid_file in "${PROJECT_DIR}/.observer.pid" "${BASE_DIR}/.observer.pid"; do
  if [ -f "$pid_file" ]; then
    observer_pid=$(cat "$pid_file")
    if kill -0 "$observer_pid" 2>/dev/null; then
      kill -USR1 "$observer_pid" 2>/dev/null || true
    fi
  fi
done

exit 0
