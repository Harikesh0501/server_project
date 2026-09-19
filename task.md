# Production Engineering Master Task Breakdown (WBS)
## Project: 100% Self-Hosted Universal Cloud Deployment Platform (Vercel + Render Sovereign Cloud Engine)

> **Architectural Objective**: Build a complete, production-grade, bare-metal / Linux-hosted private cloud platform that unifies Vercel-style frontend hosting, Render-style containerized web services, managed databases, dynamic horizontal autoscaling (3 to 10+ replicas), zero-trust security, and local AI diagnostics on our own dedicated server with **$0 cloud fees and zero third-party dependencies**.

---

## 🧭 Master Phase & Epic Directory

| Epic ID | Engineering Epic Title | Total Tasks | Total Mini-Tasks | Status |
| :--- | :--- | :---: | :---: | :---: |
| **EPIC-00** | Bare-Metal Laptop to Linux Server: OS, Firmware & Network Setup | 7 Tasks | 37 Mini-Tasks | 📝 Planned |
| **EPIC-01** | Linux Host Kernel Hardening, cgroups v2, Systemd & Core Runtime | 5 Tasks | 22 Mini-Tasks | 📝 Planned |
| **EPIC-02** | Host Network Topology, Private Bridge, Firewall & Edge Caddy Ingress | 5 Tasks | 24 Mini-Tasks | 📝 Planned |
| **EPIC-03** | Local Private Container Registry & BuildKit Sandbox Engine | 4 Tasks | 19 Mini-Tasks | 📝 Planned |
| **EPIC-04** | Zero-Trust Secrets Vault, In-Memory Injection & `.env` Quarantine | 4 Tasks | 19 Mini-Tasks | ✅ Completed |
| **EPIC-05** | Universal 3-Tier Polyglot Detection & Buildpack Compiler | 5 Tasks | 26 Mini-Tasks | 📝 Planned |
| **EPIC-06** | FastAPI Control Plane Core, Database Schemas & Docker Engine API | 6 Tasks | 33 Mini-Tasks | ✅ Completed |
| **EPIC-07** | Asynchronous Job Queue, Worker Daemons & Task Orchestration | 4 Tasks | 18 Mini-Tasks | 📝 Planned |
| **EPIC-08** | Zero-Downtime Blue-Green Deployment & Health Verification Engine | 5 Tasks | 25 Mini-Tasks | 📝 Planned |
| **EPIC-09** | Dynamic Horizontal Autoscaler Daemon (HPA) & Real-Time Metrics | 5 Tasks | 23 Mini-Tasks | 📝 Planned |
| **EPIC-10** | Render-Style Managed Databases (PostgreSQL 16 & Redis 7) Engine | 4 Tasks | 20 Mini-Tasks | 📝 Planned |
| **EPIC-11** | Authentication & Identity Provider (OAuth 2.0 + Offline Local Admin) | 5 Tasks | 24 Mini-Tasks | 📝 Planned |
| **EPIC-12** | Self-Hosted AI Diagnostic Engine (`deploy doctor` with Ollama) | 4 Tasks | 19 Mini-Tasks | 📝 Planned |
| **EPIC-13** | Universal CLI Client Engineering (TypeScript / Node.js) | 6 Tasks | 36 Mini-Tasks | 📝 Planned |
| **EPIC-14** | Next.js 16 Production Management Console (App Router + React 19) | 6 Tasks | 31 Mini-Tasks | 📝 Planned |
| **EPIC-15** | Server Production Packaging, Bootstrap Installer & Disaster Recovery | 4 Tasks | 20 Mini-Tasks | 📝 Planned |
| **EPIC-16** | Commercial Product Engine: Multi-Tenancy, Enterprise Licensing & Turnkey Appliance | 6 Tasks | 24 Mini-Tasks | 📝 Planned |
| **TOTAL** | **17 Core Engineering Epics** | **85 Tasks** | **420 Mini-Tasks** | **0% Complete** |

---

## EPIC-00: Bare-Metal Laptop to Linux Server: OS, Firmware & Network Setup

### Task 0.1: Ubuntu 24.04 LTS ISO Acquisition & Bootable USB Drive Flashing
- [ ] **Mini-Task 0.1.1**: Download official Ubuntu Server 24.04 LTS ISO (`ubuntu-24.04-live-server-amd64.iso`) and verify SHA256 checksum against official Canonical release hash.
- [ ] **Mini-Task 0.1.2**: Prepare dedicated USB flash drive (minimum 8 GB) and launch Rufus (Windows) or balenaEtcher.
- [ ] **Mini-Task 0.1.3**: Flash ISO image to USB drive using GPT partition scheme, UEFI target system, and write in DD image mode.
- [ ] **Mini-Task 0.1.4**: Verify USB drive write integrity and create ready-to-boot physical installation media.

### Task 0.2: Laptop Hardware, Firmware & BIOS/UEFI Server Tuning
- [ ] **Mini-Task 0.2.1**: Connect friend's laptop to dedicated AC power adapter (disable battery saving) and attach Ethernet LAN cable (or configure Wi-Fi).
- [ ] **Mini-Task 0.2.2**: Power on laptop and press BIOS/UEFI hotkey (`F2`, `F10`, `F12`, or `Del` depending on laptop manufacturer: Dell, HP, Lenovo, Asus, Acer).
- [ ] **Mini-Task 0.2.3**: Enable Hardware Virtualization (Intel VT-x / AMD-V / SVM Mode) in CPU configuration to support Docker container cgroups and nested virtualization.
- [ ] **Mini-Task 0.2.4**: Configure "Power On on AC / Restore AC Power Loss" in BIOS Power Management so laptop boots automatically when plugged into wall power.
- [ ] **Mini-Task 0.2.5**: Set USB flash drive as First Boot Priority in UEFI boot order and disable Secure Boot if third-party kernel modules/drivers are required.
- [ ] **Mini-Task 0.2.6**: Save BIOS settings (`F10`) and boot into Ubuntu Server installer GRUB menu.

### Task 0.3: Ubuntu Server 24.04 LTS Automated Installation & Storage Partitioning
- [ ] **Mini-Task 0.3.1**: Select "Ubuntu Server (minimized)" installation without desktop GUI to save RAM and CPU overhead for platform workloads.
- [ ] **Mini-Task 0.3.2**: Configure network interface during install (obtain DHCP IP or set static IPv4).
- [ ] **Mini-Task 0.3.3**: Configure guided storage partitioning: select primary SSD/NVMe drive, format with `ext4` filesystem root (`/`), and setup swapfile space.
- [ ] **Mini-Task 0.3.4**: Configure server identity: hostname (e.g. `deploy-server`), username (e.g. `deployadmin`), and strong administrator password.
- [ ] **Mini-Task 0.3.5**: Check "Install OpenSSH Server" and import GitHub/local SSH public keys directly during installer wizard.
- [ ] **Mini-Task 0.3.6**: Skip third-party snaps to keep OS clean and minimal, complete package installation, remove USB drive upon prompt, and reboot into Linux.

### Task 0.4: Laptop Lid-Close Sleep Prevention & Power Management Hardening
- [ ] **Mini-Task 0.4.1**: Modify `/etc/systemd/logind.conf` to set `HandleLidSwitch=ignore`, `HandleLidSwitchExternalPower=ignore`, and `HandleLidSwitchDocked=ignore`.
- [ ] **Mini-Task 0.4.2**: Mask systemd sleep and suspend targets: `sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target`.
- [ ] **Mini-Task 0.4.3**: Restart systemd-logind service (`sudo systemctl restart systemd-logind`) and test closing the laptop lid physically to verify server stays fully operational.
- [ ] **Mini-Task 0.4.4**: Set CPU power governor to `performance` or `powersave` using `cpupower` or `tuned` to prevent thermal throttling and lock maximum clock stability.
- [ ] **Mini-Task 0.4.5**: Configure screen blanking / console DPMS timeout (`consoleblank=300` in `/etc/default/grub`) to shut off laptop display backlight when lid is open/closed to preserve screen lifespan.

