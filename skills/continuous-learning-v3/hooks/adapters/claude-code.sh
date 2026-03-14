#!/usr/bin/env bash
# Claude Code Hook Adapter
#
# Transforms Claude Code hook format to generic format.
# Claude Code passes hook data via stdin as JSON with:
#   - tool_name, tool_input, tool_response, session_id, tool_use_id, cwd

set -e

INPUT="$1"
HOOK_PHASE="$2"

echo "$INPUT" | python3 -c '
import json
import sys
import os

try:
    data = json.load(sys.stdin)
    
    result = {
        "tool_name": data.get("tool_name", data.get("tool", "unknown")),
        "tool_input": data.get("tool_input", data.get("input", {})),
        "tool_response": data.get("tool_response", data.get("tool_output", data.get("output", ""))),
        "session_id": data.get("session_id", "unknown"),
        "tool_use_id": data.get("tool_use_id", ""),
        "cwd": data.get("cwd", ""),
        "agent": "claude-code"
    }
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e), "raw": sys.stdin.read()[:500]}))
'
