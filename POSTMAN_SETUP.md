# 📮 Postman Collection Setup Guide - With Authentication

This guide will help you set up and use the Postman collection to test the Legal Practice Management API with JWT authentication and role-based authorization.

## 📁 Files Included

- `Legal_Practice_Management_Auth_API.postman_collection.json` - **NEW** Complete API collection with authentication
- `Legal_Practice_Management_API.postman_collection.json` - Original collection (legacy, no auth)
- `Legal_Practice_Management.postman_environment.json` - Environment variables with auth support
- `POSTMAN_SETUP.md` - This setup guide

## 🔐 Authentication System

The API now uses **JWT (JSON Web Token) authentication** with **role-based permissions**:

### User Roles
- **Admin Lawyers**: Full access to all data and operations (create, read, update, delete)
- **Regular Lawyers**: Limited access to assigned mandates and own time entries (read, limited update)

### Demo Users
After running the setup, you'll have these test accounts:
- **Admin**: `sarah.wilson@lawfirm.com` / `admin123` (full access)
- **Regular**: `michael.chen@lawfirm.com` / `lawyer123` (limited access)
- **Junior**: `emma.rodriguez@lawfirm.com` / `lawyer123` (limited access)

## 🚀 Quick Setup

### 1. Import Collection
1. Open Postman
2. Click **Import** in the top left
3. Drag and drop `Legal_Practice_Management_Auth_API.postman_collection.json` (**use the new auth version**)
4. Click **Import**

### 2. Import Environment
1. Click **Import** again
2. Drag and drop `Legal_Practice_Management.postman_environment.json`
3. Click **Import**
4. Select the **Legal Practice Management Environment** from the environment dropdown (top right)

### 3. Start Your Server & Create Demo Users
```bash
# Start Django server
python manage.py runserver

# Create demo users with test data (REQUIRED for auth)
python manage.py create_demo_users --clear
```

### 4. Test Authentication Flow
1. **Setup Environment**: Navigate to **🚀 Setup & Quick Start > Setup Test Environment**
2. Click **Send** - this will set up current dates automatically
3. **Login First**: Navigate to **🔐 Authentication > Admin Login**
4. Click **Send** - this will automatically save your auth tokens
5. **Populate IDs**: Navigate to **🏢 Clients > Get All Clients** and click **Send** (auto-sets client IDs)
6. **Populate IDs**: Navigate to **⚖️ Lawyers > Get All Lawyers** and click **Send** (auto-sets lawyer IDs)
7. **Populate IDs**: Navigate to **📁 Mandates > Get All Mandates** and click **Send** (auto-sets mandate IDs)
8. **Test API Access**: Now all POST requests will work with correct IDs!

### 5. Test Different User Roles
1. Use **Regular Lawyer Login** to see limited access
2. Compare results between admin and regular user access
3. Try **Role-Based Access Tests** folder to see permission enforcement

## 📚 Collection Structure

### 🚀 Setup & Quick Start (1 request)
- **Environment Setup**: Automatically sets current dates and provides usage instructions
- **Quick Start Guide**: Console output shows step-by-step instructions for first-time users

### 🔐 Authentication (6 requests)
- **Login Endpoints**: Admin, Regular, and Junior lawyer logins
- **Token Management**: Refresh tokens, get current user, logout
- **Auto-Token Storage**: Tokens automatically saved to environment variables

### 👥 User Management (3 requests) - Admin Only
- **User Registration**: Create new user accounts (admin only)
- **User Listing**: View all users in the system (admin only)
- **Profile Linking**: Link user accounts to lawyer profiles (admin only)

### 🏢 Clients (4 requests)
- **CRUD Operations**: Create (admin only), Read, Update, Delete clients
- **Related Data**: Get client's mandates
- **Role-Based Access**: All users can read, only admins can modify

### ⚖️ Lawyers (3 requests)
- **CRUD Operations**: Create (admin only), Read lawyer profiles
- **Monthly Billing**: Get lawyer's monthly billing summary
- **Role-Based Access**: All users can read, only admins can create/modify

### 📁 Mandates (5 requests)
- **Role-Based Listing**: Admins see all, regular lawyers see only assigned mandates
- **Status Filtering**: Active, inactive, and overdue mandates (with proper access control)
- **CRUD Operations**: Create/modify based on role permissions
- **Cost Analysis**: Mandate summaries with cost breakdowns

### ⏱️ Time Entries (4 requests)
- **Role-Based Access**: Admins see all, regular lawyers see only their own entries
- **CRUD Operations**: Create entries for assigned mandates only
- **Filtering**: By date range, lawyer, mandate (respecting permissions)
- **Search**: Search time entry descriptions

