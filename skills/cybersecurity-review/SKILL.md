---
name: cybersecurity-review
description: >
  Perform comprehensive cybersecurity code review across 9 security dimensions:
  injection prevention, authentication/authorization, secrets management,
  supply chain security (including CI/CD pipeline integrity), cryptography,
  secure configuration/API security (including SSRF), error handling/logging/resource safety,
  LLM/AI application security, and infrastructure/API protocol security (GraphQL, Kubernetes,
  WebSockets, OAuth 2.0, gRPC). Use when reviewing newly written code,
  auditing existing repositories, evaluating open source projects, or assessing
  pull requests for security vulnerabilities. Triggers include requests like
  "security review", "check for vulnerabilities", "audit this code",
  "cybersecurity review", "is this code secure", or "check this PR for security issues".
license: MIT
---

# Cybersecurity Review

Perform structured security code review across 9 dimensions, adapting depth based on review mode.

## Review Modes

Select the appropriate mode based on context:

| Mode | Trigger | Scope | Depth |
|------|---------|-------|-------|
| **New Code** | Reviewing code just written or a new feature | Changed files only | Deep on all 9 dimensions |
| **Existing Repo** | Auditing an established codebase | Full repository scan | Prioritize high-severity, sample for depth |
| **Open Source Eval** | Evaluating a dependency or OSS project | Full project + community signals | Supply chain focus + all 9 dimensions |
| **Pull Request** | Reviewing a PR for merge readiness | Diff only + touched files | Deep on changed code, contextual on surrounding code |

## Review Workflow

### Step 1: Determine scope and mode

Identify which review mode applies. For PR reviews, obtain the diff. For repo audits, identify primary languages and frameworks.

### Step 2: Run through each applicable dimension

Load the relevant reference file for each dimension and assess the code:

1. **Input Validation & Injection Prevention** -- See [references/injection-prevention.md](references/injection-prevention.md)
   - SQL injection, XSS, command injection, path traversal, deserialization, SSTI, XXE

2. **Authentication & Authorization** -- See [references/auth-and-access-control.md](references/auth-and-access-control.md)
   - Broken auth, IDOR, privilege escalation, session management, JWT misuse

3. **Secrets & Credential Management** -- See [references/secrets-management.md](references/secrets-management.md)
   - Hardcoded secrets, API keys in source, committed .env files, missing secret scanning

4. **Dependency & Supply Chain Security** -- See [references/supply-chain-security.md](references/supply-chain-security.md)
   - Vulnerable dependencies, typosquatting, dependency confusion, lockfile integrity, CI/CD pipeline integrity, GitHub Actions SHA pinning

5. **Cryptography & Data Protection** -- See [references/cryptography.md](references/cryptography.md)
   - Weak algorithms, insecure random, hardcoded keys, missing TLS, poor password hashing

6. **Secure Configuration & API Security** -- See [references/config-and-api-security.md](references/config-and-api-security.md)
   - Debug mode, permissive CORS, missing security headers, BOLA, mass assignment, rate limiting, SSRF kill-chain patterns

7. **Error Handling, Logging & Resource Safety** -- See [references/error-logging-resources.md](references/error-logging-resources.md)
   - Stack trace exposure, sensitive data in logs, log injection, ReDoS, buffer overflows, TOCTOU, mishandling exceptional conditions

8. **LLM & AI Application Security** -- See [references/llm-ai-security.md](references/llm-ai-security.md)
   - Prompt injection (direct and indirect/RAG), improper LLM output handling, excessive agency, system prompt leakage, AI supply chain

9. **Infrastructure & API Protocol Security** -- See [references/infra-and-protocol-security.md](references/infra-and-protocol-security.md)
   - GraphQL (introspection, depth/complexity, batching), Kubernetes/container misconfig, WebSocket security, OAuth 2.0 vulnerabilities, gRPC security

### Step 3: Produce findings report

For each finding, report:
- **Severity**: Critical / High / Medium / Low / Informational
- **Dimension**: Which of the 7 categories
- **Location**: File path and line number(s)
- **CWE**: The relevant CWE identifier
- **Description**: What the vulnerability is and why it matters
- **Recommendation**: Specific fix with code example where possible

### Step 4: Summarize

Provide a summary table of all findings by severity, plus an overall security posture assessment.

## Severity Classification

| Severity | Criteria |
|----------|----------|
| **Critical** | Remotely exploitable, no auth required, leads to data breach or RCE |
| **High** | Exploitable with low complexity, significant impact (privilege escalation, data leak) |
| **Medium** | Exploitable with moderate complexity or requires some preconditions |
| **Low** | Minor issue, defense-in-depth improvement, or requires significant preconditions |
| **Informational** | Best practice recommendation, no direct exploitability |

## Mode-Specific Guidance

### New Code Review
Focus on all 9 dimensions with equal weight. Check that new code does not introduce patterns flagged in the reference files. Verify that new dependencies are pinned and scanned. For AI/LLM features, apply dimension 8. For GraphQL/K8s/WebSocket features, apply dimension 9.

### Existing Repo Audit
Start with a high-level scan using grep patterns from each reference file. Prioritize Critical/High findings. Sample representative files for deeper review. Check for missing security controls (CSP headers, rate limiting, auth middleware). If the repo uses LLM APIs or ships Kubernetes manifests/Helm charts, include dimensions 8 and 9.

### Open Source Evaluation
Begin with supply chain signals: maintenance activity, contributor count, security policy presence, OpenSSF Scorecard if available. Inspect GitHub Actions workflows for SHA pinning and `pull_request_target` usage. Then review code for all 9 dimensions. Flag any use of dangerous patterns (eval, pickle, shell=True) as higher risk since the code runs in consumer environments.

### Pull Request Review
Focus on the diff. For each changed file, assess which dimensions are relevant based on the code's function. Flag new dangerous patterns. Verify that security-sensitive changes have tests. Check that secrets were not accidentally committed. For PRs touching CI/CD workflows, always check SHA pinning and `pull_request_target` (dimension 4).
