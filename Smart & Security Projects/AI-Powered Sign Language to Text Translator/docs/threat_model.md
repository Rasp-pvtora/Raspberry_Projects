# Threat Model — AI-Powered Sign Language to Text Translator

## Overview

This document describes the security threats, attack surface, and mitigations for the Sign Language Translator system deployed on Raspberry Pi.

---

## Assets

| Asset | Sensitivity | Description |
|---|---|---|
| Camera feed | High | Live video of users' hands and surroundings |
| Admin credentials | High | Username/password for web dashboard |
| Session secret | High | Flask session encryption key |
| Recognition data | Medium | Sign labels, sentences, timestamps |
| Learning progress | Low | User practice stats |
| LSTM model | Low | Trained model weights |

---

## Threat Matrix

| # | Threat | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| T1 | **Credential exposure** — `.env` file leaked | High | Medium | `.env` in `.gitignore`, `chmod 600 .env` on Pi |
| T2 | **Brute-force login** — automated password guessing | Medium | High | Rate limiting (10 attempts / 15 min) |
| T3 | **Camera privacy** — unauthorized video access | High | Low | Local network only, no cloud upload, no recording by default |
| T4 | **Cross-site scripting (XSS)** — injected scripts in UI | Medium | Low | Jinja2 auto-escaping enabled by default |
| T5 | **Kiosk escape** — public user accessing admin functions | Medium | Medium | Kiosk mode: no navigation, no settings, no login |
| T6 | **Session hijacking** — stolen session cookie | Medium | Low | Secure session secret, session expiry (24h) |
| T7 | **WebSocket abuse** — excessive connections | Low | Medium | Single recognition loop, no per-user state |
| T8 | **Model poisoning** — tampered training data | Medium | Low | Data collection disabled by default, manual training only |
| T9 | **Denial of service** — CPU overload from MediaPipe | Low | Medium | Single camera, fixed FPS, no user-uploaded video |
| T10 | **Physical access** — someone accesses the Pi directly | High | Low | Standard OS hardening, SSH key auth recommended |

---

## Network Diagram

```
[Camera] → [Raspberry Pi] → [Local WiFi]
                │
                ├── Flask (port 5000) ← [Browser on same network]
                ├── SQLite (local file)
                └── Piper TTS (local audio)
```

**No external network access required.** All processing is local.

---

## Recommendations

1. **Change default credentials** immediately after deployment.
2. **Generate a strong `SESSION_SECRET`**: `python -c "import secrets; print(secrets.token_hex(32))"`.
3. **Restrict network access**: use firewall rules to limit port 5000 to trusted devices.
4. **Enable HTTPS** if deploying on untrusted networks (reverse proxy with nginx + Let's Encrypt).
5. **Disable SSH password auth** — use key-based authentication.
6. **Keep system updated**: `sudo apt update && sudo apt upgrade`.
7. **Monitor logs**: check Flask and systemd logs for unusual access patterns.
