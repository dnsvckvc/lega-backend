# Docker Deployment Guide

This guide provides comprehensive instructions for deploying the Legal Practice Management Backend using Docker.

## 📋 Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- At least 2GB RAM
- 10GB disk space

## 🚀 Quick Start (Development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd claude-first
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application

- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **Documentation**: http://localhost:8000/docs/
- **Monitoring**: http://localhost:8000/monitoring/

### 4. Default Demo Users

The development setup automatically creates demo users:

- **Admin**: `sarah.wilson@lawfirm.com` / `admin123`
- **Regular**: `michael.chen@lawfirm.com` / `lawyer123`
- **Junior**: `emma.rodriguez@lawfirm.com` / `lawyer123`

## 🏭 Production Deployment

### 1. Environment Configuration

Copy and customize the production environment file:

```bash
cp .env.docker .env.production
```

Edit `.env.production` with your production values:

```bash
# Critical Production Settings
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
POSTGRES_PASSWORD=your-secure-database-password

# CORS (Add your frontend domains)
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

# Email Configuration
EMAIL_HOST=smtp.your-provider.com
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password

# SSL Settings (Enable when using HTTPS)
SECURE_SSL_REDIRECT=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Superuser (for initial admin creation)
DJANGO_SUPERUSER_EMAIL=admin@yourcompany.com
DJANGO_SUPERUSER_PASSWORD=your-admin-password
DJANGO_SUPERUSER_FIRST_NAME=Admin
DJANGO_SUPERUSER_LAST_NAME=User
```

### 2. SSL Certificate Setup (Production)

For HTTPS in production, place your SSL certificates in an `ssl` directory:

```bash
mkdir ssl
# Copy your SSL certificate files
cp cert.pem ssl/
cp key.pem ssl/
```

### 3. Update Production Configuration

Edit `nginx.prod.conf` and `docker-compose.prod.yml` to match your domain and requirements.

### 4. Deploy Production

```bash
# Set database password
export POSTGRES_PASSWORD=your-secure-database-password

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d --build
```

## 📁 Project Structure

```
claude-first/
├── Dockerfile                 # Main application container
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
├── docker-entrypoint.sh       # Container initialization script
├── .dockerignore              # Files to exclude from Docker context
├── .env.docker               # Environment template
├── nginx.conf                # Nginx config for development
├── nginx.prod.conf           # Nginx config for production
└── requirements.txt          # Python dependencies (includes gunicorn)
```

## 🔧 Docker Services

### Web Service (Django)
- **Base Image**: python:3.9-slim
- **Port**: 8000
- **Features**: Auto-migration, static files, demo users (dev)

### Database Service (PostgreSQL)
- **Base Image**: postgres:15
- **Port**: 5432
- **Data**: Persistent volume storage

### Nginx Service (Reverse Proxy)
- **Base Image**: nginx:alpine
- **Ports**: 80, 443
- **Features**: SSL termination, rate limiting, static file serving

## 🛠️ Common Commands

### Development

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute commands in container
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

### Production

```bash
# Deploy production
docker-compose -f docker-compose.prod.yml up -d --build

# View production logs
docker-compose -f docker-compose.prod.yml logs -f web

# Scale web service
docker-compose -f docker-compose.prod.yml up -d --scale web=3

# Stop production
docker-compose -f docker-compose.prod.yml down
```

### Database Management

```bash
# Create database backup
docker-compose exec db pg_dump -U postgres legal_backend > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres legal_backend < backup.sql

# Access database shell
docker-compose exec db psql -U postgres legal_backend
```

## 🔍 Monitoring and Health Checks

### Application Health

```bash
# Check container status
docker-compose ps

# View application logs
docker-compose logs -f web

# Check database health
curl http://localhost/health
```

### Database Health

```bash
# Check database connection
docker-compose exec db pg_isready -U postgres

# View database logs
docker-compose logs -f db
```

## 📊 Performance Optimization

### Production Recommendations

1. **Database Optimization**:
   ```bash
   # Increase shared_buffers in PostgreSQL
   docker-compose exec db psql -U postgres -c "ALTER SYSTEM SET shared_buffers = '256MB';"
   ```

2. **Nginx Optimization**:
   - Enable gzip compression ✅
   - Configure rate limiting ✅
   - Set appropriate cache headers ✅

3. **Django Optimization**:
   - Use gunicorn with multiple workers ✅
   - Enable static file caching ✅
   - Configure database connection pooling

## 🔐 Security Considerations

### Production Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set strong database passwords
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure proper CORS origins
- [ ] Set up proper firewall rules
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

### Environment Variables Security

Never commit sensitive environment variables to version control:

```bash
# Add to .gitignore
.env.production
.env.local
ssl/
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   ```bash
   # Check database is running
   docker-compose ps db
   
   # Check connection
   docker-compose exec web python manage.py check --database default
   ```

2. **Permission Issues**:
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER logs/
   sudo chown -R $USER:$USER media/
   ```

3. **Static Files Not Loading**:
   ```bash
   # Rebuild with static files
   docker-compose exec web python manage.py collectstatic --noinput
   ```

### Log Analysis

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f --tail=100 web
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale web service
docker-compose -f docker-compose.prod.yml up -d --scale web=3

# Use load balancer
# Update nginx.conf to include multiple upstream servers
```

### Vertical Scaling

```bash
# Increase container resources
docker-compose -f docker-compose.prod.yml up -d --scale web=1 --memory=2g --cpus=2
```

## 🔄 Updates and Maintenance

### Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Database Migrations

```bash
# Create new migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Docker Guide](https://hub.docker.com/_/postgres)
- [Nginx Docker Guide](https://hub.docker.com/_/nginx)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)

## 🆘 Support

For issues related to:
- **Docker configuration**: Check logs and health checks
- **Application errors**: View Django logs in container
- **Database issues**: Check PostgreSQL logs and connections
- **Nginx issues**: Check nginx logs and configuration

Remember to check the comprehensive logging system built into the application for detailed error tracking and monitoring.