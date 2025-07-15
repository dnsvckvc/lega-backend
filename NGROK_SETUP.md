# ngrok Setup Guide

This guide explains how to use ngrok with your Django backend for HTTPS tunneling.

## 🚀 Quick Start

### 1. Install ngrok
```bash
# Download from: https://ngrok.com/download
# Or using package managers:
brew install ngrok           # macOS
sudo snap install ngrok      # Ubuntu
choco install ngrok         # Windows
```

### 2. Start ngrok tunnel
```bash
# Start ngrok tunnel to port 8000 (where Django runs)
ngrok http 8000
```

### 3. Start your Django backend
```bash
# Local development
docker-compose up -d

# Remote server
docker-compose -f docker-compose.remote.yml up -d
```

That's it! The Docker container will automatically detect the ngrok URL and configure Django.

## 🔧 How It Works

### Automatic Detection
When your Django container starts, it:
1. Checks if ngrok is running on `host.docker.internal:4040`
2. If found, extracts the HTTPS tunnel URL
3. Automatically adds the ngrok domain to `ALLOWED_HOSTS`
4. Automatically adds the ngrok URL to `CORS_ALLOWED_ORIGINS`

### Example Output
```bash
🚀 Starting Django container...
🔍 Checking for ngrok tunnel...
✅ ngrok API accessible, detecting URL...
✅ Auto-detected ngrok tunnel: https://abc123.ngrok-free.app
📝 Updated ALLOWED_HOSTS: localhost,127.0.0.1,0.0.0.0,abc123.ngrok-free.app
🌐 Updated CORS_ALLOWED_ORIGINS: http://localhost:3000,https://abc123.ngrok-free.app
```

## 🌐 Frontend Integration

### Vercel Environment Variables
Update your Vercel frontend environment variables:
```bash
NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app
NEXT_PUBLIC_AUTH_URL=https://abc123.ngrok-free.app/auth
```

### Local Frontend Development
Your frontend can now make requests to the ngrok URL:
```javascript
// Example API call
fetch('https://abc123.ngrok-free.app/api/clients/')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 🔄 URL Changes

### When ngrok URL Changes
Free ngrok URLs change every time you restart ngrok. When this happens:
1. Simply restart your Django container
2. The new URL will be automatically detected
3. No manual configuration needed

```bash
# Restart to pick up new ngrok URL
docker-compose restart web
# or
docker-compose -f docker-compose.remote.yml restart web
```

## 🛠️ Troubleshooting

### ngrok Not Detected
If you see "ngrok not accessible", check:
- ngrok is running: `curl http://localhost:4040/api/tunnels`
- Docker has host access: `extra_hosts` is configured in docker-compose.yml
- ngrok is tunneling to port 8000: `ngrok http 8000`

### CORS Errors
If you get CORS errors:
- Check the ngrok URL is correctly detected in container logs
- Verify your frontend is using the correct ngrok URL
- Try restarting the container to re-detect the URL

### Django ALLOWED_HOSTS Error
If you get "Invalid HTTP_HOST header":
- Check container logs for ngrok detection messages
- Verify ngrok is running and accessible
- Try restarting the container

## 🔒 Security Notes

### Development Only
This automatic ngrok detection is designed for development. For production:
- Use proper domain names in environment variables
- Configure ALLOWED_HOSTS and CORS explicitly
- The detection gracefully falls back if ngrok isn't available

### HTTPS
ngrok provides HTTPS by default, solving mixed content issues when your frontend is hosted on HTTPS (like Vercel).

## 🏭 Production Deployment

### Complete Production Setup

For production deployment on a remote server:

```bash
# 1. Clone repository on remote server
git clone <your-repo-url>
cd legal-practice-backend

# 2. Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# 3. Configure ngrok authtoken
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN

# 4. Deploy with automatic setup
./deploy-with-ngrok.sh
```

### Production Service Setup

Create a systemd service for ngrok:

```bash
# Create service file
sudo tee /etc/systemd/system/ngrok.service > /dev/null <<EOF
[Unit]
Description=ngrok tunnel
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
ExecStart=/usr/local/bin/ngrok http 8000 --log=stdout
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ngrok
sudo systemctl start ngrok
```

### Automatic URL Updates

Set up automatic handling of ngrok URL changes:

```bash
# Add to crontab for URL change detection
crontab -e

# Add this line (every 5 minutes):
*/5 * * * * cd /path/to/project && python3 fix_ngrok.py && docker-compose -f docker-compose.remote.yml restart web > /dev/null 2>&1
```

### Production Commands

```bash
# Complete deployment
./deploy-with-ngrok.sh

# Quick restart after code changes
git pull origin main
docker-compose -f docker-compose.remote.yml up -d --build

# Emergency restart (URL changed)
python3 fix_ngrok.py
docker-compose -f docker-compose.remote.yml restart web

# Check status
curl -I "$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')/docs/"
```

## 📚 Additional Resources

- [ngrok Documentation](https://ngrok.com/docs)
- [Django ALLOWED_HOSTS](https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts)
- [Django CORS](https://github.com/adamchainz/django-cors-headers)
- [Remote Deployment Guide](./REMOTE_DEPLOYMENT.md)