# Implementation Plan Template

Implementation plans provide checkbox-based execution guides tied to EARS specifications.

## File Location

`DOCS_DIR/planning/<feature>-implementation-plan.<date>.md`

Move completed plans to `DOCS_DIR/planning/old/` when finished.

## Standard Structure

```markdown
# [Feature] Implementation Plan

**Created**: YYYY-MM-DD
**Owner**: [Team/Person]
**Status**: Planning | In Progress | Complete
**Design Doc**: ../designs/<feature>/LLD.md
**EARS Specs**: ../designs/<feature>/*-EARS.md

## Overview

Brief description of what's being implemented.

## Success Criteria

Measurable outcomes that define success.

## Implementation Phases

### Phase 1: [Name]

**Goal**: What this phase achieves

#### Deliverables

1. **[Component Name]**
   - **Specs**: FEAT-SUB-001, FEAT-SUB-002
   - Details...

#### Testing Requirements

- ✅ **FEAT-SUB-001**: Test description
- ✅ **FEAT-SUB-002**: Test description

#### Definition of Done

- [ ] All deliverables implemented with @spec annotations
- [ ] Unit tests passing

### Phase 2: [Name]
...

## Requirements Traceability

### Phase 1
- UI Components: FEAT-UI-001 through FEAT-UI-010
- API Endpoints: FEAT-API-001 through FEAT-API-005

### Phase 2
- Enhanced features: FEAT-ENH-001 through FEAT-ENH-008

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| ... | ... |

## References

- Links to related docs
```

## Phase Structure

Each phase should include:

### 1. Goal Statement
Brief description of what the phase achieves.

### 2. Deliverables
Numbered list with spec references:

```markdown
#### Deliverables

1. **Login form component**
   - **Specs**: AUTH-LOGIN-001, AUTH-LOGIN-002, AUTH-LOGIN-003
   - Email/password inputs with validation
   - "Remember me" checkbox
   - Error state handling

2. **Authentication service**
   - **Specs**: AUTH-API-001, AUTH-API-002, AUTH-API-003
   - JWT token management
   - Refresh token rotation
   - Logout cleanup
```

### 3. Testing Requirements
Checkmarks with spec references:

```markdown
#### Testing Requirements

**Unit tests** (verify specs with @spec annotations):
- ✅ **AUTH-LOGIN-010 to AUTH-LOGIN-012**: Form validation
- ✅ **AUTH-API-001**: Token generation
- ✅ **AUTH-API-003**: Token refresh

**Integration tests**:
- ✅ **AUTH-LOGIN-020**: Full login flow
- ✅ **AUTH-API-010**: API authentication middleware
```

### 4. Definition of Done
Checklist with spec coverage:

```markdown
#### Definition of Done

- [ ] **All deliverables implemented** with @spec annotations
- [ ] **Phase specs verified**: AUTH-LOGIN-001 through AUTH-LOGIN-015 (15 total)
- [ ] **Unit tests passing** (100% coverage for business logic)
- [ ] **Integration tests passing**
- [ ] **Code review approved**
```

## Progress Updates

Check off items as you complete them:

```markdown
#### Definition of Done

- [x] **All deliverables implemented** with @spec annotations
- [x] **Unit tests passing**
- [ ] **Integration tests passing**  <-- Currently here
- [ ] **Code review approved**
```

## Complete Example

```markdown
# Authentication Feature Implementation Plan

**Created**: 2025-01-17
**Owner**: Engineering Team
**Status**: In Progress
**Design Doc**: ../designs/authentication/LLD.md
**EARS Specs**: ../designs/authentication/*-EARS.md

## Overview

Implement complete authentication flow including login, logout, and password reset.

## Success Criteria

- Users can register and login
- Sessions persist across app restarts
- Invalid credentials show appropriate errors
- Password reset flow completes successfully

## Implementation Phases

### Phase 1: Login Form UI

**Goal**: User can enter credentials and see validation

#### Deliverables

1. **Login form component**
   - **Specs**: AUTH-LOGIN-001 to AUTH-LOGIN-005
   - Email and password fields
   - Login button
   - Form validation

2. **Validation display**
   - **Specs**: AUTH-LOGIN-010 to AUTH-LOGIN-012
   - Inline validation errors
   - Email format check
   - Password presence check

#### Testing Requirements

- ✅ **AUTH-LOGIN-001**: Email field renders
- ✅ **AUTH-LOGIN-002**: Password field renders
- ✅ **AUTH-LOGIN-010**: Email format validation
- ✅ **AUTH-LOGIN-011**: Password presence validation

#### Definition of Done

- [x] Login form component implemented with @spec
- [x] Validation errors display correctly
- [x] Unit tests for validation pass

### Phase 2: Authentication API

**Goal**: Backend verifies credentials and issues tokens

#### Deliverables

1. **Login endpoint**
   - **Specs**: AUTH-API-001, AUTH-API-002
   - POST /auth/login
   - Credential verification

2. **Token management**
   - **Specs**: AUTH-API-010, AUTH-API-011
   - JWT issuance
   - Refresh token rotation

#### Testing Requirements

- [ ] **AUTH-API-001**: Valid credentials return token
- [ ] **AUTH-API-002**: Invalid credentials return 401
- [ ] **AUTH-API-010**: JWT contains correct claims
- [ ] **AUTH-API-011**: Refresh rotates token

#### Definition of Done

- [ ] Login endpoint implemented
- [ ] Token generation working
- [ ] Integration tests passing

### Phase 3: Logout & Session

**Goal**: User can logout and sessions are managed

#### Deliverables

1. **Logout functionality**
   - **Specs**: AUTH-LOGOUT-001 to AUTH-LOGOUT-003

2. **Session persistence**
   - **Specs**: AUTH-SESSION-001 to AUTH-SESSION-004

#### Testing Requirements

- [ ] **AUTH-LOGOUT-001**: Logout clears local token
- [ ] **AUTH-SESSION-002**: Token persists across restart

#### Definition of Done

- [ ] Logout works
- [ ] Sessions persist correctly
- [ ] All related tests pass

## Requirements Traceability

### Phase 1 (Login Form UI)
- Form: AUTH-LOGIN-001 to AUTH-LOGIN-005
- Validation: AUTH-LOGIN-010 to AUTH-LOGIN-012

**Phase 1 Total**: 10 requirements

### Phase 2 (Authentication API)
- Login API: AUTH-API-001 to AUTH-API-005
- Token: AUTH-API-010 to AUTH-API-012

**Phase 2 Total**: 8 requirements

### Phase 3 (Logout & Session)
- Logout: AUTH-LOGOUT-001 to AUTH-LOGOUT-003
- Session: AUTH-SESSION-001 to AUTH-SESSION-004

**Phase 3 Total**: 7 requirements

## Risk Assessment

### High Risk

**1. Token security**
- **Mitigation**: Use short-lived JWT, secure storage
- **Verification**: Security audit before launch

### Medium Risk

**2. Concurrent session handling**
- **Mitigation**: Implement token blacklist for logout
- **Fallback**: Limit to single session if complex

## References

- [Authentication LLD](../designs/authentication/LLD.md)
- [Login EARS](../designs/authentication/login-EARS.md)
- [Logout EARS](../designs/authentication/logout-EARS.md)
```

## Key Principles

1. **One plan per feature** - Don't combine unrelated features
2. **Link to LLD and EARS** - Full traceability chain
3. **Spec ID references** - Every deliverable maps to specs
4. **Phased delivery** - Break into manageable chunks
5. **Definition of Done** - Clear completion criteria
6. **Move to old/ when complete** - Keep planning dir clean
