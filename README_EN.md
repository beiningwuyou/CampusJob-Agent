# 🎓 CampusJob-Agent
### An Intelligent Dual-Track Job & Civil Exam Copilot for College Graduates (Local-First Architecture)

CampusJob-Agent is an open-source, privacy-first career copilot tailored for master's and doctoral graduates pursuing both **Enterprise Tech Campus Recruiting** and **Civil Service / Selected Candidate Examinations**.

<p align="center">
  <img src="./docs/images/dashboard.png" alt="CampusJob-Agent Dashboard" width="95%" />
</p>

---

## 🌟 Key Features

- 📡 **Multi-Source Job Radar**: Real-time aggregation from university career portals (RSS), major enterprise career sites, and official civil service announcements.
- 🧩 **Dual-Track Schema Parsing**: Automatic parsing and structuring of enterprise JDs and government exam notices (major discipline codes, CPC membership, fresh-grad restrictions).
- 🛡️ **Local-First Privacy Sandbox**: All resume data is sanitized locally via regex and AES encryption. No plaintext personally identifiable information (PII) is ever sent to LLMs.
- 🤖 **AI Career Advisory Cockpit**: Six-dimensional capability radar chart, 0-100 position fit score, and targeted interview simulation questions.
- 📋 **Full-Lifecycle Application Kanban**: Drag-and-drop tracking from Application -> Written Exam -> Tech Interviews -> Offer -> Archiving, with UTF-8 BOM CSV export.
- 📅 **Exam & Interview Calendar**: Conflict detection and one-click subscription to Apple Calendar, Google Calendar, and Outlook (.ics).
- 🍏 **Ultra-Lightweight macOS Native Client**: Native Cocoa WebKit wrapper with sub-second startup and low memory footprint (no bloated Electron).

---

## ⚡ Quick Start

```bash
# 1. Clone repository
git clone https://github.com/beiningwuyou/CampusJob-Agent.git
cd CampusJob-Agent

# 2. Install dependencies with uv
uv sync

# 3. Setup environment configuration
cp .env.example .env

# 4. Seed mock demo data (Safe & Sanitized)
uv run python scripts/seed_demo_data.py

# 5. Launch
# Option A: macOS Native App
./run_desktop.sh

# Option B: Web Dashboard
uv run uvicorn app.main:app --reload
```

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).
