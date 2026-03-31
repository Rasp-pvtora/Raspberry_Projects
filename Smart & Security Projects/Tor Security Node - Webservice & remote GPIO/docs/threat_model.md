# Threat Model — Tor Security Node

This document describes the security threats, attack surfaces, and mitigations for the Tor Security Node project.

---

## 1. Assets

| Asset | Confidentiality | Integrity | Availability |
|---|---|---|---|
| Dashboard credentials (username/password in `.env`) | HIGH | HIGH | MEDIUM |
| Session tokens (in-memory session store) | HIGH | HIGH | LOW |
| Tor Hidden Service private key (`hs_ed25519_secret_key`) | CRITICAL | CRITICAL | HIGH |
| `.onion` website content | LOW | HIGH | MEDIUM |
| GPIO pin states (physical hardware control) | MEDIUM | HIGH | MEDIUM |
| System information (temp, IP, processes) | LOW | LOW | LOW |
| `.env` file (all secrets and configuration) | HIGH | HIGH | HIGH |
| File browser access (Pi filesystem) | MEDIUM | HIGH | LOW |

---

## 2. Attack Surface

### 2.1 Network — Dashboard Web Interface (port 3000)

- **Exposure:** LAN (default). Potentially internet if port-forwarded.
- **Protocol:** HTTP (unencrypted by default).
- **Authentication:** Session cookie after username/password login.

### 2.2 Network — Tor Hidden Service (.onion)

- **Exposure:** Tor network only (via `.onion` address).
- **Protocol:** HTTP/HTTPS over Tor (end-to-end encrypted by Tor).
- **Authentication:** None (public website).

### 2.3 Network — Tor Access Point (WiFi)

- **Exposure:** Anyone within WiFi range who knows the passphrase.
- **Protocol:** WPA2 WiFi + Tor transparent proxy.

### 2.4 Physical — Raspberry Pi Hardware

- **Exposure:** Physical access to the Pi.
- **Components:** GPIO pins, storage (microSD), network ports.

### 2.5 Local — Filesystem

- **Exposure:** File browser API, `.env` file, Tor keys.

---

## 3. Threats and Mitigations

### T1 — Brute-force login attack

| | |
|---|---|
| **Threat** | Attacker repeatedly guesses the dashboard password. |
| **Likelihood** | HIGH if dashboard is exposed to the internet. |
| **Impact** | Full dashboard access, including GPIO, services, and settings. |
| **Mitigation** | express-rate-limit: 10 attempts per 15 minutes on `/auth/login`. Strong password required (documented). |

### T2 — Session hijacking

| | |
|---|---|
| **Threat** | Attacker steals the session cookie via network sniffing or XSS. |
| **Likelihood** | MEDIUM on unencrypted HTTP. LOW on HTTPS. |
| **Impact** | Full dashboard access without knowing the password. |
| **Mitigation** | `httpOnly` and `sameSite` cookie flags prevent JavaScript access and CSRF. Helmet CSP headers mitigate XSS. HTTPS recommended for production. |

### T3 — Path traversal (file browser)

| | |
|---|---|
| **Threat** | Attacker crafts a request like `/api/files/read?path=../../../etc/shadow` to read files outside the allowed root. |
| **Likelihood** | HIGH if not mitigated. |
| **Impact** | Read sensitive system files (passwords, keys, configs). |
| **Mitigation** | All file paths are resolved with `path.resolve()` and checked with `startsWith(FILE_BROWSER_ROOT)`. Requests outside the root return an error. Same protection applied to the website file editor (`TOR_WEBSITE_DIR`). |

### T4 — Service injection

| | |
|---|---|
| **Threat** | Attacker sends a request to `/api/system/service` with a malicious service name to execute arbitrary commands. |
| **Likelihood** | HIGH if not mitigated. |
| **Impact** | Arbitrary command execution as root (via `sudo systemctl`). |
| **Mitigation** | Service names are whitelisted: only `tor`, `nginx`, `hostapd`, `dnsmasq` are allowed. Actions are whitelisted: only `start`, `stop`, `restart`. |

### T5 — Tor Hidden Service key compromise

