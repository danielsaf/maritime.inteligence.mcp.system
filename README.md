# ⚓ Maritime Intelligence Backend

The core analytical engine of the Maritime Intelligence System. This backend handles high-frequency AIS data ingestion, real-time spatial analysis via PostGIS, and provides an AI-native interface through the Model Context Protocol (MCP).

---

## 🏗️ System Architecture

The backend is built on a "Producer-Consumer" architecture to handle real-time maritime data streams efficiently:

1.  **AIS Ingestion (Producer)**: Connects to AISStream via WebSockets to receive live vessel positions in the Norwegian EEZ.
2.  **Asynchronous Queue**: Buffers incoming data to prevent system overload during peak traffic.
3.  **Security Engine (Consumer)**: Analyzes each vessel update for geofence violations and anomalies (Dead Reckoning, Jamming Detection).
4.  **Spatial Persistence**: Stores and indexes data in PostGIS for high-performance spatial queries.
5.  **Multi-Channel Delivery**: Updates the React Frontend via WebSockets and provides tools for AI Agents via MCP.

---

## 🛠️ Tech Stack

* **Language**: Python 3.12+
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

## 🚀 Installation & Setup

### Prerequisites
* Python 3.12+
* PostgreSQL with PostGIS extension
* AISStream API Key (obtain from aisstream.io)

### Setup
1.  **Clone and enter directory**:
    ```bash
    cd backend
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment**: Create a `.env` file:
    ```env
    DB_URL=postgresql://user:pass@localhost:5432/maritime
    AIS_API_KEY=your_key_here
    MCP_MODE=false
    ```
4.  **Run the Server**:
    ```bash
    python -m src.main
    ```

---

## 📊 Database Schema (PostGIS)

The system relies on high-performance spatial indexing:
* **`vessels` table**: Uses `GEOGRAPHY` type for accurate distance calculations on the Earth's surface.
* **`geofences` table**: Stores complex polygons representing restricted maritime zones.
* **Spatial Index**: `GIST` indexes are applied to both tables to ensure sub-millisecond query times for `ST_DWithin` and `ST_Contains` operations.

---

## 🔒 Security Features
* **Signal Blackout Detection**: Automatic identification of vessels that have ceased transmission in sensitive areas.
* **Jamming Cluster Analysis**: Spatial clustering of lost signals to pinpoint potential localized interference.
* **Real-time Geofencing**: Instantaneous alerting when high-speed vessels enter critical harbor zones.
