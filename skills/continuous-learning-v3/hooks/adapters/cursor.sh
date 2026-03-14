#!/usr/bin/env bash
# Cursor Hook Adapter
#
# Transforms Cursor hook format to generic format.
# NOTE: Cursor's hook support may vary - adjust based on actual API.

set -e

INPUT="$1"
HOOK_PHASE="$2"

echo "$INPUT" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)
    
    result = {
        "tool_name": data.get("toolName", data.get("tool", "unknown")),
        "tool_input": data.get("toolInput", data.get("input", {})),
        "tool_response": data.get("toolResponse", data.get("output", "")),
        "session_id": data.get("sessionId", data.get("session_id", "unknown")),
        "tool_use_id": data.get("toolUseId", data.get("id", "")),
        "cwd": data.get("cwd", data.get("workingDirectory", "")),
        "agent": "cursor"
    }
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e), "raw": sys.stdin.read()[:500]}))
'
