# Enterprise Roadmap: Containerized MCP ISPW Server

This roadmap defines phased, enterprise-grade packaging and operations for the MCP ISPW server. It covers security, observability, supply chain integrity, deployment, and operations. It maps work to existing repository files and introduces new artifacts to be added.

## Overview

- Scope: Package and operate the MCP ISPW server as a secure, observable container for remote execution.
- Current repo highlights: see [ispw_mcp_server.py](ispw_mcp_server.py), [pyproject.toml](pyproject.toml), [README.md](README.md), [QUICKSTART.md](QUICKSTART.md), [ispw_openapi_spec.json](ispw_openapi_spec.json).
- Runtime options: stdio (current, default) or streamable HTTP (exposed service). Choose per deployment topology.

## Phase 1 — Containerization & Runtime Hardening

- Deliverables:
  - Multi-stage `Dockerfile` (builder → distroless/chainguard runtime)
  - Non-root user, read-only root filesystem, minimal OS footprint
  - Seccomp/AppArmor profiles; capability drops; no privilege escalation
  - Entrypoint compatible with MCP stdio or HTTP mode
- TODOs:
  - Add `Dockerfile` with pinned Python base; build wheels; copy only artifacts
  - Set `USER` to non-root; `umask` hardened; `PYTHONUNBUFFERED=1`
  - Apply `securityContext` (Kubernetes) or equivalent container-level hardening
  - Scan base images (Trivy/Grype); fail on high/critical CVEs
- Tools/Standards: Distroless/Chainguard images, Seccomp/AppArmor, Trivy/Grype
- Repo mapping: Reference `ispw_mcp_server.py` entrypoint; add CI step to build image

## Phase 2 — Secrets & Configuration Management

- Deliverables:
  - Integrate enterprise secret manager (Vault/ASM/AKV/GSM)
  - Replace local `.env` usage with Kubernetes `Secret`/CSI mounts and external secret sync
  - Rotation playbook and short-lived token policy
- TODOs:
  - Store `ISPW_API_TOKEN` in secrets manager; mount via ExternalSecrets/CSI
  - Define config profiles (dev/stage/prod) and precedence; forbid `.env` in prod
  - Ensure redaction in logs and error paths
- Tools/Standards: External Secrets Operator, HashiCorp Vault/AWS SM/Azure KV/GCP SM, SOPS/SealedSecrets
- Repo mapping: Update [README.md](README.md) guidance; ensure `ispw_mcp_server.py` reads from env/secure mounts only

## Phase 3 — TLS/PKI & Transport Security

- Deliverables:
  - Enable TLS verification; optional mTLS to CES if supported
  - CA bundle management and cert rotation documentation
  - Proxy/egress gateway allowlisting
- TODOs:
  - Remove `verify=False` in `httpx.AsyncClient` within `ispw_mcp_server.py`
  - Mount trusted CA bundle; validate SNI/CN/SAN alignment
  - Configure egress proxy/gateway; allowlist CES endpoint/ports
- Tools/Standards: cert-manager, enterprise CA, mTLS via Envoy/NGINX, TLS 1.2+/FIPS
- Repo mapping: Code changes in [ispw_mcp_server.py](ispw_mcp_server.py) and deployment manifests

## Phase 4 — Observability (Logs, Metrics, Traces)

- Deliverables:
  - Structured JSON logs with correlation IDs
  - Prometheus metrics (request count/latency/errors, process)
  - OpenTelemetry tracing for CES calls (OTLP export)
  - Health probes (liveness/readiness) suitable for Kubernetes
- TODOs:
  - Introduce logger (JSON) in `ispw_mcp_server.py`; sanitize PII/secrets
  - Add `prometheus_client` counters/histograms; document scrape
  - Instrument with OpenTelemetry SDK; spans on each CES request; OTLP to Collector
  - Implement lightweight health command or HTTP health endpoint when using HTTP mode
- Tools/Standards: OpenTelemetry SDK, Prometheus client, OTel Collector, Loki/ELK/Splunk
- Repo mapping: New observability module; doc updates in [README.md](README.md), [QUICKSTART.md](QUICKSTART.md)

## Phase 5 — CI/CD: Scanning, SBOM, Signing, Provenance

- Deliverables:
  - CI pipelines: lint/tests, dependency audit, image scanning
  - SBOM generation (CycloneDX/Syft) attached to image artifacts
  - Container signing (Sigstore Cosign), SLSA provenance attestation
  - Policy gates (fail on critical CVEs, unsigned images, missing SBOM)
