#!/usr/bin/env bash
# Continuous Learning v3 - Setup Script
#
# Configures hooks for different AI coding agents.
#
# Usage:
#   ./setup.sh <agent> [--dry-run]
#
# Agents:
#   claude-code  - Claude Code CLI
#   cursor       - Cursor IDE
#   gemini       - Gemini CLI
#   opencode     - OpenCode
#   generic      - Generic stdin-based hooks

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DRY_RUN=false

AGENT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    claude-code|cursor|gemini|opencode|generic)
      AGENT="$1"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      shift
      ;;
  esac
done

if [ -z "$AGENT" ]; then
  echo "Usage: $0 <agent> [--dry-run]"
  echo ""
  echo "Agents: claude-code, cursor, gemini, opencode, generic"
  exit 1
fi

BASE_DIR="${AGENT_LEARNING_HOME:-${HOME}/.agent-learning}"

ensure_dirs() {
  mkdir -p "${BASE_DIR}/instincts/personal"
  mkdir -p "${BASE_DIR}/instincts/inherited"
  mkdir -p "${BASE_DIR}/evolved/skills"
  mkdir -p "${BASE_DIR}/evolved/commands"
  mkdir -p "${BASE_DIR}/evolved/agents"
  mkdir -p "${BASE_DIR}/projects"
}

setup_claude_code() {
  local settings_file="${HOME}/.claude/settings.json"
  local hook_cmd="${SKILL_ROOT}/hooks/observe.sh --format claude-code"
  
  echo "Setting up Claude Code hooks..."
  echo "  Settings file: $settings_file"
  echo "  Hook command: $hook_cmd"
  
  if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "[DRY RUN] Would add to $settings_file:"
    echo ""
    cat << 'EOF'
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "/path/to/skills/continuous-learning-v3/hooks/observe.sh --format claude-code pre"
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "/path/to/skills/continuous-learning-v3/hooks/observe.sh --format claude-code post"
      }]
    }]
  }
}
EOF
    return
  fi
  
  if [ ! -f "$settings_file" ]; then
    echo '{}' > "$settings_file"
  fi
  
  echo ""
  echo "Claude Code setup complete!"
  echo ""
  echo "Add the following to your $settings_file:"
  echo ""
  echo "  \"hooks\": {"
  echo "    \"PreToolUse\": [{"
  echo "      \"matcher\": \"*\","
  echo "      \"hooks\": [{"
  echo "        \"type\": \"command\","
  echo "        \"command\": \"${hook_cmd} pre\""
  echo "      }]"
  echo "    }],"
  echo "    \"PostToolUse\": [{"
  echo "      \"matcher\": \"*\","
  echo "      \"hooks\": [{"
  echo "        \"type\": \"command\","
  echo "        \"command\": \"${hook_cmd} post\""
  echo "      }]"
  echo "    }]"
  echo "  }"
}

setup_cursor() {
  local settings_file="${HOME}/.cursor/settings.json"
  
  echo "Setting up Cursor hooks..."
  echo "  Settings file: $settings_file"
  echo ""
  
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would configure Cursor hooks"
    return
  fi
  
  echo "NOTE: Cursor hook support may vary."
  echo "Check Cursor documentation for current hook configuration."
  echo ""
  echo "Hook script: ${SKILL_ROOT}/hooks/adapters/cursor.sh"
}

setup_gemini() {
  local config_dir="${HOME}/.config/gemini"
  
  echo "Setting up Gemini CLI hooks..."
  echo "  Config directory: $config_dir"
  echo ""
  
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would configure Gemini CLI hooks"
    return
  fi
  
  echo "NOTE: Gemini CLI hook support may vary."
  echo "Hook script: ${SKILL_ROOT}/hooks/adapters/gemini.sh"
}

setup_opencode() {
  local plugin_dir="${HOME}/.config/opencode/plugins"
  local plugin_src="${SKILL_ROOT}/plugins/continuous-learning.js"
  local plugin_dst="${plugin_dir}/continuous-learning.js"
  
  echo "Setting up OpenCode plugin..."
  echo "  Plugin source: $plugin_src"
  echo "  Plugin destination: $plugin_dst"
  echo ""
  
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would copy plugin to $plugin_dst"
    return
  fi
  
  mkdir -p "$plugin_dir"
  
  if [ -f "$plugin_dst" ]; then
    local backup="${plugin_dst}.$(date +%Y%m%d-%H%M%S).bak"
    cp "$plugin_dst" "$backup"
    echo "  Backed up existing plugin to: $backup"
  fi
  
  cp "$plugin_src" "$plugin_dst"
  
  echo ""
  echo "Plugin installed successfully!"
  echo ""
  echo "The plugin will automatically:"
  echo "  - Log tool executions to ${BASE_DIR}/projects/<project-id>/observations.jsonl"
  echo "  - Track project context via git remote URL"
  echo ""
  echo "To disable temporarily:"
  echo "  export AGENT_LEARNING_DISABLED=1"
  echo ""
  echo "To change storage location:"
  echo "  export AGENT_LEARNING_HOME=/custom/path"
}

setup_generic() {
  echo "Setting up generic hooks..."
  echo ""
  echo "The generic observer reads JSON from stdin:"
  echo ""
  echo "  echo '{\"tool\":\"Edit\",\"input\":\"...\"}' | \\"
  echo "    ${SKILL_ROOT}/hooks/observe.sh --format generic"
  echo ""
  echo "Or with environment variables:"
  echo ""
  echo "  AGENT_NAME=my-agent \\"
  echo "  AGENT_PROJECT_DIR=/path/to/project \\"
  echo "  cat events.jsonl | ${SKILL_ROOT}/hooks/observe.sh"
}

echo ""
echo "========================================"
echo "  Continuous Learning v3 Setup"
echo "  Agent: $AGENT"
echo "  Storage: $BASE_DIR"
echo "========================================"
echo ""

if [ "$DRY_RUN" = false ]; then
  ensure_dirs
fi

case "$AGENT" in
  claude-code) setup_claude_code ;;
  cursor) setup_cursor ;;
  gemini) setup_gemini ;;
  opencode) setup_opencode ;;
  generic) setup_generic ;;
esac

echo ""
echo "CLI commands:"
echo "  python3 ${SKILL_ROOT}/scripts/instinct-cli.py status"
echo "  python3 ${SKILL_ROOT}/scripts/instinct-cli.py evolve"
echo "  python3 ${SKILL_ROOT}/scripts/instinct-cli.py --help"
echo ""
