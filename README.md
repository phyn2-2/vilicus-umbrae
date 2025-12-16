# Vilicus Umbrae 🛡️

*The Shadow Guardian of Your System*

A smart system monitoring and maintenance tool that watches over your Linux system, detects issues, and takes action when needed.

## Features

- 📊 Disk usage monitoring with growth detection
- 💾 Memory and swap usage tracking
- ⚡ CPU load monitoring
- 📝 Log file size tracking
- 🗑️ Automated cleanup (package cache, temp files)
- 💾 Backup verification
- 🔍 Smart differential analysis
- 📋 Beautiful reports in Markdown
- 🔒 Safe execution with dry-run mode

## Installation

```bash
# Clone the repository
git clone <>
cd vilicus-umbrae

# Install dependencies
pip3 install -r requirements.txt

# Configure
cp config.yaml config.yaml.local
# Edit config.yaml with your preferences
```

## Usage

```bash
# Dry run (safe, no changes)
python3 vilicus.py

# Actually execute cleanup actions
python3 vilicus.py --execute

# Generate report only
python3 vilicus.py --report-only
```

## Project Structure

```
vilicus-umbrae/
├── vilicus.py          # Main orchestrator
├── config.yaml         # Configuration
├── state.json          # Persistent state (auto-generated)
├── modules/            # Observer & action modules
└── utils/              # Helper utilities
```

## Development

Built with Python 3, focuses on simplicity and safety.

## License

MIT License - Do whatever you want with it!
