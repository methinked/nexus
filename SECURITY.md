# Nexus Security Analysis

**Last Updated:** 2025-11-30
**Status:** Development - Security Hardening Required

---

## Current Security Posture

### ✅ What's Implemented

1. **JWT Token Infrastructure**
   - JWT token creation with HS256 signing
   - Token expiration (default: 24 hours)
   - Token verification functions
   - Location: `nexus/shared/auth.py`

2. **Shared Secret Registration**
   - Initial node registration requires shared secret
   - Prevents unauthorized nodes from joining
   - Location: `nexus/core/api/auth.py:register_node()`

3. **Password Hashing**
   - Bcrypt for password hashing (though not currently used)
   - Secure hash verification
   - Location: `nexus/shared/auth.py`

---

## ⚠️ Critical Security Gaps

### 1. **NO AUTHENTICATION ON API ENDPOINTS** 🔴
**Severity: CRITICAL**

Currently, JWT tokens are issued but **never verified**. All API endpoints are completely open:

```python
# ❌ Current state - NO AUTH
@router.post("/api/metrics")
async def submit_metrics(metric: MetricCreate, db: Session = Depends(get_db)):
    # Anyone can submit metrics!
    pass

# ✅ Should be
@router.post("/api/metrics")
async def submit_metrics(
    metric: MetricCreate,
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(verify_jwt_token)  # ← MISSING
):
    # Only authenticated nodes can submit
    pass
```

**Affected Endpoints:**
- `/api/metrics` (POST) - Metrics submission
- `/api/nodes/*` (GET/PUT/DELETE) - Node management
- `/api/jobs/*` (POST/GET) - Job operations
- `/api/terminal/{node_id}` (WebSocket) - Terminal access
- `/api/nodes/{node_id}/health` (GET) - Health status

**Impact:**
- Anyone on the network can:
  - View all nodes and their details
  - Submit fake metrics
  - Create jobs
  - Access terminal sessions (if client exists)
  - Query sensitive information

**Fix Required:**
- Implement FastAPI dependency for JWT verification
- Add to all protected endpoints
- Verify node ownership for node-specific operations

### 2. **NO TLS/HTTPS** 🔴
**Severity: CRITICAL**

All communication is plaintext HTTP:

```
┌─────┐  HTTP (plaintext)  ┌──────┐  HTTP (plaintext)  ┌───────┐
│ CLI │ ←─────────────────→ │ Core │ ←─────────────────→ │ Agent │
└─────┘   JWT visible!      └──────┘   JWT visible!      └───────┘
```

**Impact:**
- JWT tokens interceptable via network sniffing
- Shared secrets visible during registration
- All data (metrics, jobs, terminal I/O) readable
- Man-in-the-middle attacks possible

