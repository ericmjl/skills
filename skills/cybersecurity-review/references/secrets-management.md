# Secrets & Credential Management

## Core Principles

- **Never hardcode secrets**: passwords, API keys, and cryptographic keys in source code are nearly always extractable, even from compiled binaries.
- **Use secrets management systems**: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager. For CI/CD, use platform-native secret stores.
- **Rotate credentials regularly**: automate rotation; use dynamic secrets (per-session) where possible.
- **Principle of least privilege**: secrets should have minimum privileges. Scope CI/CD service accounts to only needed secrets.
- **Encrypt secrets at rest and in transit**: TLS everywhere, audit all secret access.
- **Zero secrets in memory after use**: especially in C/C++; avoid immutable `String` in Java/.NET for secrets.
- **Never log plaintext secrets**: use masking or encryption in log pipelines.
- **Shift-left detection**: integrate secret scanning at developer level (IDE plugins, pre-commit hooks).

## Anti-Patterns to Detect

| Pattern | Example | CWE |
|---------|---------|-----|
| Hardcoded password | `password = "Mew!"` | CWE-259 |
| Hardcoded DB connection string | `DriverManager.getConnection(url, "scott", "tiger")` | CWE-798 |
| API key in source | `api_key = "AKIA..."` | CWE-798 |
| `.env` committed to repo | `.env` not in `.gitignore` | CWE-312 |
| Private key in repo | `-----BEGIN RSA PRIVATE KEY-----` | CWE-321 |
| Credentials in config files | `webapp.ldap.password=secretPassword` | CWE-256 |
| Secrets in Docker ENV/ARG | `ENV DB_PASSWORD=secret` | CWE-312 |

## Regex Patterns for Common Secret Types

### Cloud Provider Keys

```regex
# AWS Access Key
(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}

# AWS Secret Access Key
(?i)aws_secret_access_key\s*[=:]\s*[A-Za-z0-9/+=]{40}

# Google API Key
AIza[0-9A-Za-z_-]{35}
```

### Source Control Tokens

```regex
# GitHub Personal Access Token
ghp_[A-Za-z0-9_]{36}

# GitHub Fine-Grained Token
github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59}

# GitHub OAuth/App Tokens
gh[opsru]_[A-Za-z0-9_]{36,255}
```

### API/Service Keys

```regex
# Stripe Secret Key
(?:sk_live|sk_test)_[A-Za-z0-9]{24,}

# SendGrid API Key
SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}

# Twilio API Key
SK[0-9a-fA-F]{32}

# Slack Bot/User Token
xox[bpars]-[0-9]{10,}-[0-9]{10,}-[A-Za-z0-9]{24,}

# Slack Webhook URL
https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}
```

### Generic Patterns

```regex
# Private Key Header
-----BEGIN\s(?:RSA|DSA|EC|OPENSSH|PGP)?\s?PRIVATE KEY-----

# JWT
eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}

# Generic password assignment
(?i)(?:password|passwd|pwd|secret)\s*[=:]\s*['"][^\s'"]{8,}['"]

# Generic API key assignment
(?i)(?:api[_-]?key|apikey|api[_-]?secret)\s*[=:]\s*['"][A-Za-z0-9_\-]{16,64}['"]

# Database connection string with credentials
(?i)(?:mysql|postgres|postgresql|mongodb|mssql):\/\/[^:]+:[^@]+@[^/\s]+

# High-entropy secret assignment
(?i)(?:secret|token|key|password|credential|auth)\s*[=:]\s*['"][A-Za-z0-9+/=_-]{32,}['"]
```

## Tools

| Tool | Use Case |
|------|----------|
| detect-secrets (Yelp) | Pre-commit hook, baseline-aware, ~20+ secret type signatures |
| gitleaks | Pre-commit + CI, TOML rules, scans git history |
| truffleHog | Git history scan, 700+ detectors |
| git-secrets (AWS Labs) | Prevents committing AWS credentials |
| GitHub Secret Scanning | Built-in, 200+ partner patterns, push protection |

## Incident Response When a Secret is Exposed

1. **Revoke** the exposed secret immediately
2. **Rotate** to a new secret via automated process
3. **Delete** from the exposed location (code, logs, config)
4. **Audit** who had access and when the secret was used
5. **Assess** blast radius: what systems/data could have been accessed
6. **Document** the incident and remediation
7. **Improve** detection rules to prevent recurrence

## CWE Reference

| CWE | Name |
|-----|------|
| CWE-200 | Exposure of Sensitive Information |
| CWE-256 | Plaintext Storage of a Password |
| CWE-259 | Use of Hard-coded Password |
| CWE-312 | Cleartext Storage of Sensitive Information |
| CWE-321 | Use of Hard-coded Cryptographic Key |
| CWE-522 | Insufficiently Protected Credentials |
| CWE-798 | Use of Hard-coded Credentials |

## References

- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- OWASP Use of Hard-coded Password: https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password
- CWE-798: https://cwe.mitre.org/data/definitions/798.html
- NIST SP 800-63B: https://pages.nist.gov/800-63-3/sp800-63b.html
- NIST SP 800-57 Key Management: https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final
- detect-secrets: https://github.com/Yelp/detect-secrets
- gitleaks: https://github.com/gitleaks/gitleaks
- truffleHog: https://github.com/trufflesecurity/trufflehog
- GitHub Secret Scanning: https://docs.github.com/en/code-security/secret-scanning
