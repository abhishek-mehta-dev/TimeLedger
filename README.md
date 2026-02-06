# ⏱️ TimeLedger

A professional, premium desktop application for work hour tracking, featuring a modern UI, automated Google Sheets synchronization, and professional Excel reporting.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat&logo=mongodb&logoColor=white)
![Excel](https://img.shields.io/badge/Reports-Excel-217346?style=flat&logo=microsoftexcel&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Sync-Google%20Sheets-34A853?style=flat&logo=googlesheets&logoColor=white)

## ✨ Premium Features

- **Professional Excel Dashboard** - Automatically generates high-end `.xlsx` reports with productivity snapshots, zebra-striping, and color-coded event timelines.
- **Google Sheets Cloud Sync** - Seamlessly appends daily work summaries to your Google Sheet (supports both `credentials.json` and direct `.env` JSON keys).
- **Premium UI/UX** - Modern card-based interface with smooth hover effects, a dynamic pulsing "Live" timer, and high-fidelity brand assets.
- **Micro-Transitions** - Real-time visual feedback for active working vs. break states.
- **Cloud Integrity** - All events stored securely in MongoDB Atlas with SHA256 hash verification for every generated report.
- **Smart Persistence** - Lossless session recovery if the application is closed or interrupted.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- MongoDB Atlas Account (Free Tier)
- Google Cloud Project (for Sheets sync)

### Installation

1. **Clone & Setup**
   ```bash
   git clone https://github.com/abhishek-mehta-dev/TimeLedger.git
   cd TimeLedger
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   MONGODB_URI=your_mongodb_atlas_uri
   GOOGLE_SHEET_URL=your_google_sheet_link
   # Optional: Paste your Service Account JSON here to avoid using a file
   GOOGLE_SERVICE_ACCOUNT_JSON='{...}' 
   ```

3. **Google Sheets Setup (Optional)**
   - Enable **Google Sheets API** in Google Cloud Console.
   - Create a **Service Account** and download its JSON key.
   - Rename to `credentials.json` and place in root (or use the `.env` method above).
   - **Share** your target spreadsheet with the Service Account email.

4. **Launch**
   ```bash
   python main.py
   ```

## 🏗️ Project Structure

```
TimeLedger/
├── timeledger/              # Core Package
│   ├── assets/              # Brand logos and icons
│   ├── db.py                # MongoDB Atlas synchronization
│   ├── report.py            # Professional Excel generation
│   ├── sheets.py            # Google Sheets API integration
│   ├── tracker.py           # Core logic & state machine
│   └── ui.py                # Premium Tkinter implementation
├── main.py                  # Entry Point
├── requirements.txt         # Dependencies (openpyxl, Pillow, gspread, etc.)
└── README.md                # Documentation
```

## 🔧 Technical Stack

| Category | Technology |
| :--- | :--- |
| **Logic** | Python 3.12+, `dataclasses`, `enum` |
| **Database** | MongoDB Atlas, `pymongo[srv]` |
| **Reports** | `openpyxl` (High-fidelity Excel) |
| **Image Engine** | `Pillow` (Optimized asset scaling) |
| **Cloud Sync** | `gspread`, `google-auth` |
| **GUI** | Tkinter (Custom Modern Implementation) |

## 🔒 Security & Integrity

- **SHA256 Verification**: Every report is hashed and validated against a cloud-stored digest.
- **TLS 1.3 Encryption**: All traffic to MongoDB and Google APIs is fully encrypted.
- **Append-Only Ledger**: Database records are immutable (Insert-only) for audit integrity.

---

<p align="center">
  Independently developed by <b>Abhishek Mehta</b><br>
  <i>Built with ❤️ for professional work tracking and cloud efficiency.</i>
</p>