**Fix Required:**
- Generate TLS certificates (self-signed for local, Let's Encrypt for production)
- Configure Uvicorn with TLS
- Update all HTTP clients to use HTTPS
- Add certificate pinning for agent-core communication

### 3. **NO WEBSOCKET AUTHENTICATION** 🔴
**Severity: CRITICAL**

Terminal WebSocket accepts any connection:

```python
# ❌ Current state
@router.websocket("/terminal/{node_id}")
async def terminal_proxy(websocket: WebSocket, node_id: UUID):
    await websocket.accept()  # No auth check!
    # Anyone can connect to any node's terminal
```

**Impact:**
- Unauthenticated terminal access
- Complete remote control without credentials

**Fix Required:**
- Add JWT token to WebSocket connection (query param or header)
- Verify token before accepting connection
- Ensure user has permission for target node

### 4. **SHARED SECRET IN PLAINTEXT** 🟡
**Severity: HIGH**

Shared secret comparison is plaintext:

```python
def verify_shared_secret(provided_secret: str, expected_secret: str) -> bool:
    return provided_secret == expected_secret  # ❌ Timing attack vulnerable
```

**Impact:**
- Timing attacks could reveal secret
- No rate limiting on registration attempts

**Fix Required:**
- Use `secrets.compare_digest()` for constant-time comparison
- Add rate limiting to registration endpoint
- Consider using HMAC-based challenge-response

### 5. **NO RATE LIMITING** 🟡
**Severity: HIGH**

No protection against brute force or DoS:

**Impact:**
- Brute force attacks on shared secret
- API abuse (excessive metrics submission)
- Resource exhaustion

**Fix Required:**
- Implement rate limiting (slowapi or custom middleware)
- Different limits for different endpoints
- IP-based and token-based limits

### 6. **NO AUDIT LOGGING** 🟡
**Severity: MEDIUM**

No security event logging:

**Impact:**
- No visibility into:
  - Failed authentication attempts
  - Suspicious activity
  - Token usage patterns
  - Administrative actions

**Fix Required:**
- Log all authentication events
- Log failed access attempts
- Log administrative operations
- Consider structured logging (JSON) for SIEM integration

### 7. **JWT TOKENS STORED IN FILES** 🟡
**Severity: MEDIUM**

Agent stores token in `data/agent_state.json`:

```json
{
  "node_id": "...",
  "api_token": "eyJ..."  // ❌ Plaintext JWT
}
```

**Impact:**
- Token theft if file system compromised
- Token visible to any process with file access

**Fix Required:**
- Use OS keyring/credential manager
- Encrypt state file
- Restrict file permissions (0600)

### 8. **NO TOKEN ROTATION** 🟡
**Severity: MEDIUM**

Tokens live for 24 hours without rotation:

**Impact:**
- Long-lived token exposure window
- No mechanism to revoke compromised tokens
- Token refresh endpoint not implemented

**Fix Required:**
- Implement token refresh endpoint
- Shorter initial token lifetime
- Refresh tokens with longer expiration
- Token revocation list

### 9. **DATABASE NOT ENCRYPTED** 🟠
**Severity: LOW (for current use case)**

SQLite database stored in plaintext:

**Impact:**
- If filesystem compromised, all data visible
- Node metadata, job history, metrics exposed

**Fix Required:**
- SQLite encryption (SQLCipher)
- Or filesystem-level encryption
- For sensitive deployments only

### 10. **NO INPUT VALIDATION ON WEBSOCKET** 🟠
**Severity: MEDIUM**

Terminal WebSocket doesn't validate message sizes:

**Impact:**
- Memory exhaustion via large messages
- Buffer overflow potential

**Fix Required:**
- Maximum message size limits
- Rate limiting on messages
- Input sanitization

---

## Recommended Security Roadmap

### Phase 1: Critical Fixes (P0)
**Must-do before any production use**

1. **Implement JWT Authentication Dependency**
   ```python
   # Create: nexus/core/api/dependencies.py
   async def verify_jwt_token(
       authorization: str = Header(...),
       config: CoreConfig = Depends(get_config)
   ) -> TokenData:
       """Verify JWT token from Authorization header."""
       if not authorization.startswith("Bearer "):
           raise HTTPException(401, "Invalid authentication")
       token = authorization.replace("Bearer ", "")
       return verify_token(token, config.jwt_secret_key)
   ```

2. **Add Auth to All Endpoints**
   ```python
   @router.post("/api/metrics")
   async def submit_metrics(
       metric: MetricCreate,
       db: Session = Depends(get_db),
       token_data: TokenData = Depends(verify_jwt_token)  # ← ADD
   ):
       # Verify metric.node_id matches token_data.node_id
       if metric.node_id != token_data.node_id:
           raise HTTPException(403, "Cannot submit metrics for other nodes")
       ...
   ```

3. **Enable TLS/HTTPS**
   ```bash
   # Generate self-signed cert for development
   openssl req -x509 -newkey rsa:4096 -nodes \
     -keyout key.pem -out cert.pem -days 365

   # Update uvicorn.run() calls
   uvicorn.run(
       "nexus.core.main:app",
       host="0.0.0.0",
       port=8000,
       ssl_keyfile="key.pem",      # ← ADD
       ssl_certfile="cert.pem",    # ← ADD
   )
   ```

4. **Secure WebSocket Connections**
   - Add token verification before websocket.accept()
   - Use WSS:// instead of WS://

### Phase 2: Important Hardening (P1)
**Should-do before wider deployment**

1. **Rate Limiting**
   - Install: `pip install slowapi`
   - Apply to registration, auth endpoints
   - Configure reasonable limits

2. **Constant-Time Secret Comparison**
   ```python
   import secrets

   def verify_shared_secret(provided: str, expected: str) -> bool:
       return secrets.compare_digest(provided, expected)
   ```

3. **Audit Logging**
   - Log authentication events
   - Log failed attempts
   - Structured JSON logging

4. **Token Refresh Implementation**
   - Complete `/auth/token/refresh` endpoint
   - Shorter-lived access tokens
   - Refresh token mechanism

### Phase 3: Best Practices (P2)
**Nice-to-have for production readiness**

1. **Secure Token Storage**
   - OS keyring integration
   - Encrypted state files

2. **Input Validation**
   - Message size limits
   - Request body size limits
   - Pydantic strict mode

3. **Database Encryption** (if needed)
   - SQLCipher for sensitive deployments

4. **Security Headers**
   ```python
   from fastapi.middleware.security import SecurityHeadersMiddleware

   app.add_middleware(SecurityHeadersMiddleware)
   ```

5. **CORS Hardening**
   - Restrict origins in production
   - No wildcard origins

---

## Security Checklist for Deployment

Before deploying to production:

- [ ] JWT authentication enabled on ALL endpoints
- [ ] TLS/HTTPS enabled (valid certificates)
- [ ] WebSocket authentication implemented
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Secrets changed from defaults
- [ ] Token refresh working
- [ ] CORS configured for production origins
- [ ] Database backups encrypted
- [ ] Security scanning completed
- [ ] Penetration testing performed

---

## Environment Variable Security

**Current Defaults (CHANGE IN PRODUCTION):**
```bash
# ❌ INSECURE DEFAULTS
NEXUS_SHARED_SECRET=nexus-dev-secret-change-in-production
NEXUS_JWT_SECRET_KEY=nexus-jwt-secret-key-change-in-production-with-random-value
```

**Production Requirements:**
```bash
# ✅ SECURE PRODUCTION VALUES
NEXUS_SHARED_SECRET=$(openssl rand -hex 32)
NEXUS_JWT_SECRET_KEY=$(openssl rand -hex 64)

# Store in:
# - Kubernetes secrets
# - Docker secrets
# - AWS Secrets Manager
# - HashiCorp Vault
# NOT in .env files committed to git!
```

---

## Threat Model

### Assumed Threats
1. **Network Eavesdropping** - Attacker on same network
2. **Rogue Agent** - Compromised agent attempting to access other nodes
3. **Brute Force** - Attempts to guess shared secret or tokens
4. **API Abuse** - Flooding endpoints with requests

### Out of Scope (Current Phase)
1. **Physical Access** - Attacker has physical access to devices
2. **Supply Chain** - Compromised dependencies
3. **Advanced Persistent Threats** - Nation-state actors
4. **Social Engineering** - User credential theft

### Trust Boundaries
```
┌────────────────────┐
│  Untrusted Network │  ← Internet, Local Network
└─────────┬──────────┘
          │ TLS + JWT
┌─────────▼──────────┐
│    Nexus Core      │  ← Trusted - controls access
└─────────┬──────────┘
          │ TLS + JWT
┌─────────▼──────────┐
│   Nexus Agents     │  ← Semi-trusted - validated nodes
└────────────────────┘
```

---

## Questions to Consider

1. **Multi-tenancy?** - Will multiple users manage different node subsets?
   - If yes: Need RBAC and user authentication
   - If no: Current node-based auth sufficient

2. **Public Internet Exposure?**
   - If yes: Need WAF, DDoS protection, stricter limits
   - If no: Local network security sufficient

3. **Compliance Requirements?**
   - GDPR, HIPAA, SOC2, etc.
   - May require encryption at rest, audit logs, access controls

4. **Zero-Trust Architecture?**
   - Every request verified
   - Micro-segmentation
   - Principle of least privilege

---

## Security Contact

For security issues, please:
1. DO NOT open public GitHub issues
2. Email: security@your-domain.com (if applicable)
3. Use responsible disclosure

---

**Bottom Line:** The current system has good authentication *infrastructure* but **critical gaps in enforcement**. Before any production use, Phase 1 fixes are **mandatory**.
