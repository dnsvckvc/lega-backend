# 📊 Logging and Monitoring System

The Legal Practice Management API includes a comprehensive logging and monitoring system for production-ready observability, security, and performance tracking.

## 🔧 System Architecture

### Logging Components

1. **Django Logging Configuration** - Multi-handler structured logging
2. **Custom Middleware** - Performance, API, and audit trail monitoring
3. **Authentication Logging** - Login/logout tracking with security alerts
4. **Monitoring Dashboard** - Admin-only REST API endpoints for log analysis
5. **Health Check System** - Automated monitoring with alert capabilities

### Log Files Generated

- `logs/general.log` - General Django application logs
- `logs/errors.log` - Error and critical issue logs
- `logs/performance.log` - Request performance metrics
- `logs/api_requests.log` - Detailed API request/response logs
- `logs/authentication.log` - Authentication events and security logs
- `logs/audit.log` - User action audit trail

## 📈 Features Implemented

### ✅ High Priority Features

#### 1. Django Logging Configuration
- **Rotating file handlers** with automatic log rotation
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Structured formatters** for consistent log parsing
- **Separate handlers** for different log types
- **Environment-based configuration**

#### 2. Performance Monitoring Middleware
- **Request duration tracking** with automatic slow request detection
- **Response time metrics** with average calculations
- **Performance headers** (`X-Response-Time`) for debugging
- **User and role tracking** for performance analysis
- **IP address logging** for security monitoring

#### 3. API Request/Response Logging
- **Complete request logging** (method, path, headers, body)
- **Response status tracking** with error rate monitoring
- **Sensitive data sanitization** (passwords, tokens automatically redacted)
- **User context tracking** (authenticated user, role, IP)
- **Configurable path exclusions** (admin, static files)

#### 4. Audit Trail System
- **Data modification tracking** (CREATE, UPDATE, DELETE operations)
- **User action logging** with full context
- **Resource identification** (type, ID, path)
- **Timestamp and IP tracking**
- **Role-based action monitoring**

#### 5. Authentication & Security Logging
- **Login success/failure tracking**
- **Failed login attempt monitoring**
- **IP-based suspicious activity detection**
- **Token refresh and logout logging**
- **User registration audit trail**

### ✅ Medium Priority Features

#### 6. Admin Dashboard API
Four monitoring endpoints for administrators:

**`GET /monitoring/dashboard/`** - Overall system statistics
```json
{
  "total_requests_today": 45,
  "failed_requests_today": 2,
  "unique_users_today": 8,
  "avg_response_time": 0.123,
  "slow_requests_today": 1,
  "login_attempts_today": 12,
  "failed_logins_today": 1,
  "total_log_files": 6,
  "log_files_sizes": {
    "performance.log": {"size_mb": 2.3}
  }
}
```

**`GET /monitoring/logs/?type=audit&limit=50`** - Recent log entries
- Supports: `audit`, `auth`, `performance`, `api`, `error`, `general`
- Structured log parsing with metadata extraction
- Configurable limits (max 200 entries)

**`GET /monitoring/activity/?days=7&user=email@domain.com`** - User activity analysis
- Daily activity breakdowns
- User request statistics
- Top endpoint usage
- Recent user actions

**`GET /monitoring/health/`** - System health metrics
- Disk usage monitoring
- Recent error detection
- Performance issue alerts
- Security alert summary

#### 7. Error Tracking & Alerting
- **Automated health check command** (`check_system_health`)
- **Configurable alert thresholds**:
  - Critical/Fatal errors detected
  - High error rates (>10% requests failing)
  - Excessive slow requests (>20% over 1s)
  - Suspicious login activity (>5 failed attempts)
  - Disk usage alerts (>200MB log files)
- **Email alerting system** (configurable SMTP)
- **Alert severity levels** (high, medium, low)

## 🚀 Usage Guide

### Development Setup

The logging system is automatically active when you start the server:

```bash
python manage.py runserver
```

Logs are automatically created in the `logs/` directory.

### Monitoring Dashboard Access

**Admin-only endpoints** (requires JWT authentication with admin role):

```bash
# Get dashboard stats
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/monitoring/dashboard/

# View recent audit logs
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/monitoring/logs/?type=audit&limit=25

# Check user activity
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/monitoring/activity/?days=7

# System health check
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/monitoring/health/
```

### Health Check Automation

Run manual health checks:

```bash
# Check system health (dry run)
python manage.py check_system_health --dry-run --verbose

# Send alerts to email
python manage.py check_system_health --email admin@company.com

# Verbose output for debugging
python manage.py check_system_health --verbose
```

**Recommended cron job** for production monitoring:
```bash
# Check every 15 minutes
*/15 * * * * cd /path/to/project && python manage.py check_system_health --email alerts@company.com
```

### Configuration

Environment variables in `.env`:

