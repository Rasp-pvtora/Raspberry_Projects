# Threat Model — Local LLM PrivateGPT

## Overview

This document identifies threats to the Local LLM PrivateGPT system and describes mitigations.
The system runs **fully offline** on a Raspberry Pi — no external network calls are made by design.

---

## Threat Matrix

| # | Threat | Severity | Mitigation |
|---|---|---|---|
| T1 | **Credential exposure** — `.env` committed to git | High | `.env` in `.gitignore`; `chmod 600 .env` on Pi; secrets never logged |
| T2 | **Brute-force login** | Medium | Rate limiting: 10 attempts per 15 min per IP; bcrypt hashing |
| T3 | **Session hijacking** | Medium | Strong random `SESSION_SECRET`; `HttpOnly` + `SameSite` cookies; 24h expiry |
| T4 | **Cross-site scripting (XSS)** | Medium | Jinja2 auto-escaping enabled by default; `escapeHtml()` in JS |
| T5 | **SQL injection** | High | All queries use parameterized statements (`?` placeholders) |
| T6 | **Path traversal via upload** | High | `secure_filename()` + extra `..`/separator checks; files stored only in `UPLOAD_DIR` |
| T7 | **Malicious file upload** | Medium | Extension allowlist + magic-byte validation; `MAX_FILE_SIZE_MB` limit |
| T8 | **API abuse** | Medium | Rate limiting; optional API key via `X-API-Key`; input validation |
| T9 | **Data exfiltration** | Low | Fully offline — no outbound network calls; no telemetry |
| T10 | **Prompt injection** | Medium | System prompt hardening; context-only grounding; user input sanitisation |
| T11 | **Disk exhaustion** | Low | `MAX_FILE_SIZE_MB` limit; disk space checked implicitly by OS |
| T12 | **Denial of service (local)** | Low | Single-user system; resource limits via systemd (optional) |

---

## Trust Boundaries

1. **Browser ↔ Flask** — TLS recommended in production (reverse proxy with nginx/caddy).
2. **Flask ↔ Ollama** — Localhost only (`127.0.0.1:11434`).
3. **Flask ↔ ChromaDB** — Embedded, no network surface.
4. **Flask ↔ SQLite** — File-based, no network surface.

---

## Recommendations

- Change `SESSION_SECRET` and `ADMIN_PASSWORD` before first use.
- Use a reverse proxy (nginx, caddy) with TLS for LAN access.
- Review uploaded documents — the system does not scan for malware.
- Keep Ollama and Python dependencies updated.
