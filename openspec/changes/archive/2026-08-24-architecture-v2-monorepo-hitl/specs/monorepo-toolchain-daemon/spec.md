## Purpose

Provides a unified root-level development, build, and daemonization toolchain combining Node.js frontend tooling with Python `uv` package management for single-command developer operations.

## ADDED Requirements

### Requirement: Unified Toolchain Setup and Development Orchestration
The system SHALL provide unified package scripts in root `package.json` to install dependencies and run full-stack hot-reload development with a single command.

#### Scenario: Running one-command setup
- **WHEN** developer runs `npm run setup`
- **THEN** system executes frontend dependency install (`pnpm/npm install`) and backend environment synchronization (`uv sync`) without requiring manual venv activation

#### Scenario: Running concurrent development
- **WHEN** developer runs `npm run dev`
- **THEN** system concurrently spawns Vite dev server on port 5173 and FastAPI uvicorn server on port 8000 with hot-reloading

### Requirement: Monorepo Single-Port Production Build
The system SHALL compile the frontend SPA into static assets hosted directly by the FastAPI backend under `/static` and index routes.

#### Scenario: Building and serving single-port artifact
- **WHEN** developer runs `npm run build` followed by `npm run start`
- **THEN** system serves both REST APIs and the full SPA user interface from `http://localhost:8000`

### Requirement: Background Daemonization and Health Monitoring
The system SHALL support headless background daemon execution on Windows with status inspection and graceful termination commands.

#### Scenario: Launching background daemon
- **WHEN** developer runs `npm run daemon`
- **THEN** system starts the FastAPI service as a background daemon process, logs output to `data/logs/service.log`, and verifies HTTP health endpoint on `http://127.0.0.1:8000/api/health`
