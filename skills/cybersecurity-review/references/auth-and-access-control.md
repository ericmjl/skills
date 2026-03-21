# Authentication & Authorization

## Core Principles

### Authentication
- **Use proven, framework-provided authentication** -- never roll your own password hashing, session management, or token generation.
- **Store passwords using modern adaptive hashing**: Argon2id (preferred), scrypt, bcrypt, PBKDF2. Never MD5, SHA-1, or unsalted SHA-256.
- **Compare password hashes using constant-time functions** to prevent timing attacks.
- **Enforce MFA** wherever possible.
- **Return generic error messages** for auth failures -- do not reveal whether the username or password was wrong.
- **Require re-authentication for sensitive operations** (password change, email change, payment modification).
- **Transmit credentials only over TLS**.
- **Protect against automated attacks**: rate limiting, account lockout, CAPTCHA.

### Authorization
- **Least Privilege**: grant only the minimum permissions necessary.
- **Deny by Default**: if no explicit rule grants access, deny it.
- **Validate permissions on every request**: use middleware/filters. A single missed check is sufficient for compromise.
- **Defense in Depth**: layer server-side checks, middleware, and domain-level constraints.
- **Separation of Duties**: sensitive actions should require multiple actors or approval steps.
- **Prefer ABAC/ReBAC over RBAC**: attribute-based access control is more expressive and less prone to role explosion.
- **Enforce authorization on static resources too** (S3 buckets, uploaded files).
- **Server-side enforcement only**: never rely on client-side access control.

### Session Management
- **Regenerate session ID after any privilege level change** (login, role change) to prevent session fixation.
- **Set proper cookie attributes**: `Secure`, `HttpOnly`, `SameSite`, narrow `Domain`/`Path`.
- **Implement both idle and absolute session timeouts**.
- **Invalidate sessions server-side on logout**.
- **Session ID entropy**: minimum 128-bit values, generated with a CSPRNG.

## Dangerous Code Patterns

### Missing Auth Checks

```python
# BAD: Route without @login_required
def admin_dashboard(request):
    return render(request, 'admin.html')

# BAD: Flask endpoint without auth
@app.route('/admin')
def admin():
    return render_template('admin.html')
```

```javascript
// BAD: Express route without auth middleware
app.get('/api/admin', (req, res) => { ... })
```

### Insecure Direct Object References (IDOR)

```python
# BAD: No ownership check
account = Account.objects.get(id=request.GET['acct_id'])

# GOOD: Verify ownership
account = Account.objects.get(id=request.GET['acct_id'], owner=request.user)
```

### JWT Misuse

```python
# BAD: No signature verification
payload = jwt.decode(token, options={"verify_signature": False})

# BAD: Missing expiry
token = jwt.encode({"user_id": 1}, SECRET)

# BAD: Algorithm "none"
jwt.decode(token, algorithms=["none"])

# BAD: Algorithm confusion (HS256 where asymmetric expected)
jwt.decode(token, public_key, algorithms=["HS256"])
```

### Insecure Password Storage

```python
# BAD: Fast hash for passwords
hashlib.md5(password.encode()).hexdigest()
hashlib.sha256(password.encode()).hexdigest()

# BAD: Non-constant-time comparison
if stored_hash == computed_hash:  # timing attack
```

### Session Management Flaws

```python
# BAD: Session not regenerated after login
def login(request):
    user = authenticate(...)
    request.session['user'] = user.id  # session ID not rotated

# BAD: Missing cookie flags
response.set_cookie('session_id', value, secure=False)
response.set_cookie('session_id', value, httponly=False)
```

### CORS Misconfiguration

```python
# BAD: Reflecting arbitrary origins with credentials
response['Access-Control-Allow-Origin'] = request.headers['Origin']
response['Access-Control-Allow-Credentials'] = 'true'
```

## Grep Patterns

| Target | Pattern |
|--------|---------|
| Hardcoded credentials | `password\s*=\s*["'][^"']+["']` |
| JWT without verification | `verify_signature.*False`, `algorithms.*none` |
| MD5/SHA1 for passwords | `md5\(\|sha1\(\|hashlib\.md5\|hashlib\.sha1` |
| Missing cookie flags | `set_cookie.*secure\s*=\s*False`, `httponly\s*=\s*False` |
| Direct object reference | `objects\.get\(id=request\.(GET\|POST\|params)` |
| CORS wildcard | `Access-Control-Allow-Origin.*\*` |

## CWE Reference

| CWE | Name |
|-----|------|
| CWE-256 | Plaintext Storage of Password |
| CWE-284 | Improper Access Control |
| CWE-285 | Improper Authorization |
| CWE-287 | Improper Authentication |
| CWE-306 | Missing Authentication for Critical Function |
| CWE-307 | Improper Restriction of Excessive Auth Attempts |
| CWE-352 | Cross-Site Request Forgery (CSRF) |
| CWE-384 | Session Fixation |
| CWE-521 | Weak Password Requirements |
| CWE-614 | Sensitive Cookie Without Secure Flag |
| CWE-639 | AuthZ Bypass Through User-Controlled Key (IDOR) |
| CWE-798 | Use of Hard-coded Credentials |
| CWE-862 | Missing Authorization |
| CWE-863 | Incorrect Authorization |
| CWE-916 | Password Hash With Insufficient Computational Effort |

## References

- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Top 10 A01:2021 Broken Access Control: https://owasp.org/Top10/2021/A01_2021-Broken_Access_Control/
- OWASP Top 10 A07:2021 Identification & Auth Failures: https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- NIST SP 800-63B Digital Identity Guidelines: https://pages.nist.gov/800-63-4/sp800-63b.html
