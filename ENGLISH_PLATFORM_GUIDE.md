# 🚀 100% Self-Hosted Commercial Cloud Platform - Comprehensive Architecture & Product Guide
## Project: Sovereign Vercel + Render Private Cloud Engine (Product-Based Enterprise Software)

> **Commercial Vision**: This platform is designed not merely as an internal project, but as a **high-value commercial B2B software product (Enterprise On-Premise Appliance & Private Cloud SaaS)**. It allows IT enterprises, software agencies, startups, universities, and banks to deploy and host any web application (React, Next.js, Python FastAPI, Node.js, Go, PHP) on their own dedicated hardware with **$0 external cloud fees, zero vendor lock-in, and 100% data sovereignty**.

---

## 💼 1. Business & Commercial Monetization Model

This platform is engineered to be packaged and sold through three distinct commercial channels:

### Model 1: Enterprise On-Premise License (Perpetual / Annual License Key)
* **Target Audience**: Corporate IT departments, fintech firms, healthcare organizations, and software agencies who refuse to put sensitive code or client data on public cloud infrastructure (AWS/Vercel/Render).
* **Delivery**: Clients deploy the software on their own dedicated bare-metal server or internal VMware / Proxmox cluster.
* **Licensing**: Activation via an **Asymmetric Cryptographic License Key (RSA-4096 / Ed25519)** that runs completely air-gapped without requiring an internet connection.
* **Pricing Potential**: \$1,000 to \$15,000+ per server node / year.

### Model 2: Multi-Tenant Private Cloud SaaS (Subscription Hosting Provider)
* **Target Audience**: Freelancers, students, indie hackers, and SMBs looking for high-performance hosting at a fraction of public cloud costs.
* **Operation**: You host the platform on your own high-spec bare-metal hardware.
* **Monetization**: Charge monthly recurring subscriptions (e.g., \$9/mo Starter, \$29/mo Pro, \$99/mo Business) with automated tenant resource metering (CPU-hours, RAM quotas, custom domains).

### Model 3: White-Label Agency Appliance
* **Target Audience**: Digital agencies who want to provide their clients with a custom-branded deployment portal under their own company domain (e.g., `https://deploy.agencyname.com`) with custom branding, logos, and branded CLI executables.

---

## 🔒 2. Zero External Dependencies Guarantee (100% Self-Contained)

Our platform operates with **zero dependencies on third-party paid cloud providers**:

| Component | Standard Paid Cloud Equivalent | Our 100% Self-Hosted Solution | Monthly Cloud Cost |
| :--- | :--- | :--- | :---: |
| **Edge Proxy & Auto SSL** | Cloudflare Enterprise / AWS ALB (\$50-\$200/mo) | **Caddy 2 + Internal CA / Free Let's Encrypt** | **\$0** |
| **Container Sandbox** | AWS ECS / EKS / Fargate (\$100+/mo) | **Host Docker Engine CE + cgroups v2** | **\$0** |
| **Container Registry** | AWS ECR / Docker Hub Pro (\$15-\$50/mo) | **Local Private Registry v2 (`127.0.0.1:5000`)** | **\$0** |
| **Managed Relational DB** | AWS RDS PostgreSQL (\$30-\$150/mo) | **Isolated PostgreSQL 16 Alpine Engine** | **\$0** |
| **Managed In-Memory Cache** | AWS ElastiCache Redis (\$25-\$80/mo) | **Isolated Redis 7 Alpine Engine** | **\$0** |
| **AI Error Diagnostic Doctor** | OpenAI GPT-4 API (\$30-\$100/mo) | **Host-Local Ollama AI (Mistral-7B / DeepSeek)** | **\$0** |
| **TOTAL RUNTIME EXPENSE** | **\$250 - \$800+ Every Single Month** | **Our Sovereign Server Platform** | **\$0 LIFETIME** |

---

## 🏢 3. Multi-Tenancy & Workspace Isolation Architecture

Because this is a commercial-grade product, multiple independent organizations and teams can securely share the same server without cross-contamination:

```
+-----------------------------------------------------------------------------------+
|                        OUR CLOUD PLATFORM ENGINE                                  |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ TENANT 1: Acme Corp ]                    [ TENANT 2: FinTech Global ]          |
|  - Tier: Pro (Max 20 Projects, 16GB RAM)    - Tier: Enterprise (Unlimited, Airgap)|
|  - Members: Alice (Owner), Bob (Dev)        - Members: David (Admin), Sara (Dev)  |
|                                                                                   |
|  +-----------------------------+            +-----------------------------+       |
|  | Isolated Bridge Zone A      |            | Isolated Bridge Zone B      |       |
|  | - Next.js App (3 Replicas)  |            | - FastAPI Microservice      |       |
|  | - PostgreSQL 16 (Private)   |            | - Redis 7 Cache             |       |
|  +-----------------------------+            +-----------------------------+       |
|                                                                                   |
|  SECURITY BOUNDARIES:                                                             |
|  - Acme Corp CANNOT access, inspect, or ping FinTech Global's network or data     |
|  - Each tenant operates within strict cgroups v2 memory & CPU resource quotas     |
+-----------------------------------------------------------------------------------+
```

### Role-Based Access Control (RBAC):
1. **Owner**: Full administrative control, organization deletion, billing/licensing, team invitations.
2. **Admin**: Project creation, managed database provisioning, secret variable modification, rollback authorization.
3. **Developer**: Source deployment (`deploy`), live log streaming, runtime metric inspection.
4. **Viewer**: Read-only dashboard access for project managers and QA testers.

---

## 🔑 4. Asymmetric Cryptographic Licensing System (RSA-4096 / Ed25519)

When distributing the software to commercial clients:
1. **License Generation**: The platform vendor generates a digitally signed `license.lic` file containing:
   - Licensee Company Name
   - Hardware Machine Fingerprint (CPU ID + Machine-ID hash binding)
   - Expiration Timestamp
   - Maximum Concurrent Projects & Max Worker Nodes
   - Feature Flags (`ai_doctor_enabled`, `white_label_enabled`, `clustering_enabled`)
2. **Offline Verification**:
   ```bash
   deploy license activate /path/to/license.lic
   ```
   The control plane verifies the signature locally using the embedded public key. If the license expires, existing running containers remain active, but new deployments are gracefully restricted until renewed.

---

## 🌐 5. Dual HTTPS & Networking Architecture

Every project is exposed **strictly over secure HTTPS (TLS 1.3)**:

### Mode A: Local Wi-Fi / LAN Mode (`https://*.deploy.local`)
* Powered by Caddy's built-in **Internal Certificate Authority (Internal CA)**.
* Automatically generates valid SSL certificates without needing an internet connection.
* Any laptop, mobile phone, or workstation on the local Wi-Fi accesses the application with a green security lock (🔒 Secure HTTPS).

### Mode B: Worldwide Public Live Internet Mode (`https://my-app.yourdomain.com`)
* **Method 1: Zero-Config Cloudflare Tunnel (`cloudflared`)**:
  Allows instant worldwide public URLs (e.g. `https://my-app.trycloudflare.com`) on any residential Wi-Fi or mobile hotspot with **zero router port-forwarding required**.
* **Method 2: Custom Production Domain (Bring Your Own Domain)**:
  Clients point their domain's DNS A-Record or CNAME to the server's public IP. Caddy automatically requests and auto-renews free **Let's Encrypt / ZeroSSL** certificates via ACME challenge.

---

## 🏷️ 6. Custom Domain Selection & Real-Time Availability Check

Users have complete freedom to choose their preferred project domain name, protected by automated collision detection:

```
[ Developer runs `deploy` or creates project in Web Dashboard ]
                         |
                         v
          ? Enter desired domain: "my-shop"
                         |
                         v
  [ FastAPI Query: GET /api/v1/domains/check?name=my-shop ]
                         |
           +-------------+-------------+
           |                           |
     [ NOT TAKEN ]                 [ ALREADY EXISTS ]
           |                           |
           v                           v
  ✔ "my-shop" is available!    ❌ "Domain 'my-shop' already exists!"
  Reservations confirmed.      💡 Suggestions:
                                  1. my-shop-app
                                  2. my-shop-2
                                  3. my-shop-live
```

* **Database Level**: The PostgreSQL `projects` table enforces `UNIQUE(subdomain)`.
* **Web Dashboard**: An interactive input field debounces keypresses (300ms) to display a live green badge (`✔ Available`) or red alert (`❌ Taken`).

---

## 🔄 7. Git Continuous Deployment & Automatic Tech-Stack Detection

