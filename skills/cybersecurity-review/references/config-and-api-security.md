# Secure Configuration & API Security

## Secure Configuration Principles

- **Secure defaults**: never ship with debug mode, sample apps, or default credentials enabled.
- **Minimal attack surface**: remove unnecessary features, ports, services, pages, accounts, privileges.
- **Principle of least privilege**: cloud permissions (IAM, S3 ACLs, security groups) should grant minimum access.
- **Repeatable hardening**: dev, QA, and production configured identically via automation.
- **Security headers as mandatory**: every HTTP response must include security directives.
- **Automated verification**: continuously assess configuration across all environments.
- **Segmented architecture**: use containerization, security groups, and network segmentation.

### Configuration Patterns to Flag

| Pattern | Risk |
|---------|------|
| `DEBUG = True` / `debug: true` in production | Stack traces, internal paths exposed |
| `Access-Control-Allow-Origin: *` | Any origin can make cross-domain requests |
| Missing `Content-Security-Policy` header | XSS, clickjacking, data injection |
| Missing `Strict-Transport-Security` header | Downgrade attacks, MITM |
| Missing `X-Content-Type-Options: nosniff` | MIME sniffing attacks |
| Missing `Cache-Control: no-store` on sensitive responses | Private data cached |
| S3 bucket with `"Principal": "*"` or `PublicRead` | Data exposed to internet |
| IAM policy with `"Action": "*"` or `"Resource": "*"` | Full account compromise risk |
| Security group with `0.0.0.0/0` on port 22/3389 | Open SSH/RDP to internet |
| Default accounts/passwords unchanged | Trivial unauthorized access |
| Exposed management endpoints (`/admin`, `/actuator`, `/debug`) | Admin takeover |
| Directory listing enabled | Source code, configs downloadable |
| `Server` / `X-Powered-By` headers with version info | Version disclosure |

### Terraform / CloudFormation Flags

```hcl
# BAD: Open S3 bucket
resource "aws_s3_bucket_acl" "example" {
  acl = "public-read"
}

# BAD: Overly permissive IAM
resource "aws_iam_policy" "example" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

# BAD: Open security group
resource "aws_security_group_rule" "example" {
  cidr_blocks = ["0.0.0.0/0"]  # FLAG when on port 22, 3389, 3306, 5432
}
```

## API Security (OWASP API Security Top 10, 2023)

| # | Risk | Core Issue |
|---|------|------------|
| API1 | Broken Object Level Authorization (BOLA) | Missing per-object auth checks; ID manipulation |
| API2 | Broken Authentication | Weak/missing auth token validation |
| API3 | Broken Object Property Level Authorization | Excessive data exposure + mass assignment |
| API4 | Unrestricted Resource Consumption | Missing rate limits, pagination caps, size limits |
| API5 | Broken Function Level Authorization | Admin functions accessible to regular users |
| API6 | Unrestricted Access to Sensitive Business Flows | Automated abuse of business logic |
| API7 | Server Side Request Forgery (SSRF) | Unvalidated URIs in server-side fetches |
| API8 | Security Misconfiguration | Debug, verbose errors, missing headers |
| API9 | Improper Inventory Management | Deprecated API versions still accessible |
| API10 | Unsafe Consumption of APIs | Trusting third-party API responses without validation |

### API Principles

- **Object-level authorization on every endpoint**: validate that the authenticated user owns or has permission to the specific resource.
- **Rate limiting at multiple granularities**: per-client, per-endpoint, per-operation. Return `429 Too Many Requests`.
- **Explicit property allowlists, not blocklists**: never serialize full objects. Use DTOs/view models.
- **Enforce pagination and size limits server-side**: cap maximum records per page, upload file size, string lengths.
- **Restrict HTTP methods**: allowlist permitted verbs per endpoint; reject others with `405`.
- **Use GUIDs instead of sequential IDs**: makes BOLA enumeration harder.
- **Enforce workflow state server-side**: validate state transitions on every request.

### API Patterns to Flag

| Pattern | Risk | OWASP API # |
|---------|------|-------------|
| Endpoint accepts object ID with no ownership check | BOLA | API1 |
| `GET /users/123` returns full user object (password hash, SSN) | Excessive data exposure | API3 |
| `PUT /users/123` binds all request fields to model | Mass assignment | API3 |
| No rate limiter on auth endpoints (`/login`, `/forgot-password`) | Brute force | API4 |
| `GET /items?limit=999999` with no server-side cap | Resource exhaustion | API4 |
| Admin endpoint accessible without role check | Privilege escalation | API5 |
| Sensitive data in URL query params (`?apiKey=...`) | Leaked in logs, referer | Best practice |
| Error responses include stack traces | Information disclosure | API8 |
| Deprecated API versions still routable | Exploiting old vulns | API9 |

## CWE Reference

### Configuration
| CWE | Name |
|-----|------|
| CWE-16 | Configuration |
| CWE-209 | Error Message Containing Sensitive Information |
| CWE-260 | Password in Configuration File |
| CWE-614 | Sensitive Cookie Without Secure Flag |
| CWE-942 | Permissive Cross-domain Policy |
| CWE-1004 | Sensitive Cookie Without HttpOnly Flag |

### API Security
| CWE | Name |
|-----|------|
| CWE-285 | Improper Authorization |
| CWE-400 | Uncontrolled Resource Consumption |
| CWE-639 | AuthZ Bypass Through User-Controlled Key (BOLA) |
| CWE-770 | Allocation of Resources Without Limits (Rate Limiting) |
| CWE-915 | Mass Assignment |

## References

- OWASP Top 10 A05:2021 Security Misconfiguration: https://owasp.org/Top10/2021/A05_2021-Security_Misconfiguration/
- OWASP API Security Top 10 (2023): https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- OWASP Mass Assignment Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/
- CIS Security Benchmarks: https://www.cisecurity.org/cis-benchmarks/
- NIST SP 800-123 Server Hardening: https://csrc.nist.gov/publications/detail/sp/800-123/final