### Task 0.5: Network Topology, Static LAN IP & Hostname Resolution   
- [ ] **Mini-Task 0.5.1**: Identify active network interface (`ip -br a` or `ip link`, e.g. `eth0`, `enp3s0`, `wlan0`).
- [ ] **Mini-Task 0.5.2**: Configure router DHCP reservation (bind friend's laptop MAC address to static LAN IP, e.g. `192.168.1.150`), OR configure static IP in `/etc/netplan/01-netcfg.yaml`.
- [ ] **Mini-Task 0.5.3**: Apply netplan settings (`sudo netplan apply`) and verify DNS gateway connectivity (`ping -c 3 1.1.1.1` and `ping -c 3 google.com`).
- [x] **Mini-Task 0.5.4**: Add local domain mapping to Linux `/etc/hosts`: `127.0.0.1 deploy.local api.deploy.local registry.deploy.local`.
- [ ] **Mini-Task 0.5.5**: Configure user's Windows development laptop `C:\Windows\System32\drivers\etc\hosts` to point `deploy.local`, `*.deploy.local` to the server LAN IP (`192.168.1.150`).

### Task 0.6: OpenSSH Server Production Hardening & Windows-to-Linux Key-Based Auth
- [ ] **Mini-Task 0.6.1**: On Windows laptop, generate dedicated ED25519 SSH keypair via PowerShell (`ssh-keygen -t ed25519 -C "admin@deploy-server"`).
- [ ] **Mini-Task 0.6.2**: Copy public key (`id_ed25519.pub`) to Linux server's `~/.ssh/authorized_keys` and set `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`.
- [ ] **Mini-Task 0.6.3**: Configure `/etc/ssh/sshd_config`: disable root login (`PermitRootLogin no`), enforce public key authentication (`PubkeyAuthentication yes`), set `MaxAuthTries 3`.
- [ ] **Mini-Task 0.6.4**: Restart SSH service (`sudo systemctl restart ssh`) and verify passwordless SSH connection from Windows PowerShell (`ssh deployadmin@192.168.1.150`).
- [x] **Mini-Task 0.6.5**: Install and configure `ufw` (Uncomplicated Firewall): allow SSH port 22, HTTP port 80, HTTPS port 443, Docker registry port 5000, and enable UFW (`sudo ufw enable`).

### Task 0.7: Core Platform Toolchain & Container Runtime Installation
- [x] **Mini-Task 0.7.1**: Perform full OS system update and security patching (`sudo apt update && sudo apt upgrade -y && sudo apt install -y curl wget git htop net-tools ca-certificates gnupg lsb-release`).
- [x] **Mini-Task 0.7.2**: Install official Docker Engine CE and Docker Compose v2 via official Docker apt repository (avoid Ubuntu snap Docker).
- [x] **Mini-Task 0.7.3**: Add `deployadmin` user to the `docker` group (`sudo usermod -aG docker deployadmin`) so Docker commands can run without `sudo`.
- [x] **Mini-Task 0.7.4**: Install Python 3.12, `python3-venv`, `python3-pip`, and build-essential packages for FastAPI control plane.
- [x] **Mini-Task 0.7.5**: Install Node.js 22 LTS and npm via NodeSource repository for CLI and frontend build toolchains.
- [x] **Mini-Task 0.7.6**: Install standalone Caddy 2 reverse proxy binary via official Caddy repository (`sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https caddy`).
- [ ] **Mini-Task 0.7.7**: Install local Ollama runtime (`curl -fsSL https://ollama.com/install.sh | sh`) and pull `mistral:7b-instruct` or `deepseek-coder:6.7b` for local AI diagnostic engine.

---

## EPIC-01: Linux Host Kernel Hardening, cgroups v2, Systemd & Core Runtime

### Task 1.1: Host Linux Kernel Tuning & Sysctl Configuration
- [ ] **Mini-Task 1.1.1**: Create `/etc/sysctl.d/99-deploy-platform.conf` for optimizing Linux kernel network and memory parameters.
- [ ] **Mini-Task 1.1.2**: Configure `net.core.somaxconn = 65535` and `net.ipv4.tcp_max_syn_backlog = 65535` to prevent TCP dropouts under high concurrency.
- [ ] **Mini-Task 1.1.3**: Configure `fs.file-max = 2097152` and set system security limits in `/etc/security/limits.d/99-deploy.conf` (nofile 1048576).
- [ ] **Mini-Task 1.1.4**: Enable TCP BBR Congestion Control (`net.core.default_qdisc = fq`, `net.ipv4.tcp_congestion_control = bbr`).
- [ ] **Mini-Task 1.1.5**: Set `vm.max_map_count = 262144` and `vm.overcommit_memory = 1` for PostgreSQL, Redis, and high-memory container support.

### Task 1.2: Unified cgroups v2 Resource Isolation Setup
- [ ] **Mini-Task 1.2.1**: Verify unified cgroup v2 hierarchy is active on Linux host (`/sys/fs/cgroup/cgroup.controllers`).
- [ ] **Mini-Task 1.2.2**: Configure systemd slice `/etc/systemd/system/deploy-platform.slice` with strict resource bounds for system services.
- [ ] **Mini-Task 1.2.3**: Enable CPU, Memory, IO, and PIDs controllers in `cgroup.subtree_control` for sub-processes.
- [ ] **Mini-Task 1.2.4**: Implement PID limits (`pids.max = 500`) per deployed application container to prevent fork-bomb attacks.

### Task 1.3: Docker Engine Daemon Production Hardening
- [ ] **Mini-Task 1.3.1**: Create hardened `/etc/docker/daemon.json` with `log-driver: json-file` and max log-size rotation (`max-size: 50m`, `max-file: 3`).
- [ ] **Mini-Task 1.3.2**: Enable `live-restore: true` to keep application containers running even if the Docker daemon restarts.
- [ ] **Mini-Task 1.3.3**: Configure storage driver explicitly to `overlay2` with native diff validation.
- [ ] **Mini-Task 1.3.4**: Restrict default container bridge (`icc: false`) and disable userland proxy (`userland-proxy: false`) for native iptables performance.
- [ ] **Mini-Task 1.3.5**: Expose Docker daemon metrics endpoint on `127.0.0.1:9323/metrics` for local resource scraping.

### Task 1.4: Dedicated System User & Directory Layout
- [ ] **Mini-Task 1.4.1**: Create unprivileged system user and group `deploy` with fixed UID/GID `10001:10001` (`useradd -r -s /bin/false deploy`).
- [ ] **Mini-Task 1.4.2**: Create base filesystem layout: `/var/lib/deploy/` (data), `/etc/deploy/` (configs), `/var/log/deploy/` (logs), `/var/run/deploy/` (sockets).
- [ ] **Mini-Task 1.4.3**: Set strict POSIX directory permissions (`chmod 750` and `chown -R deploy:deploy /var/lib/deploy`).
- [ ] **Mini-Task 1.4.4**: Configure logrotate rule `/etc/logrotate.d/deploy-platform` for daily log compression and 14-day retention.

### Task 1.5: Local DNS & Host Resolution (CoreDNS / dnsmasq)
- [ ] **Mini-Task 1.5.1**: Deploy lightweight local DNS server (dnsmasq or CoreDNS) listening on `127.0.0.1:53`.
- [ ] **Mini-Task 1.5.2**: Configure wildcard local domain mapping `*.deploy.local` pointing to the host's private or LAN IP address.
- [ ] **Mini-Task 1.5.3**: Configure fallback upstream resolvers in `/etc/dnsmasq.d/upstream.conf` for external domain lookups.
- [ ] **Mini-Task 1.5.4**: Write automated script verifying DNS resolution: `dig test.deploy.local @127.0.0.1`.

---

## EPIC-02: Host Network Topology, Private Bridge, Firewall & Edge Caddy Ingress

### Task 2.1: Isolated Docker Bridge Network Architecture
- [x] **Mini-Task 2.1.1**: Create dedicated Docker bridge network `deploy-private-net` with subnet `172.28.0.0/16` and gateway `172.28.0.1`.
- [ ] **Mini-Task 2.1.2**: Configure internal DNS resolution inside `deploy-private-net` so containers resolve by container name.
- [ ] **Mini-Task 2.1.3**: Verify inter-container communication is restricted: containers can only talk to each other if attached to the same project network.
- [ ] **Mini-Task 2.1.4**: Implement automated cleanup script removing dangling virtual network interfaces (veth pairs) on container deletion.

### Task 2.2: Host Linux Firewall & iptables / nftables Hardening
- [ ] **Mini-Task 2.2.1**: Set default incoming firewall policy to DROP (`ufw default deny incoming` or `iptables -P INPUT DROP`).
- [ ] **Mini-Task 2.2.2**: Allow incoming traffic ONLY on port 22 (SSH), port 80 (HTTP), and port 443 (HTTPS).
- [ ] **Mini-Task 2.2.3**: Block public internet traffic from accessing Docker bridge subnet `172.20.0.0/16` directly.
- [ ] **Mini-Task 2.2.4**: Verify with `nmap` that application ports (3000, 5000, 8000, 8080) and database ports (5432, 6379) are completely filtered from the outside.
- [ ] **Mini-Task 2.2.5**: Configure SYN-flood protection rules in iptables (`limit --limit 25/minute --limit-burst 100`).

### Task 2.3: Caddy 2 Reverse Proxy Edge Gateway Setup
- [x] **Mini-Task 2.3.1**: Deploy Caddy 2 as a dedicated host systemd service or host-networking container (`/etc/caddy/Caddyfile`).
- [x] **Mini-Task 2.3.2**: Enable Caddy Admin API listening strictly on `127.0.0.1:2019` with authentication enabled.
- [x] **Mini-Task 2.3.3**: Configure global Caddy defaults: HTTP/3 (QUIC) enabled, strict TLS 1.3 ciphers, and gzip/zstd compression.
- [ ] **Mini-Task 2.3.4**: Configure dynamic JSON configuration loading endpoint (`POST /load`) for runtime upstream updates without process reload.
- [ ] **Mini-Task 2.3.5**: Configure logging pipeline exporting structured JSON access logs to `/var/log/deploy/caddy_access.log`.

### Task 2.4: Dual TLS Certificate Authority Engine
- [ ] **Mini-Task 2.4.1**: Configure Caddy ACME client for automated Let's Encrypt / ZeroSSL TLS certificates on public FQDNs.
- [ ] **Mini-Task 2.4.2**: Configure Caddy internal Certificate Authority (`tls internal`) for generating trusted local certificates on `*.deploy.local` domains.
- [ ] **Mini-Task 2.4.3**: Export root CA certificate (`/var/lib/deploy/caddy/pki/authorities/local/root.crt`) for easy installation on developer machines.
- [ ] **Mini-Task 2.4.4**: Implement automated certificate expiration monitoring probe checking cert validity weekly.
- [ ] **Mini-Task 2.4.5**: Implement Cloudflare Tunnel (`cloudflared`) integration for instant zero-port-forwarding public worldwide HTTPS live URLs (e.g. `https://my-app.trycloudflare.com` or custom domain).

### Task 2.5: Edge Ingress WAF & Attack Mitigation
- [ ] **Mini-Task 2.5.1**: Implement Caddy route matcher dropping requests containing `/.env*`, `/.git*`, and `*.config*` with HTTP 403 Forbidden.
- [ ] **Mini-Task 2.5.2**: Implement directory traversal filter blocking requests with `../` or encoded traversal sequences (`%2e%2e%2f`).
- [x] **Mini-Task 2.5.3**: Inject mandatory security headers on all reverse-proxied responses:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] **Mini-Task 2.5.4**: Configure request body size limit (default 25 MB) to prevent buffer overflow and memory exhaustion attacks.
- [ ] **Mini-Task 2.5.5**: Implement rate-limiting rules (100 req/sec per IP) with automatic 60-second cool-off ban for abusers.

