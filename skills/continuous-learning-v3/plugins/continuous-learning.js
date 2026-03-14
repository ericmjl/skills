/**
 * Continuous Learning v3 - OpenCode Plugin
 *
 * Observes tool execution and logs observations for pattern analysis.
 * Install by copying to ~/.config/opencode/plugins/ or .opencode/plugins/
 *
 * Environment variables:
 *   AGENT_LEARNING_HOME    - Base directory (default: ~/.agent-learning)
 *   AGENT_LEARNING_DISABLED - Set to "1" to disable
 */

import { appendFileSync, existsSync, mkdirSync, writeFileSync } from "fs"
import { homedir } from "os"
import { join, dirname } from "path"
import { createHash } from "crypto"
import { execSync } from "child_process"

const BASE_DIR = process.env.AGENT_LEARNING_HOME || join(homedir(), ".agent-learning")
const MAX_FILE_SIZE_MB = 10

const SECRET_RE = /(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)(["\s:=]+)([A-Za-z]+\s+)?([A-Za-z0-9_\-/.+=]{8,})/g

function redactSecrets(str) {
  if (!str) return str
  return str.replace(SECRET_RE, "$1$2$3[REDACTED]")
}

function ensureDir(dir) {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true })
  }
}

function getProjectInfo(cwd) {
  if (!cwd) {
    return { id: "global", name: "global", root: "" }
  }

  const projectName = cwd.split("/").pop() || "unknown"
  
  let remoteUrl = ""
  let projectRoot = cwd
  
  try {
    projectRoot = execSync("git rev-parse --show-toplevel", { 
      cwd, 
      encoding: "utf-8", 
      stdio: ["pipe", "pipe", "pipe"] 
    }).trim()
    
    remoteUrl = execSync("git remote get-url origin", { 
      cwd: projectRoot, 
      encoding: "utf-8", 
      stdio: ["pipe", "pipe", "pipe"] 
    }).trim()
    
    remoteUrl = remoteUrl.replace(/:\/\/[^@]+@/, "://")
  } catch {
  }

  const hashSource = remoteUrl || projectRoot
  const projectId = createHash("sha256").update(hashSource).digest("hex").slice(0, 12)
  
  return {
    id: projectId,
    name: projectName,
    root: projectRoot,
    remote: remoteUrl
  }
}

function writeObservation(project, observation) {
  const projectDir = join(BASE_DIR, "projects", project.id)
  const instinctsDir = join(projectDir, "instincts", "personal")
  const evolvedDir = join(projectDir, "evolved")
  
  ensureDir(instinctsDir)
  ensureDir(join(evolvedDir, "skills"))
  ensureDir(join(evolvedDir, "commands"))
  ensureDir(join(evolvedDir, "agents"))
  
  const observationsFile = join(projectDir, "observations.jsonl")
  
  try {
    appendFileSync(observationsFile, JSON.stringify(observation) + "\n")
  } catch (err) {
    console.error("[continuous-learning] Failed to write observation:", err.message)
  }
}

function updateRegistry(project) {
  const registryFile = join(BASE_DIR, "projects.json")
  const projectMetaFile = join(BASE_DIR, "projects", project.id, "project.json")
  
  ensureDir(dirname(registryFile))
  ensureDir(dirname(projectMetaFile))
  
  let registry = {}
  try {
    if (existsSync(registryFile)) {
      registry = JSON.parse(require("fs").readFileSync(registryFile, "utf-8"))
    }
  } catch {
    registry = {}
  }
  
  const now = new Date().toISOString()
  const existing = registry[project.id] || {}
  
  registry[project.id] = {
    name: project.name,
    root: project.root,
    remote: project.remote,
    created_at: existing.created_at || now,
    last_seen: now
  }
  
  try {
    writeFileSync(registryFile, JSON.stringify(registry, null, 2))
    writeFileSync(projectMetaFile, JSON.stringify({
      id: project.id,
      name: project.name,
      root: project.root,
      remote: project.remote,
      last_seen: now
    }, null, 2))
  } catch (err) {
    console.error("[continuous-learning] Failed to update registry:", err.message)
  }
}

export const ContinuousLearningPlugin = async ({ project, client, directory, worktree }) => {
  if (process.env.AGENT_LEARNING_DISABLED === "1") {
    return {}
  }
  
  ensureDir(join(BASE_DIR, "instincts", "personal"))
  ensureDir(join(BASE_DIR, "instincts", "inherited"))
  ensureDir(join(BASE_DIR, "evolved", "skills"))
  ensureDir(join(BASE_DIR, "evolved", "commands"))
  ensureDir(join(BASE_DIR, "evolved", "agents"))

  return {
    "tool.execute.before": async (input, output) => {
      const cwd = directory || worktree || process.cwd()
      const proj = getProjectInfo(cwd)
      const timestamp = new Date().toISOString()
      
      const observation = {
        timestamp,
        event: "tool_start",
        tool: input.tool,
        session: process.env.OPENCODE_SESSION_ID || "unknown",
        agent: "opencode",
        project_id: proj.id,
        project_name: proj.name
      }
      
      if (output?.args) {
        try {
          const inputStr = JSON.stringify(output.args).slice(0, 5000)
          observation.input = redactSecrets(inputStr)
        } catch {
          observation.input = "[unserializable]"
        }
      }
      
      writeObservation(proj, observation)
      updateRegistry(proj)
    },
    
    "tool.execute.after": async (input, output) => {
      const cwd = directory || worktree || process.cwd()
      const proj = getProjectInfo(cwd)
      const timestamp = new Date().toISOString()
      
      const observation = {
        timestamp,
        event: "tool_complete",
        tool: input.tool,
        session: process.env.OPENCODE_SESSION_ID || "unknown",
        agent: "opencode",
        project_id: proj.id,
        project_name: proj.name
      }
      
      if (output?.result !== undefined) {
        try {
          const outputStr = typeof output.result === "string" 
            ? output.result 
            : JSON.stringify(output.result)
          observation.output = redactSecrets(outputStr.slice(0, 5000))
        } catch {
          observation.output = "[unserializable]"
        }
      }
      
      writeObservation(proj, observation)
    }
  }
}

export default ContinuousLearningPlugin
