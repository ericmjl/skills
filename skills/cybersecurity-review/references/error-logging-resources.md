# Error Handling, Logging & Resource Safety

## Error Handling & Information Disclosure

### Principles

- **Never expose internal details to users**: stack traces, SQL errors, file paths, framework versions aid attacker reconnaissance.
- **Use a global error handler**: configure centrally so no exception path is missed.
- **Return generic error responses**: use RFC 7807 `application/problem+json` with safe messages only.
- **Log the full error server-side**: detail goes to logs, not HTTP responses.
- **Use appropriate HTTP status codes**: 4xx for client errors, 5xx for server errors, no implementation details in body.
- **Remove server version headers**: strip `Server`, `X-Powered-By`, `X-AspNet-Version` from production.
- **Use constant-time comparisons** for secrets (passwords, tokens, HMAC values) to prevent timing attacks.
- **Disable debug/development error pages** in production.

### Patterns to Flag

```python
# BAD: Stack trace in response
@app.errorhandler(Exception)
def handle_error(e):
    return {"error": str(e), "trace": traceback.format_exc()}, 500

# BAD: Database error detail exposed
except sqlalchemy.exc.OperationalError as e:
    return {"error": f"Database error: {e}"}, 500

# BAD: Timing-vulnerable comparison
if user_token == stored_token:  # not constant-time

# GOOD: Generic response
@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(f"Unhandled: {e}", exc_info=True)
    return {"message": "An error occurred"}, 500
```

## Logging & Monitoring Security

### What to Log
- Authentication events (successes and failures)
- Authorization / access control failures
- Input validation failures (discrete-list violations are attack indicators)
- Session management failures (cookie tampering, JWT validation failures)
- Application errors and system events
- High-risk functionality: user admin actions, privilege changes, data export, crypto key rotation

### What NOT to Log
- Passwords / authentication credentials
- Session IDs (use hashed values if needed)
- Access tokens / API keys
- Encryption keys
- Credit card / payment card data
- Sensitive PII (health data, government IDs)
- Database connection strings

### Log Injection Prevention

```python
# BAD: Unsanitized user input in logs
logger.info(f"Login attempt for user: {username}")
# username = "admin\n2025-03-20 INFO Login successful for user: admin"

# GOOD: Sanitize before logging
import re
safe_username = re.sub(r'[\r\n\t]', '', username)
logger.info("Login attempt for user: %s", safe_username)
```

### Audit Trail Requirements
Every log entry must record when, where, who, what:
- **When**: timestamp in international format, synchronized across servers
- **Where**: application name/version, hostname/IP, service name
- **Who**: source IP, authenticated user identity
- **What**: event type, severity, action, target object, result

## Resource Safety

### Memory Safety (C/C++)

```c
// BAD: Buffer overflow
char buf[64];
strcpy(buf, user_input);           // CWE-120

// BAD: sprintf without bounds
sprintf(msg, "Hello %s", name);    // CWE-120

// GOOD: Bounded alternatives
strncpy(buf, user_input, sizeof(buf) - 1);
buf[sizeof(buf) - 1] = '\0';
snprintf(msg, sizeof(msg), "Hello %s", name);
```

### Regular Expression DoS (ReDoS)

```python
# BAD: Catastrophic backtracking
pattern = re.compile(r'^(a+)+$')   # CWE-1333

# GOOD: Use regex with timeout
import regex
pattern = regex.compile(r'^a+$', flags=regex.V1)
pattern.match(user_input, timeout=1.0)
```

### XML Bombs (Billion Laughs)

```python
# BAD: No entity expansion limit
from xml.etree.ElementTree import parse
tree = parse(untrusted_xml)        # CWE-776

# GOOD: Use defusedxml
import defusedxml.ElementTree as ET
tree = ET.parse(untrusted_xml)
```

### Unbounded File Uploads

```python
# BAD: No size limit or name sanitization
uploaded = request.files['file']
uploaded.save('/uploads/' + uploaded.filename)

# GOOD: Enforce limits
MAX_SIZE = 10 * 1024 * 1024
if uploaded.content_length > MAX_SIZE:
    abort(413)
filename = secure_filename(uploaded.filename)
```

### TOCTOU Race Conditions

```c
// BAD: Check-then-use race condition
if (access(filepath, R_OK) == 0) {  // CHECK
    fd = open(filepath, O_RDONLY);   // USE -- file could change between
}

// GOOD: Open first, then check with fstat on fd
fd = open(filepath, O_RDONLY);
if (fd >= 0) {
    struct stat st;
    fstat(fd, &st);  // operates on opened fd, not path
}
```

## CWE Reference

### Error Handling
| CWE | Name |
|-----|------|
| CWE-200 | Exposure of Sensitive Information |
| CWE-208 | Observable Timing Discrepancy |
| CWE-209 | Error Message Containing Sensitive Information |
| CWE-497 | Exposure of Sensitive System Information |

### Logging
| CWE | Name |
|-----|------|
| CWE-117 | Log Injection |
| CWE-223 | Omission of Security-relevant Information |
| CWE-532 | Sensitive Information in Log File |
| CWE-778 | Insufficient Logging |

### Resource Safety
| CWE | Name |
|-----|------|
| CWE-120 | Buffer Overflow |
| CWE-190 | Integer Overflow or Wraparound |
| CWE-362 | Race Condition |
| CWE-367 | TOCTOU Race Condition |
| CWE-400 | Uncontrolled Resource Consumption |
| CWE-416 | Use After Free |
| CWE-434 | Unrestricted Upload of Dangerous File Type |
| CWE-776 | XML Bomb (Billion Laughs) |
| CWE-1333 | ReDoS |

## References

- OWASP Error Handling Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- OWASP Logging Vocabulary Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Application_Logging_Vocabulary_Cheat_Sheet.html
- OWASP Top 10 A09:2025 Security Logging and Alerting Failures: https://owasp.org/Top10/2025/en/A09_2025-Security_Logging_and_Alerting_Failures/
- OWASP Top 10 A09:2021 Security Logging and Monitoring Failures (archived): https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
- OWASP Top 10 A10:2025 Mishandling of Exceptional Conditions: https://owasp.org/Top10/2025/en/A10_2025-Mishandling_of_Exceptional_Conditions/
- NIST SP 800-92 Log Management Guide: https://csrc.nist.gov/publications/nistpubs/800-92/SP800-92.pdf
- RFC 7807 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc7807
