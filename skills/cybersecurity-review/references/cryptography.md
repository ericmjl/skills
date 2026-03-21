# Cryptography & Data Protection

## Core Principles

- **Never implement custom cryptographic algorithms**: use well-tested, peer-reviewed libraries only.
- **Encrypt all sensitive data at rest and in transit**: classify data by sensitivity and apply controls per classification.
- **Use authenticated encryption** (e.g., AES-GCM) instead of encryption alone.
- **Hash passwords; never encrypt them**: hashing is one-way; encryption is reversible.
- **Use cryptographically secure random number generators (CSPRNG)** for all security-critical randomness.
- **Manage keys properly**: generate with CSPRNG, rotate on schedule, store separately from data, never hardcode.
- **Minimize storage of sensitive information**: data not retained cannot be stolen.
- **Enforce TLS everywhere**: all pages, all traffic (including internal), with HSTS headers.

## Weak Algorithms and Secure Replacements

### Symmetric Encryption

| Weak / Deprecated | Secure Replacement |
|---|---|
| DES, 3DES | AES-128 minimum, AES-256 preferred |
| RC4 | AES-256-GCM or AES-256-CCM |
| ECB mode | GCM (preferred), CCM, or CTR with Encrypt-then-MAC |
| CBC without authentication | GCM or CCM (authenticated encryption) |

### Password Hashing

| Weak / Deprecated | Secure Replacement |
|---|---|
| MD5 | Argon2id (preferred), scrypt, bcrypt, PBKDF2 |
| SHA-1 | Argon2id (preferred), scrypt, bcrypt, PBKDF2 |
| SHA-256/SHA-512 (plain, unsalted) | Argon2id (m=19MiB, t=2, p=1 minimum) |

OWASP preference order: Argon2id > scrypt > bcrypt (work factor >= 10) > PBKDF2 (600K iterations HMAC-SHA-256)

### Asymmetric Encryption / Signatures

| Weak / Deprecated | Secure Replacement |
|---|---|
| RSA < 2048 bits | Curve25519/X25519 (preferred), RSA >= 2048 |
| DSA | Ed25519 or ECDSA with secure curves |
| RSA without OAEP | RSA-OAEP |

### TLS / Transport

| Weak / Deprecated | Secure Replacement |
|---|---|
| SSL 2.0, SSL 3.0 | TLS 1.3 (preferred), TLS 1.2 minimum |
| TLS 1.0, TLS 1.1 | TLS 1.3 (preferred), TLS 1.2 |
| Null/Anonymous/EXPORT ciphers | GCM cipher suites with forward secrecy |

### Random Number Generation

| Weak (PRNG) | Secure (CSPRNG) |
|---|---|
| Python: `random()` | Python: `secrets` module |
| Java: `Math.random()`, `java.util.Random` | Java: `java.security.SecureRandom` |
| Node.js: `Math.random()` | Node.js: `crypto.randomBytes()`, `crypto.randomUUID()` |
| C: `rand()`, `random()` | C: `getrandom(2)` |
| Go: `math/rand` | Go: `crypto/rand` |
| Ruby: `rand()` | Ruby: `SecureRandom` |
| Rust: `rand::prng::XorShiftRng` | Rust: `ChaChaRng` / CSPRNG family |

## Code Patterns to Flag

### Weak Password Hashing
```python
hashlib.md5(password.encode()).hexdigest()       # FLAGGED
hashlib.sha1(password.encode()).hexdigest()       # FLAGGED
hashlib.sha256(password.encode()).hexdigest()     # FLAGGED (no salt, no work factor)
```

### Insecure Random for Security Tokens
```javascript
const token = Math.random().toString(36);         // FLAGGED
```
```python
import random
token = random.randint(0, 999999)                 # FLAGGED
```
```java
Random rand = new Random();
int otp = rand.nextInt(999999);                   // FLAGGED
```

### Deprecated Ciphers
```python
from Crypto.Cipher import DES                     # FLAGGED
from Crypto.Cipher import DES3                    # FLAGGED
from Crypto.Cipher import ARC4                    # FLAGGED
```
```java
Cipher.getInstance("DES/ECB/PKCS5Padding");       // FLAGGED
Cipher.getInstance("RC4");                         // FLAGGED
```

### ECB Mode
```python
cipher = AES.new(key, AES.MODE_ECB)              # FLAGGED
```
```java
Cipher.getInstance("AES/ECB/PKCS5Padding");       // FLAGGED
```

### Hardcoded Keys/IVs
```python
SECRET_KEY = "my-secret-key-12345"                # FLAGGED
IV = b'\x00' * 16                                 # FLAGGED: static IV
```

### Missing/Weak TLS
```python
requests.get(url, verify=False)                   # FLAGGED
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)  # FLAGGED: TLS 1.0
```

### RSA Without OAEP
```java
Cipher.getInstance("RSA/ECB/PKCS1Padding");       // FLAGGED
// SECURE: Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding");
```

### UUID v1 for Security Tokens
```python
token = uuid.uuid1()  # FLAGGED: time+MAC based, predictable
# SECURE: uuid.uuid4() or secrets.token_hex()
```

## CWE Reference

| CWE | Name |
|-----|------|
| CWE-259 | Use of Hard-coded Password |
| CWE-319 | Cleartext Transmission of Sensitive Information |
| CWE-321 | Use of Hard-coded Cryptographic Key |
| CWE-326 | Inadequate Encryption Strength |
| CWE-327 | Use of Broken or Risky Cryptographic Algorithm |
| CWE-328 | Reversible One-Way Hash |
| CWE-329 | Not Using a Random IV with CBC Mode |
| CWE-330 | Use of Insufficiently Random Values |
| CWE-338 | Use of Cryptographically Weak PRNG |
| CWE-347 | Improper Verification of Cryptographic Signature |
| CWE-759 | Use of One-Way Hash without a Salt |
| CWE-780 | Use of RSA Algorithm without OAEP |
| CWE-916 | Password Hash With Insufficient Computational Effort |

## References

- OWASP Top 10 A04:2025 Cryptographic Failures: https://owasp.org/Top10/2025/en/A04_2025-Cryptographic_Failures/
- OWASP Top 10 A02:2021 Cryptographic Failures (archived): https://owasp.org/Top10/2021/A02_2021-Cryptographic_Failures/
- OWASP Cryptographic Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP Transport Layer Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- OWASP Key Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html
- NIST SP 800-57 Key Management: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf
- NIST SP 800-52r2 TLS Guidelines: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf
- Mozilla TLS Config Generator: https://ssl-config.mozilla.org/
- SSL Labs Server Test: https://www.ssllabs.com/ssltest
