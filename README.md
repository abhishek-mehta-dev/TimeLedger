# ⏱️ TimeLedger

A professional desktop application for manually tracking work and break hours with cloud storage and CSV report generation.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat&logo=mongodb&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

## ✨ Features

- **Work Session Tracking** - Start, pause, resume, and end your work day with a single click
- **Break Logging** - Mandatory reason input when taking breaks for accountability
- **Live Timer Display** - Real-time elapsed work time (excluding breaks)
- **Cloud Storage** - All events stored securely in MongoDB Atlas with append-only inserts
- **CSV Reports** - Professional daily reports with summary and event timeline
- **Data Integrity** - SHA256 hash verification for generated reports
- **State Persistence** - Automatically restores your session if the app is closed and reopened

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- MongoDB Atlas account (free tier works great)
- Internet connection for cloud storage

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/TimeLedger.git
   cd TimeLedger
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   
   # On Linux/macOS
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MongoDB connection**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and replace with your MongoDB Atlas connection string:
   ```
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/timeledger?retryWrites=true&w=majority
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## 📖 Usage

### State Flow

```
┌─────────┐     Start     ┌──────────┐     Pause      ┌────────┐
│  IDLE   │ ────────────► │ WORKING  │ ─────────────► │ PAUSED │
└─────────┘               └──────────┘                └────────┘
                               │                           │
                               │ End Day            Resume │
                               ▼                           ▼
                         ┌──────────┐               ┌──────────┐
                         │  ENDED   │ ◄──── End ────│ WORKING  │
                         └──────────┘      Day      └──────────┘
```

### Actions

| Action | Description |
|--------|-------------|
| **Start Work** | Begin a new work session. Only available from idle state. |
| **Pause** | Take a break. Requires entering a reason. Only available while working. |
| **Resume** | Continue working after a break. Only available while paused. |
| **End Day** | Finish the work day. Locks all records. Available while working or paused. |
| **Generate Report** | Create a CSV report for the current day. |

### CSV Reports

Reports include:
- **Summary Section** - Date, start/end times, total span, break time, net work time
- **Break Reasons** - List of all breaks with their reasons
- **Event Timeline** - Chronological list of all events with timestamps

Reports are saved as `YYYY-MM-DD-TimeLedger.csv` in the current directory.

## 🏗️ Project Structure

```
TimeLedger/
├── timeledger/              # Python package
│   ├── __init__.py          # Package exports and version
│   ├── app.py               # Main application logic
│   ├── db.py                # MongoDB Atlas operations
│   ├── tracker.py           # State management & time calculations
│   ├── report.py            # CSV report generation
│   └── ui.py                # Tkinter GUI implementation
│
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── .env                     # Your MongoDB URI (git-ignored)
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

### Module Details

| Module | Purpose |
|--------|---------|
| `app.py` | Application orchestration, environment checks, main run loop |
| `db.py` | MongoDB connection, CRUD operations, hash storage |
| `tracker.py` | State machine, transition validation, time calculations |
| `report.py` | CSV report generation with structured sections |
| `ui.py` | Complete Tkinter GUI with styles and event handlers |

## 🔧 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pymongo[srv]` | ≥4.6.0 | MongoDB Atlas driver with DNS seedlist support |
| `python-dotenv` | ≥1.0.0 | Environment variable management |

## 🔒 Security & Data Integrity

- **Append-Only Storage** - Events are only inserted, never modified or deleted
- **Hash Verification** - Each report's SHA256 hash is stored in MongoDB for verification
- **TLS Encryption** - All database connections use TLS by default
- **No Local Data** - All data is stored in your MongoDB Atlas cluster

## 🛠️ MongoDB Setup

1. Create a free [MongoDB Atlas](https://www.mongodb.com/atlas) account
2. Create a new cluster (M0 free tier is sufficient)
3. Create a database user with read/write access
4. Whitelist your IP address (or use `0.0.0.0/0` for all IPs)
5. Get your connection string from the cluster's "Connect" menu
6. Add the connection string to your `.env` file

The application automatically creates two collections:
- `events` - Stores all work session events
- `report_hashes` - Stores SHA256 hashes of generated reports

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for better work-life tracking
</p>
