#!/bin/bash
echo "🛡️  VILICUS SYSTEMD STATUS"
echo "=========================="
echo ""

# Timer status
echo "⏰ Timer Status:"
systemctl status vilicus.timer --no-pager | head -10
echo ""

# Next run time  
echo "📅 Schedule:"
systemctl list-timers --all | grep vilicus
echo ""

# Last 3 runs
echo "📊 Last 3 Runs:"
sudo journalctl -u vilicus.service --since "3 days ago" | grep "completed successfully" | tail -3
echo ""

# Recent output
echo "📋 Last Run Output:"
sudo journalctl -u vilicus.service -n 15 --no-pager | grep -E "STATS|Disk|RAM|CPU|CLEANUP|completed"
echo ""

# File logs
echo "📝 Recent File Logs:"
tail -5 logs/vilicus.log
