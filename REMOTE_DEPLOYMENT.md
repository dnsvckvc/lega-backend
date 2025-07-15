# Remote Server Deployment Guide

This guide walks you through deploying the Legal Practice Management Backend on a remote server for development/testing and production use, including ngrok setup for HTTPS tunneling.

## 🚀 Quick Start for Remote Development

### Prerequisites
- Remote server with Docker and Docker Compose installed
- Server ports 80 and 8000 open to internet
- Git installed on remote server

### Step 1: Clone and Configure

```bash
# On your remote server
git clone <your-repository-url>
cd legal-practice-backend

# Copy the remote environment template
cp .env.remote .env

# Edit the .env file with your server details
nano .env
```

### Step 2: Update Environment Variables

In the `.env` file, replace placeholders with actual values:

```bash
# Replace YOUR_SERVER_IP with your actual server IP
ALLOWED_HOSTS=192.168.1.100,your-domain.com
CORS_ALLOWED_ORIGINS=http://192.168.1.100:3000,http://localhost:3000

# IMPORTANT: Generate a secure password for PostgreSQL
# Run: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Replace the default password with the generated one
POSTGRES_PASSWORD=your_generated_secure_password_here

# For testing, you can temporarily enable all origins
# CORS_ALLOW_ALL_ORIGINS=True
```

### Step 3: Deploy

```bash
# Build and start the containers
docker-compose -f docker-compose.remote.yml up -d --build

# Check status
docker-compose -f docker-compose.remote.yml ps

# View logs if needed
docker-compose -f docker-compose.remote.yml logs web
```

### Step 4: Access Points

Your API will be available at:
- **Documentation**: `http://YOUR_SERVER_IP/docs/`
- **Admin Interface**: `http://YOUR_SERVER_IP/admin/`
- **API Base**: `http://YOUR_SERVER_IP/api/`
- **Direct Django**: `http://YOUR_SERVER_IP:8000/` (if port 8000 is open)

## 🔧 Configuration Details

### Default Demo Users
The system creates these demo users automatically:
- **Admin**: `sarah.wilson@lawfirm.com` / `admin123`
- **Regular**: `michael.chen@lawfirm.com` / `lawyer123`
- **Junior**: `emma.rodriguez@lawfirm.com` / `lawyer123`

### CORS Configuration
For **development/testing**, you can use permissive CORS settings:
```bash
# In .env file
CORS_ALLOW_ALL_ORIGINS=True
```

For **production**, specify exact origins:
```bash
CORS_ALLOWED_ORIGINS=http://yourfrontend.com:3000,https://yourfrontend.com
```

### Frontend Connection
To connect a frontend application:

1. **Same Server**: `http://YOUR_SERVER_IP:3000`
2. **Different Server**: `http://FRONTEND_SERVER_IP:3000`
3. **Local Development**: `http://localhost:3000`

Add all frontend origins to `CORS_ALLOWED_ORIGINS` in `.env`.

## 📝 Testing with Postman

### Update Postman Environment
1. Open your Postman environment
2. Update the `base_url` variable:
   ```
   base_url: http://YOUR_SERVER_IP:8000
   ```
   or
   ```
   base_url: http://YOUR_SERVER_IP
   ```

### Test Authentication
1. **Login**: `POST {{base_url}}/auth/login/`
2. **Get Token**: Use admin credentials from above
3. **Test API**: `GET {{base_url}}/api/clients/`

## 🐳 Container Management

### View Status
```bash
docker-compose -f docker-compose.remote.yml ps
```

### View Logs
```bash
# All logs
docker-compose -f docker-compose.remote.yml logs

# Specific service
docker-compose -f docker-compose.remote.yml logs web
docker-compose -f docker-compose.remote.yml logs nginx
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.remote.yml restart

# Restart specific service
docker-compose -f docker-compose.remote.yml restart web
```

### Update Code
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.remote.yml down
docker-compose -f docker-compose.remote.yml up -d --build
```

## 🔒 Security Considerations

### Development Environment
- ✅ DEBUG=True for easier troubleshooting
- ✅ Permissive CORS for testing
- ✅ Demo users auto-created
- ⚠️ Database accessible on port 5432

### Production Environment
- ❌ DEBUG=False
- ❌ Restricted CORS origins
- ❌ No demo users
- ❌ Database not externally accessible
- ✅ SSL/HTTPS required
- ✅ Secure secret keys

## 🌐 Firewall Configuration

Ensure these ports are open on your server:
- **Port 80**: HTTP (Nginx)
- **Port 443**: HTTPS (Nginx, for production)
- **Port 8000**: Django (optional, for direct access)

Block these ports from external access:
- **Port 5432**: PostgreSQL (security risk)

## 🔧 Troubleshooting

### Common Issues

1. **Cannot access docs**:
   ```bash
   # Check container status
   docker-compose -f docker-compose.remote.yml ps
   
   # Check logs
   docker-compose -f docker-compose.remote.yml logs nginx
   ```

2. **CORS errors from frontend**:
   - Add frontend origin to `CORS_ALLOWED_ORIGINS`
   - Temporarily set `CORS_ALLOW_ALL_ORIGINS=True`

3. **Database connection issues**:
   ```bash
   # Check database logs
   docker-compose -f docker-compose.remote.yml logs db
   
   # Verify password in .env
   grep POSTGRES_PASSWORD .env
   ```

4. **Permission denied errors**:
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

### Health Checks
```bash
# Test endpoints
curl http://YOUR_SERVER_IP/health
curl http://YOUR_SERVER_IP/docs/
curl http://YOUR_SERVER_IP/api/clients/
```

## 📊 Monitoring

### Container Resources
```bash
# Check resource usage
docker stats

