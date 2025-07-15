# Vercel Frontend Deployment Configuration

This guide covers the necessary changes to deploy your frontend on Vercel and connect it to your Django backend.

## 1. Django Backend Configuration

### CORS Settings
The Django settings have been updated to support Vercel deployments. The following regex patterns are now enabled:
- `https://*.vercel.app` - Supports all Vercel preview deployments
- Local development URLs for testing

### Environment Variables Required
Add these environment variables to your deployment environment:

```bash
# Production CORS settings
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app
DEBUG=False
ALLOWED_HOSTS=your-backend-domain.com,127.0.0.1,localhost

# If using custom domain on Vercel
CORS_ALLOWED_ORIGINS=https://your-custom-domain.com,https://your-app.vercel.app
```

### Security Settings for Production
Ensure these settings are configured for production:

```python
# In your .env file or environment variables
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-backend-domain.com,your-api-server.com
```

## 2. Vercel Frontend Configuration

### Environment Variables in Vercel
In your Vercel dashboard, add these environment variables:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend-domain.com/api
NEXT_PUBLIC_AUTH_URL=https://your-backend-domain.com/auth

# Or if using different environments
NEXT_PUBLIC_API_URL=https://your-backend-domain.com/api
NEXT_PUBLIC_AUTH_URL=https://your-backend-domain.com/auth
```

### Frontend Code Changes
Update your API base URL configuration:

```javascript
// api/config.js or similar
const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  authURL: process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:8000/auth',
};

export default API_CONFIG;
```

### axios/fetch Configuration
Ensure your HTTP client is configured for CORS:

```javascript
// For axios
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // Important for JWT cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// For fetch
const fetchWithAuth = async (url, options = {}) => {
  return fetch(url, {
    ...options,
    credentials: 'include', // Important for JWT cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
};
```

## 3. Backend Deployment Requirements

### Server Configuration
Your Django backend needs to be deployed on a server that supports:
- HTTPS (required for production)
- Static file serving
- Database connection
- Environment variable configuration

### Common Deployment Options
- **Railway**: Easy Django deployment
- **Heroku**: Traditional PaaS
- **DigitalOcean App Platform**: Managed deployment
- **AWS Elastic Beanstalk**: AWS managed service
- **Google Cloud Run**: Container-based deployment

### Database Configuration
Ensure your production database is configured:

```python
# For PostgreSQL (recommended)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

## 4. Testing the Connection

### Local Testing
1. Start your Django backend locally
2. Deploy your frontend to Vercel
3. Test API calls from Vercel to your local backend

### Production Testing
1. Deploy Django backend to production
2. Update Vercel environment variables
3. Test full production setup

### Common Issues and Solutions

#### CORS Errors
- Ensure your Vercel domain is in `CORS_ALLOWED_ORIGINS`
- Check that `CORS_ALLOW_CREDENTIALS = True`
- Verify HTTPS is used in production

#### Authentication Issues
- Ensure JWT tokens are properly handled
- Check that cookies are set with correct domain
- Verify token expiration settings

#### API Endpoint Issues
- Confirm API URLs are correctly configured
- Check network tab for failed requests
- Verify authentication headers are sent

## 5. Security Considerations

### Production Security
- Use HTTPS only in production
- Set secure cookie settings
- Configure proper CSRF protection
- Use environment variables for secrets

### Rate Limiting
Consider adding rate limiting to your API endpoints:

```python
# In settings.py
INSTALLED_APPS = [
    'django_ratelimit',
]

# In views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h', method='POST')
def login_view(request):
    # Login logic
    pass
```

## 6. Monitoring and Logging

### Backend Monitoring
- Monitor API response times
- Track authentication failures
- Log CORS-related errors

### Frontend Monitoring
- Monitor API call success rates
- Track authentication flow
- Monitor console errors

## Example Environment Files

### Backend (.env)
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,127.0.0.1
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app

# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

### Frontend (Vercel Environment Variables)
```bash
NEXT_PUBLIC_API_URL=https://your-backend.com/api
NEXT_PUBLIC_AUTH_URL=https://your-backend.com/auth
```

This configuration should enable your Vercel frontend to successfully communicate with your Django backend APIs.