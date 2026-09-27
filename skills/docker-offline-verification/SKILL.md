---
name: docker-offline-verification
description: >-
  Verify a containerized Docker app runs with ZERO network access (offline verification of demos, teaching sites, deployed containers). Use when: you must prove a containerized app serves every route without internet; a docker run combining --network none with -p fails to publish or reach ports; a --network none container's ports time out and it LOOKS like an app failure. ROOT CAUSE: port publishing (-p) requires an attached network — with --network none there is no network to publish from, so -p silently does nothing; a Docker networking fact, not an app failure. PROCEDURE: (1) run with --network none and NO -p; (2) docker exec INTO the container; (3) from inside, fetch each route against localhost (docker exec <container> sh -c 'curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT/route') and assert expected status/body per route.
created_at: "2026-09-09"
---

# Docker Offline Verification

Verify a containerized Docker app runs with ZERO network access (offline/airtight verification of demos, teaching sites, deployed containers). Use when: you must prove a containerized app serves every route without internet; a docker run combining --network none with -p fails to publish or reach ports; a --network none container's ports time out and it LOOKS like an app failure. ROOT CAUSE: port publishing (-p) requires an attached network - with --network none there is no network to publish from, so -p silently does nothing; it is a Docker networking fact, not an app failure. PROCEDURE: (1) run the container with --network none and NO -p flag; (2) docker exec INTO the isolated container; (3) from inside, fetch each route against localhost (docker exec <container> sh -c 'curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT/route' or wget -qO- if curl is absent) and assert the expected status/body per route. Distilled 2026-09-09 verifying the next-token bootcamp site served all routes with zero network.

## Instructions

TODO: Add specific instructions based on observed patterns.