# Check disk usage
docker system df
```

### Application Logs
```bash
# View Django logs
docker-compose -f docker-compose.remote.yml exec web tail -f logs/general.log

# View API logs
docker-compose -f docker-compose.remote.yml exec web tail -f logs/api_requests.log
```

## 🌍 Production Deployment with ngrok

For production deployments requiring HTTPS tunneling (e.g., for Vercel frontend integration), follow these steps:

### Step 1: Install ngrok on Remote Server

```bash
# On your remote server
# Download ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin

# Alternative: using package manager
# Ubuntu/Debian:
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Add your authtoken (get from https://dashboard.ngrok.com/get-started/your-authtoken)
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

### Step 2: Deploy with ngrok

```bash
# Terminal 1: Start ngrok tunnel
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &

# Get the ngrok URL
curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'

# Terminal 2: Update environment and deploy
python3 fix_ngrok.py  # Auto-update .env with current ngrok URL
docker-compose -f docker-compose.remote.yml up -d --build
```

### Step 3: Production ngrok Service (Recommended)

Create a systemd service for ngrok to ensure it starts automatically:

```bash
# Create ngrok service file
sudo tee /etc/systemd/system/ngrok.service > /dev/null <<EOF
[Unit]
Description=ngrok tunnel
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/legal-practice-backend
ExecStart=/usr/local/bin/ngrok http 8000 --log=stdout
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable ngrok
sudo systemctl start ngrok

# Check status
sudo systemctl status ngrok
```

### Step 4: Auto-Update Script for URL Changes

Create a deployment script that handles ngrok URL changes:

```bash
# Create deploy-with-ngrok.sh
tee deploy-with-ngrok.sh > /dev/null <<'EOF'
#!/bin/bash
set -e

echo "🚀 Deploying with ngrok..."

# Wait for ngrok to be ready
echo "⏳ Waiting for ngrok..."
until curl -s http://localhost:4040/api/tunnels > /dev/null; do
    echo "Waiting for ngrok to start..."
    sleep 2
done

# Get current ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[] | select(.proto=="https") | .public_url')
echo "📍 Current ngrok URL: $NGROK_URL"

# Update environment files
python3 fix_ngrok.py

# Deploy containers
echo "🐳 Deploying containers..."
docker-compose -f docker-compose.remote.yml up -d --build

# Test the deployment
echo "🧪 Testing deployment..."
sleep 10
curl -I "$NGROK_URL/docs/" || echo "⚠️  Deployment test failed"

echo "✅ Deployment complete!"
echo "📍 Your API is available at: $NGROK_URL"
echo "📚 Documentation: $NGROK_URL/docs/"
echo "🔧 Admin: $NGROK_URL/admin/"
EOF

chmod +x deploy-with-ngrok.sh
```

### Step 5: Frontend Integration

Update your frontend environment variables:

```bash
# For Vercel deployment
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://your-ngrok-url.ngrok-free.app

vercel env add NEXT_PUBLIC_AUTH_URL  
# Enter: https://your-ngrok-url.ngrok-free.app/auth
```

### Step 6: Production Monitoring

Monitor your ngrok tunnel and Django backend:

```bash
# Check ngrok status
curl -s http://localhost:4040/api/tunnels | jq '.'

# Check Django logs
docker-compose -f docker-compose.remote.yml logs web | tail -50

# Monitor container health
docker-compose -f docker-compose.remote.yml ps
```

## 🔄 URL Change Management

### Automatic Updates (Recommended)

Set up a cron job to handle ngrok URL changes:

```bash
# Add to crontab (every 5 minutes)
crontab -e

# Add this line:
*/5 * * * * cd /path/to/your/project && python3 fix_ngrok.py && docker-compose -f docker-compose.remote.yml restart web > /dev/null 2>&1
```

### Manual Updates

When ngrok URL changes (free accounts):

```bash
# Get new URL and update
python3 fix_ngrok.py

# Restart Django to pick up new configuration
docker-compose -f docker-compose.remote.yml restart web

# Update Vercel environment variables
vercel env rm NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_API_URL
# Enter the new ngrok URL
```

## ⚡ Quick Production Commands

```bash
# Complete deployment from scratch
git pull origin main
./deploy-with-ngrok.sh

# Quick restart after code changes  
git pull origin main
docker-compose -f docker-compose.remote.yml up -d --build

# Emergency restart (if ngrok URL changed)
python3 fix_ngrok.py
docker-compose -f docker-compose.remote.yml restart web

# Check everything is working
curl -I "$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')/docs/"
```

## 🎯 Next Steps

1. **ngrok Production Setup**: Follow the ngrok production steps above
2. **Test Documentation**: Visit your ngrok URL `/docs/`
3. **Update Frontend**: Configure Vercel with your ngrok URL
4. **Test API Endpoints**: Use Postman collections with ngrok URL
5. **Monitor Service**: Set up systemd service for ngrok

## 📞 Support

If you encounter issues:
1. Check ngrok status: `curl -s http://localhost:4040/api/tunnels`
2. Check Django logs: `docker-compose -f docker-compose.remote.yml logs web`
3. Verify environment variables: `cat .env`
4. Test ngrok tunnel: `curl -I YOUR_NGROK_URL/docs/`
5. Restart services: `sudo systemctl restart ngrok && docker-compose -f docker-compose.remote.yml restart web`