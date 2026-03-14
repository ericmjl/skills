#!/usr/bin/env bash
# OpenCode Hook Adapter
#
# Transforms OpenCode hook format to generic format.
# NOTE: Adjust field mappings based on OpenCode actual hook API.

set -e

INPUT="$1"
HOOK_PHASE="$2"

echo "$INPUT" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)
    
    result = {
        "tool_name": data.get("tool", data.get("toolName", "unknown")),
        "tool_input": data.get("tool_input", data.get("input", {})),
        "tool_response": data.get("tool_response", data.get("output", "")),
        "session_id": data.get("session_id", data.get("sessionId", "unknown")),
        "tool_use_id": data.get("tool_use_id", data.get("id", "")),
        "cwd": data.get("cwd", data.get("workingDirectory", "")),
        "agent": "opencode"
    }
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e), "raw": sys.stdin.read()[:500]}))
'
