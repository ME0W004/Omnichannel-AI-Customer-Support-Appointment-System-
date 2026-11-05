# Enterprise Deployment & Configuration Guide

This guide provides a step-by-step walkthrough to deploy, configure, and orchestrate all components of the system:
**Chatwoot (Omnichannel Inbox) + Dify (RAG & Knowledge Brain) + FastAPI (Bridge Middleware) + Typebot & Google Calendar**
on an enterprise Linux server (Ubuntu 22.04 / 24.04 LTS).

---

## 1. Server Prerequisites

- **Operating System:** Ubuntu 22.04 or 24.04 LTS (x86_64)
- **Recommended Hardware Specifications:**
  - 4 to 8 vCPUs
  - 16 to 32 GB RAM
  - Minimum 80 GB NVMe SSD storage
- **Base Package Installation:**
  ```bash
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y git curl wget ufw
  ```
- **Docker and Docker Compose Installation:**
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  ```

---

## 2. Create Shared Docker Network

To allow all microservices (Chatwoot, Dify, Middleware, Caddy) to communicate securely over an internal virtual bridge without exposing unnecessary internal ports to the public internet:

```bash
docker network create omnichannel-net
```

---

## 3. Deploying Dify (AI Knowledge Base & RAG Engine)

1. Clone the official Dify repository:
   ```bash
   git clone https://github.com/langgenius/dify.git /opt/dify
   cd /opt/dify/docker
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. In Dify's `docker-compose.yaml`, attach the external `omnichannel-net` network to the `api` and `web` services:
   ```yaml
   networks:
     default:
     omnichannel-net:
       external: true
   ```

4. Start Dify services:
   ```bash
   docker compose up -d
   ```

5. Access the Dify dashboard (e.g., `http://SERVER_IP:3000` or `https://brain.yourdomain.com`) and complete the admin onboarding.

### Anti-Hallucination Guardrails Configuration:
In the **Knowledge** section, upload official business documents, clinical protocols, tariffs, and operating policies:
- **Segment Mode:** Custom
- **Segment Length:** 500 Tokens
- **Overlap:** 50 Tokens (10%)
- **Index Mode:** High Quality (using embedding models like `text-embedding-3-small` or local BGE)
- **Retrieval Setting:**
  - **Search Method:** Hybrid Search (Vector Embedding + Full-text Keyword)
  - **Top K:** 3
  - **Score Threshold:** `0.75` (Blocks any chunk with similarity lower than 75%)
  - **Reranker Model:** Enabled (BGE Reranker or Cohere Rerank v3)

#### Production Anti-Hallucination System Prompt:
```text
You are the official verified medical/service AI assistant.

CRITICAL GUARDRAILS (STRICT ZERO-HALLUCINATION RULES):
1. You must answer strictly and solely based on the retrieved context provided in the knowledge base.
2. Never guess, infer, or prescribe treatments or tariffs that are not explicitly documented.
3. If the user's question cannot be answered with 100% certainty from the provided context, output ONLY the token:
   [TRIGGER_HUMAN_HANDOFF]
4. If the user exhibits extreme frustration, anger, mentions medical emergencies, or demands a human operator, output ONLY the token:
   [TRIGGER_HUMAN_HANDOFF]
```

Next, open the **Develop** tab of your Dify chat app and copy the **API Secret Key** (formatted as `app-...`).

---

## 4. Deploying Chatwoot (Customer Inbox & Agent Portal)

1. Clone Chatwoot's deployment repository:
   ```bash
   git clone https://github.com/chatwoot/chatwoot.git /opt/chatwoot
   cd /opt/chatwoot
   ```

2. Prepare environment variables:
   ```bash
   cp .env.example .env
   ```

3. Configure `SECRET_KEY_BASE`, database credentials, and attach the `omnichannel-net` network to the Chatwoot containers.

4. Initialize the Chatwoot database and boot the stack:
   ```bash
   docker compose run --rm rails bundle exec rails db:chatwoot_prepare
   docker compose up -d
   ```

5. Log in to Chatwoot (`https://chat.yourdomain.com`).
6. Create an administrator account, configure inboxes (Website widget, Telegram, or WhatsApp), and create a team named **"Front Desk / Human Support"**.
7. Navigate to **Settings -> Profile Settings** and generate an **API Access Token**.
8. Navigate to **Settings -> Integrations -> Webhooks** and register a new webhook:
   - **Webhook URL:** `http://middleware:8000/webhook/chatwoot` (or `https://api.yourdomain.com/webhook/chatwoot`)
   - **Subscriptions:** Check `Message Created` and `Conversation Created`.

---

## 5. Deploying FastAPI Middleware Bridge