---

## EPIC-03: Local Private Container Registry & BuildKit Sandbox Engine

### Task 3.1: Host-Local Docker Registry v2 Deployment
- [x] **Mini-Task 3.1.1**: Deploy official `registry:2` container bound strictly to `127.0.0.1:5000` on the host.
- [x] **Mini-Task 3.1.2**: Mount persistent storage volume `/var/lib/deploy/registry` for storing container image blobs and manifests.
- [ ] **Mini-Task 3.1.3**: Configure Registry HTTP API delete enablement (`REGISTRY_STORAGE_DELETE_ENABLED: "true"`).
- [x] **Mini-Task 3.1.4**: Configure `/etc/docker/daemon.json` to trust `127.0.0.1:5000` as an insecure registry for zero-overhead local pushing.
- [ ] **Mini-Task 3.1.5**: Write automated health check testing `GET http://127.0.0.1:5000/v2/` returning HTTP 200.

### Task 3.2: Docker BuildKit Daemon & Sandboxed Compilation
- [ ] **Mini-Task 3.2.1**: Configure BuildKit daemon (`buildkitd`) with dedicated root directory `/var/lib/deploy/buildkit`.
- [ ] **Mini-Task 3.2.2**: Enable BuildKit layer caching (`--export-cache type=local`, `--import-cache type=local`) in build scripts.
- [ ] **Mini-Task 3.2.3**: Configure build container isolation: no host network access, read-only rootfs, and unprivileged user during compilation.
- [ ] **Mini-Task 3.2.4**: Implement strict build resource ceilings: maximum 2.0 vCPU and 2048 MB RAM per build process.
- [ ] **Mini-Task 3.2.5**: Set hard execution timeout watchdog (600 seconds): automatically kill and purge stuck build containers.
- [ ] **Mini-Task 3.2.6**: Implement BuildKit package cache mounts (`--mount=type=cache,target=/root/.npm`, `--mount=type=cache,target=/root/.cache/pip`) ensuring package dependencies (`node_modules`, python wheels) are cached across builds for 3-second rapid redeployments without redownloading.

### Task 3.3: Image Tagging, Registration & Lifecycle Pipeline
- [ ] **Mini-Task 3.3.1**: Standardize image naming convention: `127.0.0.1:5000/{project_name}:{deployment_id}`.
- [ ] **Mini-Task 3.3.2**: Implement SHA-256 content digest verification after build completion before tagging.
- [ ] **Mini-Task 3.3.3**: Implement automated push routine pushing built images from BuildKit cache directly into local registry.
- [ ] **Mini-Task 3.3.4**: Implement manifest inspection utility reading image labels, exposed ports, and environment metadata from local registry.

### Task 3.4: Automated Image Garbage Collection & Disk Governance
- [ ] **Mini-Task 3.4.1**: Create Python cron script (`server/scripts/registry_gc.py`) running daily at 03:00 UTC.
- [ ] **Mini-Task 3.4.2**: Query PostgreSQL database to find image tags older than 7 days that are not linked to active deployments.
- [ ] **Mini-Task 3.4.3**: Send HTTP `DELETE` requests to local registry API for expired image manifests.
- [ ] **Mini-Task 3.4.4**: Trigger registry garbage collector (`registry garbage-collect /etc/docker/registry/config.yml`) to reclaim disk space.
- [ ] **Mini-Task 3.4.5**: Run `docker system prune -f --volumes` to purge unreferenced build cache and dangling layers.

---

## EPIC-04: Zero-Trust Secrets Vault, In-Memory Injection & `.env` Quarantine

### Task 4.1: AES-256-GCM Cryptographic Vault Service
- [x] **Mini-Task 4.1.1**: Implement `SecretManager` class in Python using `cryptography.hazmat.primitives.ciphers.aead.AESGCM`.
- [x] **Mini-Task 4.1.2**: Generate master encryption key on initial platform setup and store in `/etc/deploy/master.key` with `chmod 400`.
- [x] **Mini-Task 4.1.3**: Derive per-project encryption keys using PBKDF2HMAC with SHA-256 and unique project salt.
- [x] **Mini-Task 4.1.4**: Generate fresh 96-bit cryptographic nonce/IV for every encrypted environment variable value.
- [x] **Mini-Task 4.1.5**: Implement unit tests validating encryption, decryption, and tampering detection (authentication tag failure).

### Task 4.2: Pre-Flight `.env` Quarantine Protocol (CLI + Server)
- [x] **Mini-Task 4.2.1**: Implement local quarantine scanner in TypeScript (`cli/src/scanner/quarantine.ts`).
- [x] **Mini-Task 4.2.2**: Define comprehensive sensitive & OS-binary exclusion glob list:
  - `.env`, `.env.*`, `*.env` (secrets quarantine)
  - `id_rsa`, `id_ed25519`, `*.pem`, `*.key`
  - `credentials.json`, `service-account.json`
  - `.git`, `.github`, `.gitlab`
  - `node_modules/`, `.venv/`, `__pycache__/`, `dist/`, `.next/` (heavy / OS-specific binary folders excluded so fresh Linux-native container installation occurs)
- [x] **Mini-Task 4.2.3**: Build archive packager (`tar-stream` / `archiver`) that actively filters out all matching files during project compression.
- [x] **Mini-Task 4.2.4**: Implement server-side verification: unpack tarball in memory, abort build immediately if any `.env` file is found.
- [x] **Mini-Task 4.2.5**: Display bold terminal warning showing quarantined sensitive files so developer knows they were excluded.

### Task 4.3: Runtime In-Memory Process Environment Injection
- [x] **Mini-Task 4.3.1**: Implement decrypt-on-provisioning routine in FastAPI orchestrator.
- [x] **Mini-Task 4.3.2**: Inject decrypted environment variables directly into Docker container creation API parameters (`Env: ["KEY=VALUE"]`).
- [x] **Mini-Task 4.3.3**: Ensure NO `.env` file is ever written to host disk, container volume, or intermediate image layers.
- [x] **Mini-Task 4.3.4**: Test container filesystem to verify that `cat .env` returns `No such file or directory` while `printenv KEY` returns value.

### Task 4.4: Streaming Log Secret Masking & Redaction Engine
- [x] **Mini-Task 4.4.1**: Build `SecretRedactor` pipeline in Python processing real-time stdout and stderr byte streams.
- [x] **Mini-Task 4.4.2**: Extract all secret values for active project into a Trie-based or regex multi-pattern matcher.
- [x] **Mini-Task 4.4.3**: Replace exact secret values and URL-encoded variants with `[REDACTED]` before writing to database or WebSocket.
- [x] **Mini-Task 4.4.4**: Implement automated security test: print known dummy secret in build script &rarr; verify terminal output shows `[REDACTED]`.
- [x] **Mini-Task 4.4.5**: Mask common token formats automatically (JWT regex, AWS key regex, GitHub token regex) even if not registered.

---

## EPIC-05: Universal 3-Tier Polyglot Detection & Buildpack Compiler