```bash
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENABLE_PERFORMANCE_LOGGING=True   # Enable/disable performance middleware
ENABLE_AUDIT_LOGGING=True         # Enable/disable audit trail logging
ALERT_EMAIL=admin@company.com     # Email for automated alerts
```

## 📊 Log Analysis Examples

### Performance Analysis
```bash
# Find slow requests
grep "SLOW_REQUEST" logs/performance.log

# Average response time analysis
grep "Duration:" logs/performance.log | awk -F'Duration:' '{print $2}' | awk '{print $1}' | sed 's/s//'
```

### Security Analysis
```bash
# Failed login attempts
grep "LOGIN_FAILED" logs/authentication.log

# Suspicious IP activity
grep "IP:" logs/authentication.log | grep "LOGIN_FAILED" | sort | uniq -c
```

### User Activity Analysis
```bash
# Most active users
grep "User:" logs/performance.log | awk -F'User:' '{print $2}' | awk '{print $1}' | sort | uniq -c | sort -nr

# API endpoint usage
grep "URL:" logs/performance.log | awk -F'URL:' '{print $2}' | awk '{print $1}' | sort | uniq -c | sort -nr
```

## 🔒 Security Features

### Sensitive Data Protection
- **Automatic redaction** of passwords, tokens, keys in logs
- **IP address tracking** for security monitoring
- **Failed authentication tracking** with rate limiting detection
- **User action audit trails** for compliance

### Access Control
- **Admin-only monitoring endpoints** with JWT authentication
- **Role-based log access** (admins see all, users see relevant data)
- **Secure log file storage** with proper file permissions

## 🏭 Production Deployment

### Log Rotation
- **Automatic rotation** at 10MB (general/auth) to 50MB (audit/API)
- **Configurable backup count** (10-20 files retained)
- **No external logrotate needed**

### Performance Impact
- **Minimal overhead** (~1-2ms per request)
- **Asynchronous logging** where possible
- **Configurable via environment variables**
- **Optional middleware** can be disabled

### Monitoring Integration
- **Prometheus/Grafana ready** (structured log format)
- **ELK Stack compatible** (JSON parsing available)
- **Custom dashboard API** for internal tools
- **Health check endpoint** for uptime monitoring

## 📋 Alert Thresholds

| Alert Type | Threshold | Severity | Action Required |
|------------|-----------|----------|-----------------|
| Critical Errors | >5 per day | High | Immediate investigation |
| Error Rate | >10% requests | High | Check application health |
| Slow Requests | >20% over 1s | Medium | Performance optimization |
| Failed Logins | >5 per day | Medium | Security review |
| Disk Usage | >200MB logs | Medium | Log cleanup/rotation |
| Very Slow Requests | >5 over 5s | High | Immediate performance fix |

## 🔧 Customization

### Adding Custom Loggers
```python
import logging

# In your views or services
custom_logger = logging.getLogger('legal_backend.custom')
custom_logger.info("Custom log message", extra={
    'user': request.user.email,
    'action': 'custom_action',
    'resource_id': resource.id
})
```

### Custom Alert Rules
Modify `monitoring/management/commands/check_system_health.py` to add:
- Custom threshold values
- New alert types
- Different notification methods
- Integration with external monitoring tools

### Dashboard Extensions
Add new monitoring endpoints in `monitoring/views.py`:
- Custom metrics collection
- Business-specific KPIs
- Integration with external APIs
- Real-time monitoring dashboards

## 📞 Troubleshooting

### Common Issues

**Logs not being created:**
- Check `LOGS_DIR` permissions
- Verify middleware is properly configured in `settings.py`
- Ensure `monitoring` app is in `INSTALLED_APPS`

**Performance impact:**
- Adjust `LOG_LEVEL` to reduce verbosity
- Disable performance logging: `ENABLE_PERFORMANCE_LOGGING=False`
- Configure log rotation more aggressively

**Dashboard not accessible:**
- Verify JWT authentication is working
- Check user has admin role (`role='admin'`)
- Ensure monitoring URLs are included

**Alerts not working:**
- Configure SMTP settings for email alerts
- Check `ALERT_EMAIL` environment variable
- Verify health check command permissions

### Log File Locations
- Development: `./logs/`
- Production: Set `LOGS_DIR` in settings for custom location
- Docker: Mount `/app/logs` volume for persistence

---

## 🎯 Next Steps

This logging and monitoring system provides production-ready observability. Consider these enhancements:

1. **Real-time Dashboards** - WebSocket-based live monitoring
2. **Metrics Aggregation** - Custom metrics collection for business KPIs
3. **External Integrations** - Slack/Teams notifications, PagerDuty alerts
4. **Advanced Analytics** - User behavior analysis, performance trends
5. **Compliance Logging** - Enhanced audit trails for legal requirements

The system is designed to scale with your application and provide comprehensive insights into system health, security, and performance.