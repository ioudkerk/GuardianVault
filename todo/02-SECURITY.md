# Production Security Hardening

**Priority**: HIGH
**Estimated Time**: 1-2 weeks
**Status**: Not Started

## Overview

The coordination server currently works for testing/development but lacks critical security features needed for production use. This task implements authentication, authorization, encryption, and security monitoring.

## Current Security Status

### ✅ Already Implemented
- [x] Basic invitation code system
- [x] Guardian-vault access validation
- [x] Round data validation
- [x] Transaction timeout tracking
- [x] MongoDB parameter validation (no injection)

### ⚠️ Missing (Critical for Production)
- [ ] JWT-based authentication
- [ ] TLS/HTTPS encryption
- [ ] Rate limiting
- [ ] Input sanitization
- [ ] Audit logging
- [ ] Session management
- [ ] Secrets management
- [ ] Database encryption
- [ ] API key authentication (admin operations)
- [ ] Intrusion detection

## Tasks

### Phase 1: Authentication & Authorization (Days 1-3)

- [ ] **1.1 JWT Authentication**
  - [ ] Install PyJWT library
  - [ ] Create JWT token generation
  - [ ] Token expiration (15 min access, 7 day refresh)
  - [ ] Token refresh endpoint
  - [ ] JWT validation middleware
  - [ ] Token revocation (blacklist)

- [ ] **1.2 Guardian Authentication Flow**
  ```
  1. Guardian joins with invitation code
  2. Server generates JWT access + refresh tokens
  3. Guardian uses JWT for all subsequent requests
  4. Access token expires after 15 minutes
  5. Guardian refreshes using refresh token
  ```

- [ ] **1.3 Replace Invitation Codes**
  - [ ] Keep invitation code for initial join
  - [ ] After join, switch to JWT authentication
  - [ ] Store JWT securely in guardian app
  - [ ] Validate JWT on every WebSocket message
  - [ ] Validate JWT on REST API calls

- [ ] **1.4 Authorization System**
  - [ ] Role-based access control (RBAC)
    - [ ] Guardian role (can sign transactions in their vaults)
    - [ ] Admin role (can create vaults, invite guardians)
    - [ ] Viewer role (read-only access)
  - [ ] Permission checks on all operations
  - [ ] Guardian can only access their vaults
  - [ ] Admin operations require admin role

### Phase 2: TLS/HTTPS Encryption (Days 4-5)

- [ ] **2.1 TLS Configuration**
  - [ ] Generate/obtain SSL certificates
    - [ ] Self-signed for development
    - [ ] Let's Encrypt for production
  - [ ] Configure uvicorn with TLS
  - [ ] Redirect HTTP to HTTPS
  - [ ] Configure certificate renewal

- [ ] **2.2 WebSocket Security**
  - [ ] Enable WSS (WebSocket Secure)
  - [ ] Certificate validation
  - [ ] Update guardian app to use wss://
  - [ ] Test with self-signed certs

- [ ] **2.3 Database Connection Security**
  - [ ] Enable MongoDB authentication
  - [ ] Use TLS for MongoDB connections
  - [ ] Store credentials securely
  - [ ] Rotate MongoDB passwords

### Phase 3: Rate Limiting & DDoS Protection (Days 6-7)

- [ ] **3.1 API Rate Limiting**
  - [ ] Install slowapi or similar
  - [ ] Rate limit REST endpoints:
    - [ ] 10 requests/min per IP for public endpoints
    - [ ] 100 requests/min per guardian for authenticated
  - [ ] Rate limit WebSocket connections:
    - [ ] Max 3 connections per guardian
    - [ ] Max signing attempts per transaction
  - [ ] Custom limits for admin operations

- [ ] **3.2 Request Validation**
  - [ ] Maximum request size limits
  - [ ] Request timeout (30 seconds)
  - [ ] Validate all JSON schemas
  - [ ] Reject malformed requests

- [ ] **3.3 DDoS Protection**
  - [ ] Connection limits per IP
  - [ ] Exponential backoff for failed auth
  - [ ] Ban IPs after excessive failures
  - [ ] CAPTCHA for sensitive operations (optional)

