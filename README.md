# Legal Practice Management Backend

A Django REST API backend for managing legal practice operations including clients, lawyers, mandates (projects), and time tracking with **JWT authentication and role-based authorization**.

## 🔐 Authentication & Security Features

- **JWT Authentication**: Secure token-based authentication with automatic refresh
- **Role-Based Authorization**: Admin lawyers vs Regular lawyers with different access levels
- **User Management**: Admin-only user registration and profile linking
- **Data Protection**: Role-based data filtering ensures lawyers only see relevant data
- **Permission System**: Granular permissions for all CRUD operations

## 📋 Core Features

- **Client Management**: Store client information with contact details and addresses
- **Lawyer Management**: Manage lawyer profiles with hourly rates and user account linking
- **Mandate Management**: Track legal projects with assigned lawyers, due dates, and cost ceilings
- **Time Tracking**: Log billable hours with automatic cost calculations
- **Change Tracking**: Comprehensive audit trail for all data modifications with field-level changes
- **REST API**: Full CRUD operations with filtering, searching, and pagination
- **Admin Interface**: Django admin interface for easy data management
- **Postman Integration**: Complete API collection with authentication testing

## 🏗️ System Architecture

### User & Authentication
- **Custom User Model**: Extends Django's AbstractUser with role management
- **Roles**: Admin Lawyer (full access) vs Regular Lawyer (limited access)
- **Profile Linking**: User accounts linked to Lawyer profiles for data access control

### Core Models

#### Client
- Name, email, phone, address
- Relationship to mandates
- **Access**: All users can read, only admins can modify

#### Lawyer
- Name, email, phone, hourly rate
- Can be assigned to multiple mandates
- Linked to user accounts for authentication
- **Access**: All users can read, only admins can create/modify

#### Mandate
- Name, description, client, assigned lawyers
- Due date and optional cost ceiling
- Active/inactive status flag
- Tracks total hours and costs
- **Access**: Admins see all, regular lawyers see only assigned mandates

#### TimeEntry
- Links lawyer to mandate with date and hours
- Automatic cost calculation based on lawyer's hourly rate
- Optional description for work performed
- **Access**: Admins see all, regular lawyers see only their own entries

#### ChangeLog
- Unified change tracking for all data modifications
- Field-level audit trail with old/new values
- User attribution and timestamp tracking
- Generic foreign key system for extensibility
- **Access**: Role-based filtering matching source data permissions

## 🔗 API Endpoints

**All API endpoints require JWT authentication** via `Authorization: Bearer <token>` header.

### Authentication Endpoints
Base URL: `/auth/`

- `POST /auth/login/` - Login and get JWT tokens
- `POST /auth/token/refresh/` - Refresh access token
- `POST /auth/logout/` - Logout and blacklist refresh token
- `GET /auth/current-user/` - Get current user info
- `POST /auth/register/` - Register new user (admin only)
- `GET /auth/users/` - List all users (admin only)
- `POST /auth/link-lawyer/` - Link user to lawyer profile (admin only)

### Core API Endpoints
Base URL: `/api/`

#### Clients (Role-Based Access)
- `GET /api/clients/` - List all clients *(all users)*
- `POST /api/clients/` - Create new client *(admin only)*
- `GET /api/clients/{id}/` - Get client details *(all users)*
- `PUT/PATCH /api/clients/{id}/` - Update client *(admin only)*
- `DELETE /api/clients/{id}/` - Delete client *(admin only)*
- `GET /api/clients/{id}/mandates/` - Get client's mandates *(role-filtered)*

#### Lawyers (Role-Based Access)
- `GET /api/lawyers/` - List all lawyers *(all users)*
- `POST /api/lawyers/` - Create new lawyer *(admin only)*
- `GET /api/lawyers/{id}/` - Get lawyer details *(all users)*
- `PUT/PATCH /api/lawyers/{id}/` - Update lawyer *(admin only)*
- `DELETE /api/lawyers/{id}/` - Delete lawyer *(admin only)*
- `GET /api/lawyers/{id}/mandates/` - Get lawyer's mandates *(role-filtered)*
- `GET /api/lawyers/{id}/time_entries/` - Get lawyer's time entries *(role-filtered)*
- `GET /api/lawyers/{id}/monthly_billing/` - Get lawyer's monthly billing summary *(role-filtered)*

