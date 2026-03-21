# Infrastructure & API Protocol Security

## GraphQL Security

GraphQL's flexible query model introduces attack surfaces absent from REST APIs.

### Key Risks

| Risk | Description |
|------|-------------|
| **Introspection in Production** | `__schema` queries reveal full API structure to attackers |
| **Unbounded Query Depth** | Deeply nested queries consume exponential server resources |
| **Batching Attacks** | Multiple operations in one request bypass per-request rate limits |
| **Field Suggestion Oracle** | GraphQL error messages suggest valid field names, aiding enumeration |
| **Mass Assignment via Mutations** | Input objects expose all fields including admin/internal ones |
| **Missing Object-Level Auth** | Resolvers that don't check ownership (GraphQL equivalent of BOLA) |

### Grep Patterns

| Pattern | Risk |
|---------|------|
| `introspection.*true\|enableIntrospection.*true` | Introspection enabled in production config |
| `depthLimit.*undefined\|queryDepth.*0` | No query depth limiting |
| `queryComplexity.*undefined` | No query complexity analysis |
| `batchRequests.*true` | Batching enabled without rate-limit awareness |
| `graphiql.*true\|playground.*true` in non-dev | Interactive IDE exposed in production |

### Mitigations

```javascript
// GOOD: Disable introspection in production
const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.NODE_ENV !== 'production',  // disable in prod
  plugins: [
    // Query depth limiting
    depthLimitPlugin({ maxDepth: 7 }),
    // Query complexity analysis
    createComplexityPlugin({ maximumComplexity: 1000 }),
  ],
});

// GOOD: Object-level authorization in every resolver
const resolvers = {
  Query: {
    document: async (_, { id }, context) => {
      const doc = await Document.findById(id);
      if (doc.ownerId !== context.userId) throw new ForbiddenError();  // always check
      return doc;
    },
  },
};
```

## Kubernetes & Container Security

### Critical Misconfigurations

| Misconfiguration | Risk | CWE |
|-----------------|------|-----|
| `privileged: true` | Container runs with host root — full node compromise | CWE-269 |
| Missing `runAsNonRoot: true` | Container runs as UID 0 | CWE-250 |
| `allowPrivilegeEscalation: true` | Process can gain more privileges than parent | CWE-269 |
| `hostNetwork: true` | Container shares host network namespace | CWE-284 |
| `hostPID: true` | Container can see/signal all host processes | CWE-284 |
| `automountServiceAccountToken: true` (default) | JWT auto-mounted; readable by any process in pod | CWE-522 |
| RBAC `verbs: ["*"]` or `resources: ["*"]` | Wildcard grants — cluster takeover risk | CWE-284 |
| `etcd` without TLS or auth | All cluster state (including secrets) readable | CWE-319 |

### Grep Patterns

| Pattern | Risk |
|---------|------|
| `privileged:\s*true` | Privileged container |
| `runAsNonRoot:\s*false\|runAsUser:\s*0` | Runs as root |
| `allowPrivilegeEscalation:\s*true` | Privilege escalation allowed |
| `automountServiceAccountToken:\s*true` | Default token mounted (check if needed) |
| `verbs:\s*\[.*"\*"` | Wildcard RBAC verb |
| `resources:\s*\[.*"\*"` | Wildcard RBAC resource |
| `hostNetwork:\s*true\|hostPID:\s*true` | Host namespace sharing |
| `image:.*:latest` | Mutable image tag — unpinned |

### Secure Pod Spec Pattern

```yaml
# GOOD: Hardened pod security context
apiVersion: v1
kind: Pod
spec:
  automountServiceAccountToken: false  # disable unless needed
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:sha256-abc123...  # pinned digest
    securityContext:
      allowPrivilegeEscalation: false
      privileged: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        cpu: "500m"
        memory: "256Mi"
```

### RBAC Least Privilege

```yaml
# BAD: Wildcard permissions
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]

# GOOD: Minimal scoped permissions
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]  # read-only, specific resource type
```

## WebSocket Security

WebSocket connections upgrade from HTTP but bypass many HTTP-level security controls.

### Key Risks

| Risk | Description |
|------|-------------|
| **Missing Origin Validation** | Cross-Site WebSocket Hijacking (CSWSH) — analogous to CSRF |
| **No Authentication on Upgrade** | WebSocket upgrade succeeds without auth token |
| **Message Injection** | Unsanitized messages relayed to other clients (XSS, command injection) |
| **DoS via Unbounded Messages** | No rate limiting or message size caps |
| **Insecure `ws://`** | Unencrypted WebSocket (use `wss://` only) |

### Grep Patterns

| Pattern | Risk |
|---------|------|
| `ws://` in client or server config | Unencrypted WebSocket |
| `WebSocket.*on\('message'\)` without auth check | Message handler without session validation |
| `io\.on\('connection'\)` without middleware auth | Socket.io without auth middleware |
| `allowedOrigins.*\*\|origin.*true` | Any origin allowed (CSWSH) |

