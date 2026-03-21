# Dependency & Supply Chain Security

## Core Principles

- **Know your inventory**: continuously inventory all direct and transitive dependencies, including versions.
- **Pin versions and use lockfiles**: lock to specific, verified versions. Missing lockfiles mean non-reproducible, vulnerable builds.
- **Remove unused dependencies**: strip unnecessary components to reduce attack surface.
- **Obtain packages from official sources only**: prefer signed packages.
- **Monitor continuously**: subscribe to CVE/NVD alerts and advisories for components in use.
- **Generate and consume SBOMs**: automate SBOM production in CI/CD using CycloneDX or SPDX formats.
- **Verify provenance**: ensure artifacts trace back to their source. Use SLSA provenance attestations.
- **Enforce code signing**: only accept digitally signed components; validate signatures before use.
- **Use private artifact repositories**: review artifacts before allowing them in; prevent bypass of the private registry.
- **Ephemeral, isolated builds**: build in temporary, isolated environments to prevent cache poisoning.
- **Assess suppliers before adoption**: evaluate maintenance activity, contributor count, security history, vulnerability response, license compatibility.

## What to Check

### Package Manifests (`package.json`, `pyproject.toml`, `pom.xml`, `Gemfile`, etc.)
- Unpinned or loosely pinned versions (`^`, `~`, `>=`, `*`)
- Dependencies from unofficial/private registries without explicit scoping
- Package names that are near-misspellings of popular packages (typosquatting)
- `preinstall`/`postinstall`/`install` scripts with network access or shell commands
- Excessive number of dependencies
- Abandoned/unmaintained packages (no recent commits, no security policy)

### Lockfiles (`package-lock.json`, `yarn.lock`, `poetry.lock`, `Cargo.lock`, etc.)
- Missing lockfile entirely
- Lockfile not committed to version control
- Integrity hash mismatches (SRI hashes missing or inconsistent)
- Lockfile drift from manifest
- Resolved URLs pointing to unexpected registries

### Build & CI/CD Configuration
- Install scripts with network access (`curl | sh`, `wget`, downloading binaries)
- Post-install hooks executing arbitrary code
- Excessive permissions granted to build pipelines
- Build environments that are shared or persistent (not ephemeral)

## Common Risks

| Risk | Description |
|------|-------------|
| **Typosquatting** | Attacker publishes packages with similar names to popular ones |
| **Dependency Confusion** | Higher-versioned public package shadows internal/private package name |
| **Malicious Packages** | Packages containing backdoors, cryptominers, credential stealers |
| **Abandoned Packages** | No active maintainer; known vulnerabilities go unpatched |
| **Transitive Vulnerabilities** | Your direct dependency is fine, but pulls in a vulnerable sub-dependency |
| **Compromised Maintainer** | Attacker takes over a maintainer's credentials and publishes malicious updates |
| **Build Environment Compromise** | Cache poisoning or CI/CD credential compromise injects malicious code |

## Frameworks & Standards

### SLSA (Supply-chain Levels for Software Artifacts)

| Level | Requirements |
|-------|-------------|
| Build L0 | No guarantees |
| Build L1 | Provenance exists (may be unsigned) |
| Build L2 | Signed provenance from hosted build platform |
| Build L3 | Hardened build platform with run isolation |

### OpenSSF Scorecard
Automated assessment of OSS project security: branch protection, dependency tooling, CI test coverage, code review enforcement, signed releases, vulnerability disclosure policy.

### Sigstore
Free signing, verification, and provenance infrastructure: Cosign (image signing), Fulcio (certificate authority), Rekor (transparency log).

## Scanning Tools

| Tool | Type | Coverage |
|------|------|----------|
| OWASP Dependency-Check | SCA (free) | Java, .NET, Python, Ruby, PHP, Node, C/C++ |
| `npm audit` / `yarn audit` | Built-in | Node.js/JavaScript |
| `pip-audit` | SCA (free) | Python |
| Snyk | Commercial (free tier) | Multi-language |
| Trivy | Free | Multi-language, containers, IaC |
| Grype | Free | Multi-language, containers |
| OpenSSF Scorecard | Free | Any GitHub/GitLab project |

### Build & CI/CD Configuration
- Install scripts with network access (`curl | sh`, `wget`, downloading binaries)
- Post-install hooks executing arbitrary code
- Excessive permissions granted to build pipelines
- Build environments that are shared or persistent (not ephemeral)