### 🔍 Role-Based Access Tests (2 requests)
- **Permission Testing**: Verify unauthenticated access is blocked
- **Role Enforcement**: Test that regular lawyers can't perform admin actions
- **Access Validation**: Confirm proper role-based data filtering

## 🎯 Key Features to Test

### 🔐 Authentication Flow
```bash
# 1. Login (returns tokens)
POST /auth/login/
{
  "email": "sarah.wilson@lawfirm.com",
  "password": "admin123"
}

# 2. All subsequent requests automatically include:
Authorization: Bearer <access_token>

# 3. Token refresh (when needed)
POST /auth/token/refresh/
{
  "refresh": "<refresh_token>"
}
```

### 👑 Role-Based Data Access
```bash
# Admin user sees ALL mandates
GET /api/mandates/  # Returns 3 mandates

# Regular lawyer sees ONLY assigned mandates  
GET /api/mandates/  # Returns 2 mandates (only assigned ones)

# Unauthenticated request
GET /api/mandates/  # Returns 401 Unauthorized
```

### 🔒 Permission-Based Operations
```bash
# Admin can create clients
POST /api/clients/  # Returns 201 Created

# Regular lawyer cannot create clients
POST /api/clients/  # Returns 403 Forbidden

# Only admin can register new users
POST /auth/register/  # Admin: 201 Created, Regular: 403 Forbidden
```

### 📊 Filtering & Search (with role-based results)
```bash
GET /api/mandates/?status=active     # Only active mandates (role-filtered)
GET /api/mandates/?status=overdue    # Only overdue AND active mandates (role-filtered)
GET /api/time-entries/?date_from=2025-06-01  # Date range (role-filtered)
GET /api/mandates/?search=contract   # Search mandates (role-filtered)
```

## 🔧 Environment Variables

The environment includes these key variables:

### 🌐 Server Configuration
- `base_url`: `http://127.0.0.1:8000` (Django server)
- `api_base`: `{{base_url}}/api` (API endpoint base)
- `auth_base`: `{{base_url}}/auth` (Authentication endpoint base)

### 🔑 Authentication Variables (Auto-managed)
- `access_token`: JWT access token (set automatically after login)
- `refresh_token`: JWT refresh token (set automatically after login)
- `current_user_id`: Logged-in user ID (set automatically after login)
- `current_user_role`: User role - 'admin' or 'lawyer' (set automatically after login)
- `current_lawyer_id`: Linked lawyer profile ID (set automatically after login)

### 👥 Demo User Credentials
- `admin_email`: `sarah.wilson@lawfirm.com` (Admin user)
- `admin_password`: `admin123`
- `regular_email`: `michael.chen@lawfirm.com` (Regular lawyer)
- `regular_password`: `lawyer123`
- `junior_email`: `emma.rodriguez@lawfirm.com` (Junior lawyer)
- `junior_password`: `lawyer123`

### 🧪 Test Data IDs (Auto-Populated)
- `test_client_id`: Auto-set when you run "Get All Clients"
- `test_lawyer_id`: Auto-set when you run "Get All Lawyers"  
- `test_mandate_id`: Auto-set when you run "Get All Mandates"
- `current_date`: Auto-set by "Setup Test Environment" to today's date
- `current_month`: Auto-set to current month
- `current_year`: Auto-set to current year

## 📝 Sample Request Bodies

### Create Client
```json
{
    "name": "New Tech Startup Inc.",
    "email": "contact@newtechstartup.com",
    "phone": "555-0199",
    "address": "456 Innovation Drive, Silicon Valley, CA 94000"
}
```

### Create Lawyer
```json
{
    "name": "Alex Partner",
    "email": "alex.partner@lawfirm.com",
    "phone": "555-0300",
    "hourly_rate": "475.00"
}
```

### Create Mandate
```json
{
    "name": "Merger & Acquisition Review",
    "description": "Legal review and due diligence for corporate merger",
    "client": 1,
    "lawyers": [1, 2],
    "due_date": "2025-09-30",
    "cost_ceiling": "125000.00",
    "is_active": true
}
```

### Create Time Entry
```json
{
    "mandate": 1,
    "lawyer": 1,
    "date": "2025-06-24",
    "hours": "5.5",
    "description": "Contract review and client consultation"
}
```

## 🤖 Automated Token Management

The collection includes smart token management:

### Pre-Request Scripts
- **Auto-Refresh**: Tokens are automatically refreshed when expired
- **Token Storage**: Login responses automatically save tokens to environment
- **Error Handling**: Failed refresh attempts clear invalid tokens

### Login Flow
1. Use any login request (Admin/Regular/Junior)
2. Tokens are automatically saved to environment variables
3. All subsequent requests use the saved access token
4. When access token expires, refresh token is used automatically

