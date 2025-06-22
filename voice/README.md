# pippin – AI-Powered Relocation Intelligence

> _“Moving to a new city? We got you.”_

pippin is your personal AI relocation consultant that plans and executes an
end-to-end move – from immigration paperwork to cultural onboarding.  Under the
hood, we combine realtime conversational AI with automated
back-office workflows, giving employees clarity, compliance and white-glove
support while companies stay focused on productivity.

This repository contains a **monorepo skeleton** that will evolve into the
production platform.  For now it demonstrates – and lets you iterate on – the
core building blocks:

• Frontend (Vue 3) → captures microphone audio, establishes a **WebRTC**
  connection to the OpenAI Realtime API, and streams both speech & data-channel
  events to / from the model.
• Backend (FastAPI) → handles user auth, persists domain data (moves & tasks),
  and mints **ephemeral tokens** that the browser needs to authenticate a
  WebRTC session without ever exposing the server’s secret API key.
• PostgreSQL for durable storage.

Future milestones: automatic function-calls from the LLM to create / update
database records, multi-tenant billing, SOC-2 controls, etc.

## Quick Start

To kick start the app, simply run:

```bash
docker compose up
```
  
### Essentials

Make sure you have the following installed:
- Git: https://git-scm.com/downloads
- Docker: https://docs.docker.com/get-docker/
- Docker Compose: Included with Docker Desktop, or https://docs.docker.com/compose/install/

Create a `.env` file in the project root with the following content:

```env
OPENAI_API_KEY="sk-..."
```

