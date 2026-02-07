# ⚓ Maritime Intelligence Backend

The core analytical engine of the Maritime Intelligence System. This backend handles high-frequency AIS data ingestion, real-time spatial analysis via PostGIS, and provides an AI-native interface through the Model Context Protocol (MCP).

## 🔒 Security Features
* **Signal Blackout Detection**: Automatic identification of vessels that have ceased transmission in sensitive areas.
* **Jamming Cluster Analysis**: Spatial clustering of lost signals to pinpoint potential localized interference.
* **Real-time Geofencing**: Instantaneous alerting when high-speed vessels enter critical harbor zones.

---

### 📺 Application Preview (Frontend & Claude) `[DEMO]`
  <br/>

  ### Tactical Map & AI Integration
  This clip demonstrates the real-time vessel tracking on the React dashboard and the MCP tool execution within Claude Desktop.
  
  <video src="https://github.com/user-attachments/assets/d9bd8c22-c82e-45c3-a093-7ba4bdf03e95" width="100%" controls>
    Your browser does not support the video tag.
  </video>


## 🏗️ System Architecture & Perfomance

### The backend is built on a "Producer-Consumer" architecture to handle real-time maritime data streams efficiently:

1.  **AIS Ingestion (Producer)**: Connects to AISStream via WebSockets to receive live vessel positions in the Norwegian EEZ.
2.  **Asynchronous Queue**: Buffers incoming data to prevent system overload during peak traffic.
3.  **Security Engine (Consumer)**: Analyzes each vessel update for geofence violations and anomalies (Dead Reckoning, Jamming Detection).
4.  **Spatial Persistence**: Stores and indexes data in PostGIS for high-performance spatial queries.
5.  **Multi-Channel Delivery**: Updates the React Frontend via WebSockets and provides tools for AI Agents via MCP.

### The system is built on an **asynchronous architecture** using Python's `asyncio` to handle high-volume data streams without blocking execution. 

**Performance Optimization (Batching):**
To ensure database stability and prevent overhead on the PostGIS instance, the system does not write every single AIS message immediately. Instead:
* Incoming data is buffered in an asynchronous queue.
* Vessels are processed and saved in **batches of 50 records**.
* This batching strategy significantly improves write throughput and prevents database connection exhaustion during peak maritime traffic.

---

## 🛠️ Tech Stack

* **Language**: Python 3.13+
* **API Framework**: FastAPI & Uvicorn
* **Database**: PostgreSQL 16 + PostGIS 3.4
* **AI Protocol**: Anthropic Model Context Protocol (MCP)
* **Real-time**: WebSockets & `asyncio`
* **Data Stream**: AISStream.io

---

## 🤖 Model Context Protocol (MCP) Integration

This project implements an **AI-Native interface**. When connected to an MCP-compatible client (like Claude Desktop), the AI gains the following "superpowers":

### Registered Tools
* `get_ships_in_area(lat, lon, radius)` - Allows the AI to query the live database for nearby traffic.
* `analyze_maritime_security(threshold)` - Triggers a deep scan for "dark targets" (vessels that stopped transmitting) and potential GPS jamming clusters.

### Knowledge Resources
* `maritime://critical-infrastructure` - Provides the AI with coordinates of oil platforms and wind farms.
* `maritime://security-zones` - Explains the severity and purpose of various geofences to the AI.

---

## 📁 Project Structure

```text
.
├── backend/                        # Python Backend (FastAPI)
│   ├── src/
│   │   ├── api/                    # Communication Layer (AIS Client, WebSockets)
│   │   ├── core/                   # Intelligence Layer (Anomaly Detection)
│   │   ├── db/                     # Persistence Layer (PostGIS, Session Management)
│   │   ├── mcp/                    # AI Integration (Tools, Prompts, Resources)
│   │   └── main.py                 # FastAPI Application Entry
│   ├── docker/                     # Backend Dockerization
│   │   └── Dockerfile              # API Container Definition
│   ├── tests/                      # Automated Test Suites
│   │   ├── unit/                   # Business Logic & Core Functionality Testing
│   │   ├── api/                    # Integration Tests for REST Endpoints & WebSockets
│   │   └── performance/            # Locust scripts for Stress & Load Testing
│   ├── .env                        # Local Environment Variables
│   └── requirements.txt            # Python Dependencies
├── frontend/                       # React Frontend (Vite)
│   ├── src/                        # UI Components & Logic
│   ├── playwright.config.js        # E2E Test Configuration
│   └── tests/                      # UI Testing (Playwright POM)
├── infrastructure/                 # DevOps & Global Infrastructure
│   ├── db/                         # Database Configuration
│   │   └── init.sql                # PostGIS Schema & Spatial Extensions
│   ├── docker-compose.yml          # Services Orchestration (API, DB, UI)
│   └── .env                        # Infrastructure Environment Variables
└── README.md                       # Project Documentation
```
## 📊 Database Schema (PostGIS)

