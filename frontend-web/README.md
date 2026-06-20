# ResiliNet AI Command Center — Frontend Client

Welcome to the frontend application for the **ResiliNet AI Command Center**, a premium geospatial dispatch and monitoring panel designed to coordinate real-time emergency services. 

This client is built using **React**, **Vite**, **Leaflet**, and **Vanilla CSS**, featuring a state-of-the-art dark mode UI with glassmorphism effects, live WebSocket streams, interactive mapping, and incident dispatching capabilities.

---

## 🎨 Visual Design & Aesthetics

The interface is custom-designed from the ground up to feel modern, responsive, and premium:
- **Harmonious Dark Theme**: Built around a deeply rich dark palette (`#0a0f1e` background) using curated CSS variables to ensure high contrast, readability, and modern aesthetics.
- **Glassmorphism**: Panels utilize semi-transparent backdrops (`backdrop-filter: blur(10px)`) with thin borders to create a high-tech layered overlay aesthetic.
- **Micro-Animations & Visual Cues**:
  - Live connection status indicators feature a pulsing green glow for active streams.
  - Interactive map incident markers feature nested pulsing circles to denote ongoing activity.
  - Hover effects on cards, input fields, and custom buttons enhance engagement.
  - Seamlessly styled custom scrollbars prevent generic browser layouts from cluttering the layout.
- **Typography**: Utilizing the clean, modern **Inter** typeface loaded directly from Google Fonts.

---

## 🚀 Core Features

1. **Interactive Geospatial Canvas**:
   - Rendered using **React Leaflet** with OpenStreetMap tiles.
   - Interactive panning, zooming, and marker details.
   - Emergency assets (Hospitals, Fire Stations, Police Stations) plotted as solid color-coded markers based on their category.
2. **Real-Time Dispatch Feeds**:
   - Connects to the backend WebSocket server to instantly receive live dispatches.
   - Prepend incoming updates so the newest incident is always placed at the top of the feed list.
   - Live category count badges for **Critical**, **High**, **Medium**, and **Low** severity levels automatically updated.
3. **Resilient Network Hook**:
   - Implements auto-reconnection with **exponential backoff** (starting at 1.5s, scaling up to 30s) inside a custom React hook (`useDispatchSocket`).
   - Graceful status tracking transitions (Connecting, Connected, Reconnecting, Offline, Error).
   - Clean local state flushing via a "Clear" button.
4. **Manual Dispatch Pinning**:
   - Click anywhere on the map to drop a custom location pin.
   - Opens a floating glassmorphism dispatch modal where users can type a description and submit it.
   - Submissions are sent as POST requests to the backend API (`/reports`), auto-updating the map upon completion.
5. **Interactive Filtering**:
   - Filter the live dispatch sidebar feed dynamically by severity levels (Critical, High, Medium, Low) to isolate high-priority emergencies instantly.

---

## 📂 Project Structure & Component Roles

The workspace components are organized cleanly under the `src/` directory:

```
frontend-web/src/
├── assets/                  # Media and static asset files
├── AlertPanel.jsx           # Panel listing high-priority (CRITICAL / HIGH) summaries
├── AlertPanel.css           # Alert specific styled classes and glow patterns
├── App.jsx                  # Main orchestrator, manages state, layout & styling
├── App.css                  # Grid scaffolding, header stats, and shell styles
├── IncidentFeed.jsx         # Renders the vertical stream of active dispatch cards
├── IncidentFeed.css         # Styling, severity left-border highlights, badges
├── MapView.jsx              # Main Leaflet layout, marker popups & manual pin reports
├── useDispatchSocket.js     # Custom React hook managing the WebSocket connection
├── index.css                # Global CSS variables, fonts, reset, and scrollbar
└── main.jsx                 # Vite application mount point
```

---

## 🔌 API & Integration Specifications

The client communicates with the backend via the following interface:

| Protocol | Endpoint | Method | Description | Fallback Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **HTTP** | `http://localhost:8000/stations` | `GET` | Retrieve list of operational stations. | Uses built-in Pune-centered seed stations if offline. |
| **HTTP** | `http://localhost:8000/incidents` | `GET` | Fetches historical incidents snapshot. | Fails silently; live feed still loads via WebSocket. |
| **HTTP** | `http://localhost:8000/reports` | `POST` | Submits a manual incident dispatch. | Informs user with validation feedback status message. |
| **WS** | `ws://localhost:8000/ws/dispatches` | *Stream* | Live duplex event stream of dispatch messages. | Starts connection attempts and auto-reconnects. |

### Expected Data Model (WebSocket Dispatch Update)
```json
{
  "incident_id": "string-uuid",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "dispatch_text": "string (Description of incident)",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "category": "string (Category header)",
  "recommended_responder_id": "string | null"
}
```

---

## 🛠️ Setup & Running Locally

### Prerequisites
- **Node.js**: `v18.x` or higher recommended.
- **npm**: `v9.x` or higher.

### Installation
Clone the repository, navigate to the `frontend-web` folder, and install the dependencies:
```bash
cd frontend-web
npm install
```

### Run the Development Server
Start the local server with hot module replacement (HMR) enabled:
```bash
npm run dev
```
The application will start, typically accessible at [http://localhost:5173](http://localhost:5173).

### Production Build & Preview
To create an optimized production bundle and inspect the final build:
```bash
npm run build
npm run preview
```

---

## 🤝 Developer Workspace Ownership

- **Saurabh**: Led the main grid framework, Leaflet Map configuration, coordinates pinning system, WebSocket hooks with exponential backoff logic, and integration.
- **Vaishnav**: Led the Incident Feed panel interface, Emergency Alert cards, severity badges formatting, and responsive scroll container styling.