#### Mandates (Role-Based Access)
- `GET /api/mandates/` - List mandates *(admin: all, regular: only assigned)*
- `POST /api/mandates/` - Create new mandate *(admin/limited regular)*
- `GET /api/mandates/{id}/` - Get mandate details *(access-controlled)*
- `PUT/PATCH /api/mandates/{id}/` - Update mandate *(admin/limited regular)*
- `DELETE /api/mandates/{id}/` - Delete mandate *(admin only)*
- `GET /api/mandates/{id}/time_entries/` - Get mandate's time entries *(access-controlled)*
- `GET /api/mandates/{id}/summary/` - Get mandate summary with costs *(access-controlled)*

#### Time Entries (Role-Based Access)
- `GET /api/time-entries/` - List time entries *(admin: all, regular: own only)*
- `POST /api/time-entries/` - Create new time entry *(for assigned mandates)*
- `GET /api/time-entries/{id}/` - Get time entry details *(access-controlled)*
- `PUT/PATCH /api/time-entries/{id}/` - Update time entry *(access-controlled)*
- `DELETE /api/time-entries/{id}/` - Delete time entry *(access-controlled)*

#### Change Logs (Role-Based Access)
- `GET /api/change-logs/` - List all change logs *(role-filtered)*
- `GET /api/change-logs/{id}/` - Get change log details *(access-controlled)*
- `GET /api/change-logs/client-changes/` - Get client changes only *(role-filtered)*
- `GET /api/change-logs/mandate-changes/` - Get mandate changes only *(role-filtered)*
- `GET /api/change-logs/timeentry-changes/` - Get time entry changes only *(role-filtered)*
- `GET /api/change-logs/recent/` - Get recent changes (last 24 hours) *(role-filtered)*
- `GET /api/change-logs/user-activity/` - Get changes by specific user *(role-filtered)*
- `GET /api/change-logs/object-history/` - Get change history for specific object *(role-filtered)*

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- pip
- PostgreSQL (for production) - SQLite used for development

### Quick Start

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd claude-first
   pip install -r requirements.txt
   ```

2. **Environment setup:**
   The `.env` file is included with default settings. For production, update:
   ```bash
   SECRET_KEY=your-secure-secret-key
   DEBUG=False
   # Add database settings for PostgreSQL
   ```

3. **Database setup:**
   ```bash
   python manage.py migrate
   ```

4. **Create demo users and data:**
   ```bash
   python manage.py create_demo_users --clear
   ```
   
   This creates:
   - **Admin**: `sarah.wilson@lawfirm.com` / `admin123`
   - **Regular**: `michael.chen@lawfirm.com` / `lawyer123`
   - **Junior**: `emma.rodriguez@lawfirm.com` / `lawyer123`

5. **Start development server:**
   ```bash
   python manage.py runserver
   ```

6. **Test the API:**
   - **Login**: `POST http://localhost:8000/auth/login/`
   - **API Access**: `GET http://localhost:8000/api/mandates/` (with Bearer token)
   - **Admin Interface**: `http://localhost:8000/admin/`

### 📮 Postman Testing

1. **Import Postman collection:**
   - Import `Legal_Practice_Management_Auth_API.postman_collection.json`
   - Import `Legal_Practice_Management.postman_environment.json`

2. **Start testing:**
   - Use **Admin Login** to get tokens
   - Test role-based access with different user logins
   - See `POSTMAN_SETUP.md` for detailed testing guide

### 🔐 Authentication Flow

```bash
# 1. Login to get tokens
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "sarah.wilson@lawfirm.com", "password": "admin123"}'

# 2. Use access token for API requests
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/mandates/

# 3. Refresh token when expired
curl -X POST http://localhost:8000/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

## 🧪 Testing

### Unit Tests

Run all tests:
```bash
python manage.py test
```

Run specific test modules:
```bash
python manage.py test authentication      # Authentication & authorization tests
python manage.py test core.tests          # Model tests
python manage.py test core.test_api       # API endpoint tests (requires auth updates)
python manage.py test core.test_serializers  # Serializer tests
python manage.py test core.test_filtering    # Filtering tests (requires auth updates)
python manage.py test core.test_change_tracking  # Change tracking tests (24 tests)
```

**Note**: Some core tests need authentication setup. The authentication tests (11 tests) and change tracking tests (24 tests) are fully functional.

### Authentication Testing

Test the complete authentication system:
```bash
python manage.py test authentication -v 2
```

Tests include:
- ✅ User model creation and role management
- ✅ JWT login and token generation
- ✅ Admin-only user registration
- ✅ Role-based permission enforcement
- ✅ Data access control validation

### Manual API Testing

**Quick validation:**
```bash
# 1. Create demo data
python manage.py create_demo_users --clear

# 2. Test authentication endpoints
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "sarah.wilson@lawfirm.com", "password": "admin123"}'

