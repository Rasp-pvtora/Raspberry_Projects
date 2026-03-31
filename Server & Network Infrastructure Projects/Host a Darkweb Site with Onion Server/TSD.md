# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for the **Host a Darkweb Site with Onion Server** project.

---

## 1. Scope

This project configures a Raspberry Pi to host a web server that is accessible exclusively through the Tor network via a `.onion` (v3) Hidden Service address. The server is hardened to prevent any clearnet exposure, uses a static site generator to minimize attack surface, and includes optional vanity address generation, TLS over onion, and monitoring.

---

## 2. Minimum Viable Features (MVP)

- **Tor Hidden Service configuration:**
  - Install and configure the Tor daemon to expose a v3 Hidden Service.
  - Generate the `.onion` address and private key automatically.
  - Configure `HiddenServiceDir` and `HiddenServicePort` in `torrc`.

- **Nginx web server (localhost-only):**
  - Install Nginx and bind it exclusively to `127.0.0.1` to prevent clearnet exposure.
  - Disable server version disclosure (`server_tokens off`) and add security headers.
  - Serve static HTML content from `/var/www/onion-site`.

- **Onion-only hardening:**
  - Verify Nginx is not listening on `0.0.0.0` or any external interface.
  - Configure iptables to drop all non-local inbound traffic except SSH.
  - Remove the default Nginx site.
  - Persist firewall rules with `iptables-persistent`.

- **Vanity .onion address generation:**
  - Build `mkp224o` from source to generate a v3 onion address with a custom prefix.
  - Document prefix length vs. computation time tradeoffs.
  - Replace the auto-generated keys with the vanity keys.

- **HTTPS over .onion (self-signed TLS):**
  - Generate a self-signed TLS certificate with the `.onion` address as the CN.
  - Configure Nginx to serve HTTPS on `127.0.0.1:443`.
  - Update Tor port mapping to route through the HTTPS port.
  - Provides defense in depth beyond Tor's built-in encryption.

- **Static site deployment with Hugo:**
  - Install Hugo as the static site generator.
  - Create a site, add a theme, build to `/var/www/onion-site`.
  - Eliminates all server-side code execution risks (no PHP, no CGI, no dynamic content).

- **Monitoring and logging:**
  - Install and configure `fail2ban` with an Nginx jail.
  - Document access log monitoring commands.
  - Document privacy implications of logging on a Hidden Service.

- **Legal disclaimer and responsible use documentation:**
  - Clearly state the educational purpose of the project.
  - Document the legality of running Tor Hidden Services.
  - Emphasize legal compliance with local laws.

---

## 3. Nice-to-Have Features

- **Full-disk encryption:**
  - Encrypt the Pi's storage (LUKS) so that physical seizure does not expose the Hidden Service keys or site content. Requires manual passphrase entry on each boot or a remote unlock mechanism.

- **Onion load balancing:**
  - Run multiple backend servers behind the same `.onion` address using Tor's `HiddenServicePort` with multiple targets or a reverse proxy for high availability.

- **CMS integration:**
  - Use a flat-file CMS (e.g., Grav) that does not require a database but provides a web-based editor. This introduces server-side code and increases attack surface, so it is optional.

- **Automated uptime monitoring:**
  - A cron job or external Tor-based monitor that periodically checks the `.onion` address and sends an alert (e.g., email or Telegram notification) if the site is down.

---

## 4. High-level Architecture

```
          Tor Network
              │
              ▼
     ┌────────────────┐
     │   Tor Daemon    │
     │  (Hidden Svc)   │
     │                 │
     │  .onion:80 ─────┼──► 127.0.0.1:443 (Nginx HTTPS)
     └────────────────┘            │
              │                    ▼
              │          /var/www/onion-site/
              │          (Hugo static files)
              │
   ┌──────────┴──────────┐
   │   iptables firewall  │
   │  DROP all non-local  │
   │  ACCEPT SSH (LAN)    │
   └──────────────────────┘
```

**Data flow:**

1. Visitor opens the `.onion` address in Tor Browser.
2. The request travels through Tor circuits to the Pi's Tor daemon.
3. Tor forwards the request to `127.0.0.1:443` (Nginx).
4. Nginx serves the static site over HTTPS.
5. The response travels back through Tor to the visitor.