### Manual Token Management
- **Current User**: `GET /auth/current-user/` to check who's logged in
- **Logout**: `POST /auth/logout/` to clear tokens and blacklist refresh token
- **Refresh**: `POST /auth/token/refresh/` to manually refresh tokens

## 🚨 Common Issues & Solutions

### 1. 401 Unauthorized
- **Problem**: Authentication credentials not provided
- **Solution**: Login first using one of the authentication endpoints
- **Check**: Verify `access_token` is set in environment variables

### 2. 403 Forbidden
- **Problem**: User doesn't have permission for this action
- **Solution**: Use admin account for admin-only operations, or check user role
- **Check**: Verify `current_user_role` in environment (should be 'admin' for admin actions)

### 3. Connection Refused
- **Problem**: Can't connect to server
- **Solution**: Make sure Django server is running (`python manage.py runserver`)

### 4. Empty Responses / No Test Data
- **Problem**: API returns empty lists
- **Solution**: Create demo users and data (`python manage.py create_demo_users --clear`)

### 5. Token Expired
- **Problem**: 401 error even when logged in
- **Solution**: Use refresh token endpoint or login again
- **Auto-Fix**: Pre-request scripts should handle this automatically

### 6. Role-Based Filtering Confusion
- **Problem**: Different users see different data
- **Solution**: This is expected! Admin sees all data, regular lawyers see only assigned data
- **Check**: Compare results between admin and regular user logins

## 🎨 Testing Workflows

### Workflow 1: Authentication & Role Testing
1. **Admin Login** - Login as admin and note the role in console
2. **Get All Mandates** - See all 3 mandates (admin view)
3. **Regular Lawyer Login** - Switch to regular lawyer 
4. **Get All Mandates** - See only 2 mandates (assigned ones)
5. **Test Access Control** - Try creating a client (should fail for regular user)

### Workflow 2: Admin User Management
1. **Admin Login** - Login as admin user
2. **List All Users** - See all users in the system
3. **Register New User** - Create a new lawyer account
4. **Link to Lawyer Profile** - Connect user account to existing lawyer
5. **Test Regular User Access** - Login as new user and test limited access

### Workflow 3: Time Tracking with Permissions
1. **Regular Lawyer Login** - Login as Michael Chen
2. **Get My Time Entries** - See only own time entries
3. **Create Time Entry** - Log time on assigned mandate
4. **Get Mandate Summary** - View cost summary for assigned mandate
5. **Test Restrictions** - Try accessing other lawyer's time entries (should be filtered)

### Workflow 4: Complete Mandate Lifecycle
1. **Admin Login** - Start with full permissions
2. **Create Mandate** - Create new mandate and assign lawyers
3. **Switch to Regular User** - Login as assigned lawyer
4. **Add Time Entries** - Log work on the mandate
5. **Monthly Billing** - View billing summary with new entries

## 🏆 Pro Tips

1. **Login First**: Always start by logging in - all API endpoints require authentication
2. **Check Console**: Login responses log user info to console for confirmation
3. **Role Awareness**: Remember admin vs regular lawyer differences when testing
4. **Status Codes**: 200=Success, 201=Created, 401=Unauthorized, 403=Forbidden, 400=Bad Request
5. **Token Auto-Management**: Tokens are handled automatically - just login and test
6. **Role-Based Results**: Expect different data based on user role (this is correct behavior)
7. **Permission Testing**: Use the Role-Based Access Tests folder to verify security
8. **Environment Variables**: Check environment variables to see current user role and tokens
9. **Switch Users**: Logout and login as different users to test various permission levels
10. **Real-Time Updates**: Create data as admin, then view as regular user to see role filtering

## 📞 Need Help?

If you encounter issues:
1. **Check Authentication**: Ensure you're logged in and tokens are set
2. **Verify User Role**: Check `current_user_role` in environment variables
3. **Django Server Logs**: Look for authentication/permission errors
4. **Demo Data**: Ensure demo users exist (`python manage.py create_demo_users --clear`)
5. **Environment Selection**: Make sure the correct environment is selected
6. **Start Simple**: Begin with login endpoints, then basic GET requests

## 🎯 Quick Test Checklist

✅ **Server Running**: `python manage.py runserver`  
✅ **Demo Data Created**: `python manage.py create_demo_users --clear`  
✅ **Environment Selected**: "Legal Practice Management Environment"  
✅ **Collection Imported**: Use the **Auth** version of the collection  
✅ **First Login**: Start with "Admin Login" to get tokens  
✅ **API Access**: Test "Get All Mandates" to confirm role-based filtering  

Happy testing with authentication! 🔐🚀