## CI/CD Pipeline Integrity (GitHub Actions)

Real-world incidents (e.g., `tj-actions/changed-files`, `reviewdog/action-setup`, March 2025) demonstrated that compromised GitHub Actions can exfiltrate `GITHUB_TOKEN` and repository secrets to all downstream consumers. CI/CD is now a primary supply-chain attack surface.

### SHA Pinning for Actions

Always pin third-party actions to a full commit SHA, not a mutable tag or branch:

```yaml
# BAD: mutable tag — can be silently updated by attacker
- uses: actions/checkout@v4
- uses: tj-actions/changed-files@v44

# GOOD: pinned to immutable SHA
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
- uses: tj-actions/changed-files@d6e91a2df3fae459d12a712ef81e2e3d76d37d69  # v44.5.1
```

Tools to automate pinning: [`pin-github-actions`](https://github.com/mheap/pin-github-actions), [`Ratchet`](https://github.com/sethvargo/ratchet), Dependabot for Actions.

### Grep Patterns for CI/CD Risks

| Pattern | Risk |
|---------|------|
| `uses: \w+/\w+@v\d` | Mutable version tag (not SHA-pinned) |
| `uses: \w+/\w+@main\|master` | Branch ref — always mutable |
| `pull_request_target:` | Dangerous trigger — runs with write access against PR code |
| `secrets\.GITHUB_TOKEN` with `write-all` perms | Overly broad token |
| `permissions:` absent from workflow | Defaults to legacy permissive token |
| `env:.*\${{ github\.event\.pull_request` | PR attacker-controlled data in env vars |

### `pull_request_target` Escalation

`pull_request_target` runs in the context of the **base branch** (with secrets and write permissions), but processes code from the **PR branch**. Checking out PR code inside this trigger is a critical vulnerability:

```yaml
# CRITICAL: Attacker-controlled code checked out with write permissions
on: pull_request_target
jobs:
  build:
    steps:
      - uses: actions/checkout@...
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # DANGER
      - run: make test  # Executes attacker code with repo secrets
```

### GITHUB_TOKEN Least Privilege

```yaml
# GOOD: Explicit minimal permissions at workflow and job level
permissions:
  contents: read        # only what is needed
  pull-requests: write  # only if PR comments are required

jobs:
  build:
    permissions:
      contents: read    # job-level overrides for defense-in-depth
```

### Actions Security Checklist

| Check | Pass Condition |
|-------|----------------|
| All third-party `uses:` pinned to SHA | No mutable tags or branches |
| Workflow-level `permissions:` declared | No implicit write-all default |
| `pull_request_target` absent or guarded | No checkout of PR head code |
| No `curl \| sh` or `wget \| bash` | No remote code execution in steps |
| Secrets not echoed to logs | No `echo ${{ secrets.FOO }}` |
| Dependabot / Renovate configured for Actions | Automated SHA updates |

## CWE Reference

| CWE | Name |
|-----|------|
| CWE-427 | Uncontrolled Search Path Element (dependency confusion) |
| CWE-494 | Download of Code Without Integrity Check |
| CWE-506 | Embedded Malicious Code |
| CWE-829 | Inclusion of Functionality from Untrusted Control Sphere |
| CWE-915 | Improperly Controlled Modification of Object Attributes (prototype pollution) |
| CWE-1104 | Use of Unmaintained Third-Party Components |

## References

- OWASP Top 10 A03:2025 Software Supply Chain Failures: https://owasp.org/Top10/2025/en/A03_2025-Software_Supply_Chain_Failures/
- OWASP Top 10 A06:2021 Vulnerable and Outdated Components (archived): https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/
- OWASP Vulnerable Dependency Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Vulnerable_Dependency_Management_Cheat_Sheet.html
- OWASP Software Supply Chain Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Software_Supply_Chain_Security_Cheat_Sheet.html
- SLSA Specification v1.0: https://slsa.dev/spec/v1.0/levels
- OpenSSF Scorecard: https://securityscorecards.dev/
- OpenSSF Concise Guide for Evaluating OSS: https://best.openssf.org/Concise-Guide-for-Evaluating-Open-Source-Software
- Sigstore: https://www.sigstore.dev/
- OSV Database: https://osv.dev/
- NVD: https://nvd.nist.gov/
- GitHub Advisory Database: https://github.com/advisories
- CISA Known Exploited Vulnerabilities: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