The system relies on high-performance spatial indexing:
* **`vessels` table**: Uses `GEOGRAPHY` type for accurate distance calculations on the Earth's surface.
* **`geofences` table**: Stores complex polygons representing restricted maritime zones.
* **Spatial Index**: `GIST` indexes are applied to both tables to ensure sub-millisecond query times for `ST_DWithin` and `ST_Contains` operations.

---

## 🚀 Installation & Setup

### Prerequisites
* Python 3.13+
* PostgreSQL with PostGIS extension
* AISStream API Key (obtain from aisstream.io)

## Setup

---

## 🚀 Quick Start (Automated Infrastructure)

This is the recommended way to run the entire stack (Database, Backend, and Frontend) with a single command using Docker Compose.

### Step 0: Run with Docker Compose
1.  **Navigate to Infrastructure**:
    ```bash
    cd infrastructure
    ```
2.  **Launch the Stack**:
    ```bash
    docker-compose up --build
    ```
    *This command pulls the PostGIS image, initializes the database schema, builds the backend container, and starts the frontend.*

3.  **Access the System**:
    * **Frontend**: [http://localhost:5173](http://localhost:5173)
    * **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)
---

### 📄 Example .env File

Create a file named `.env` in your `infrastructure/` directories and populate it with the following variables:

```ini
# --- Database Configuration ---
# Local development (direct access)
DB_URL=postgresql://maritime:maritime_pass@localhost:5432/maritime_intelligence
# Docker infrastructure (internal network access)
# DB_URL=postgresql://maritime:maritime_pass@db:5432/maritime_intelligence

# PostGIS Container Credentials (used by docker-compose)
POSTGRES_USER=maritime
POSTGRES_PASSWORD=maritime_pass
POSTGRES_DB=maritime_intelligence

# --- AIS API Keys ---
# Get your free key at [https://aisstream.io/](https://aisstream.io/)
AIS_API_KEY=your_aisstream_api_key_here

# --- App Settings ---
LOG_LEVEL=INFO
DEBUG=True
MCP_MODE=false # Set to true only when running as a Claude Desktop agent
```

## 🚦 Step-by-Step Installation

Follow these steps in the exact order to get the system running locally.

### Step 1: Database Setup (PostGIS)

Instead of a full infrastructure setup, we will run a standalone PostGIS container and initialize it.

1.  **Pull the PostGIS Image**:
    Run this command to download the official PostGIS image:
    ```bash
    docker pull postgis/postgis:latest
    ```

2.  **Start the Container**:
    Run the container with a default user and password:
    ```bash
    docker run --name maritime-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=maritime_db -p 5432:5432 -d postgis/postgis:latest
    ```

3.  **Initialize the Database**:
    Use the provided SQL script to set up spatial tables and extensions:
    ```bash
    docker exec -i maritime-db psql -U postgres -d maritime_db < infrastructure/db/init.sql
    ```
    *This enables PostGIS and creates the `vessels` table with geographic indexes.*

### Step 2: Backend Setup

The backend handles real-time data ingestion and anomaly detection.

1.  **Configure Environment**:
    Navigate to the `backend` folder and create a `.env` file:
    ```ini
    DATABASE_URL=postgresql://postgres:password@localhost:5432/maritime_db
    ```

2.  **Install Dependencies**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Run the Server**:
    ```bash
    export PYTHONPATH=$PYTHONPATH:. && python src/main.py
    ```
    *Access the API documentation at http://localhost:8000/docs.*
