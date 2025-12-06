# Nexus Web Dashboard - UI/UX Planning

**Version:** 1.0
**Date:** 2025-11-30
**Status:** Planning Phase

---

## 🎨 Design Philosophy

### Inspiration: UniFi Controller
The Nexus dashboard draws inspiration from Ubiquiti's UniFi Controller:
- **Clean, modern interface** - Minimal clutter, maximum information
- **Status at a glance** - Immediate visibility into fleet health
- **Logical drill-down** - Overview → Detail → Action workflow
- **Real-time updates** - Live metrics without manual refresh
- **Professional aesthetic** - Suitable for both homelab and production

### Nexus Unique Identity
**Theme:** **Purple & Dark** (not blue like UniFi)
- Primary: Purple/violet shades (#7C3AED, #A78BFA, #DDD6FE)
- Background: Dark mode (#1F2937, #111827)
- Accents: Cyan for healthy, amber for warnings, red for critical
- Professional yet distinctive

---

## 📐 UI Structure

### 1. Main Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [LOGO]  NEXUS     Dashboard  Nodes  Jobs  Logs  ⚙️  [>_]   │  ← Header (60px)
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│   Sidebar    │           Main Content Area                 │
│   (240px)    │           (Responsive)                      │
│              │                                              │
│   • Overview │                                              │
│   • Nodes    │                                              │
│   • Services │                                              │
│   • Jobs     │                                              │
│   • Logs     │                                              │
│   • Settings │                                              │
│              │                                              │
│              │                                              │
│   [Status]   │                                              │
│   3/3 Online │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘

When CLI View is toggled (click [>_] in header):

┌─────────────────────────────────────────────────────────────┐
│  [LOGO]  NEXUS     Dashboard  Nodes  Jobs  Logs  ⚙️  [>_]   │
├──────────────┬────────────────────────┬─────────────────────┤
│              │                        │ CLI View            │
│   Sidebar    │   Main Content Area    │ ┌─────────────────┐ │
│   (240px)    │   (Responsive)         │ │ $ nexus node... │ │
│              │                        │ │ GET /api/nodes  │ │
│              │                        │ │ 200 OK (45ms)   │ │
│              │                        │ │                 │ │
│              │                        │ │ $ nexus node... │ │
│              │                        │ │ GET /api/nodes  │ │
│              │                        │ │ /abc-123        │ │
│              │                        │ │ 200 OK (32ms)   │ │
│              │                        │ │                 │ │
│              │                        │ │ [Auto-scroll ☑] │ │
│              │                        │ └─────────────────┘ │
└──────────────┴────────────────────────┴─────────────────────┘
```

**Rationale:**
- Fixed header for branding and global navigation
- Collapsible sidebar for navigation (mobile-friendly)
- Fleet status summary always visible in sidebar
- Main content area responsive and scrollable
- **NEW:** CLI View panel (toggle via [>_] button)
  - Shows equivalent CLI command for each UI action
  - Displays actual API calls being made
  - Educational and transparent
  - Collapsible to save screen space

---

## 🖥️ CLI View Feature (Unique!)

### Concept
A collapsible panel that shows the "behind-the-scenes" of every UI action:
- **CLI Command Equivalent** - What would you type in terminal?
- **API Call Details** - HTTP method, endpoint, timing
- **Response Status** - Success/error, response time
- **Optional Verbosity** - Show request/response bodies

### Example Scenarios

**Scenario 1: User clicks "Nodes" in sidebar**
```
CLI View shows:
┌─────────────────────────────────────────┐
│ $ nexus node list                       │
│ ↓ GET /api/nodes                        │
│ ← 200 OK (45ms)                         │
│ Found 3 nodes                           │
│                                         │
│ [Show Request] [Show Response]          │
└─────────────────────────────────────────┘
```

**Scenario 2: User clicks on "pi-kitchen" node**
```
CLI View shows:
┌─────────────────────────────────────────┐
│ $ nexus node get f6b858e2-...           │
│ ↓ GET /api/nodes/f6b858e2-...           │
│ ← 200 OK (32ms)                         │
│ Node: pi-kitchen (online)               │
│                                         │
│ [Show Request] [Show Response]          │
└─────────────────────────────────────────┘
```

**Scenario 3: User submits a job**
```
CLI View shows:
┌─────────────────────────────────────────┐
│ $ nexus job submit \                    │
│     --node f6b858e2-... \               │
│     --type shell \                      │
│     --command "df -h"                   │
│ ↓ POST /api/jobs                        │
│   Body: {"node_id": "f6b...", ...}      │
│ ← 201 Created (156ms)                   │
│ Job #45 created and dispatched          │
│                                         │
│ [Show Request] [Show Response]          │
└─────────────────────────────────────────┘
```

### Implementation Details

**Data Structure:**
```javascript
{
  id: "action-123",
  timestamp: "2025-11-30T15:42:31Z",
  cliCommand: "nexus node get f6b858e2-...",
  apiCall: {
    method: "GET",
    endpoint: "/api/nodes/f6b858e2-...",
    headers: { ... },
    body: null
  },
  response: {
    status: 200,
    statusText: "OK",
    timing: 32,  // milliseconds
    body: { ... }
  },
  summary: "Node: pi-kitchen (online)"
}
```

**Storage:**
- Keep last 50 actions in memory (or localStorage)
- Auto-scroll to newest by default
- Allow manual scrolling and pausing
- Clear button to reset history

**Verbosity Levels:**
1. **Compact** (Default) - Just CLI command + status
2. **Normal** - + API endpoint + timing
3. **Verbose** - + Request/response bodies (expandable)

**Visual Design:**
- Monospace font (JetBrains Mono)
- Syntax highlighting for JSON
- Color-coded status (green = 2xx, amber = 4xx, red = 5xx)
- Subtle animations when new action appears
- Dark terminal aesthetic (matches theme)

### Benefits

1. **Educational** - Users learn CLI commands naturally
2. **Debugging** - See exactly what's happening
3. **Transparency** - No "magic" - everything is visible
4. **Copy-Paste** - Click to copy CLI command
5. **Unique** - Not seen in other dashboards (like UniFi)

### Mobile Behavior
- Hidden by default on mobile (< 768px)
- Available via bottom sheet/modal when [>_] tapped
- Swipe down to dismiss

---

## 📄 Pages & Views

### Page 1: Dashboard (Overview)

**Purpose:** Fleet health at a glance, like UniFi's dashboard

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                                    [Auto-refresh] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Nodes   │  │ Jobs    │  │ Alerts  │  │ Uptime  │        │
│  │   3     │  │   12    │  │   0     │  │  99.8%  │        │
│  │ 🟢 All  │  │ 2 Run   │  │ 🟢 Good │  │ 30 days │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Fleet Topology                          [Refresh]     │  │
│  │                                                        │  │
│  │    ┌──────┐                                           │  │
│  │    │ Core │                                           │  │
│  │    └──┬───┘                                           │  │
│  │       ├──── 🟢 pi-kitchen   (75% CPU, 62% RAM)       │  │
│  │       ├──── 🟢 pi-study     (45% CPU, 51% RAM)       │  │
│  │       └──── 🟢 pi-garage    (23% CPU, 38% RAM)       │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ Fleet Metrics       │  │ Recent Activity     │           │
│  │                     │  │                     │           │
│  │ [CPU Line Chart]    │  │ • Job #45 complete  │           │
│  │ [Memory Line Chart] │  │ • pi-kitchen alert  │           │
│  │ [Disk Line Chart]   │  │ • Node registered   │           │
│  │                     │  │ • Job #44 started   │           │
│  └─────────────────────┘  └─────────────────────┘           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Stat Cards** - Quick metrics (like UniFi's client count, traffic, etc.)
- **Topology View** - Visual node hierarchy with live status
- **Live Charts** - Aggregated fleet metrics (last 24h default)
- **Activity Feed** - Recent events, jobs, alerts

**Rationale:**
- Everything important visible without scrolling
- Color-coded health indicators
- Similar to UniFi's main dashboard showing network status
- Real-time updates via WebSocket or polling

---

### Page 2: Nodes (Fleet Management)

**Purpose:** Detailed node list and management, like UniFi's devices page

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Nodes                           [+ Register] [Filters ▼]    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Showing 3 nodes • 3 online, 0 offline                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Name         Status  IP           CPU   RAM   Temp   │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 🟢 pi-kitchen  Online  192.168.1.10  75%   62%  🔥68°C│   │
│  │ 🟢 pi-study    Online  192.168.1.11  45%   51%   52°C│   │
│  │ 🟢 pi-garage   Online  192.168.1.12  23%   38%   48°C│   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  [Click row to view details]                                 │
│                                                               │
└───────────────────────────────────────────────────────────────┘

When clicking a node → Slide-out panel or modal:

┌───────────────────────────────────┐
│ pi-kitchen           [X Close]    │
├───────────────────────────────────┤
│ Status: 🟢 Online                 │
│ IP: 192.168.1.10                  │
│ Last Seen: 5 seconds ago          │
│ Uptime: 15 days                   │
│                                   │
│ ┌─ Metrics (Live) ──────────────┐│
│ │ CPU:  ▓▓▓▓▓▓▓░░░ 75%         ││
│ │ RAM:  ▓▓▓▓▓▓░░░░ 62%         ││
│ │ Disk: ▓▓░░░░░░░░ 24%         ││
│ │ Temp: 🔥 68°C (Warning)       ││
│ └───────────────────────────────┘│
│                                   │
│ ┌─ Historical Charts ───────────┐│
│ │ [CPU 24h line chart]          ││
│ │ [Memory 24h line chart]       ││
│ │ [Temp 24h line chart]         ││
│ └───────────────────────────────┘│
│                                   │
│ [View Logs] [Run Job] [Settings] │
└───────────────────────────────────┘
```

**Key Features:**
- **Sortable table** - Click column headers to sort
- **Live status indicators** - Green/amber/red dots
- **Quick metrics** - CPU/RAM/Temp visible in list
- **Detail panel** - Like UniFi's device properties
- **Action buttons** - Jump to logs, run jobs, configure

**Rationale:**
- Similar to UniFi device list with status badges
- Temperature warnings highlighted (important for Pi)
- Drill-down for details without leaving page
- Quick actions for common tasks

---

### Page 3: Jobs (Task Management)

**Purpose:** Job queue and execution history

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Jobs                              [+ New Job] [Filters ▼]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─ Active Jobs ────────────────────────────────────────┐   │
│  │ #45  pi-kitchen   Shell    🔵 Running   30s ago      │   │
│  │ #46  pi-study     Shell    ⏳ Pending   15s ago      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ Recent Jobs ────────────────────────────────────────┐   │
│  │ ID   Node         Type    Status      Started        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ #44  pi-garage    Shell   ✅ Success   2 min ago     │   │
│  │ #43  pi-kitchen   Shell   ✅ Success   15 min ago    │   │
│  │ #42  pi-study     Shell   ❌ Failed    1 hour ago    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘

Click job → Detail modal:

┌─────────────────────────────────────┐
│ Job #45                  [X Close]  │
├─────────────────────────────────────┤
│ Type: Shell Command                 │
│ Node: pi-kitchen                    │
│ Status: 🔵 Running                  │
│ Started: 30 seconds ago             │
│                                     │
│ ┌─ Command ─────────────────────┐  │
│ │ uptime && free -h             │  │
│ └───────────────────────────────┘  │
│                                     │
│ ┌─ Output (Live) ───────────────┐  │
│ │ 15:42:31 up 15 days, 3:21     │  │
│ │ Mem:  941M  583M  358M        │  │
│ │                               │  │
│ │ [Auto-scrolling...]           │  │
│ └───────────────────────────────┘  │
│                                     │
│ [Cancel Job]                        │
└─────────────────────────────────────┘
```

**Key Features:**
- **Active jobs section** - Prominent, auto-updating
- **Job history** - Filterable and searchable
- **Live output** - For running jobs (WebSocket)
- **Job templates** - Quick actions (future)

**Rationale:**
- Like UniFi's traffic stats or DPI - organized by time
- Running jobs need visibility
- Historical jobs for debugging
- Live output essential for shell jobs

---

### Page 4: Logs (Centralized Logging)

**Purpose:** Fleet-wide log aggregation and search

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Logs                                    [Filters ▼] [🔄]    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─ Filters ────────────────────────────────────────────┐   │
│  │ Node: [All ▼]  Level: [All ▼]  Source: [All ▼]      │   │
│  │ Time: [Last 1 hour ▼]         Search: [______]      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ Log Stream ──────────────────────────────────────────┐  │
│  │ Time       Node        Level    Source      Message   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 15:42:31  pi-kitchen  🔴 ERROR  metrics    Temp...   │  │
│  │ 15:42:15  pi-study    🟡 WARN   jobs       Queue...  │  │
│  │ 15:42:10  pi-garage   🔵 INFO   system     Health... │  │
│  │ 15:41:58  pi-kitchen  🔵 INFO   metrics    CPU 75%   │  │
│  │ 15:41:45  pi-study    🔵 INFO   jobs       Job #45   │  │
│  │                                                       │  │
│  │ [Load More...]                     [Export CSV]      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ☑️ Auto-scroll (Follow mode)                                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Multi-dimensional filters** - Node, level, source, time
- **Search** - Full-text search across logs
- **Color-coded levels** - Red errors, amber warnings, etc.
- **Follow mode** - Auto-scroll like `tail -f`
- **Export** - Download logs as CSV

**Rationale:**
- Similar to UniFi's event log
- Essential for debugging fleet issues
- Real-time updates for active monitoring
- Filters for noise reduction

---

### Page 5: Settings

**Purpose:** Dashboard configuration and system settings

**Sections:**
1. **Dashboard Preferences**
   - Theme (dark/light)
   - Auto-refresh interval
   - Default time ranges

2. **Alerting** (Future)
   - Health thresholds per node
   - Email/webhook notifications
   - Alert history

3. **Users & Auth** (Future)
   - API tokens
   - User management
   - Access control

4. **System**
   - Core server status
   - Database stats
   - Log retention settings

---

### Page 6: Services (Docker Orchestration) - Phase 7

**Purpose:** Deploy and manage Docker containers across the fleet

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Services                           [+ Deploy Service]       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─ Service Catalog ──────────────────────────────────────┐ │
│  │                                                          │ │
│  │  Popular Services:                                       │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐             │ │
│  │  │ 🐳 Pi-hole│ │ 🏠 Home   │ │ 📊 Prom   │             │ │
│  │  │  DNS      │ │  Assistant│ │  etheus   │             │ │
│  │  │  v5.18    │ │  v2024.11 │ │  v2.48    │             │ │
│  │  │           │ │           │ │           │             │ │
│  │  │  0/2 ●    │ │  1/2 ●    │ │  0/2 ●    │             │ │
│  │  │ [Deploy]  │ │ [Manage]  │ │ [Deploy]  │             │ │
│  │  └───────────┘ └───────────┘ └───────────┘             │ │
│  │                                                          │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐             │ │
│  │  │ 📈 Grafana│ │ 🔍 Portain│ │ ⚙️  Custom │             │ │
│  │  │  Analytics│ │  er       │ │  Compose  │             │ │
│  │  │  v10.2    │ │  v2.19    │ │           │             │ │
│  │  │           │ │           │ │           │             │ │
│  │  │  0/2 ●    │ │  2/2 ●    │ │  Upload   │             │ │
│  │  │ [Deploy]  │ │ [Manage]  │ │ [YAML]    │             │ │
│  │  └───────────┘ └───────────┘ └───────────┘             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ Deployed Services ──────────────────────────────────────┐│
│  │ Service      Nodes     Status    CPU    RAM    Actions   ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ Home Assist  moria-pi  🟢 Running 12%    340MB  [●●●]    ││
│  │ Portainer    all (2)   🟢 Running  2%    120MB  [●●●]    ││
│  │                                                           ││
│  └──────────────────────────────────────────────────────────┘│
│                                                               │
└───────────────────────────────────────────────────────────────┘

When clicking "Deploy" button:

┌─────────────────────────────────────┐
│ Deploy Pi-hole                      │
│                            [X Close]│
├─────────────────────────────────────┤
│ Service: Pi-hole DNS Server         │
│ Version: v5.18                      │
│                                     │
│ ┌─ Configuration ─────────────────┐│
│ │ Service Name: pihole            ││
│ │                                 ││
│ │ Deploy to:                      ││
│ │ ○ Single node                   ││
│ │ ● Multiple nodes                ││
│ │ ○ All nodes                     ││
│ │                                 ││
│ │ Select Nodes:                   ││
│ │ ☑ moria-pi (10.243.14.179)     ││
│ │ ☐ default-agent (10.243.29.55) ││
│ │                                 ││
│ │ Environment Variables:          ││
│ │ TZ: [Europe/London        ]     ││
│ │ WEBPASSWORD: [**********  ]     ││
│ │                                 ││
│ │ Ports:                          ││
│ │ 80:80 (HTTP)  ☑                ││
│ │ 53:53 (DNS)   ☑                ││
│ │                                 ││
│ │ [Advanced Options ▼]            ││
│ └─────────────────────────────────┘│
│                                     │
│ [Cancel]              [Deploy Now] │
└─────────────────────────────────────┘
```

**Key Features:**
- **Service Catalog** - Pre-built templates for popular services
  - Pi-hole (DNS ad-blocker)
  - Home Assistant (home automation)
  - Prometheus (metrics collection)
  - Grafana (visualization)
  - Portainer (Docker management UI)
  - Custom Docker Compose uploads

- **Deployment Status** - Visual overview of what's running where
  - Service name and nodes deployed to
  - Running status (green = healthy, amber = degraded, red = failed)
  - Resource usage (CPU, RAM per service)
  - Quick actions menu (view logs, restart, stop, update, remove)

- **Deployment Wizard** - Step-by-step service deployment
  - Select service template or upload custom compose file
  - Choose target nodes (single, multiple, or all)
  - Configure environment variables and ports
  - Advanced options (volumes, networks, restart policies)
  - One-click deployment

- **Service Management** - Per-service control panel
  - Container status and health
  - Resource usage charts
  - Live logs streaming
  - Quick actions (start/stop/restart/update/remove)
  - Container shell access (future)

**CLI Integration:**
All actions show equivalent commands in CLI view:
```
$ nexus service deploy pihole --node moria-pi \
    --env TZ=Europe/London \
    --env WEBPASSWORD=secret \
    --port 80:80 --port 53:53
```

**Technical Implementation:**
- Uses Docker SDK for Python on agent side
- Service definitions stored in Core database
- Deployment state tracked per node
- WebSocket updates for real-time status
- Docker Compose YAML templates embedded or uploaded

**Rationale:**
- **Docker-First:** Makes service deployment the primary use case
- **User-Friendly:** No need to SSH and manually run docker commands
- **Fleet-Wide:** Deploy the same service to multiple nodes with one click
- **Template-Based:** Common services pre-configured for quick deployment
- **Extensible:** Custom Docker Compose support for any service

---

## 🎨 Color Palette

### Primary Colors (Purple Theme)
```css
--nexus-purple-600: #7C3AED;  /* Primary actions, highlights */
--nexus-purple-500: #8B5CF6;  /* Hover states */
--nexus-purple-400: #A78BFA;  /* Secondary elements */
--nexus-purple-300: #C4B5FD;  /* Disabled states */
--nexus-purple-200: #DDD6FE;  /* Borders, dividers */
```

### Background (Dark Mode)
```css
--nexus-gray-900: #111827;    /* Main background */
--nexus-gray-800: #1F2937;    /* Card backgrounds */
--nexus-gray-700: #374151;    /* Hover backgrounds */
--nexus-gray-600: #4B5563;    /* Borders */
```

### Status Colors
```css
--nexus-green:  #10B981;  /* Healthy, online, success */
--nexus-amber:  #F59E0B;  /* Warning, degraded */
--nexus-red:    #EF4444;  /* Critical, error, offline */
--nexus-blue:   #3B82F6;  /* Info, running */
--nexus-cyan:   #06B6D4;  /* Accents, links */
```

### Typography
```css
--font-display: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

**Rationale:**
- Purple distinguishes from UniFi's blue
- Dark mode reduces eye strain
- Status colors follow universal conventions
- Inter for clean UI, monospace for logs/code

---

## 🔧 Technology Stack Options

### Option A: Lightweight (htmx + Alpine.js)
**Pros:**
- Minimal JavaScript
- Server-side rendering
- Fast initial load
- Easy to maintain

**Cons:**
- Less interactive
- Harder to do complex state management
- Limited real-time updates

**Stack:**
- **Backend:** FastAPI (Jinja2 templates)
- **Frontend:** htmx + Alpine.js + Tailwind CSS
- **Charts:** Chart.js or Apache ECharts
- **WebSocket:** Native or simple wrapper

**Best for:** Simple, fast dashboard with server-heavy logic

---

### Option B: Full-Featured (React/Vue)
**Pros:**
- Rich interactions
- Component reusability
- Better real-time updates
- Modern UX patterns

**Cons:**
- More complex build process
- Larger bundle size
- Steeper learning curve

**Stack:**
- **Backend:** FastAPI (REST API only)
- **Frontend:** React + Vite + Tailwind CSS
- **State:** Zustand or React Query
- **Charts:** Recharts or Chart.js
- **WebSocket:** Socket.io-client or native

**Alternative:** Vue 3 + Vite (simpler than React)

**Best for:** Feature-rich dashboard with complex interactions

---

### Recommendation: **Start with Option A, Migrate to B if Needed**

**Phase 6.1:** Build core dashboard with htmx + Alpine.js
- Faster to implement
- Sufficient for current needs
- Can add React components later (islands architecture)

**Phase 6.2+:** Consider React/Vue for advanced features
- Terminal in browser (xterm.js)
- Real-time metrics streaming
- Complex job scheduling UI

---

## 📊 Data Flow

### Real-time Updates

```
Agent Nodes                Core Server              Web Dashboard
    │                          │                         │
    │─── Metrics (30s) ────────>│                         │
    │                          │                         │
    │                          │<─── HTTP: GET /nodes ───│
    │                          │──── JSON: Nodes List ───>│
    │                          │                         │
    │                          │<─── WS: Connect ─────────│
    │                          │──── WS: Metrics push ───>│
    │                          │                         │
    │<─── Job Execute ─────────│<─── POST /jobs ─────────│
    │─── Job Result ──────────>│──── WS: Job update ─────>│
```

**Strategies:**
1. **Initial Load:** HTTP requests for all data
2. **Live Updates:** WebSocket for metrics/jobs/logs
3. **Polling Fallback:** Every 5s if WebSocket fails
4. **Optimistic UI:** Update UI before server confirms

---

## 🎯 User Flows

### 1. Fleet Health Check (Primary Use Case)
1. User opens dashboard
2. Sees stat cards → Fleet healthy? ✅
3. Sees topology → All nodes green? ✅
4. Sees metrics chart → CPU spike? 🔍
5. Clicks node in topology → Drill down
6. Views node details → Temperature warning! 🔥
7. Clicks "View Logs" → Investigates logs
8. Identifies issue → Runs cooling job

**Time:** < 1 minute from dashboard to action

---

### 2. Run Job on Node
1. User goes to Nodes page
2. Clicks node row → Detail panel opens
3. Clicks "Run Job" button
4. Modal: Select job type (Shell)
5. Enters command: `df -h`
6. Click "Submit"
7. Redirected to Jobs page
8. Sees live output in job detail

**Time:** < 30 seconds

---

### 3. Investigate Error
1. User sees alert count > 0 on dashboard
2. Clicks "Alerts" stat card
3. Redirected to Logs page (filtered to errors)
4. Sees recent error from pi-kitchen
5. Clicks node name → Opens node detail
6. Sees temperature chart → Spike at error time
7. Takes corrective action

**Time:** < 1 minute

---

## 📱 Responsive Design

### Breakpoints
- **Mobile:** < 640px (Sidebar collapses to hamburger)
- **Tablet:** 640px - 1024px (Sidebar visible, cards stack)
- **Desktop:** > 1024px (Full layout)

### Mobile Priorities
1. Node list with status
2. Quick metrics (stat cards)
3. Recent jobs/logs
4. Simplified topology (list view)

**Rationale:** Most users will use desktop, but mobile view useful for quick checks

---

## ✅ Success Metrics

Dashboard is successful if:
1. **< 5 seconds** to identify unhealthy node
2. **< 30 seconds** to run a job on a node
3. **< 1 minute** to investigate an error
4. **Zero clicks** to see fleet status (visible on load)
5. **Auto-updates** without manual refresh

---

## 🚀 Implementation Phases

### Phase 6.1: Core Dashboard (MVP)
- [ ] Dashboard overview page (stat cards, topology)
- [ ] Nodes list page (table + detail panel)
- [ ] Live metrics charts (last 24h)
- [ ] Web-based log viewer with filtering and search
- [x] **Phase 6.6: UI Polish**
  - [x] Global Toast Notifications
  - [x] Loading states for actions
  - [x] Standardized visual language

**Estimated Effort:** 2-3 weeks

---

### Phase 6.2: Job Management
- [ ] Jobs page (active + history)
- [ ] Job submission form
- [ ] Live job output viewer
- [ ] Job templates (common commands)

**Estimated Effort:** 1 week

---

### Phase 6.3: Log Viewer
- [ ] Logs page with filters
- [ ] Search functionality
- [ ] Follow mode (tail -f)
- [ ] Export to CSV

**Estimated Effort:** 1 week

---

### Phase 6.4: Advanced Features
- [ ] Terminal in browser (xterm.js)
- [ ] Alerting system
- [ ] User authentication
- [ ] Settings page

**Estimated Effort:** 2-3 weeks per feature

---

## 📝 Notes

- **Performance:** Dashboard should handle 50+ nodes without lag
- **Accessibility:** WCAG 2.1 AA compliance (keyboard nav, screen readers)
- **Browser Support:** Modern browsers only (Chrome, Firefox, Safari, Edge)
- **API Design:** Dashboard uses same API as CLI (consistency)

---

**Next Steps:**
1. Review and approve this plan
2. Choose tech stack (htmx vs React)
3. Create design mockups (Figma/Excalidraw)
4. Build Phase 6.1 MVP
5. User testing and iteration
