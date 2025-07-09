# Remote Server Deployment Guide

This guide walks you through deploying the Legal Practice Management Backend on a remote server for development/testing and production use.

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

# Set a secure password
POSTGRES_PASSWORD=your_secure_password_here

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

## 🎯 Next Steps

1. **Test Documentation**: Visit `http://YOUR_SERVER_IP/docs/`
2. **Update Postman**: Change base_url to your server IP
3. **Test API Endpoints**: Use Postman collections
4. **Connect Frontend**: Add CORS origins for your frontend
5. **Production Setup**: Use `docker-compose.prod.yml` when ready

## 📞 Support

If you encounter issues:
1. Check the logs: `docker-compose -f docker-compose.remote.yml logs`
2. Verify environment variables in `.env`
3. Ensure firewall ports are open
4. Test with curl commands above