### Task 5.1: Tier 1 Native Framework Detectors (Heuristic Analyzers)
- [x] **Mini-Task 5.1.1**: Build `NextJsDetector`: checks `package.json` for `next`, checks `next.config.*`, sets output to `.next/standalone`, default port 3000.
- [x] **Mini-Task 5.1.2**: Build `ViteReactDetector`: checks `vite.config.*` and `react`, sets build `npm run build`, output `dist`, port 80 (static Nginx/Caddy).
- [x] **Mini-Task 5.1.3**: Build `FastApiDetector`: checks `requirements.txt`/`pyproject.toml` for `fastapi`, start `uvicorn main:app --host 0.0.0.0 --port 8000`.
- [x] **Mini-Task 5.1.4**: Build `DjangoDetector`: checks `manage.py`, start `gunicorn {project}.wsgi:application --bind 0.0.0.0:8000`.
- [x] **Mini-Task 5.1.5**: Build `GolangDetector`: checks `go.mod`, build `go build -o server .`, start `./server`, detects port from code or default 8080.
- [x] **Mini-Task 5.1.6**: Build `RustDetector`: checks `Cargo.toml`, build `cargo build --release`, start `./target/release/{bin}`, default port 8080.
- [x] **Mini-Task 5.1.7**: Build `JavaDetector`: checks `pom.xml` (Maven) or `build.gradle` (Gradle), builds `.jar`, start `java -jar app.jar`, default port 8080.
- [x] **Mini-Task 5.1.8**: Build `PhpDetector`: checks `composer.json` + `artisan` (Laravel), builds with PHP-FPM, default port 80.
- [x] **Mini-Task 5.1.9**: Build `DotNetDetector`: checks `*.csproj`, build `dotnet publish -c Release -o out`, start `dotnet out/*.dll`, default port 5000.

### Task 5.2: Host-Binding Automated Shimmer & Port Rewriter
- [x] **Mini-Task 5.2.1**: Implement AST and string scanner checking start commands for `localhost` or `127.0.0.1`.
- [x] **Mini-Task 5.2.2**: Automatically rewrite start command to bind `0.0.0.0` (e.g. `uvicorn --host 0.0.0.0`, `flask run --host=0.0.0.0`).
- [x] **Mini-Task 5.2.3**: Inject environment variable `HOST=0.0.0.0` and `PORT={port}` into container runtime specification.
- [x] **Mini-Task 5.2.4**: Log information banner to developer: `Notice: Automatically configured host binding to 0.0.0.0 for private container network`.

### Task 5.3: Tier 2 Universal Nixpacks / Cloud-Native Buildpack Engine
- [ ] **Mini-Task 5.3.1**: Install and configure `nixpacks` CLI on the Linux server host.
- [ ] **Mini-Task 5.3.2**: Implement fallback detector: if Tier 1 yields no match, invoke `nixpacks plan .` to generate container plan.
- [ ] **Mini-Task 5.3.3**: Parse Nixpacks plan: extract identified language, packages to install, build phases, and launch commands.
- [ ] **Mini-Task 5.3.4**: Generate optimized multi-stage Dockerfile from Nixpacks plan and pass to local BuildKit runner.
- [ ] **Mini-Task 5.3.5**: Handle system dependency auto-injection (e.g. `ffmpeg`, `libpq-dev`, `python3-dev`, `libssl-dev`).

### Task 5.4: Tier 3 Custom Dockerfile Engine & Fallback Wizard
- [x] **Mini-Task 5.4.1**: Implement `DockerfileDetector`: if root contains `Dockerfile`, set mode to `custom_docker`.
- [x] **Mini-Task 5.4.2**: Parse `EXPOSE` instruction in Dockerfile to automatically determine container listening port.
- [ ] **Mini-Task 5.4.3**: Parse `docker-compose.yml` if present: extract main web service, ports, and environment declarations.
- [ ] **Mini-Task 5.4.4**: Implement CLI Interactive Wizard (`deploy init --custom`) prompting 4 simple questions:
  1. Base Runtime / Language
  2. Install Command
  3. Build Command
  4. Start Command & Listening Port
- [ ] **Mini-Task 5.4.5**: Auto-generate standard `deploy.config.json` and minimal Dockerfile from wizard answers.

### Task 5.5: Multi-Architecture Build Testing & Verification
- [x] **Mini-Task 5.5.1**: Ensure builds target the host's native CPU architecture (`linux/amd64` or `linux/arm64`).
- [x] **Mini-Task 5.5.2**: Write automated smoke-test suite testing 10 sample repositories (React, Next.js, FastAPI, Go, Rust, Java, Laravel).
- [ ] **Mini-Task 5.5.3**: Measure build times and verify layer cache hits reduce rebuild times to under 10 seconds.

---

## EPIC-06: FastAPI Control Plane Core, Database Schemas & Docker Engine API

### Task 6.1: FastAPI Application Core & Lifespan Architecture
- [x] **Mini-Task 6.1.1**: Scaffold FastAPI application (`server/app/main.py`) with async lifespan context manager.
- [x] **Mini-Task 6.1.2**: Implement Pydantic v2 `BaseSettings` reading environment variables from `/etc/deploy/platform.env`.
- [x] **Mini-Task 6.1.3**: Configure CORS middleware strictly allowing Next.js dashboard origin and CLI requests.
- [x] **Mini-Task 6.1.4**: Configure structured JSON logging with `structlog` tracking request IDs, status codes, and execution times.
- [x] **Mini-Task 6.1.5**: Implement global exception handler returning standard RFC 7807 Problem Details JSON format.

### Task 6.2: Direct Docker Engine API Socket Client (`/var/run/docker.sock`)
- [x] **Mini-Task 6.2.1**: Implement async Docker client service using `httpx` connecting over Unix domain socket (`http+unix://%2Fvar%2Frun%2Fdocker.sock`).
- [x] **Mini-Task 6.2.2**: Implement `create_container` method passing CPU limits, memory limits, network attachments, and environment vars.
- [x] **Mini-Task 6.2.3**: Implement `start_container`, `stop_container` (with 15s timeout), and `remove_container` methods.
- [x] **Mini-Task 6.2.4**: Implement `inspect_container` returning internal IP address on `deploy-private-net` and health state.
- [x] **Mini-Task 6.2.5**: Implement `stream_container_logs` streaming stdout/stderr frames over async generators.

### Task 6.3: Relational PostgreSQL Schema & Alembic Setup
- [x] **Mini-Task 6.3.1**: Configure SQLAlchemy 2.0 async engine (`asyncpg` / `aiosqlite`) and session dependency `get_db`.
- [x] **Mini-Task 6.3.2**: Implement base declarative model with UUID primary keys and timestamp mixins (`created_at`, `updated_at`).
- [x] **Mini-Task 6.3.3**: Create migration and SQLAlchemy schemas creating:
  - `users`
  - `projects`
  - `deployments`
  - `container_replicas`
  - `autoscale_events`
  - `deployment_logs`
  - `managed_databases`
  - `environment_variables`
- [x] **Mini-Task 6.3.4**: Add foreign key constraints with `ON DELETE CASCADE` on child entities.
- [x] **Mini-Task 6.3.5**: Create database indexes on `deployments.project_id`, `container_replicas.deployment_id`, and `users.email`.

### Task 6.4: Projects & Deployment API Routers
- [x] **Mini-Task 6.4.1**: Implement `POST /api/v1/projects` (register new project, custom or auto-generated subdomain slug, link user).
- [x] **Mini-Task 6.4.2**: Implement `GET /api/v1/projects/{id}` and `GET /api/v1/projects` (list user projects).
- [x] **Mini-Task 6.4.3**: Implement `POST /api/v1/deployments` (accepts project metadata, config overrides, enqueues build job).
- [x] **Mini-Task 6.4.4**: Implement `GET /api/v1/deployments/{id}` (returns active state, replica list, public URL).
- [x] **Mini-Task 6.4.5**: Implement `POST /api/v1/deployments/{id}/cancel` (terminates running build or deployment).
- [x] **Mini-Task 6.4.6**: Implement `GET /api/v1/domains/check?name={slug}` endpoint: validates subdomain format (RFC 1123), checks database uniqueness, and if taken returns HTTP 409 Conflict with friendly message ("Domain already exists, please choose another name") and 3 auto-generated alternative suggestions.
- [x] **Mini-Task 6.4.7**: Implement `GET /api/v1/git/repositories` (lists connected user repositories) and `POST /api/v1/git/deploy` (clones repo URL and branch into sandbox, triggers automated Frontend vs Backend polyglot detection, and dispatches container build).
- [x] **Mini-Task 6.4.8**: Implement GitHub Webhook Continuous Deployment (CD) receiver (`POST /api/v1/webhooks/github`): validates HMAC SHA-256 webhook signature (`X-Hub-Signature-256`), detects push events to target branch (e.g. `main`), automatically triggers build and zero-downtime deployment, and reports commit status back to GitHub.

### Task 6.5: Real-Time Log Streaming via Server-Sent Events (SSE)
- [x] **Mini-Task 6.5.1**: Implement Redis Pub/Sub channel per deployment (`deployments:{id}:logs`).
- [x] **Mini-Task 6.5.2**: Implement `GET /api/v1/deployments/{id}/logs/stream` returning `text/event-stream`.
- [x] **Mini-Task 6.5.3**: Implement historical log playback: fetch stored logs from PostgreSQL first, then stream live entries.
- [x] **Mini-Task 6.5.4**: Implement SSE keep-alive heartbeat comments (`: ping\n\n`) every 15 seconds to prevent proxy timeouts.

### Task 6.6: Swagger / OpenAPI Documentation Customization
- [x] **Mini-Task 6.6.1**: Customize FastAPI OpenAPI schema metadata (title, version 1.0.0, description, security schemes).
- [x] **Mini-Task 6.6.2**: Add Bearer token security definition to OpenAPI specification.
- [x] **Mini-Task 6.6.3**: Verify interactive Swagger UI is available and functional at `http://127.0.0.1:8000/docs`.

---

