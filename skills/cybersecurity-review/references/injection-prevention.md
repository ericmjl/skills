# Input Validation & Injection Prevention

## Core Principles

- **Perform proper input validation**: use allowlist (positive) validation. Define what IS authorized; reject everything else. Validate at syntactic (format) and semantic (business logic) levels.
- **Use safe APIs**: prefer parameterized interfaces that avoid interpreters entirely (prepared statements, ORMs, library functions instead of OS commands).
- **Contextually escape user data**: if a parameterized API is unavailable, escape using the specific syntax for the target interpreter.
- **Allowlisting over denylisting**: denylist validation is trivially bypassed. It can supplement but never replace allowlisting.
- **Output encoding is context-dependent**: HTML entity encoding, JS encoding, URL encoding, and CSS encoding are NOT interchangeable.
- **Server-side validation is mandatory**: client-side validation is for UX only.
- **Input validation is NOT a primary defense**: it reduces impact but does not replace parameterized queries (SQL), output encoding (XSS), or safe APIs (command injection).
- **Least privilege**: minimize database and OS account privileges to limit blast radius.
- **Defense in depth**: layer parameterization + input validation + output encoding + least privilege + CSP.
- **Prefer data formats over native serialization**: use JSON/XML instead of pickle, Java ObjectInputStream.
- **Only deserialize signed data** when native serialization is unavoidable.

## Dangerous Code Patterns by Language

### Python

| Category | Dangerous Pattern | Grep Pattern | Safe Alternative |
|----------|------------------|--------------|------------------|
| SQL Injection | String formatting in queries | `execute\(.*%s`, `execute\(.*\.format\(`, `execute\(.*f"` | `cursor.execute("SELECT * FROM t WHERE id = %s", (id,))` |
| Command Injection | `subprocess` with `shell=True` | `subprocess\.\w+\(.*shell\s*=\s*True` | `subprocess.run(["cmd", "arg1"], shell=False)` |
| Command Injection | `os.system()` | `os\.system\(` | `subprocess.run()` with list args |
| Code Injection | `eval()` / `exec()` | `\beval\(`, `\bexec\(` | `ast.literal_eval()` for data |
| Deserialization | `pickle.loads()` / `pickle.load()` | `pickle\.loads?\(` | `json.loads()` |
| Deserialization | `yaml.load()` without SafeLoader | `yaml\.load\(` | `yaml.safe_load()` |
| Path Traversal | Unsanitized path joins | `os\.path\.join\(.*request`, `open\(.*request` | `os.path.realpath()` + prefix check |
| SSTI | `render_template_string()` with user input | `render_template_string\(` | `render_template()` with file templates |

### JavaScript / TypeScript

| Category | Dangerous Pattern | Grep Pattern | Safe Alternative |
|----------|------------------|--------------|------------------|
| XSS | `innerHTML` assignment | `\.innerHTML\s*=` | `.textContent` or `.innerText` |
| XSS | `document.write()` | `document\.write\(` | DOM manipulation methods |
| XSS | `dangerouslySetInnerHTML` | `dangerouslySetInnerHTML` | Sanitize with DOMPurify first |
| XSS | `bypassSecurityTrust` (Angular) | `bypassSecurityTrust` | Angular built-in sanitization |
| Code Injection | `eval()` | `\beval\(` | `JSON.parse()` for data |
| Code Injection | `Function()` constructor | `new\s+Function\(` | Static code |
| Code Injection | `setTimeout`/`setInterval` with strings | `setTimeout\(\s*["']` | Function references, not strings |
| SQL Injection (Node) | String concat in queries | Template literals in query strings | Parameterized: `query("SELECT ... WHERE id = $1", [id])` |
| Command Injection | `child_process.exec()` | `child_process\.exec\(` | `execFile()` or `spawn()` with args array |
| Prototype Pollution | Deep merge of user input | `Object.assign` with unsanitized input | Block `__proto__`, `constructor`, `prototype` keys |

### Java

| Category | Dangerous Pattern | Grep Pattern | Safe Alternative |
|----------|------------------|--------------|------------------|
| SQL Injection | String concat in SQL | `Statement.*createStatement`, `"SELECT.*" \+` | `PreparedStatement` with `?` placeholders |
| Command Injection | `Runtime.exec()` single string | `Runtime\.getRuntime\(\)\.exec\(` | `ProcessBuilder` with separate args |
| Deserialization | `ObjectInputStream.readObject()` | `ObjectInputStream`, `readObject\(` | Override `resolveClass()` with allowlist; use JSON |
| Deserialization | `XMLDecoder` | `XMLDecoder` | Avoid entirely |
| XXE | Default XML parsers | `DocumentBuilderFactory`, `SAXParserFactory` | Disable DTDs and external entities |

### Go

| Category | Dangerous Pattern | Grep Pattern | Safe Alternative |
|----------|------------------|--------------|------------------|
| SQL Injection | `fmt.Sprintf` in SQL | `fmt\.Sprintf\(.*SELECT`, `db\.Query\(.*\+` | `db.Query("SELECT ... WHERE id = $1", id)` |
| Command Injection | `exec.Command` with shell | `exec\.Command\("sh"`, `exec\.Command\("bash"` | `exec.Command("program", "arg1")` directly |
| SSTI | `template.HTML()` coercion | `template\.HTML\(` | Let `html/template` auto-escape |
| SSTI | `text/template` for HTML | `text/template` in web output | Use `html/template` |

### C/C++

| Category | Dangerous Pattern | Grep Pattern | Safe Alternative |
|----------|------------------|--------------|------------------|
| Command Injection | `system()` | `\bsystem\(` | `execve()` family with explicit args |
| Format String | `printf(variable)` | `printf\(\w+\)` | `printf("%s", variable)` |
| Buffer Overflow | `strcpy`, `strcat`, `gets`, `sprintf` | `\bstrcpy\(`, `\bstrcat\(`, `\bgets\(`, `\bsprintf\(` | `strncpy`, `strncat`, `fgets`, `snprintf` |

### Rust

| Category | Dangerous Pattern | Grep Pattern | Safe Alternative |
|----------|------------------|--------------|------------------|
| SQL Injection | `format!` in SQL queries | `format!\(.*SELECT` | `sqlx::query("... WHERE id = $1").bind(id)` |
| Command Injection | `Command::new("sh")` with user input | `Command::new\("sh"\)` | `Command::new("program").arg(safe_value)` |

## CWE Reference

| CWE | Name |
|-----|------|
| CWE-20 | Improper Input Validation |
| CWE-22 | Path Traversal |
| CWE-77 | Command Injection |
| CWE-78 | OS Command Injection |
| CWE-79 | Cross-Site Scripting (XSS) |
| CWE-89 | SQL Injection |
| CWE-90 | LDAP Injection |
| CWE-94 | Code Injection |
| CWE-116 | Improper Encoding or Escaping of Output |
| CWE-502 | Deserialization of Untrusted Data |
| CWE-611 | XXE (XML External Entity) |
| CWE-917 | Server-Side Template Injection (SSTI) |
| CWE-943 | Improper Neutralization in Data Query Logic (NoSQL injection) |

## References

- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- OWASP Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html
- OWASP SQL Injection Prevention: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP XSS Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- OWASP OS Command Injection Defense: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html
- OWASP Deserialization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html
- OWASP Top 10 A05:2025 Injection: https://owasp.org/Top10/2025/en/A05_2025-Injection/
- OWASP Top 10 A03:2021 Injection (archived): https://owasp.org/Top10/2021/A03_2021-Injection/