1. Navigate to the project directory:
   ```bash
   cd /opt/omnichannel-ai
   ```

2. Configure environment variables in `middleware/.env`:
   ```bash
   cp middleware/.env.example middleware/.env
   ```

3. Update the values:
   ```env
   CHATWOOT_BASE_URL=http://chatwoot-web:3000
   CHATWOOT_API_ACCESS_TOKEN=your_chatwoot_token_here
   CHATWOOT_ACCOUNT_ID=1

   DIFY_API_BASE_URL=http://dify-api:5001/v1
   DIFY_API_KEY=app-your_dify_token_here

   GOOGLE_CALENDAR_ID=your_clinic_calendar_id@group.calendar.google.com
   GOOGLE_SERVICE_ACCOUNT_FILE=google-credentials.json
   CLINIC_TIMEZONE=UTC
   TYPEBOT_PUBLIC_URL=https://bot.yourdomain.com/clinic-booking
   ```

4. Build and start the Middleware and Caddy reverse proxy:
   ```bash
   docker compose up -d --build
   ```

5. Verify service health:
   ```bash
   curl http://localhost:8000/health
   # Expected response: {"status":"healthy","service":"Omnichannel AI Bridge",...}
   ```

---

## 6. Google Calendar Service Account Setup (Automated Booking)

For secure, server-to-server calendar scheduling without requiring patients to authenticate:

1. Open [Google Cloud Console](https://console.cloud.google.com) and create a project.
2. In **APIs & Services -> Library**, enable the **Google Calendar API**.
3. In **Credentials -> Create Credentials**, select **Service Account** (e.g., `clinic-booking-bot@project-id.iam.gserviceaccount.com`).
4. Under the **Keys** tab of the newly created service account, click **Add Key -> Create new key (JSON)**.
5. Save the file as `google-credentials.json` and place it in the `middleware/` directory.
6. Open the clinic calendar in [Google Calendar](https://calendar.google.com):
   - Right-click the calendar and select **Settings and sharing**.
   - Under **Share with specific people or groups**, add the Service Account email.
   - Set permissions to **Make changes to events**.
   - Copy the **Calendar ID** from the bottom of the settings page and assign it to `GOOGLE_CALENDAR_ID` in `.env`.

---

## 7. Phase 1: Web Live Chat Widget Integration

1. In Chatwoot, go to **Settings -> Inboxes -> Add Inbox**.
2. Select **Website**:
   - **Website Name:** Clinic Official Portal
   - **Website Domain:** `yourdomain.com`
   - **Widget Color:** Your corporate brand color
3. Insert the generated SDK snippet into the `<body>` of your web pages. A turnkey implementation is provided in [`web/widget-demo.html`](../web/widget-demo.html).

---

## 8. Phase 2: Telegram Bot Integration

The architecture connects messaging channels to the same central logic without changing backend code:

1. In Telegram, message **@BotFather**, create a new bot, and copy the API token.
2. In Chatwoot, navigate to **Settings -> Inboxes -> Add Inbox** and select **Telegram**.
3. Paste the Bot token.
4. Telegram messages now automatically leverage the same Dify RAG, appointment booking, and human handoff mechanisms.

---

## 9. Phase 3: WhatsApp Business API Integration

1. Register for the WhatsApp Cloud API in Meta Developer Portal.
2. In Chatwoot, select **Add Inbox -> WhatsApp**.
3. Connect your WhatsApp Phone Number ID and System User Access Token.
4. WhatsApp customer chats will be triaged by the AI assistant and routed to human staff when necessary.

---

## 10. Zero-Fail Human Handoff Verification Matrix

| Scenario | Customer Input | Expected System Behavior |
| :--- | :--- | :--- |
| **1. Grounded RAG Query** | "What are the clinic's operating hours?" | AI delivers verified answer from knowledge base with citations. |
| **2. Direct Human Request** | "Please connect me to a human operator" | Middleware instantly sets `human-needed` label, unassigns bot, and notifies human staff. |
| **3. Out-of-Scope (RAG Miss)** | "Do you perform open-heart surgery?" (in a dermatology clinic) | Dify detects score below 0.75, emits handoff token, and hands conversation to receptionist. |
| **4. Frustration / Anger** | "This service is unacceptable! I want to file a complaint!" | Sentiment filter immediately escalates conversation to high-priority human queue. |
| **5. Silence After Handoff** | Follow-up user messages | AI bot stays completely silent while conversation has `human-needed` label. |
| **6. Calendar Booking** | "I'd like to book an appointment next week" | Intent detected; returns personalized interactive Typebot link; locks slot in Google Calendar. |