## EPIC-07: Asynchronous Job Queue, Worker Daemons & Task Orchestration

### Task 7.1: Redis 7 Deployment & ARQ Worker Architecture
- [x] **Mini-Task 7.1.1**: Provision Redis 7 container on host bound to `127.0.0.1:6379` with persistent AOF storage.
- [ ] **Mini-Task 7.1.2**: Implement ARQ worker settings (`server/app/worker/settings.py`) with max 10 concurrent jobs.
- [ ] **Mini-Task 7.1.3**: Configure job timeout (900 seconds) and automatic retry policy for network-related failures.
- [ ] **Mini-Task 7.1.4**: Create systemd service unit `/etc/systemd/system/deploy-worker.service` to keep ARQ worker active.

### Task 7.2: Build Execution Background Task
- [x] **Mini-Task 7.2.1**: Implement `execute_build_task` in `server/app/worker/tasks.py`.
- [x] **Mini-Task 7.2.2**: Download and extract source tarball into isolated build workspace `/tmp/deploy_builds/{job_id}`.
- [x] **Mini-Task 7.2.3**: Execute BuildKit build command streaming logs line-by-line into Redis channel.
- [x] **Mini-Task 7.2.4**: Push successfully built image to local registry `127.0.0.1:5000/{project}:{id}`.
- [x] **Mini-Task 7.2.5**: Clean up temporary build workspace directory upon task completion or failure.

### Task 7.3: Deployment Provisioning Background Task
- [x] **Mini-Task 7.3.1**: Implement `execute_deployment_task` in `server/app/worker/tasks.py`.
- [x] **Mini-Task 7.3.2**: Resolve environment variables, decrypt secrets in-memory.
- [x] **Mini-Task 7.3.3**: Launch target number of container replicas (`min_replicas`, default 3) attached to `deploy-private-net`.
- [x] **Mini-Task 7.3.4**: Record container IDs, internal IPs, and ports in `container_replicas` table.
- [x] **Mini-Task 7.3.5**: Trigger health verification and traffic cutover workflows.

### Task 7.4: Dead-Letter Queue & Worker Error Governance
- [x] **Mini-Task 7.4.1**: Implement failure handler: on uncaught task exception, transition deployment state to `FAILED`.
- [x] **Mini-Task 7.4.2**: Record detailed traceback and failure reason in `deployments.error_message`.
- [x] **Mini-Task 7.4.3**: Clean up any orphaned containers created during the aborted deployment.
- [x] **Mini-Task 7.4.4**: Trigger AI Doctor diagnostic routine in background to prepare immediate fix suggestion.

---

## EPIC-08: Zero-Downtime Blue-Green Deployment & Health Verification Engine

### Task 8.1: Finite State Machine (FSM) Engine
- [x] **Mini-Task 8.1.1**: Implement `DeploymentFSM` class in Python managing state transitions.
- [x] **Mini-Task 8.1.2**: Define valid transitions:
  - `CREATED` &rarr; `QUARANTINING`
  - `QUARANTINING` &rarr; `BUILDING`
  - `BUILDING` &rarr; `PROVISIONING_GREEN`
  - `PROVISIONING_GREEN` &rarr; `VERIFYING_CLUSTER`
  - `VERIFYING_CLUSTER` &rarr; `TRAFFIC_SWAP`
  - `TRAFFIC_SWAP` &rarr; `TEARDOWN_BLUE` &rarr; `SUCCESS`
  - Any active state &rarr; `FAILED` on unrecoverable error
- [x] **Mini-Task 8.1.3**: Persist every state change with timestamp and actor in `deployment_logs`.
- [x] **Mini-Task 8.1.4**: Broadcast state change events via Redis Pub/Sub to active SSE/WebSocket clients.

### Task 8.2: Hardened Container Runtime Provisioning
- [x] **Mini-Task 8.2.1**: Enforce unprivileged user execution (`User: "10001:10001"`).
- [x] **Mini-Task 8.2.2**: Mount root filesystem as read-only (`ReadonlyRootfs: true`).
- [x] **Mini-Task 8.2.3**: Mount temporary writable `/tmp` as in-memory tmpfs (`Tmpfs: {"/tmp": "rw,noexec,nosuid,size=64m"}`).
- [x] **Mini-Task 8.2.4**: Drop all Linux capabilities (`CapDrop: ["ALL"]`) and set `NoNewPrivileges: true`.
- [x] **Mini-Task 8.2.5**: Set restart policy to `unless-stopped` with max 5 retry attempts.

### Task 8.3: Automated Multi-Replica Health Checker
- [x] **Mini-Task 8.3.1**: Implement async health-probe service using `httpx.AsyncClient`.
- [x] **Mini-Task 8.3.2**: Read health check path (default `/` or `/health`), expected status (200 OK), and timeout (5s) from config.
- [x] **Mini-Task 8.3.3**: Execute concurrent probes against every newly spawned "Green" replica's private IP.
- [x] **Mini-Task 8.3.4**: Implement retry loop: up to 10 attempts with 2-second intervals before declaring failure.
- [x] **Mini-Task 8.3.5**: If ANY replica fails all attempts, mark deployment `FAILED` and do NOT switch traffic.

### Task 8.4: Atomic Reverse Proxy Traffic Cutover
- [x] **Mini-Task 8.4.1**: Build `CaddyLoadBalancerService` communicating with Caddy Admin API (`127.0.0.1:2019`).
- [x] **Mini-Task 8.4.2**: Generate Caddy reverse proxy upstream JSON payload containing all healthy "Green" replica IPs.
- [x] **Mini-Task 8.4.3**: Execute atomic HTTP `PATCH` to `/config/apps/http/servers/srv0/routes/...` updating upstream pool.
- [x] **Mini-Task 8.4.4**: Verify Caddy returns HTTP 200 OK confirming traffic is now routed to Green replicas.
- [ ] **Mini-Task 8.4.5**: Implement Sub-100ms Instant Atomic Rollback (`POST /api/v1/deployments/{id}/rollback`): bypasses compilation entirely, launches containers from existing immutable registry image tag in under 2 seconds, verifies health, and performs sub-100ms Caddy upstream cutover.

### Task 8.5: Graceful Draining & Decommissioning of Old Replicas
- [x] **Mini-Task 8.5.1**: Mark old "Blue" replicas as "DRAINING".
- [x] **Mini-Task 8.5.2**: Allow 15-second grace period for ongoing in-flight HTTP requests to complete on Blue containers.
- [x] **Mini-Task 8.5.3**: Send `SIGTERM` signal to old Blue containers.
- [x] **Mini-Task 8.5.4**: If container does not exit after 10 seconds, send `SIGKILL` and remove container.
- [x] **Mini-Task 8.5.5**: Update database: mark old deployment as `SUPERSEDED`, mark new deployment as `ACTIVE`.

---

## EPIC-09: Dynamic Horizontal Autoscaler Daemon (HPA) & Real-Time Metrics

### Task 9.1: Real-Time Docker Engine Metrics Collector Daemon
- [x] **Mini-Task 9.1.1**: Build `AutoscalerDaemon` in Python running as a standalone background service.
- [x] **Mini-Task 9.1.2**: Implement metrics collector connecting to `/var/run/docker.sock` streaming container stats.
- [x] **Mini-Task 9.1.3**: Calculate precise CPU percentage:
  $$\text{CPU \%} = \frac{\Delta \text{container\_cpu}}{\Delta \text{system\_cpu}} \times \text{number\_of\_cpus} \times 100$$
- [x] **Mini-Task 9.1.4**: Calculate Memory usage percentage and active TCP socket connections.
- [x] **Mini-Task 9.1.5**: Sample metrics on a strict 5-second interval and maintain a 30-second rolling window per deployment.

### Task 9.2: Scale-Out Execution Engine
- [x] **Mini-Task 9.2.1**: Evaluate cluster load: check if rolling average CPU exceeds `targetCpuPercent` (default 75%).
- [x] **Mini-Task 9.2.2**: Verify current replica count is less than `maxReplicas` (default 10).
- [x] **Mini-Task 9.2.3**: Determine scale increment: add 1 replica (or proportional to load spike).
- [x] **Mini-Task 9.2.4**: Spawn new container replica `Replica N+1` on `deploy-private-net`.
- [x] **Mini-Task 9.2.5**: Execute health check probe on new replica until HTTP 200 OK.
- [x] **Mini-Task 9.2.6**: Dynamically append new replica IP to Caddy upstream pool via Admin API.
- [x] **Mini-Task 9.2.7**: Insert record into `autoscale_events` table (`action: "SCALE_OUT"`, `new_replicas: N+1`).

### Task 9.3: Scale-In & Cooldown Management Engine
- [x] **Mini-Task 9.3.1**: Evaluate cluster load: check if rolling average CPU drops below 30% and replicas > `minReplicas` (default 3).
- [x] **Mini-Task 9.3.2**: Start 300-second (5-minute) cooldown timer.
- [x] **Mini-Task 9.3.3**: If load spikes above 50% at any point during cooldown, cancel scale-in immediately.
- [x] **Mini-Task 9.3.4**: After full cooldown completion, select oldest surplus replica for decommissioning.
- [x] **Mini-Task 9.3.5**: Remove replica IP from Caddy upstream pool.
- [x] **Mini-Task 9.3.6**: Gracefully drain and stop surplus container, freeing host RAM and CPU.
- [x] **Mini-Task 9.3.7**: Insert record into `autoscale_events` table (`action: "SCALE_IN"`, `new_replicas: N-1`).