# 3. Test role-based data access
TOKEN="<access_token_from_login>"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/mandates/
```

### Postman Testing Suite

Use the comprehensive Postman collection:
1. Import `Legal_Practice_Management_Auth_API.postman_collection.json`
2. Import environment file
3. Run **Authentication > Admin Login**
4. Test role-based access patterns
5. Verify permission enforcement

### Test Coverage

**Authentication System** (✅ Complete):
- JWT token authentication and refresh
- Role-based authorization (admin vs regular lawyers)
- User registration and profile linking (admin only)
- Permission-based data filtering
- Security validation and access control

**Core API** (⚠️ Requires auth token setup):
- All model operations and validations
- CRUD endpoints with role-based permissions
- Filtering, searching, and pagination
- Business logic (billing, cost calculations)
- Custom endpoints (summaries, monthly billing)

## API Features

- **Filtering**: Filter by various fields (e.g., client, lawyer, date)
- **Searching**: Full-text search across relevant fields
- **Ordering**: Sort results by different criteria
- **Pagination**: Paginated responses (20 items per page)
- **Validation**: Input validation with meaningful error messages
- **CORS**: Configured for frontend integration

## Query Parameters

### Time Entries
- `date_from` - Filter entries from date (YYYY-MM-DD)
- `date_to` - Filter entries to date (YYYY-MM-DD)
- `mandate` - Filter by mandate ID
- `lawyer` - Filter by lawyer ID

### Search
Add `?search=keyword` to search endpoints

### Ordering
Add `?ordering=field_name` or `?ordering=-field_name` (descending)

### Mandate Filtering
- `status=active` - Only active mandates (is_active=True)
- `status=inactive` - Only inactive mandates (is_active=False)
- `status=overdue` - Only overdue AND active mandates (due_date < today AND is_active=True)
- `is_active=true/false` - Direct filtering by active status
- `due_date_from` - Filter by due date from (YYYY-MM-DD)
- `due_date_to` - Filter by due date to (YYYY-MM-DD)

## 🔧 Production Deployment

### Dependencies
All required packages are in `requirements.txt`:
```
Django==4.2.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.5.0
psycopg2-binary==2.9.7
django-cors-headers==4.3.1
python-decouple==3.8
django-filter==23.3
```

### Environment Configuration
Update `.env` for production:
```bash
SECRET_KEY=your-very-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# PostgreSQL Database
DB_NAME=legal_backend_prod
DB_USER=your_db_user
DB_PASSWORD=secure_db_password
DB_HOST=your_db_host
DB_PORT=5432

# Security Settings
SECURE_SSL_REDIRECT=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

### Deployment Checklist
- ✅ Update SECRET_KEY to a secure value
- ✅ Set DEBUG=False
- ✅ Configure PostgreSQL database
- ✅ Set up HTTPS/SSL
- ✅ Configure ALLOWED_HOSTS
- ✅ Run migrations: `python manage.py migrate`
- ✅ Create admin user: `python manage.py createsuperuser`
- ✅ Collect static files: `python manage.py collectstatic`
- ✅ Set up proper logging
- ✅ Configure CORS for your frontend domain

## 📊 Logging and Monitoring System

**Comprehensive production-ready observability:**

- ✅ **Multi-level logging** with automatic rotation (general, errors, performance, API, auth, audit)
- ✅ **Performance monitoring** with request duration tracking and slow request alerts
- ✅ **Security logging** with failed login detection and IP tracking
- ✅ **Audit trails** for all data modifications with user context
- ✅ **Admin dashboard API** with system health metrics and log analysis
- ✅ **Automated health checks** with email alerting for critical issues
- ✅ **Sensitive data protection** with automatic redaction of passwords/tokens

**Monitoring Endpoints** (Admin Only):
- `GET /monitoring/dashboard/` - System statistics and metrics
- `GET /monitoring/logs/` - Recent log entries with filtering
- `GET /monitoring/activity/` - User activity analysis
- `GET /monitoring/health/` - System health and alerts

**Health Check Command:**
```bash
python manage.py check_system_health --email admin@company.com
```

See `LOGGING_AND_MONITORING.md` for complete documentation.

## 🚀 Future Enhancements

- ✅ **Authentication and user permissions** - COMPLETED
- ✅ **Logging and monitoring system** - COMPLETED
- Document management and file uploads
- Invoice generation and PDF reports
- Advanced reporting and analytics dashboard
- Email notifications for due dates and milestones
- Calendar integration for court dates and deadlines
- Advanced search with full-text search
- API rate limiting and throttling
- Mobile app support
- Integration with legal research tools

## 📄 License

This project is available for educational and development purposes.