### Phase 4: Input Sanitization & Validation (Day 8)

- [ ] **4.1 Pydantic Model Validation**
  - [ ] Review all Pydantic models
  - [ ] Add field validators
  - [ ] Validate hex strings (nonceShare, rPoint, etc.)
  - [ ] Validate transaction amounts
  - [ ] Validate addresses (Bitcoin/Ethereum format)

- [ ] **4.2 SQL Injection Prevention**
  - [ ] Already using Motor (no SQL injection risk)
  - [ ] Review all MongoDB queries
  - [ ] Use parameterized queries
  - [ ] Validate guardian_id/vault_id/transaction_id format

- [ ] **4.3 XSS Prevention**
  - [ ] Sanitize all user inputs before storage
  - [ ] Escape output in error messages
  - [ ] Set proper Content-Security-Policy headers
  - [ ] Validate memo/name fields

### Phase 5: Audit Logging & Monitoring (Days 9-10)

- [ ] **5.1 Comprehensive Audit Log**
  - [ ] Log all authentication attempts
  - [ ] Log all vault operations (create, activate, delete)
  - [ ] Log all guardian operations (invite, join, remove)
  - [ ] Log all transaction operations (create, sign, complete)
  - [ ] Log all signing round submissions
  - [ ] Log all admin operations

- [ ] **5.2 Security Event Logging**
  - [ ] Failed authentication attempts
  - [ ] Invalid JWT tokens
  - [ ] Rate limit violations
  - [ ] Malformed requests
  - [ ] Unusual signing patterns
  - [ ] Multiple concurrent connections

- [ ] **5.3 Log Management**
  - [ ] Structured JSON logging
  - [ ] Rotate logs daily
  - [ ] Store logs securely (separate from app)
  - [ ] No sensitive data in logs (redact keys)
  - [ ] Log retention policy (90 days)

- [ ] **5.4 Monitoring & Alerts**
  - [ ] Set up monitoring (Prometheus/Grafana optional)
  - [ ] Alert on suspicious activity:
    - [ ] 10+ failed auth in 1 minute
    - [ ] Transaction signing timeout
    - [ ] Database connection failures
    - [ ] High error rates

### Phase 6: Session Management (Day 11)

- [ ] **6.1 Guardian Sessions**
  - [ ] Track active sessions per guardian
  - [ ] Limit concurrent sessions (max 3)
  - [ ] Session timeout (30 min inactivity)
  - [ ] Force logout on suspicious activity
  - [ ] Device fingerprinting (optional)

- [ ] **6.2 WebSocket Session Security**
  - [ ] Associate WebSocket with authenticated session
  - [ ] Validate session on every message
  - [ ] Close connection on token expiration
  - [ ] Heartbeat/ping to detect dead connections

- [ ] **6.3 Session Storage**
  - [ ] Store sessions in Redis (optional) or MongoDB
  - [ ] Track last activity timestamp
  - [ ] Track IP address and user agent
  - [ ] Allow guardian to view/revoke sessions

### Phase 7: Secrets Management (Day 12)

- [ ] **7.1 Move Secrets Out of .env**
  - [ ] Use environment variables instead of .env file
  - [ ] Or use secrets manager (AWS Secrets Manager, HashiCorp Vault)
  - [ ] Never commit secrets to git
  - [ ] Document secret requirements

- [ ] **7.2 Key Management**
  - [ ] JWT secret key rotation
  - [ ] MongoDB password rotation
  - [ ] API keys for admin operations
  - [ ] Encrypt sensitive config values

- [ ] **7.3 Secure Deployment**
  - [ ] Use systemd secrets or Docker secrets
  - [ ] Restrict file permissions (600 for secrets)
  - [ ] No secrets in logs or error messages
  - [ ] Secure secret backup/recovery

### Phase 8: Database Security (Day 13)

- [ ] **8.1 MongoDB Security**
  - [ ] Enable authentication
  - [ ] Create restricted user (not root)
  - [ ] Enable TLS for connections
  - [ ] Network isolation (firewall)
  - [ ] Regular backups

