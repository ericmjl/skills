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

## SSRF (Server-Side Request Forgery) — Deep Coverage

SSRF is API7 in OWASP API Security Top 10. In cloud environments the full kill chain is:

> User-controlled URL → server fetches it → reaches cloud metadata endpoint → returns IAM credentials

### SSRF Kill Chain

```
1. Attacker supplies URL: http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name
2. Server blindly fetches the URL (requests.get(url), urllib.request.urlopen(url), etc.)
3. Cloud IMDS (Instance Metadata Service) returns temporary AWS/GCP/Azure credentials
4. Attacker uses credentials to exfiltrate data, pivot to other services, or achieve RCE
```

Cloud metadata endpoints to block/detect:
- AWS: `169.254.169.254`, `fd00:ec2::254`, `169.254.170.2` (ECS task metadata)
- GCP: `metadata.google.internal`, `169.254.169.254`
- Azure: `169.254.169.254`, `fd00:ec2::254`

### SSRF Grep Patterns

| Pattern | Risk |
|---------|------|
| `requests\.get\(.*request\.(GET\|POST\|args\|form\|json)` | Python SSRF — user URL passed to requests |
| `urllib\.request\.urlopen\(.*request` | Python SSRF — urllib with user input |
| `axios\.get\(.*req\.(query\|body\|params)` | Node.js SSRF — axios with user input |
| `fetch\(.*req\.(query\|body\|params)` | Node.js SSRF — fetch with user input |
| `HttpClient.*new URL\(.*getParam` | Java SSRF — HttpClient with user URL |
| `169\.254\.169\.254` | Direct IMDS reference in code or configs |
| `metadata\.google\.internal` | GCP metadata endpoint reference |
| `http\.Get\(.*r\.(URL\|FormValue\|Query)` | Go SSRF — http.Get with user input |

### SSRF Prevention

```python
from urllib.parse import urlparse
import ipaddress

ALLOWED_SCHEMES = {"https"}
BLOCKLISTED_HOSTS = {
    "169.254.169.254",   # AWS/GCP/Azure IMDS
    "metadata.google.internal",
    "169.254.170.2",     # ECS task metadata
}

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    host = parsed.hostname or ""
    if host in BLOCKLISTED_HOSTS:
        return False
    # Block private/loopback ranges
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return False
    except ValueError:
        pass  # hostname, not IP — resolve and re-check in production
    return True
```

Also consider: enforce `IMDSv2` (AWS) to require PUT token before metadata access; use VPC endpoint policies to block outbound to IMDS from application subnets.

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

- OWASP Top 10 A02:2025 Security Misconfiguration: https://owasp.org/Top10/2025/en/A02_2025-Security_Misconfiguration/
- OWASP Top 10 A05:2021 Security Misconfiguration (archived): https://owasp.org/Top10/2021/A05_2021-Security_Misconfiguration/
- OWASP API Security Top 10 (2023): https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- OWASP Mass Assignment Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/
- CIS Security Benchmarks: https://www.cisecurity.org/cis-benchmarks/
- NIST SP 800-123 Server Hardening: https://csrc.nist.gov/publications/detail/sp/800-123/final
