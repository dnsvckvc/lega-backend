# 🚀 Deployment Checklist

This checklist ensures the Legal Practice Management API is properly deployed and configured.

## ✅ Pre-Deployment Verification

### Code Quality
- [x] All authentication tests pass (`python manage.py test authentication`)
- [x] System check passes (`python manage.py check`)
- [x] No security warnings (`python manage.py check --deploy`)
- [x] Requirements file is up-to-date
- [x] Environment variables are properly configured

### Dependencies
- [x] Django==4.2.7
- [x] djangorestframework==3.14.0
- [x] djangorestframework-simplejwt==5.5.0
- [x] psycopg2-binary==2.9.7 (for PostgreSQL)
- [x] django-cors-headers==4.3.1
- [x] python-decouple==3.8
- [x] django-filter==23.3

## 🔧 Environment Configuration

### Required Environment Variables
```bash
# Security
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL for production)
DB_NAME=legal_backend_prod
DB_USER=your_db_user
DB_PASSWORD=secure_db_password
DB_HOST=your_db_host
DB_PORT=5432

# CORS (update for your frontend domain)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security Headers (HTTPS only)
SECURE_SSL_REDIRECT=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

## 🗄️ Database Setup

### PostgreSQL Configuration
```sql
-- Create database and user
CREATE DATABASE legal_backend_prod;
CREATE USER your_db_user WITH PASSWORD 'secure_db_password';
GRANT ALL PRIVILEGES ON DATABASE legal_backend_prod TO your_db_user;
```

### Migration Commands
```bash
# Apply all migrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser

# Create demo data (development only)
python manage.py create_demo_users --clear
```

## 🔐 Security Configuration

### Django Settings
- [x] `DEBUG=False` in production
- [x] Strong `SECRET_KEY` (50+ random characters)
- [x] `ALLOWED_HOSTS` configured for your domain
- [x] HTTPS redirect enabled (`SECURE_SSL_REDIRECT=True`)
- [x] Secure cookies (`CSRF_COOKIE_SECURE=True`, `SESSION_COOKIE_SECURE=True`)
- [x] HSTS headers (`SECURE_HSTS_SECONDS=31536000`)

### Authentication Security
- [x] JWT tokens with reasonable expiration (1 hour access, 7 days refresh)
- [x] Token rotation enabled
- [x] Refresh token blacklisting on logout
- [x] Role-based permissions properly configured
- [x] Admin-only user registration

## 🌐 Server Configuration

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### CORS Configuration
- [x] Frontend domain added to `CORS_ALLOWED_ORIGINS`
- [x] `CORS_ALLOW_CREDENTIALS=True` for authentication
- [x] Remove development domains in production

### Logging (Recommended)
```python
# Add to settings.py for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/path/to/django_errors.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

## 🧪 Post-Deployment Testing

### Health Checks
```bash
# Test basic connectivity
curl https://yourdomain.com/admin/

# Test authentication endpoint
curl -X POST https://yourdomain.com/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your_admin@example.com", "password": "your_password"}'

# Test API with authentication
curl -H "Authorization: Bearer <token>" \
  https://yourdomain.com/api/mandates/
```

### Security Verification
- [ ] All API endpoints require authentication
- [ ] Unauthenticated requests return 401
- [ ] Regular users cannot access admin functions
- [ ] HTTPS is properly configured
- [ ] Security headers are present

### Functionality Testing
- [ ] User login works correctly
- [ ] Token refresh works
- [ ] Role-based data filtering functions
- [ ] Admin can create users and manage data
- [ ] Regular lawyers see only assigned mandates
- [ ] All CRUD operations work with proper permissions

## 📊 Monitoring Setup

### Performance Monitoring
- [ ] Database query optimization
- [ ] API response time monitoring
- [ ] Error rate tracking
- [ ] Resource usage monitoring

### Security Monitoring
- [ ] Failed login attempt tracking
- [ ] Unusual API access patterns
- [ ] Token usage monitoring
- [ ] Permission violation alerts

## 🚨 Troubleshooting

### Common Issues
1. **500 Server Error**
   - Check Django logs
   - Verify database connectivity
   - Ensure all migrations are applied

2. **Authentication Issues**
   - Verify JWT secret key consistency
   - Check token expiration settings
   - Validate user accounts exist

3. **CORS Issues**
   - Verify frontend domain in `CORS_ALLOWED_ORIGINS`
   - Check `CORS_ALLOW_CREDENTIALS` setting
   - Validate HTTPS configuration

4. **Database Connection**
   - Test PostgreSQL connectivity
   - Verify database credentials
   - Check network security groups/firewalls

### Emergency Rollback
```bash
# Backup database before deployment
pg_dump legal_backend_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Rollback migrations if needed
python manage.py migrate core 0001  # Rollback to specific migration
```

## 📈 Post-Launch

### User Account Management
```bash
# Create admin user
python manage.py createsuperuser

# Create lawyer users via API or admin interface
# Link user accounts to lawyer profiles via admin or API
```

### Data Migration (if needed)
```bash
# Import existing client/lawyer data
python manage.py shell
# Use Django ORM to import existing data
```

### Performance Optimization
- [ ] Enable database connection pooling
- [ ] Configure caching (Redis/Memcached)
- [ ] Set up CDN for static files
- [ ] Enable gzip compression
- [ ] Configure database indexing

---

**Deployment Complete!** 🎉

Your Legal Practice Management API is now secure, authenticated, and ready for production use.