### Task 9.4: High-Availability Baseline Enforcement
- [x] **Mini-Task 9.4.1**: Enforce hard lower floor: replica count can NEVER drop below `minReplicas` (default 3).
- [x] **Mini-Task 9.4.2**: Implement auto-healing watchdog: if any baseline replica crashes or exits unexpectedly:
  - Detect dead container within 5 seconds.
  - Remove dead IP from Caddy upstream pool.
  - Automatically boot replacement replica.
  - Verify health and re-add to Caddy upstream pool.

### Task 9.5: Real-Time Metrics Streaming & TUI Engine (`deploy top`)
- [x] **Mini-Task 9.5.1**: Implement `GET /api/v1/deployments/{id}/metrics` streaming SSE metrics every 2 seconds.
- [ ] **Mini-Task 9.5.2**: Build terminal dashboard in Node.js using `blessed` or `cli-table3` with ANSI color charts.
- [ ] **Mini-Task 9.5.3**: Render active replica table showing: Container ID, Private IP, CPU %, RAM MB, and Health State.
- [ ] **Mini-Task 9.5.4**: Render live graph showing historical scaling events and average CPU utilization.

---

## EPIC-10: Render-Style Managed Databases (PostgreSQL 16 & Redis 7) Engine

### Task 10.1: Managed Database Provisioner Service
- [x] **Mini-Task 10.1.1**: Build `DatabaseProvisionerService` in Python (`server/app/services/db_provisioner.py`).
- [x] **Mini-Task 10.1.2**: Implement cryptographically secure password generator (32 characters, alphanumeric + symbols).
- [x] **Mini-Task 10.1.3**: Create host storage directory `/var/lib/deploy/databases/{db_id}/data` with restricted permissions (`chmod 700`).
- [x] **Mini-Task 10.1.4**: Implement `POST /api/v1/databases` accepting `name`, `type` (`postgres` | `redis`), and `project_id`.

### Task 10.2: PostgreSQL 16 Isolated Container Provisioning
- [x] **Mini-Task 10.2.1**: Pull and run official `postgres:16-alpine` attached to `deploy-private-net`.
- [x] **Mini-Task 10.2.2**: Mount persistent host directory `/var/lib/deploy/databases/{db_id}/data` to `/var/lib/postgresql/data`.
- [x] **Mini-Task 10.2.3**: Inject environment variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
- [x] **Mini-Task 10.2.4**: Do NOT expose port 5432 to host; database is accessible ONLY within `deploy-private-net`.
- [x] **Mini-Task 10.2.5**: Execute `pg_isready` probe inside container to confirm database is operational.

### Task 10.3: Redis 7 Isolated Container Provisioning
- [x] **Mini-Task 10.3.1**: Pull and run official `redis:7-alpine` attached to `deploy-private-net`.
- [x] **Mini-Task 10.3.2**: Mount persistent host directory `/var/lib/deploy/databases/{db_id}/data` to `/data`.
- [x] **Mini-Task 10.3.3**: Launch with password protection (`--requirepass {generated_password}`) and AOF persistence (`--appendonly yes`).
- [x] **Mini-Task 10.3.4**: Execute `redis-cli ping` probe to confirm Redis is operational.

### Task 10.4: Connection String Generation, Injection & Automated Backups
- [x] **Mini-Task 10.4.1**: Construct internal connection strings:
  - `postgresql://{user}:{password}@pg-{name}.deploy-private-net:5432/{dbname}`
  - `redis://:{password}@redis-{name}.deploy-private-net:6379/0`
- [x] **Mini-Task 10.4.2**: Encrypt connection string with AES-256-GCM and store in `managed_databases` table.
- [x] **Mini-Task 10.4.3**: Automatically inject `DATABASE_URL` or `REDIS_URL` into connected application container environment variables.
- [x] **Mini-Task 10.4.4**: Implement automated daily backup script (`server/scripts/backup_db.py`): executes `pg_dump` and saves compressed `.sql.gz` to `/var/lib/deploy/backups/`.
- [x] **Mini-Task 10.4.5**: Implement database restoration endpoint (`POST /api/v1/databases/{id}/restore`).

---

## EPIC-11: Authentication & Identity Provider (OAuth 2.0 + Offline Local Admin)