### Step 1: Push Code to GitHub / Git
Developers write code and push to their remote repository as usual:
```bash
git add . && git commit -m "feat: core release" && git push origin main
```

### Step 2: Interactive CLI Repository Selection
In their terminal, the developer runs:
```bash
deploy repo
```
The CLI displays an interactive terminal picker listing all repositories associated with their account:
```text
? Select a repository to deploy:
  ❯ my-nextjs-portfolio (GitHub)
    fastapi-ecommerce-backend (GitHub)
    fullstack-food-delivery (Monorepo)
    react-chat-app (GitHub)
    [+] Enter custom Git URL...
```
The developer selects the repository using the arrow keys (`↑` / `↓`) and presses `ENTER`.

### Step 3: 3-Tier Polyglot Engine Automatically Decides Frontend vs. Backend
The server inspects the cloned codebase without requiring any manual configuration:
* **Frontend Web App Detected** (Presence of `package.json` with `next`, `react`, `vite`, or `vue`):
  - Automatically runs `npm ci` and `npm run build`.
  - Configures output directory (`.next/standalone` or `dist/`).
  - Sets internal container port to `3000` or `80`.
* **Backend REST API Detected** (Presence of `requirements.txt`, `main.py`, `server.js`, or `go.mod`):
  - Automatically configures Python virtualenv or Node backend.
  - Launches with `uvicorn main:app --host 0.0.0.0 --port 8000` or `node server.js`.
  - Sets internal container port to `8000` or `5000`.
* **Fullstack Monorepo Detected** (Presence of both `/frontend` and `/backend` directories):
  - Prompts the developer: `Detected Monorepo: Deploy Frontend, Backend, or Both?`

---

## 📦 8. Package Management & `node_modules` Handling

Developers never push `node_modules/` or `.venv/` to Git because they are hundreds of megabytes in size and contain OS-specific compiled binaries.

### How our server handles dependencies:
1. **Clean Clone**: The server clones only the clean source code and manifest files (`package.json` and `package-lock.json`).
2. **Linux-Native Clean Install (`npm ci`)**: Dependencies are downloaded and compiled directly inside an isolated Linux container, eliminating binary mismatches (such as Windows `bcrypt` or `sharp` crashing on Linux).
3. **BuildKit Package Cache Mounts (`--mount=type=cache`)**:
   - The first build downloads packages and caches them in `/var/lib/deploy/buildkit/cache`.
   - On subsequent deployments, if `package.json` has not changed, **the server reuses the cached packages from local disk**.
   - **Result**: Subsequent builds finish in **3 to 5 seconds**!

---

## 🔒 9. Zero-Trust API Key & Secret Management (`.env`)

Sensitive credentials (OpenAI API keys, Stripe secrets, database URLs) are protected by our Zero-Trust architecture:

### 3 Methods for Developers to Inject Keys:
1. **Direct CLI Command**:
   ```bash
   deploy env set OPENAI_API_KEY="sk-proj-xxxxxxxxxxxx"
   ```
2. **Bulk One-Shot Import**:
   ```bash
   deploy env push
   ```
   Reads local `.env`, strips whitespace and comments, encrypts all values via AES-256-GCM, and pushes directly to the server vault.
3. **Web Dashboard Portal**:
   Enter environment variables in the project settings tab with masked values (`********`).

### Security Architecture:
* **Never in Git**: Keys are excluded during upload and never sent to GitHub.
* **Never on Disk in Plaintext**: Keys are encrypted at rest in PostgreSQL using AES-256-GCM.
* **In-Memory Injection**: At container startup, keys are decrypted in server RAM and injected directly into the container's process environment (`process.env` in Node, `os.getenv` in Python).
* **WAF Protection**: Caddy actively blocks any public requests matching `/.env*` with HTTP 403 Forbidden.

---

## 🖥️ 10. Project-Wise Web Dashboard & Multi-Stream Log Hub

While developers have full control via the CLI, the **Next.js 16 Web Management Console** provides a unified visual control center:

### 1. Project Overview (`/projects/[id]`)
* **Live HTTPS URL Badge**: Click-to-open button.
* **Health Indicators**: Real-time container state (Healthy, Unhealthy, Draining).
* **Active Replicas**: Visual node cards showing Private IP, CPU %, and RAM consumption.
* **Resource Graphs**: Historical charts of CPU and Memory utilization over time.
* **Git Commit Provenance**: Commit SHA, author, branch, and deployment duration.

