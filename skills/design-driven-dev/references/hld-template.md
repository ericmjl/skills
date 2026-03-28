# High-Level Design Template

High-Level Designs (HLDs) document the project vision, architecture, and key decisions. There is typically ONE HLD per project that covers the entire scope.

## File Location

`DOCS_DIR/high-level-design.md`

## Standard Structure

```markdown
# [Project Name] - High-Level Design

**Created**: YYYY-MM-DD
**Status**: Draft | Review | Approved | Implemented

## Problem Statement

What problem are we solving? Why does this project exist?

## Goals

1. **[Goal 1]** - Brief description
2. **[Goal 2]** - Brief description
3. **[Goal 3]** - Brief description

## Non-Goals

What is explicitly **NOT** in scope for this project?

- **Non-goal 1**: Reason it's out of scope
- **Non-goal 2**: Reason it's out of scope

## Target Users / Personas

Who is this for?

- **Persona 1**: Description and needs
- **Persona 2**: Description and needs

## Architecture Overview

High-level system architecture. Can include:
- Component diagram
- Data flow description
- Technology choices

## Key Design Decisions

### Decision 1: [Title]

**Choice**: [What was chosen]

**Rationale**: Why this choice was made

**Alternatives considered**: Other options and why they were rejected

### Decision 2: [Title]

**Choice**: [What was chosen]

**Rationale**: Why this choice was made

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Risk 1 | Mitigation approach |
| Risk 2 | Mitigation approach |

## Related Designs

Link to all LLDs for this project:

- [Feature A LLD](../designs/feature-a/LLD.md)
- [Feature B LLD](../designs/feature-b/LLD.md)
```

## Example: Complete HLD

```markdown
# Shopping App - High-Level Design

**Created**: 2025-01-15
**Status**: Approved

## Problem Statement

Users need a mobile shopping experience that allows them to browse products, add items to cart, and complete purchases. Current website is not mobile-optimized and conversion rates are low.

## Goals

1. **Mobile-first shopping** - Allow users to browse and purchase from mobile devices
2. **Fast checkout** - Reduce cart abandonment with streamlined payment flow
3. **Offline capability** - Let users browse cached products without internet

## Non-Goals

- **In-store inventory checks**: Not part of v1
- **Social features**: Reviews and ratings deferred to v2
- **International shipping**: US-only for launch

## Target Users

- **Mobile shopper**: Prefers app over browser, values speed
- **Casual browser**: Browses on commute, buys later
- **Returning customer**: Wants quick re-order capability

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Mobile App                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐    │
│  │  Store  │→ │  Cart   │→ │    Checkout     │    │
│  │ Browser │  │ Manager │  │    Flow         │    │
│  └─────────┘  └─────────┘  └─────────────────┘    │
│        ↓            ↓              ↓              │
│  ┌─────────────────────────────────────────┐      │
│  │         Local Storage (Offline)         │      │
│  └─────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
        │
        ▼ (REST API)
┌─────────────────────────────────────────────────────┐
│                   Backend API                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐    │
│  │ Product │  │  Order  │  │   Payment       │    │
│  │ Service │  │ Service │  │   Gateway       │    │
│  └─────────┘  └─────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Key Design Decisions

### Decision 1: Native vs. Cross-platform

**Choice**: React Native

**Rationale**: Team has JavaScript expertise, need iOS and Android, fast iteration important

**Alternatives considered**:
- Native (Swift/Kotlin): Would require hiring new team, slower initial development
- Flutter: Smaller community, less hiring pool

### Decision 2: Offline Strategy

**Choice**: Cache products locally, queue orders

**Rationale**: Users browse during commute; need graceful degradation

**Alternatives considered**:
- Online-only: Loses mobile commuter use case
- Full offline: Too complex for v1, payment reconciliation difficult

### Decision 3: Payment Provider

**Choice**: Stripe

**Rationale**: Best documentation, excellent fraud detection, familiar API

**Alternatives considered**:
- PayPal: Higher fees, less mobile-friendly SDK
- Square: Better for in-person, weaker online APIs

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Payment provider downtime | Show "temporarily unavailable" message, queue purchases |
| Offline payment conflicts | Require online for checkout, show clear offline limitations |
| Slow image loading | Progressive JPEG, lazy loading, CDN |

## Related Designs

- [Authentication LLD](../designs/authentication/LLD.md)
- [Product Browsing LLD](../designs/product-browsing/LLD.md)
- [Cart & Checkout LLD](../designs/cart-checkout/LLD.md)
```

## Key Principles

1. **One HLD per project** - Don't create multiple HLDs
2. **Link to ALL LLDs** - The "Related Designs" section is critical
3. **Keep it high-level** - Don't dive into implementation details
4. **Decisions, not just descriptions** - Explain *why*
5. **Update when scope changes** - If goals change, update the HLD