### Mitigations

```javascript
// GOOD: Validate Origin and authenticate on WebSocket upgrade
const wss = new WebSocket.Server({ noServer: true });

server.on('upgrade', (request, socket, head) => {
  const origin = request.headers.origin;
  if (!ALLOWED_ORIGINS.includes(origin)) {
    socket.destroy();
    return;
  }
  // Validate session/JWT from cookie or subprotocol header
  const token = parseCookies(request).session;
  if (!validateToken(token)) {
    socket.destroy();
    return;
  }
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});
```

## OAuth 2.0 & OpenID Connect Security

### Common Vulnerabilities

| Vulnerability | Description |
|---------------|-------------|
| **Open Redirect in Redirect URI** | Unvalidated `redirect_uri` sends auth code to attacker |
| **CSRF on Authorization Endpoint** | Missing `state` parameter allows auth code injection |
| **Authorization Code Injection** | Stolen code replayed at token endpoint |
| **Implicit Flow** | Returns tokens in URL fragment — exposed in browser history/logs |
| **Client Secret Exposure** | Secret hardcoded in frontend/mobile app |
| **Insufficient Scope Validation** | Server doesn't validate requested scopes are appropriate for client |
| **Token Leakage via Referrer** | Access token in URL query params leaks via Referer header |

### Grep Patterns

| Pattern | Risk |
|---------|------|
| `response_type=token` | Implicit flow (deprecated by RFC 9700) |
| `redirect_uri.*\*\|redirect_uri.*regexp` | Overly permissive redirect URI matching |
| `state` absent from authorization request | Missing CSRF protection |
| `client_secret.*=.*["'][^"']+["']` in frontend code | Hardcoded secret in public client |
| `access_token.*query\|token.*getParam` | Token in URL |
| `nonce` absent from OIDC auth request | ID token replay possible |

### Secure OAuth Flow

```python
import secrets

# GOOD: Generate unpredictable state and nonce
state = secrets.token_urlsafe(32)  # CSRF protection
nonce = secrets.token_urlsafe(32)  # OIDC replay protection
session['oauth_state'] = state

# In callback — verify state before exchanging code
if request.args.get('state') != session.pop('oauth_state', None):
    abort(400, "Invalid state parameter")

# Use PKCE for public clients (mobile, SPA) — no client_secret needed
code_verifier = secrets.token_urlsafe(64)
code_challenge = base64url(sha256(code_verifier.encode()))
```

## gRPC Security

| Risk | Description |
|------|-------------|
| **Missing mTLS** | Services accept unauthenticated connections in service mesh |
| **No server-side auth** | gRPC metadata/headers (equivalent of HTTP headers) not validated |
| **Plaintext gRPC** | `grpc://` instead of `grpcs://` or TLS-enabled channel |
| **Unrestricted streaming** | Unbounded server/client streaming without rate limits or size caps |

### Grep Patterns

| Pattern | Risk |
|---------|------|
| `grpc\.insecure_channel\(` | Unencrypted gRPC channel |
| `grpc\.local_channel_credentials\(` | Development-only credentials in prod code |
| `ServerCredentials\.insecure\(\)` | Server accepts plaintext connections |
| Interceptor/middleware absent in gRPC service | No auth enforcement on requests |

## CWE Reference

| CWE | Name |
|-----|------|
| CWE-250 | Execution with Unnecessary Privileges (container root) |
| CWE-269 | Improper Privilege Management (RBAC wildcard, privileged containers) |
| CWE-284 | Improper Access Control (K8s namespace sharing, missing auth) |
| CWE-319 | Cleartext Transmission (ws://, grpc://, unencrypted etcd) |
| CWE-352 | CSRF (WebSocket origin bypass, missing OAuth state) |
| CWE-522 | Insufficiently Protected Credentials (auto-mounted SA tokens) |
| CWE-601 | URL Redirection to Untrusted Site (OAuth open redirect) |
| CWE-770 | Uncontrolled Resource Consumption (unbounded GraphQL/WebSocket) |
| CWE-918 | SSRF (GraphQL resolvers, WebSocket message proxying) |

## References

- OWASP GraphQL Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html
- OWASP WebSocket Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#websockets
- OWASP OAuth 2.0 Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html
- NSA/CISA Kubernetes Hardening Guide: https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF
- CIS Kubernetes Benchmark: https://www.cisecurity.org/benchmark/kubernetes
- NIST SP 800-204 Microservices Security: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204.pdf
- RFC 9700 OAuth 2.0 Security Best Current Practice: https://www.rfc-editor.org/rfc/rfc9700
- RFC 7523 JWT Bearer Token for OAuth: https://www.rfc-editor.org/rfc/rfc7523