- [ ] **8.2 Data Encryption**
  - [ ] Enable MongoDB encryption at rest (if available)
  - [ ] Encrypt backups
  - [ ] Secure backup storage location
  - [ ] Test backup restoration

- [ ] **8.3 Database Hardening**
  - [ ] Disable unnecessary features
  - [ ] Update MongoDB to latest version
  - [ ] Monitor for vulnerabilities
  - [ ] Regular security patches

### Phase 9: API Security (Day 14)

- [ ] **9.1 Admin API Protection**
  - [ ] Require API key for admin operations
  - [ ] Separate admin endpoints from guardian endpoints
  - [ ] IP whitelist for admin access (optional)
  - [ ] Extra validation for destructive operations

- [ ] **9.2 CORS Configuration**
  - [ ] Restrict allowed origins
  - [ ] No wildcard CORS in production
  - [ ] Validate Origin header
  - [ ] Set proper CORS headers

- [ ] **9.3 Security Headers**
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] X-XSS-Protection: 1; mode=block
  - [ ] Strict-Transport-Security (HSTS)
  - [ ] Content-Security-Policy

## Implementation Details

### JWT Authentication Example

```python
# coordination-server/app/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer

SECRET_KEY = "your-secret-key"  # Load from secrets manager
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Use in WebSocket
@sio.event
async def connect(sid, environ, auth):
    token = auth.get("token")
    if not token:
        return False

    payload = verify_token(token)
    guardian_id = payload.get("guardian_id")
    vault_id = payload.get("vault_id")

    # Store in session
    async with sio.session(sid) as session:
        session["guardian_id"] = guardian_id
        session["vault_id"] = vault_id

    return True
```

### Rate Limiting Example

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/vaults")
@limiter.limit("10/minute")
async def create_vault(request: Request, vault: VaultCreate):
    # Create vault logic
    pass
```

### Audit Logging Example

```python
# coordination-server/app/audit.py
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")

def log_audit_event(event_type: str, user_id: str, details: dict):
    audit_logger.info({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details
    })

# Usage
log_audit_event("TRANSACTION_SIGNED", guardian_id, {
    "transaction_id": tx_id,
    "vault_id": vault_id,
    "round": 3
})
```

## Testing Strategy

### Security Tests

- [ ] Test JWT expiration and refresh
- [ ] Test invalid/expired tokens rejected
- [ ] Test rate limiting works
- [ ] Test unauthorized access blocked
- [ ] Penetration testing (optional)
- [ ] Vulnerability scanning

### Integration Tests

- [ ] Guardian can authenticate and sign
- [ ] Multiple guardians can connect
- [ ] Rate limits don't affect normal operation
- [ ] TLS connections work correctly

## Security Audit Checklist

- [ ] No hardcoded secrets in code
- [ ] All endpoints require authentication
- [ ] All inputs validated
- [ ] All errors logged
- [ ] No sensitive data in logs
- [ ] TLS enabled everywhere
- [ ] Rate limiting active
- [ ] MongoDB secured
- [ ] JWT tokens expire
- [ ] Sessions timeout properly
- [ ] Audit logs complete
- [ ] Secrets properly managed
- [ ] Database encrypted
- [ ] Regular security updates

## Deployment Security

- [ ] Use production-grade WSGI server (not development server)
- [ ] Run as non-root user
- [ ] Use firewall to restrict ports
- [ ] Deploy behind reverse proxy (nginx)
- [ ] Enable fail2ban or similar
- [ ] Regular security patches
- [ ] Backup encryption keys separately
- [ ] Disaster recovery plan

## Success Criteria

- [ ] All API endpoints require JWT authentication
- [ ] WebSocket connections use JWT
- [ ] All traffic encrypted with TLS/WSS
- [ ] Rate limiting prevents abuse
- [ ] Audit logs capture all security events
- [ ] No secrets in code or logs
- [ ] Database authentication enabled
- [ ] Passes security audit checklist
- [ ] No critical vulnerabilities found in scan

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/)

## Dependencies on Other Tasks

- **01-GUARDIAN-APP.md**: Guardian app needs JWT authentication support
- **04-ADMIN-DASHBOARD.md**: Admin dashboard needs admin API keys
