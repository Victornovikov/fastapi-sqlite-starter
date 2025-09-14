#!/bin/bash
echo "=== FastAPI App Health Check ==="
echo ""
echo "1. Service Status:"
sudo systemctl status fastapi-app --no-pager | head -10
echo ""
echo "2. Port 8000 Status:"
sudo lsof -i :8000 || echo "Port 8000 is free"
echo ""
echo "3. Recent Errors:"
sudo journalctl -u fastapi-app -n 5 --no-pager | grep -i error || echo "No recent errors"
echo ""
echo "4. File Permissions:"
ls -la /opt/fastapi-sqlite/.env
ls -la /opt/fastapi-sqlite/app.db* 2>/dev/null || echo "Database not yet created"
echo ""
echo "5. App Response:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/
echo "=== Check Complete ==="