| | |
|---|---|
| **Threat** | Attacker gains access to `hs_ed25519_secret_key` and impersonates the `.onion` site. |
| **Likelihood** | LOW (requires Pi filesystem access). |
| **Impact** | CRITICAL — attacker controls the `.onion` identity permanently. |
| **Mitigation** | Key directory owned by `debian-tor` with `chmod 700`. Keys never exposed through the dashboard API. Backup keys to encrypted offline storage. |

### T6 — GPIO abuse

| | |
|---|---|
| **Threat** | Unauthorized user controls GPIO pins connected to relays, motors, or other hardware. |
| **Likelihood** | MEDIUM (requires dashboard access). |
| **Impact** | Physical damage or unauthorized hardware activation. |
| **Mitigation** | All GPIO API endpoints require authentication. Pin numbers are validated against the known 40-pin layout. Only configured pins can be read/written. |

### T7 — `.env` file exposure

| | |
|---|---|
| **Threat** | `.env` file (containing passwords, session secret) is committed to git or read by an unauthorized user. |
| **Likelihood** | MEDIUM. |
| **Impact** | Full credential disclosure. |
| **Mitigation** | `.env` is in `.gitignore`. Settings API masks passwords in responses. `chmod 600 .env` recommended. |

### T8 — Cross-Site Scripting (XSS)

| | |
|---|---|
| **Threat** | Attacker injects malicious JavaScript through file content or settings values. |
| **Likelihood** | LOW (EJS auto-escapes output). |
| **Impact** | Session theft, page manipulation. |
| **Mitigation** | EJS auto-escaping on all rendered values. Helmet CSP restricts script sources. `X-Content-Type-Options: nosniff` prevents MIME sniffing. |

### T9 — Network sniffing of dashboard traffic

| | |
|---|---|
| **Threat** | Attacker on the same LAN captures dashboard HTTP traffic, including login credentials and session cookies. |
| **Likelihood** | MEDIUM on shared networks. |
| **Impact** | Credential theft, session hijacking. |
| **Mitigation** | Use HTTPS (self-signed cert or Nginx reverse proxy with TLS) in production. Dashboard should only be accessed on trusted networks. |

### T10 — Physical access to the Pi

| | |
|---|---|
| **Threat** | Attacker physically accesses the Raspberry Pi, removes the SD card, or modifies hardware. |
| **Likelihood** | Depends on physical environment. |
| **Impact** | Full compromise — all keys, data, and configuration exposed. |
| **Mitigation** | Physical security (locked enclosure). Full-disk encryption (LUKS) for high-threat scenarios. |

---

## 4. Security Controls Summary

| Control | Implementation |
|---|---|
| Authentication | Session-based login with credentials from `.env` |
| Rate limiting | 10 login attempts per 15 minutes |
| Session security | `httpOnly`, `sameSite=lax`, configurable `maxAge` |
| HTTP security headers | Helmet (CSP, X-Frame-Options, X-Content-Type-Options, etc.) |
| Path traversal protection | `path.resolve()` + `startsWith()` validation |
| Service whitelisting | Only `tor`, `nginx`, `hostapd`, `dnsmasq` allowed |
| Action whitelisting | Only `start`, `stop`, `restart` allowed for services |
| GPIO validation | Pin numbers validated against known layout |
| Password masking | Settings API never returns plaintext passwords |
| File gitignore | `.env`, `node_modules`, `tor-data`, `sessions` excluded |
| Input validation | Request body validation on all POST/PUT endpoints |

---

## 5. Recommendations

1. **Always use HTTPS** in production — add an Nginx reverse proxy with a self-signed or Let's Encrypt certificate.
2. **Change default credentials immediately** after deployment.
3. **Generate a strong session secret** — never use the default.
4. **Restrict network access** — use `ufw` to allow only SSH and port 3000 from trusted IPs.
5. **Monitor logs** — check `journalctl -u tor-security-node` for suspicious activity.
6. **Keep software updated** — regularly run `apt update && apt upgrade` and `npm audit fix`.
7. **Physical security** — secure the Pi in a locked enclosure if GPIO controls critical hardware.
8. **Backup Tor keys** — store Hidden Service keys on encrypted offline media in case the SD card fails.