### 2. Multi-Stream Live Log Hub (`/projects/[id]/logs`)
A high-performance virtualized dark terminal streaming logs via Server-Sent Events (SSE) with a specialized **Tab Switcher**:
* 🌐 **[Frontend Logs]**: Client and server-side rendering logs from Next.js/React.
* ⚙️ **[Backend Logs]**: Incoming HTTP requests, database queries, and error traces from FastAPI/Node.
* 🔨 **[Build Logs]**: Compiler output, npm/pip installation progress, and BuildKit execution steps.
* 🗄️ **[Database Logs]**: Internal connection and query logs from PostgreSQL and Redis.
* **Features**: Live text filter (`ERROR`, `WARN`, `INFO`), keyword search bar, and 1-click **Download Logs (.txt)** button.

---

## ⚡ 11. Two Pro Killer Features

### Feature 1: GitHub Webhook Continuous Deployment (CD)
* The platform exposes an endpoint: `POST /api/v1/webhooks/github`.
* When a developer runs `git push origin main`, GitHub sends a webhook signed with HMAC SHA-256 (`X-Hub-Signature-256`).
* The platform automatically verifies the signature, clones the new commit, builds the container, tests health, and switches traffic. **Zero manual commands required!**

### Feature 2: Sub-100ms Instant Atomic Rollback (`deploy rollback`)
* If a newly deployed version has a critical bug in production, the developer does not need to rebuild.
* Running `deploy rollback` launches new replicas from the **previously cached Docker image tag in the local registry** within 2 seconds.
* Caddy hot-swaps the upstream proxy targets in **under 100 milliseconds** with zero downtime!

---

## 💻 12. Developer CLI Command Reference (Cheat Sheet)

| Command | Action Performed |
| :--- | :--- |
| `deploy login` | Authenticates developer via GitHub, Google, or Offline Admin credentials |
| `deploy` | Automatically detects local project runtime and deploys to HTTPS |
| `deploy repo` | Launches interactive terminal selector to deploy any connected Git repository |
| `deploy env set KEY=VAL` | Encrypts and stores environment variable in the AES-256 secrets vault |
| `deploy env push` | Bulk parses and uploads local `.env` file to the platform vault |
| `deploy db create postgres <name>` | Provisions an isolated Render-style managed PostgreSQL 16 database |
| `deploy db create redis <name>` | Provisions an isolated Render-style managed Redis 7 in-memory cache |
| `deploy scale --min 3 --max 10` | Configures horizontal autoscaler replica thresholds and CPU targets |
| `deploy status <app>` | Displays active replica count, CPU/RAM utilization, and live URL |
| `deploy logs <app> --tail 50 -f` | Streams real-time container logs directly to the terminal |
| `deploy rollback [id]` | Triggers sub-100ms atomic rollback to the previous healthy deployment |
| `deploy doctor` | Local AI diagnostic engine scans error logs and provides remediation code |
| `deploy destroy <app>` | Gracefully tears down containers, routes, and associated volumes |

---

## ⚡ 13. Turnkey 1-Command Customer Appliance Installer

When a client purchases the software for on-premise installation, they run a single shell command on their clean Ubuntu 22.04 / 24.04 LTS server:

```bash
curl -fsSL https://get.ourplatform.com/install.sh | bash
```

**Automated 3-Minute Provisioning:**
1. Hardens Linux kernel parameters (`somaxconn = 65535`, `bbr` congestion control).
2. Sets up cgroups v2 controllers and systemd slices.
3. Installs Docker CE, Caddy 2, Python 3.12, Redis 7, PostgreSQL 16, and local Ollama.
4. Launches the Web Setup Wizard on `http://server-ip/setup` to configure superadmin credentials and upload the enterprise license key.

---

## 📊 14. Master Architecture Summary

* **WBS Structure**: 17 Core Engineering Epics, 85 Tasks, 420 Granular Mini-Tasks.
* **100% Self-Hosted**: Zero dependence on AWS, GCP, Vercel, or Render.
* **Enterprise High Availability**: Dynamic autoscaling from 3 to 10+ replicas, zero-downtime blue/green deployment, and in-memory rate limiting.
* **Commercial-Ready**: Multi-tenancy, cryptographic offline licensing, white-labeling, and turnkey installation make this a complete, market-ready enterprise product!