---
### Step 3: Frontend Setup
1.  **Install & Start**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
---

## 🧪 Verification & QA

### 1. Unit Tests
Focuses on isolated business logic, such as anomaly detection algorithms.
```bash
cd backend
PYTHONPATH=. pytest tests/unit
```
### 2. End-to-End UI Tests (Playwright)
Verifies the full user flow using the Page Object Model (POM).

**Current Test Scenarios:**
* **Initial Load**: Verifies if the map, header, and live connection status (WebSocket) are visible on the dashboard.
* **Vessel Interaction**: Clicks a vessel icon and verifies that the Leaflet popup containing MMSI and Speed (SOG) details is displayed correctly.

```bash
cd frontend
# Run all Playwright tests
npx playwright test

# Run a specific test with UI mode for debugging
npx playwright test tests/ui_tests_playwright/tests/maritime-vts.spec.js --ui
```

### 3. API Integration Tests `[IN PROGRESS]` 🏗️
Testing REST endpoints and WebSocket broadcasting stability.

### 4. Performance Benchmarks [IN PROGRESS] 🏗️
Stress testing the system's ability to handle high-density AIS data streams.

### 5. Security Tets [IN PROGRESS] 🏗️

---
### MCP Inspector (Optional) `[DEBUG]` 🏗️
Use the Model Context Protocol Inspector to manually test and debug registered tools, prompts, and resources.

```bash
cd backend
# Run the inspector to debug MCP components in real-time
npx @modelcontextprotocol/inspector env PYTHONPATH=$PYTHONPATH:. python src/main.py
```
---

### 6. Claude Desktop Integration (MCP) `[OPTIONAL]` 🤖
You can integrate this system with Claude Desktop to allow the AI to perform maritime security audits and vessel lookups directly.

1.  **Open Claude Desktop Config**:
    * **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
    * **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2.  **Add the Configuration**:
    Add the following entry to the `mcpServers` section (adjust the path to your project):
    ```json
    {
      "mcpServers": {
        "maritime-intelligence": {
          "command": "python",
          "args": [
            "-m",
            "src.main"
          ],
          "env": {
            "PYTHONPATH": "C:/path/to/your/project/backend",
            "DB_URL": "postgresql://postgres:password@localhost:5432/maritime_db",
            "MCP_MODE": "true"
          },
          "cwd": "C:/path/to/your/project/backend"
        }
      }
    }
    ```

3.  **Restart Claude Desktop**:
    Once restarted, you will see a 🔌 icon indicating that the Maritime Intelligence tools are ready to use.

---

## 📝 TODO / Roadmap

List of ideas and planned features to expand the Maritime Intelligence system.

### 🛡 Security & Intelligence
- [ ] **Advanced Anomaly Detection**: Implement Machine Learning models (e.g., Isolation Forest) to detect unusual vessel patterns based on historical data.
- [ ] **Geofencing Alerts**: Add a UI editor to define custom "No-Go" zones with instant Email notifications.
- [ ] **Weather Overlay**: Integrate OpenWeatherMap API to correlate vessel behavior with sea conditions (e.g., seeking shelter during storms).

### 🖥 Frontend & UX
- [ ] **Dark Mode Support**: Professional high-contrast theme for night watch operations.
- [ ] **Vessel History Trails**: Ability to click a vessel and see its path (breadcrumbs) for the last 24 hours.
- [ ] **Search & Filter**: Advanced filtering by Vessel Type, Flag, or Speed directly on the map.

### 🤖 AI & MCP Integration
- [ ] **Automated PDF Reports**: Generate security shift reports using Claude based on detected anomalies.
- [ ] **Voice Commands**: Integrated voice interface via MCP to ask "Where is the nearest suspicious vessel?".
- [ ] **Multi-Agent Simulation**: Use agents to simulate "Red Team" vessel behavior for training operators.

### ⚙️ DevOps & Infrastructure
- [ ] **CI/CD Pipeline**: Automate Playwright and Unit tests using GitHub Actions.
- [ ] **K8s Deployment**: Helm charts for scaling the system in a Kubernetes cluster.
- [ ] **TimescaleDB Integration**: Optimize storage for massive historical AIS data tracking.

