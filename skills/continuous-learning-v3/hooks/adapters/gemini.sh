#!/usr/bin/env bash
# Gemini CLI Hook Adapter
#
# Transforms Gemini CLI hook format to generic format.
# NOTE: Adjust field mappings based on Gemini CLI actual hook API.

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
        "tool_input": data.get("input", data.get("toolInput", {})),
        "tool_response": data.get("output", data.get("toolResponse", "")),
        "session_id": data.get("session_id", data.get("sessionId", "unknown")),
        "tool_use_id": data.get("id", data.get("toolUseId", "")),
        "cwd": data.get("cwd", data.get("workingDirectory", "")),
        "agent": "gemini"
    }
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e), "raw": sys.stdin.read()[:500]}))
'
