# Host a Darkweb Site with Onion Server

Configure a Raspberry Pi to host a website accessible exclusively through the Tor network via a `.onion` address. Includes a hardened Nginx web server, optional vanity address generation, TLS over onion, static site deployment, and monitoring.

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Important disclaimer](#important-disclaimer)
4. [Quickstart — Set up the Onion server](#quickstart--set-up-the-onion-server)
5. [Install and configure Nginx](#install-and-configure-nginx)
6. [Configure Tor Hidden Service](#configure-tor-hidden-service)
7. [Access your .onion site](#access-your-onion-site)
8. [Onion-only hardening](#onion-only-hardening)
9. [Generate a vanity .onion address](#generate-a-vanity-onion-address)
10. [Add HTTPS over .onion (self-signed TLS)](#add-https-over-onion-self-signed-tls)
11. [Deploy a static site with Hugo](#deploy-a-static-site-with-hugo)
12. [Monitoring and logging](#monitoring-and-logging)
13. [Security notes](#security-notes)
14. [Troubleshooting](#troubleshooting)
15. [Where to next](#where-to-next)

---

## Project structure

```
.
├── README.md           ← This file
├── TSD.md              ← Technical Specification Description
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 3B+ / 4 / 5 | Yes | Any model with Ethernet support |
| microSD card (16 GB+) | Yes | For the OS and site content |
| Ethernet cable | Recommended | More reliable than WiFi for a server |
| Power supply (official) | Yes | 5V 3A for Pi 4/5 |

---

## Important disclaimer

> **This project is for educational and privacy research purposes only.**
>
> Hosting a Tor Hidden Service is **legal** in most jurisdictions. However, the content you host and the services you provide must comply with the laws of your country.
>
> The Tor network exists to protect privacy and enable free speech. It is widely used by journalists, activists, whistleblowers, and privacy-conscious individuals.
>
> **Do not use this project for illegal purposes.** The authors take no responsibility for misuse. Understand the legal implications in your jurisdiction before proceeding.

---

## Quickstart — Set up the Onion server

**1. Update the system**

```bash
sudo apt update && sudo apt upgrade -y
```

**2. Install Tor**

```bash
sudo apt install tor -y
```

**3. Install Nginx**

```bash
sudo apt install nginx -y
```

**4. Configure and start (see detailed sections below)**

After following the configuration steps, your site will be available at:

```
http://your-onion-address.onion
```

Accessible only through the Tor Browser or a Tor-connected client.

---

## Install and configure Nginx

**1. Create a directory for your site**

```bash
sudo mkdir -p /var/www/onion-site
sudo chown www-data:www-data /var/www/onion-site
```

**2. Create a simple index page**

```bash
sudo nano /var/www/onion-site/index.html
```

Paste:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My Onion Site</title>
</head>
<body>
    <h1>Welcome to my Onion Site</h1>
    <p>This site is accessible only through the Tor network.</p>
</body>
</html>
```

**3. Configure Nginx to listen only on localhost**

```bash
sudo nano /etc/nginx/sites-available/onion-site
```

Paste:

```nginx
server {
    listen 127.0.0.1:80;
    server_name localhost;

    root /var/www/onion-site;
    index index.html;

    # Disable server version disclosure
    server_tokens off;

    # Remove identifying headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;

    location / {
        try_files $uri $uri/ =404;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
    }
}
```

**4. Enable the site**

```bash
sudo ln -s /etc/nginx/sites-available/onion-site /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## Configure Tor Hidden Service

**1. Edit the Tor configuration**

```bash
sudo nano /etc/tor/torrc
```

Find the Hidden Service section and add:

```
HiddenServiceDir /var/lib/tor/onion-site/
HiddenServicePort 80 127.0.0.1:80
```

**2. Restart Tor**

```bash
sudo systemctl restart tor
```

**3. Get your .onion address**

```bash
sudo cat /var/lib/tor/onion-site/hostname
```

This outputs a v3 `.onion` address (56 characters + `.onion`), for example:

```
abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567ab.onion
```

**4. Save this address — it is your site's URL.**

---

## Access your .onion site

1. Download and install the [Tor Browser](https://www.torproject.org/download/).
2. Open the Tor Browser and navigate to your `.onion` address.
3. Your site should appear.

> **Note:** The first connection may take 30–60 seconds while Tor establishes circuits.

---

## Onion-only hardening

Ensure the web server is **never** accessible from the clearnet (regular internet).

**1. Bind Nginx exclusively to localhost**

Already done in the configuration above (`listen 127.0.0.1:80`). Verify:

```bash
sudo ss -tlnp | grep nginx
```

Should show only `127.0.0.1:80`, NOT `0.0.0.0:80`.

**2. Block all external traffic with iptables**

```bash
# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT
# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
# Allow SSH (so you can still manage the Pi)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
# Drop everything else from external sources
sudo iptables -A INPUT -j DROP
```

Persist the rules:

```bash
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

**3. Disable unnecessary Nginx headers**

Already configured with `server_tokens off` and security headers in the Nginx config above.

**4. Remove default Nginx page**

```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

---

## Generate a vanity .onion address

By default, Tor generates a random `.onion` address. Use `mkp224o` to generate a v3 address with a custom prefix (e.g., `mysite...`).

> **Note:** Longer prefixes take exponentially longer to compute. 5–6 characters is practical on a Pi; longer prefixes may take days or weeks.

**1. Install build dependencies**

```bash
sudo apt install gcc libsodium-dev make autoconf -y
```

**2. Clone and build mkp224o**

```bash
cd /tmp
git clone https://github.com/cathugger/mkp224o.git
cd mkp224o
./autogen.sh
./configure
make
```

**3. Generate a vanity address**

```bash
./mkp224o mysite -n 1 -d /tmp/vanity-keys
```

This generates one key pair with an address starting with `mysite`. Output goes to `/tmp/vanity-keys/`.

**4. Replace the Tor Hidden Service keys**

```bash
sudo systemctl stop tor

# Back up the existing keys
sudo cp -r /var/lib/tor/onion-site/ /var/lib/tor/onion-site.bak/

# Copy the vanity keys
sudo cp /tmp/vanity-keys/mysite*/hs_ed25519_secret_key /var/lib/tor/onion-site/
sudo cp /tmp/vanity-keys/mysite*/hs_ed25519_public_key /var/lib/tor/onion-site/
sudo cp /tmp/vanity-keys/mysite*/hostname /var/lib/tor/onion-site/

# Fix ownership
sudo chown -R debian-tor:debian-tor /var/lib/tor/onion-site/
sudo chmod 700 /var/lib/tor/onion-site/
sudo chmod 600 /var/lib/tor/onion-site/hs_ed25519_secret_key

sudo systemctl start tor
```

**5. Verify the new address**

```bash
sudo cat /var/lib/tor/onion-site/hostname
```

**6. Clean up the temporary vanity keys**

```bash
rm -rf /tmp/vanity-keys /tmp/mkp224o
```

---

## Add HTTPS over .onion (self-signed TLS)

While Tor already provides end-to-end encryption, adding TLS provides defense in depth and prevents certain advanced attacks.

**1. Generate a self-signed certificate**

```bash
sudo mkdir -p /etc/nginx/ssl
ONION_ADDR=$(sudo cat /var/lib/tor/onion-site/hostname)
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/onion.key \
    -out /etc/nginx/ssl/onion.crt \
    -subj "/CN=$ONION_ADDR"
```

**2. Update Nginx to serve HTTPS**

```bash
sudo nano /etc/nginx/sites-available/onion-site
```

Replace the server block:

```nginx
server {
    listen 127.0.0.1:443 ssl;
    server_name localhost;

    ssl_certificate     /etc/nginx/ssl/onion.crt;
    ssl_certificate_key /etc/nginx/ssl/onion.key;

    root /var/www/onion-site;
    index index.html;

    server_tokens off;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ /\. {
        deny all;
    }
}
```

**3. Update Tor to point to port 443**

```bash
sudo nano /etc/tor/torrc
```

Change:

```
HiddenServicePort 80 127.0.0.1:443
```

> This maps the visitor's port 80 to your local HTTPS port 443. Alternatively, use `HiddenServicePort 443 127.0.0.1:443` for native HTTPS.

**4. Restart both services**

```bash
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl restart tor
```

---

## Deploy a static site with Hugo

Using a static site generator eliminates server-side code execution risks entirely.

**1. Install Hugo**

```bash
sudo apt install hugo -y
```

If the version in apt is too old:

```bash
# Download the latest release for ARM
wget https://github.com/gohugoio/hugo/releases/download/v0.139.0/hugo_0.139.0_linux-arm64.deb
sudo dpkg -i hugo_0.139.0_linux-arm64.deb
```

**2. Create a new Hugo site**

```bash
hugo new site /home/pi/onion-site-source
cd /home/pi/onion-site-source
```

**3. Add a theme and create content**

```bash
git init
git submodule add https://github.com/theNewDynamic/gohugo-theme-ananke themes/ananke
echo 'theme = "ananke"' >> hugo.toml
hugo new content posts/hello.md
```

Edit `content/posts/hello.md` with your content.

**4. Build and deploy**

```bash
hugo --destination /var/www/onion-site
sudo chown -R www-data:www-data /var/www/onion-site
```

**5. To update the site, repeat the build command:**

```bash
hugo --destination /var/www/onion-site
```

---

## Monitoring and logging

**1. Install fail2ban**

```bash
sudo apt install fail2ban -y
```

Create a jail for Nginx:

```bash
sudo nano /etc/fail2ban/jail.local
```

```ini
[nginx-http-auth]
enabled = true
port    = http,https
filter  = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 3600
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**2. Monitor Nginx access logs**

```bash
sudo tail -f /var/log/nginx/access.log
```

**3. Monitor Tor service status**

```bash
sudo systemctl status tor
journalctl -u tor -f
```

**4. Check Hidden Service availability**

From a machine with Tor Browser, periodically visit your `.onion` address to verify uptime.

> **Privacy warning:** Be careful with logging. Access logs on a Hidden Service could potentially be used to correlate visitors. Consider disabling access logging if maximum privacy is required:

```nginx
access_log off;
```

---

## Security notes

- **Never expose the web server to the clearnet.** Nginx must listen only on `127.0.0.1`. Use iptables to block all non-local traffic.
- **Protect the Hidden Service private key** (`hs_ed25519_secret_key`). Anyone with this key can impersonate your `.onion` site. Keep backups encrypted and offline.
- **Disable server information disclosure.** Use `server_tokens off` and remove any headers that reveal the software version.
- **Use a static site** to eliminate server-side code execution vulnerabilities (XSS, injection, RCE).
- **Keep Tor and Nginx updated.** Regularly run `sudo apt update && sudo apt upgrade`.
- **Firewall the Pi.** Allow only SSH from your LAN and block all other inbound connections.
- **Be cautious with logging.** Excessive logging on a Hidden Service can create privacy risks.
- **Physical security:** If the Pi is seized, the Hidden Service keys and site content are accessible. Consider full-disk encryption for high-threat scenarios.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `.onion` address not loading | Check Tor status: `sudo systemctl status tor`. Wait 1–2 minutes after restart for circuits to establish. |
| `sudo cat hostname` shows nothing | Tor may have failed to start. Check `journalctl -u tor -e` for errors. |
| Nginx returns 502/404 | Verify Nginx config: `sudo nginx -t`. Ensure the root path exists and has correct permissions. |
| Site accessible from clearnet | Check Nginx is NOT listening on `0.0.0.0`: `sudo ss -tlnp \| grep nginx`. Fix `listen` directive. |
| Vanity address generation is too slow | Reduce prefix length. 5–6 characters is practical on a Pi. |
| Permission denied on Tor directory | Run `sudo chown -R debian-tor:debian-tor /var/lib/tor/onion-site/` and `sudo chmod 700 /var/lib/tor/onion-site/`. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- [Tor Project Documentation](https://community.torproject.org/onion-services/setup/) — official Hidden Service setup guide.
- [Tor Project FAQ](https://support.torproject.org/) — frequently asked questions.
