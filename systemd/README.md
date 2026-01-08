# Vilicus Systemd Setup

## Installation
```bash
# Copy files
sudo cp systemd/vilicus.service /etc/systemd/system/
sudo cp systemd/vilicus.timer /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable vilicus.timer
sudo systemctl start vilicus.timer
```

## Monitoring
```bash
# Check timer status
systemctl status vilicus.timer

# See schedule
systemctl list-timers vilicus*

# View logs
sudo journalctl -u vilicus.service -f

# Manual run
sudo systemctl start vilicus.service
```

## Configuration

- Runs 10 minutes after boot
- Runs every 12 hours after last run
- Catches up on missed runs (Persistent=yes)
- Random 0-5 min delay to prevent stampede

## Troubleshooting
```bash
# Check service status
sudo systemctl status vilicus.service

# View recent logs
sudo journalctl -u vilicus.service -n 50

# Test manual run
sudo systemctl start vilicus.service

# Verify timer is active
systemctl is-active vilicus.timer
```