### Task 11.1: Google & GitHub OAuth 2.0 Backend Handlers
- [ ] **Mini-Task 11.1.1**: Configure OAuth client settings (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`).
- [ ] **Mini-Task 11.1.2**: Implement GitHub callback: exchange code for access token, fetch profile from `api.github.com/user`, upsert local user.
- [ ] **Mini-Task 11.1.3**: Implement Google callback: exchange code for ID token, verify Google signature, fetch user info, upsert local user.
- [ ] **Mini-Task 11.1.4**: Generate signed platform JWT containing user ID, email, avatar URL, and roles.

### Task 11.2: RFC 8628 OAuth Device Authorization Flow for CLI
- [ ] **Mini-Task 11.2.1**: Implement `POST /api/v1/auth/device/code`:
  - Generate 8-character human-friendly user code (e.g. `WDJB-4921`).
  - Generate 32-character random device code.
  - Store mapping in Redis with 10-minute expiration.
- [ ] **Mini-Task 11.2.2**: Implement `POST /api/v1/auth/device/token`:
  - CLI polls endpoint with device code every 5 seconds.
  - If pending, returns `{ "status": "authorization_pending" }`.
  - If approved, returns platform JWT and user profile.
- [ ] **Mini-Task 11.2.3**: Build verification page on Next.js dashboard (`/auth/device`) where user confirms the displayed code.

### Task 11.3: Offline / Local Admin Authentication
- [ ] **Mini-Task 11.3.1**: Implement local user registration and login endpoints: `POST /api/v1/auth/local/login`.
- [ ] **Mini-Task 11.3.2**: Hash passwords using Argon2id or bcrypt with cost factor 12.
- [ ] **Mini-Task 11.3.3**: Provide automated CLI command `deploy admin create` for initializing root credentials without internet.
- [ ] **Mini-Task 11.3.4**: Enforce role-based access control (RBAC): `admin` vs `developer`.

### Task 11.4: Session Management & Token Revocation
- [ ] **Mini-Task 11.4.1**: Implement short-lived access tokens (1 hour) paired with long-lived refresh tokens (30 days).
- [ ] **Mini-Task 11.4.2**: Implement token refresh endpoint: `POST /api/v1/auth/refresh`.
- [ ] **Mini-Task 11.4.3**: Implement Redis token blacklist for instant session revocation on logout or user deactivation.
- [ ] **Mini-Task 11.4.4**: Write automated integration tests for complete login, refresh, and revocation cycles.

---

## EPIC-12: Self-Hosted AI Diagnostic Engine (`deploy doctor` with Ollama)

### Task 12.1: Host Linux Ollama Deployment & Systemd Service
- [ ] **Mini-Task 12.1.1**: Install Ollama on Linux host (`curl -fsSL https://ollama.com/install.sh | sh`).
- [ ] **Mini-Task 12.1.2**: Create systemd override `/etc/systemd/system/ollama.service.d/override.conf` binding strictly to `127.0.0.1:11434`.
- [ ] **Mini-Task 12.1.3**: Pull target open-weights model on host: `ollama pull llama3:8b` or `ollama pull mistral:7b`.
- [ ] **Mini-Task 12.1.4**: Verify Ollama API responsiveness: `curl http://127.0.0.1:11434/api/tags`.

### Task 12.2: Error Extraction & Sanitization Pipeline
- [ ] **Mini-Task 12.2.1**: Build `ErrorLogExtractor` in Python parsing failed build logs and container crash dumps.
- [ ] **Mini-Task 12.2.2**: Isolate non-zero exit codes, compiler errors, stack traces, and uncaught exceptions.
- [ ] **Mini-Task 12.2.3**: Pass extracted snippet through `SecretRedactor` to guarantee no credentials reach the LLM prompt.
- [ ] **Mini-Task 12.2.4**: Truncate context to last 200 lines of error logs to fit within LLM context window.

### Task 12.3: Diagnostic Prompt Engineering & LLM Client
- [ ] **Mini-Task 12.3.1**: Design specialized system prompt instructing LLM to behave as an expert Cloud DevOps & Systems Engineer.
- [ ] **Mini-Task 12.3.2**: Format prompt with: Project Tech Stack, Command Executed, Exit Code, and Sanitized Error Trace.
- [ ] **Mini-Task 12.3.3**: Require structured JSON output containing:
  - `root_cause`: Plain-language explanation of why the build or runtime failed.
  - `category`: `MISSING_DEPENDENCY` | `PORT_BINDING` | `SYNTAX_ERROR` | `ENV_VAR_MISSING` | `MEMORY_LIMIT`.
  - `remediation_steps`: Numbered list of exact actions to fix.
  - `suggested_command`: Copy-pasteable terminal command (e.g. `deploy env set DATABASE_URL=...`).
- [ ] **Mini-Task 12.3.4**: Implement async HTTP client querying `http://127.0.0.1:11434/api/generate` with temperature 0.2.

### Task 12.4: API Endpoint & CLI `deploy doctor` Visualizer
- [ ] **Mini-Task 12.4.1**: Implement `POST /api/v1/deployments/{id}/diagnose` endpoint.
- [ ] **Mini-Task 12.4.2**: Implement CLI command `deploy doctor [--id <dep_id>]`.
- [ ] **Mini-Task 12.4.3**: Format terminal output with box borders, colored root-cause badge, and syntax-highlighted fix commands.
- [ ] **Mini-Task 12.4.4**: Implement optional cloud LLM fallback: if user configures `OPENAI_API_KEY`, route diagnosis through OpenAI if Ollama is unavailable.

---

## EPIC-13: Universal CLI Client Engineering (TypeScript / Node.js)

### Task 13.1: CLI Architecture, Packaging & Distribution
- [ ] **Mini-Task 13.1.1**: Initialize TypeScript project (`cli/package.json`) with binary bin entry `deploy`.
- [ ] **Mini-Task 13.1.2**: Configure `tsup` or `esbuild` for bundling into a standalone zero-dependency executable.
- [ ] **Mini-Task 13.1.3**: Configure global npm distribution (`npm install -g @deploy/cli`).
- [ ] **Mini-Task 13.1.4**: Implement global configuration storage in `~/.deployrc` (API endpoint, auth token, default project).

### Task 13.2: Project Scanner & Manifest Generator (`deploy init`)
- [ ] **Mini-Task 13.2.1**: Implement `deploy init` command.
- [ ] **Mini-Task 13.2.2**: Scan workspace using Universal 3-Tier Polyglot Engine.
- [ ] **Mini-Task 13.2.3**: Check for host-binding pitfalls (`127.0.0.1`) and prompt developer for auto-fix.
- [ ] **Mini-Task 13.2.4**: Generate standardized `deploy.config.json` schema with recommended settings.
- [ ] **Mini-Task 13.2.5**: Implement `deploy plan` showing preview table of build command, start command, ports, and autoscaling policy.
- [ ] **Mini-Task 13.2.6**: Add interactive domain slug selection prompt (`Choose domain name: [my-project]`), query `/api/v1/domains/check`, and if taken display: `❌ Domain 'my-project' already exists! Please choose another name (Suggestions: my-project-app, my-project-2)`.

### Task 13.3: Deployment Execution Command (`deploy`)
- [ ] **Mini-Task 13.3.1**: Implement `deploy` main command.
- [ ] **Mini-Task 13.3.2**: Trigger pre-flight `.env` quarantine scanner, display quarantined files banner.
- [ ] **Mini-Task 13.3.3**: Compress sanitized source workspace into `.tar.gz` archive in memory.
- [ ] **Mini-Task 13.3.4**: Upload archive to FastAPI `POST /api/v1/deployments` with upload progress bar.
- [ ] **Mini-Task 13.3.5**: Connect to SSE log stream (`GET /api/v1/deployments/{id}/logs/stream`), print colorized logs in real time.
- [ ] **Mini-Task 13.3.6**: On success, print deployment summary box with public HTTPS URL, active replica count, and execution time.
- [ ] **Mini-Task 13.3.7**: Implement interactive Git repository deployment mode (`deploy repo`): fetches connected user repos, renders interactive arrow-key selector with search, prompts for branch (`main`), automatically auto-detects Frontend vs Backend runtime, and streams live deployment to HTTPS.

### Task 13.4: Autoscaling & Replica Management Commands
- [ ] **Mini-Task 13.4.1**: Implement `deploy scale --min <n> --max <m> [--cpu <pct>]` sending PATCH request to backend.
- [ ] **Mini-Task 13.4.2**: Implement `deploy top`:
  - Clear terminal screen.
  - Stream live metrics via SSE.
  - Render ASCII table updating every 2 seconds with CPU %, RAM MB, active replicas, and network I/O.
- [ ] **Mini-Task 13.4.3**: Add keybindings to `deploy top` (`q` to quit, `+` to add replica, `-` to scale down).

### Task 13.5: Database & Environment Commands
- [ ] **Mini-Task 13.5.1**: Implement `deploy db create <postgres|redis> [--name <name>]`.
- [ ] **Mini-Task 13.5.2**: Implement `deploy db list` displaying database status, type, and internal connection strings.
- [ ] **Mini-Task 13.5.3**: Implement `deploy env set KEY=VALUE` (encrypts and saves to vault).
- [ ] **Mini-Task 13.5.4**: Implement `deploy env list` (displays all keys with values masked as `********`).
- [ ] **Mini-Task 13.5.5**: Implement `deploy env pull [--file <path>]` (decrypts and downloads to local `.env`).
- [ ] **Mini-Task 13.5.6**: Implement `deploy env push [--file <path>]`: parses local `.env`, removes comments/whitespace, encrypts variables via AES-256-GCM, and bulk-uploads directly into platform secrets vault in one command.
- [ ] **Mini-Task 13.5.7**: Add interactive `.env` prompt during `deploy repo` / `deploy`: scans repository for referenced `process.env.*` or `os.getenv(*)` variables, and interactively prompts the developer for missing secret values before compiling the build.

### Task 13.6: Rollback, Status & Cleanup Commands
- [ ] **Mini-Task 13.6.1**: Implement `deploy status` querying active deployment, health state, and URL.
- [ ] **Mini-Task 13.6.2**: Implement `deploy history` displaying formatted table of previous deployments and commit hashes.
- [ ] **Mini-Task 13.6.3**: Implement `deploy rollback <deployment-id>` triggering instant atomic traffic reversion.
- [ ] **Mini-Task 13.6.4**: Implement `deploy destroy --confirm` deallocating project containers, networks, and databases.

---

## EPIC-14: Next.js 16 Production Management Console (App Router + React 19)

### Task 14.1: Next.js 16 Project Scaffold & Authentication
- [ ] **Mini-Task 14.1.1**: Initialize Next.js 16 application with Turbopack, App Router, React 19, and Tailwind CSS.
- [ ] **Mini-Task 14.1.2**: Configure Auth.js / NextAuth with Google, GitHub, and Credentials providers.
- [ ] **Mini-Task 14.1.3**: Build authentication pages (`/login`, `/register`, `/auth/device`).
- [ ] **Mini-Task 14.1.4**: Implement middleware protecting dashboard routes (`/dashboard/*`) redirecting unauthenticated users to `/login`.

### Task 14.2: Dashboard Core Layout & Project Navigation
- [ ] **Mini-Task 14.2.1**: Build responsive sidebar navigation with Lucide React icons.
- [ ] **Mini-Task 14.2.2**: Build project overview page displaying all active projects, health statuses, and public URLs.
- [ ] **Mini-Task 14.2.3**: Build "New Project" modal supporting GitHub repo import, manual upload, or CLI connect.
- [ ] **Mini-Task 14.2.4**: Implement dark/light theme switcher with system preference detection.
- [ ] **Mini-Task 14.2.5**: In "New Project" modal, build interactive domain slug picker input with real-time 300ms debounced verification: displays animated green badge `✔ Available` if free, or red warning `❌ Domain already exists! Please choose another name` with clickable alternative suggestions.
- [ ] **Mini-Task 14.2.6**: Build comprehensive Project Detail Overview page (`/projects/[id]`) displaying: Live HTTPS URL, Git repository info & branch, active replica health status, live CPU/RAM summary badges, last deployment timestamp, and quick-action buttons (Redeploy, Rollback, View Logs).

### Task 14.3: Real-Time Deployment & Live Log Terminal View
- [ ] **Mini-Task 14.3.1**: Build deployment detail page (`/projects/[id]/deployments/[depId]`).
- [ ] **Mini-Task 14.3.2**: Build interactive deployment state machine visualizer (Blue/Green indicators, health probe badges).
- [ ] **Mini-Task 14.3.3**: Build `TerminalLogViewer` component using `@xterm/xterm` or custom virtualized list.
- [ ] **Mini-Task 14.3.4**: Connect to SSE endpoint, auto-scroll to bottom, support search and log filter by level (INFO, WARN, ERROR).
- [ ] **Mini-Task 14.3.5**: Add one-click "Rollback to this deployment" button with confirmation dialog.
- [ ] **Mini-Task 14.3.6**: Build dedicated Project-Wise Observability & Log Hub page (`/projects/[id]/logs`) with multi-stream tab switcher: toggles between [All Logs], [Frontend Logs], [Backend Logs], [Build Logs], and [Database Logs] with keyword search, live pause/resume, and one-click "Download Logs (.txt)" button.

### Task 14.4: Dynamic Autoscaling Monitor & Controls
- [ ] **Mini-Task 14.4.1**: Build live metrics chart using Chart.js or Recharts showing CPU % and Memory usage over time.
- [ ] **Mini-Task 14.4.2**: Render active replica cards displaying container ID, private IP, CPU load, and health indicator.
- [ ] **Mini-Task 14.4.3**: Build autoscaling configuration panel with dual-handle slider for Min Replicas (1–5) and Max Replicas (3–20).
- [ ] **Mini-Task 14.4.4**: Implement live autoscaling event feed showing historical scale-out and scale-in triggers.

### Task 14.5: Managed Database Portal (PostgreSQL & Redis)
- [ ] **Mini-Task 14.5.1**: Build database management page (`/projects/[id]/databases`).
- [ ] **Mini-Task 14.5.2**: Build "Create Database" modal with one-click PostgreSQL and Redis options.
- [ ] **Mini-Task 14.5.3**: Render database connection cards with masked connection strings and "Copy Connection URL" button.
- [ ] **Mini-Task 14.5.4**: Add manual backup button ("Create Snapshot Now") and list downloadable backup files.

### Task 14.6: AI Doctor Modal Visualizer
- [ ] **Mini-Task 14.6.1**: Build `AiDoctorModal` component triggering on failed deployments.
- [ ] **Mini-Task 14.6.2**: Render AI diagnostic analysis: root cause summary, explanation, and syntax-highlighted code fix.
- [ ] **Mini-Task 14.6.3**: Add "Apply Fix via CLI" copy button for instant terminal execution.

---

## EPIC-15: Server Production Packaging, Bootstrap Installer & Disaster Recovery

### Task 15.1: Host Bootstrap Automated Installer (`install.sh`)
- [ ] **Mini-Task 15.1.1**: Write automated Bash bootstrap installer script for Ubuntu 22.04 / 24.04 LTS and Debian 12.
- [ ] **Mini-Task 15.1.2**: Automatically check prerequisites (CPU cores, RAM >= 4GB, Disk >= 20GB, root permissions).
- [ ] **Mini-Task 15.1.3**: Automate installation of Docker Engine, Caddy 2, Ollama, and system utilities.
- [ ] **Mini-Task 15.1.4**: Pull all base platform containers (`registry:2`, `postgres:16-alpine`, `redis:7-alpine`, `caddy:2`).
- [ ] **Mini-Task 15.1.5**: Pull default Ollama model (`ollama pull llama3:8b`).
- [ ] **Mini-Task 15.1.6**: Prompt admin for initial root username and password, save to database.

### Task 15.2: Production Systemd Service Units
- [ ] **Mini-Task 15.2.1**: Create `/etc/systemd/system/deploy-api.service` for FastAPI control plane (Uvicorn).
- [ ] **Mini-Task 15.2.2**: Create `/etc/systemd/system/deploy-worker.service` for ARQ background worker.
- [ ] **Mini-Task 15.2.3**: Create `/etc/systemd/system/deploy-autoscaler.service` for metrics autoscaling daemon.
- [ ] **Mini-Task 15.2.4**: Create `/etc/systemd/system/deploy-dashboard.service` for Next.js 16 web portal.
- [ ] **Mini-Task 15.2.5**: Configure `Restart=always` and `RestartSec=5` on all service units for high availability.

### Task 15.3: Automated Platform Self-Backup & Snapshotting
- [ ] **Mini-Task 15.3.1**: Implement automated backup script `/var/lib/deploy/scripts/system_backup.sh`.
- [ ] **Mini-Task 15.3.2**: Backup platform control PostgreSQL database to `/var/lib/deploy/backups/platform_db_{date}.sql.gz`.
- [ ] **Mini-Task 15.3.3**: Backup Caddy TLS certificates and configurations to `/var/lib/deploy/backups/caddy_{date}.tar.gz`.
- [ ] **Mini-Task 15.3.4**: Configure cron job running backup script nightly at 02:00 UTC with 30-day retention.

### Task 15.4: Disaster Recovery & Host Cold-Restart Validation
- [ ] **Mini-Task 15.4.1**: Implement disaster recovery restore script `/var/lib/deploy/scripts/system_restore.sh`.
- [ ] **Mini-Task 15.4.2**: Execute simulated server hard reboot test:
  - Reboot host machine completely (`reboot`).
  - Verify all systemd services start automatically on boot.
  - Verify all active application replicas resume serving traffic via Caddy.
  - Verify zero data loss in managed PostgreSQL and Redis databases.
- [ ] **Mini-Task 15.4.3**: Write comprehensive Runbook documentation (`docs/runbook-disaster-recovery.md`).

---

## EPIC-16: Commercial Product Engine: Multi-Tenancy, Enterprise Licensing & Turnkey Appliance

### Task 16.1: Multi-Tenant Organization & Workspace Architecture
- [ ] **Mini-Task 16.1.1**: Design multi-tenant database schema (`organizations`, `workspaces`, `organization_members`, `tenant_quotas`) with strict tenant foreign keys.
- [ ] **Mini-Task 16.1.2**: Implement hierarchical RBAC model (`Owner`, `Admin`, `Developer`, `BillingAdmin`, `Viewer`) with granular action-level permission decorators.
- [ ] **Mini-Task 16.1.3**: Enforce strict tenant isolation middleware: all database queries, container operations, Redis cache keys, and Caddy routes are scoped by `tenant_id` so Tenant A cannot access Tenant B.
- [ ] **Mini-Task 16.1.4**: Implement organization team invite system via signed cryptographic invitation tokens with role assignment and expiration.

### Task 16.2: Cryptographic Offline License Key System & Feature Gating
- [ ] **Mini-Task 16.2.1**: Implement asymmetric cryptographic licensing engine (RSA-4096 / Ed25519 digital signature validation) in Python (`server/app/services/licensing.py`).
- [ ] **Mini-Task 16.2.2**: Build license payload schema encoding: Licensee Name, Machine Fingerprint (CPU ID + Machine-ID hash), Expiry Date, Max Projects, Max Nodes/Replicas, and Feature Flags (`ai_doctor_enabled`, `white_label_enabled`).
- [ ] **Mini-Task 16.2.3**: Build offline license activator (`deploy license activate <key-file>` and web UI upload) that validates signature without requiring external internet connection.
- [ ] **Mini-Task 16.2.4**: Implement license enforcement interceptor: gracefully warns administrators 14 days prior to expiration and restricts provisioning when license limits are breached while keeping running containers alive.

### Task 16.3: Tenant Resource Quotas, Usage Metering & Tier Limits
- [ ] **Mini-Task 16.3.1**: Build tenant resource metering daemon tracking cumulative CPU-hours, RAM-gigabyte-hours, storage usage, and active project counts per workspace.
- [ ] **Mini-Task 16.3.2**: Enforce hard quota limits on container creation: block deployments that exceed workspace memory allotment or replica maximums.
- [ ] **Mini-Task 16.3.3**: Implement usage export endpoint (`GET /api/v1/tenant/usage/export`) outputting standard CSV and JSON summaries for commercial invoice billing.
- [ ] **Mini-Task 16.3.4**: Build visual quota consumption widgets on Next.js dashboard showing real-time progress bars for CPU, RAM, and storage allocation against tier ceilings.

### Task 16.4: Enterprise White-Labeling & Custom Domain Management
- [ ] **Mini-Task 16.4.1**: Build white-label configuration engine allowing organization admins to customize platform name, brand logo, favicon, accent colors, and custom login screen.
- [ ] **Mini-Task 16.4.2**: Implement enterprise custom root domain routing: allow clients to bring their own vanity domain (e.g. `deploy.mycompany.com`) mapped directly to Caddy ingress.
- [ ] **Mini-Task 16.4.3**: Integrate automated Caddy on-demand TLS provisioning for customer-supplied custom domains without server restart.
- [ ] **Mini-Task 16.4.4**: Provide CLI white-label flag generation (`npm run build:cli -- --brand "MyCompany Cloud"`) to compile branded CLI executables for enterprise buyers.

### Task 16.5: Comprehensive Enterprise Audit Logging & Activity Trail
- [ ] **Mini-Task 16.5.1**: Build immutable `audit_logs` database table tracking: `timestamp`, `actor_id`, `actor_email`, `action_type`, `resource_type`, `resource_id`, `ip_address`, `user_agent`, and `payload_diff`.
- [ ] **Mini-Task 16.5.2**: Log all security-sensitive events: user logins, privilege escalations, secret creation/decryption, database deletions, rollback actions, and license updates.
- [ ] **Mini-Task 16.5.3**: Build searchable, filterable Audit Log viewer in Next.js console with date-range filters, user search, and CSV/SIEM export.
- [ ] **Mini-Task 16.5.4**: Implement SHA-256 HMAC hash chaining across log entries to guarantee tamper-evident verification for enterprise SOC-2 and ISO compliance.

### Task 16.6: Turnkey 1-Command Commercial Customer Installer & Air-Gapped Distribution
- [ ] **Mini-Task 16.6.1**: Build public commercial bootstrap script (`https://get.ourplatform.com/install.sh` / `curl -fsSL ... | bash`) that auto-detects hardware, OS, and provisions the entire platform in under 3 minutes.
- [ ] **Mini-Task 16.6.2**: Package 100% offline air-gapped commercial release tarball (`deploy-platform-enterprise-v1.0.tar.gz`) containing pre-saved Docker images, wheels, Caddy, and Ollama weights for high-security defense/banking clients.
- [ ] **Mini-Task 16.6.3**: Build interactive web first-run onboarding wizard (`/setup`): guides customer administrator through Initial Superadmin Setup, License Key Activation, and Domain Configuration.
- [ ] **Mini-Task 16.6.4**: Implement self-diagnostic platform health tester (`deploy-admin doctor`) verifying all internal daemons, database connections, and Caddy bindings before declaring appliance operational.
