# pippin – AI Assistant for Opentrons FLEX

Pippin is an AI-powered assistant designed to simplify the use of the Opentrons FLEX robotic platform. It provides a user-friendly interface for managing protocols, runs, and robot settings, leveraging OpenAI's capabilities to enhance user experience.
This project is built with a modern tech stack including FastAPI, React, and Docker, ensuring a robust and scalable solution for laboratory automation.

## Quick Start

### Prerequisites

Ensure you have the following installed:
- Git: https://git-scm.com/downloads
- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/

### Setup

1. Clone the repository and navigate into it:
   ```bash
   git clone <REPO_URL>
   cd pippin
   ```
2. Create a `.env` file in the project root with the following content:
   ```env
   OPENAI_API_KEY="sk-..."
   EXTERNAL_API_BASE_URL="http://<ROBOT_IP_OR_HOST>/api"
   ```
   - `OPENAI_API_KEY`: your OpenAI API key.
   - `EXTERNAL_API_BASE_URL`: base URL for the Opentrons FLEX API (e.g., `http://192.168.1.100/api`).
3. Start the services:
   ```bash
   docker compose up
   ```
4. Access the frontend at http://localhost:5173 and the backend API docs at http://localhost:8000/docs.

## Opentrons API Endpoint Summary

For full endpoint details, see `backend/instructions.txt`. Key endpoints include:

- **Blink Lights**: `POST /blink` – `{ "seconds": <number> }`
- **Advanced Settings**: `GET /settings`
- **Change Setting**: `POST /settings` – `{ "id": "<setting_id>", "value": <boolean|null> }`
- **Robot Settings**: `GET /robot/settings`
- **Pipette Settings**: `GET /settings/pipettes`, `PATCH /settings/pipettes/{pipette_id}`
- **Calibration Status**: `GET /calibration/status`
- **Attached Pipettes**: `GET /pipettes`
- **Disengage Motors**: `POST /motors/disengage` – `{ "axes": ["x","y","z_l"] }`
- **Protocol Management**:
  - Upload: `POST /protocols` (multipart/form-data)
  - List: `GET /protocols`
- **Run Management**:
  - Create Run: `POST /runs` – `{ "data": { "protocolId": "<id>" } }`
  - Control Run: `POST /runs/{runId}/actions` – `{ "data": { "actionType": "<play|pause|stop>" } }`
  - List Commands: `GET /runs/{runId}/commands`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

