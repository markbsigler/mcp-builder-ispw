---
name: mcp-builder-enterprise
description: Comprehensive MCP Server Skill combining base development guidance with enterprise packaging best practices (security, observability, CI/CD, Kubernetes, network, compliance). Use for building MCP servers in Python (FastMCP) or TypeScript with production readiness.
license: Informational guidance; follow org policies.
---

# MCP Server Development Skill (Enterprise Edition)

This skill merges the base MCP builder guidance with enterprise-grade packaging and operations. Use it to design and deliver secure, observable, and compliant MCP servers that run locally (stdio) or remotely (streamable HTTP) at scale.

## Overview

Create MCP servers that enable LLMs to interact with external services through well-designed tools. Quality is measured by how well an MCP server enables real workflows while meeting org standards for security, reliability, and compliance.

---

# Process

## 🚀 High-Level Workflow

Creating a high-quality, production-ready MCP server involves these phases:

### Phase 1: Deep Research and Planning

1. Understand modern MCP design
   - API coverage vs workflow tools: favor comprehensive coverage while adding convenient workflows.
   - Tool naming and discoverability: action-oriented, service-prefixed (e.g., `service_create_…`).
   - Context management: concise descriptions, filtering, pagination.
   - Actionable errors: guide agents to correct inputs and next steps.

2. Study the MCP protocol
   - Start with sitemap: https://modelcontextprotocol.io/sitemap.xml
   - Read spec pages (.md): tools, resources, prompts; transports (stdio vs streamable HTTP).

3. Study framework documentation
   - TypeScript SDK and patterns; Python SDK (FastMCP) patterns.

4. Plan implementation
   - Understand target API (auth, data models, rate limits).
   - Select tools/endpoints to implement; prioritize common workflows.

### Phase 2: Implementation

1. Project structure
   - Follow language-specific guides; add tests and lint config.

2. Core infrastructure
   - Shared API client with authentication
   - Error handling helpers
   - Response formatting (JSON/Markdown)
   - Pagination support

3. Tool implementation
   - Inputs: Zod (TS) or Pydantic (Python) with constraints and clear descriptions
   - Outputs: structured where possible (`outputSchema`, structured content)
   - Implementation: async I/O, pagination, robust errors, dual format returns
   - Annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`

### Phase 3: Review and Test

- Code quality: DRY, type coverage, clear tool docs
- Build and test: `npx @modelcontextprotocol/inspector` | `python -m py_compile` (Python)

### Phase 4: Create Evaluations

- Generate 10 complex read-only questions; verify answers; use XML format for evaluations.

---

# Enterprise Packaging & Operations

The following phases add security, observability, and operational excellence. Apply them to new or existing MCP servers.

### Phase 5: Containerization & Runtime Hardening

- Multi-stage Dockerfile → distroless/chainguard runtime
- Non-root UID/GID; read-only root FS; writable tmp only if needed
- Drop Linux capabilities; no privilege escalation; Seccomp/AppArmor profiles
- stdout-only logging; `PYTHONUNBUFFERED=1`
- Scan base/final images (Trivy/Grype) and fail on high/critical CVEs

### Phase 6: Secrets & Configuration Management

- Use enterprise secrets manager (Vault/ASM/AKV/GSM) via ExternalSecrets/CSI
- Replace `.env` in prod; define config profiles and precedence
- Redact secrets in logs; adopt short-lived tokens and rotation runbooks

### Phase 7: TLS/PKI & Transport Security

- Enable TLS verification; mount CA bundle; validate SNI/CN/SAN
- Prefer mTLS to upstream services where supported; enforce TLS 1.2+/FIPS
- Egress gateway/proxy with allowlist to required endpoints

### Phase 8: Observability (Logs, Metrics, Traces)

- Structured JSON logs with correlation IDs; sanitize PII/secrets
- Prometheus metrics (request count/latency/error rate, process)
- OpenTelemetry tracing for external calls (OTLP via OTel Collector)
- Health signals suitable for Kubernetes (liveness/readiness) via HTTP mode or self-check

### Phase 9: CI/CD, Scanning, SBOM, Signing, Provenance

- CI pipeline: lint (ruff/eslint), tests, pip-audit/dependency audit, image scan
- SBOM (CycloneDX/Syft) for app and container; publish artifacts
- Sign images with Sigstore Cosign; verify signatures in admission
- SLSA provenance; dependency pinning; reproducible builds; optional CodeQL

### Phase 10: Kubernetes & Helm Deployment

- Helm chart: Deployment, (optional) Service for HTTP, ConfigMap/Secret, PDB, HPA
- PodSecurity (restricted), resource requests/limits, seccomp/AppArmor annotations
- Readiness/liveness probes; ServiceAccount + RBAC; ExternalSecrets integration

### Phase 11: Network Security & Egress Controls

- Default-deny NetworkPolicy; allowlist egress to required endpoints; DNS restrictions
- Ingress only when HTTP mode is exposed; mTLS and IP allowlists
- Kyverno/Cilium policy to enforce non-root/read-only/signed images/SBOM presence

### Phase 12: Compliance, SLOs, Alerts, Runbooks

- SIEM integration; audit event schema for destructive operations
- Retention policies (logs/metrics/traces) aligned to org requirements
- SLOs (availability, latency, error rate); alerting (PagerDuty/Opsgenie)
- Runbooks for token rotation, cert renewal, upstream outage handling; DR plan

---

# Implementation Patterns (Python/FastMCP)

- Tool naming & annotations: clear, action-oriented; set `destructiveHint` where applicable
- Inputs: Pydantic v2 models with `ConfigDict`, `Field`, `field_validator`
- HTTP client: `httpx.AsyncClient` with `verify=True`, per-request timeouts, actionable errors, safe retries
- Logging: centralized JSON logger with correlation IDs; redact secrets; summarize requests/responses
- Metrics: Prometheus counters/histograms around external calls; include process metrics
- Tracing: OTel spans per tool/external call; add endpoint, status, duration, identifiers
- Health: self-check tool or HTTP health endpoint for readiness/liveness

---

# Quality Gates & Checklists

## Security
- Non-root, read-only FS, capability drop, Seccomp/AppArmor
- TLS verification enabled; mTLS where supported; managed CA
- Secrets from vault; short TTLs; rotation documented; redaction verified

## Supply Chain
- SBOM generated; image signed; provenance attached; scans pass policies

## Observability
- JSON logs; Prometheus metrics; OTel traces; SLOs + alerts configured

## Deployment
- Helm chart validated; PodSecurity/NetworkPolicy enforced; HPA tuned

## Compliance
- SIEM ingest; audit events for destructive tools; retention documented

---

# Air‑Gapped Guidance

- Mirror scanners and registries; offline Cosign keys/KMS
- On‑prem OTel/Prometheus/Loki/SIEM; cert-manager with internal CA

---

# Reference Library

## Core MCP Documentation
- MCP Protocol sitemap: https://modelcontextprotocol.io/sitemap.xml (fetch pages as .md)
- Best practices: naming, response formats, pagination, transport, security

## SDK Documentation
- Python SDK (FastMCP) README
- TypeScript SDK README

## Language Guides
- Python/FastMCP implementation patterns: server init, Pydantic, decorators, examples, quality checklist
- TypeScript patterns: project structure, Zod schemas, tool registration, examples, quality checklist

## Evaluation Guide
- Create realistic, verifiable, read‑only questions; verify answers; XML format

---

Use this enterprise skill as a single, standalone reference for building MCP servers that meet production standards—no external roadmap required.