**Key principle:** At no point is the web server reachable from the clearnet. All communication passes exclusively through the Tor network.

---

## 5. Security and Threat Model

**Primary assets:**
- Hidden Service private key (`hs_ed25519_secret_key`) — identity of the `.onion` site.
- Site content — whatever is published.
- Server anonymity — the Pi's real IP must never be exposed.

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Clearnet exposure of the server | Bind Nginx to `127.0.0.1` only; iptables DROP all non-local inbound traffic |
| Hidden Service key theft | File permissions (`chmod 600`); owned by `debian-tor`; consider full-disk encryption |
| Server-side code execution (RCE) | Use Hugo static site — no server-side code to exploit |
| Information disclosure via headers | `server_tokens off`; remove `X-Powered-By`; add security headers |
| DDoS against the Hidden Service | Tor has built-in rate limiting; fail2ban for application-layer protection |
| Traffic correlation attacks | Operational security — do not access the `.onion` site from the same network as the Pi without Tor |
| Physical seizure of the Pi | Full-disk encryption (nice-to-have); offline backups of keys |
| Brute-force attacks on SSH | fail2ban SSH jail; key-based authentication only; disable password login |

**Operational guidance:**
- Never SSH into the Pi and browse to your own `.onion` site from the same session without Tor.
- Do not link your `.onion` address to your real identity unless intentional.
- Regular updates: `sudo apt update && sudo apt upgrade`.
- Backup the Hidden Service keys to an encrypted offline medium.

---

## 6. Suggested Tech Stack

| Tool | Purpose |
|---|---|
| Raspberry Pi OS (Lite) | Operating system (headless) |
| `tor` | Tor daemon providing the Hidden Service |
| `nginx` | Lightweight web server (localhost-only) |
| `openssl` | Self-signed TLS certificate generation |
| `mkp224o` | Vanity v3 `.onion` address generator |
| `hugo` | Static site generator |
| `fail2ban` | Intrusion prevention (brute-force protection) |
| `iptables` / `iptables-persistent` | Firewall |
| `systemd` | Service management |

---

## 7. Development Phases & Concrete Steps

### Phase A — Base setup (Day 1)

1. Flash Raspberry Pi OS Lite and enable SSH.
2. Update the system.
3. Install Tor and Nginx.
4. Create the site directory and a placeholder `index.html`.
5. Configure Nginx to listen on `127.0.0.1:80` only.
6. Configure Tor Hidden Service in `torrc`.
7. Start both services and verify the `.onion` address works in Tor Browser.

### Phase B — Hardening (Day 1–2)

1. Configure iptables to block all non-local inbound traffic (except SSH).
2. Persist firewall rules.
3. Verify Nginx is not accessible from the clearnet.
4. Remove default Nginx site.
5. Add security headers to Nginx config.

### Phase C — Enhancements (Day 2–3)

1. Build `mkp224o` and generate a vanity `.onion` address.
2. Replace the auto-generated keys with vanity keys.
3. Generate a self-signed TLS certificate.
4. Configure HTTPS in Nginx and update Tor port mapping.
5. Install Hugo and deploy a static site.
6. Install and configure fail2ban.

### Phase D — Documentation and polish

1. Write the legal disclaimer section.
2. Document all configuration steps in README.md.
3. Test the complete setup from scratch on a fresh Pi.

---

## 8. Deliverables

- Working Tor Hidden Service with a v3 `.onion` address.
- Hardened Nginx web server (localhost-only, security headers, no version disclosure).
- iptables firewall blocking all non-local traffic.
- Optional vanity `.onion` address.
- HTTPS over onion with self-signed TLS.
- Hugo static site deployed.
- fail2ban monitoring.
- `README.md` with full setup guide.
- `TSD.md` (this document).

---

## 9. Open Questions

- Do you want to host dynamic content (e.g., a blog with comments) or purely static pages?
- Is full-disk encryption needed for your threat model?
- Do you plan to publish the `.onion` address publicly or keep it private?
- Do you need automated backups of the Hidden Service keys?