- TODOs:
  - Add GitHub Actions/GitLab pipeline: `ruff`, `pytest`, `pip-audit`, `trivy/grype`
  - Generate SBOM for app and container; publish artifacts
  - Sign image with Cosign (OIDC/KMS) and verify in admission
  - Produce SLSA attestation; pin deps; reproducible builds
- Tools/Standards: pip-audit, Trivy/Grype, Syft/CycloneDX, Cosign, SLSA, CodeQL
- Repo mapping: Add `.github/workflows/*.yml` and SBOM publication; enhance [pyproject.toml](pyproject.toml) if needed

## Phase 6 — Kubernetes & Helm Deployment

- Deliverables:
  - Helm chart: Deployment, (optional) Service for HTTP, ConfigMap/Secret, PDB, HPA
  - PodSecurity (restricted), resource requests/limits, seccomp/AppArmor annotations
  - Readiness/liveness probes; ServiceAccount + RBAC
- TODOs:
  - Create `charts/ispw-mcp/` with values for TLS, secrets, observability, resources
  - Enforce non-root, read-only FS, capability drops
  - Integrate ExternalSecrets and CA bundles; configure probes
  - Define HPA (CPU/memory or custom metrics)
- Tools/Standards: Helm, PodSecurity, RBAC, PDB, HPA
- Repo mapping: New `charts/` directory and deployment docs in [README.md](README.md)

## Phase 7 — Network Security & Egress Controls

- Deliverables:
  - Default-deny `NetworkPolicy`; allowlist egress to CES
  - Ingress only if HTTP mode; mTLS with IP allowlists
  - Policy engine enforcing signed images and security contexts
- TODOs:
  - Author `NetworkPolicy` resources; restrict DNS and egress
  - Configure ingress (if needed) with mTLS via Envoy/NGINX
  - Apply Kyverno/Cilium policies (non-root, read-only, signed images, SBOM presence)
- Tools/Standards: NetworkPolicy, Envoy/NGINX, Kyverno/Cilium
- Repo mapping: Helm templates for network/security policies

## Phase 8 — Compliance, Audit, SLOs & Operations

- Deliverables:
  - SIEM integration; audit event schema for destructive operations (e.g., deploy)
  - Retention policies (logs/metrics/traces)
  - SLOs, alerts, runbooks; DR plan
- TODOs:
  - Forward structured logs/events to SIEM (Splunk/Elastic)
  - Define retention windows (90–365 days as required)
  - Define SLOs (availability, CES latency, error rate) and alerting (PagerDuty/Opsgenie)
  - Write runbooks (token rotation, cert renewal, CES incident handling)
  - Quarterly compliance reviews with artifacts (SBOM, signatures, scan reports)
- Tools/Standards: SIEM, PagerDuty/Opsgenie, DLP policies
- Repo mapping: Docs in [README.md](README.md) and `docs/runbooks/*.md`

## Runtime Topology Options

- Option A (Preferred for isolation): Stdio-only MCP server as a sidecar/batch with strict egress-only policies; no inbound traffic.
- Option B: MCP HTTP mode with mTLS ingress for multi-client access; requires Service/Ingress and stricter perimeter controls.

## Air‑Gapped Alternatives

- Mirror base images and vulnerability DBs; internal registries (Harbor/Artifactory)
- On-prem Vault/OTel/Prometheus/Loki/SIEM; offline Cosign keys/KMS; internal CA via cert-manager

## Token Strategy & Risk Controls

- Prefer short-lived tokens; automate rotation; least-privilege roles
- Redact tokens in logs; strict access to Secret mounts; audit access

## Milestones & Acceptance Criteria

- M1: Docker image builds and passes vulnerability gates; runs non-root/read-only
- M2: Secrets via Vault/ExternalSecrets; TLS verification enabled; egress allowlist
- M3: Observability operational (logs/metrics/traces); health probes green
- M4: CI/CD enforces SBOM/signing/provenance and fails on critical CVEs
- M5: Helm deploy with PodSecurity/NetworkPolicy; HPA tuned; SLOs defined
- M6: SIEM ingest; runbooks complete; quarterly compliance ready

## Change Map (Repo Artifacts to Add)

- `Dockerfile`, `.dockerignore`
- `.github/workflows/*` (lint/test/scan/build/sign/SBOM)
- `charts/ispw-mcp/*` (Helm)
- `docs/runbooks/*`, `docs/policies/*`
- Observability module updates in [ispw_mcp_server.py](ispw_mcp_server.py)

---

This roadmap is designed to be implemented incrementally. Each phase yields deployable, testable artifacts and advances the server toward enterprise-grade security and operability.