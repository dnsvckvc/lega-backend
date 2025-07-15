#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Legal Backend Docker Container...${NC}"

# Function to wait for database
wait_for_db() {
    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    
    until nc -z ${POSTGRES_HOST:-db} ${POSTGRES_PORT:-5432}; do
        echo -e "${YELLOW}Database is unavailable - sleeping${NC}"
        sleep 2
    done
    
    echo -e "${GREEN}Database is ready!${NC}"
}

# Function to run migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    if [ "$(id -u)" = "0" ]; then
        su -s /bin/sh appuser -c "python manage.py migrate --noinput"
    else
        python manage.py migrate --noinput
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Migrations completed successfully!${NC}"
    else
        echo -e "${RED}Migration failed!${NC}"
        exit 1
    fi
}

# Function to collect static files
collect_static() {
    echo -e "${YELLOW}Collecting static files...${NC}"
    if [ "$(id -u)" = "0" ]; then
        su -s /bin/sh appuser -c "python manage.py collectstatic --noinput"
    else
        python manage.py collectstatic --noinput
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Static files collected successfully!${NC}"
    else
        echo -e "${RED}Static file collection failed!${NC}"
        exit 1
    fi
}

# Function to create demo users (only in development)
create_demo_users() {
    if [ "${DEBUG:-True}" = "True" ]; then
        echo -e "${YELLOW}Creating demo users...${NC}"
        if [ "$(id -u)" = "0" ]; then
            su -s /bin/sh appuser -c "python manage.py create_demo_users --clear"
        else
            python manage.py create_demo_users --clear
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Demo users created successfully!${NC}"
        else
            echo -e "${YELLOW}Demo users creation failed or already exist${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping demo users creation in production mode${NC}"
    fi
}

# Function to create superuser in production
create_superuser() {
    if [ "${DEBUG:-True}" = "False" ] && [ -n "${DJANGO_SUPERUSER_EMAIL}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
        echo -e "${YELLOW}Creating superuser...${NC}"
        if [ "$(id -u)" = "0" ]; then
            su -s /bin/sh appuser -c "python manage.py createsuperuser \
                --noinput \
                --email=\"${DJANGO_SUPERUSER_EMAIL}\" \
                --first_name=\"${DJANGO_SUPERUSER_FIRST_NAME:-Admin}\" \
                --last_name=\"${DJANGO_SUPERUSER_LAST_NAME:-User}\" \
                --role=admin" \
                || echo -e "${YELLOW}Superuser already exists or creation failed${NC}"
        else
            python manage.py createsuperuser \
                --noinput \
                --email="${DJANGO_SUPERUSER_EMAIL}" \
                --first_name="${DJANGO_SUPERUSER_FIRST_NAME:-Admin}" \
                --last_name="${DJANGO_SUPERUSER_LAST_NAME:-User}" \
                --role=admin \
                || echo -e "${YELLOW}Superuser already exists or creation failed${NC}"
        fi
    fi
}

# Function to ensure logs directory permissions
ensure_logs_permissions() {
    echo -e "${YELLOW}Ensuring logs directory permissions...${NC}"
    
    # Create logs directory if it doesn't exist
    mkdir -p /app/logs
    
    # If we're running as root, fix ownership (this happens in some environments)
    if [ "$(id -u)" = "0" ]; then
        echo -e "${YELLOW}Running as root, fixing ownership...${NC}"
        chown -R appuser:appuser /app/logs /app/media
        chmod -R 755 /app/logs
        echo -e "${GREEN}Ownership fixed as root!${NC}"
    fi
    
    # Test if we can create a log file (as the current user)
    if [ "$(id -u)" = "0" ]; then
        # Test as appuser if we're root
        if su -s /bin/sh appuser -c "touch /app/logs/test.log 2>/dev/null && rm -f /app/logs/test.log"; then
            echo -e "${GREEN}Log file creation test passed (as appuser)!${NC}"
        else
            echo -e "${RED}Cannot create log files in /app/logs directory (as appuser)!${NC}"
            exit 1
        fi
    else
        # Test as current user
        if touch /app/logs/test.log 2>/dev/null && rm -f /app/logs/test.log; then
            echo -e "${GREEN}Log file creation test passed!${NC}"
        else
            echo -e "${RED}Cannot create log files in /app/logs directory!${NC}"
            exit 1
        fi
    fi
}

# Function to auto-detect ngrok tunnel
detect_ngrok() {
    echo -e "${YELLOW}Checking for ngrok tunnel...${NC}"
    
    # Check if ngrok API is accessible
    if curl -s --connect-timeout 2 host.docker.internal:4040/api/tunnels > /dev/null 2>&1; then
        echo -e "${GREEN}ngrok API accessible, detecting URL...${NC}"
        
        # Get the HTTPS tunnel URL
        NGROK_URL=$(curl -s host.docker.internal:4040/api/tunnels | jq -r '.tunnels[] | select(.proto=="https") | .public_url' 2>/dev/null || echo '')
        
        if [ -n "$NGROK_URL" ] && [ "$NGROK_URL" != "null" ]; then
            # Extract domain from URL
            NGROK_DOMAIN=$(echo "$NGROK_URL" | sed 's|https://||' | sed 's|/.*||')
            
            # Add ngrok domain to ALLOWED_HOSTS
            if [ -n "$ALLOWED_HOSTS" ]; then
                export ALLOWED_HOSTS="${ALLOWED_HOSTS},${NGROK_DOMAIN}"
            else
                export ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0,${NGROK_DOMAIN}"
            fi
            
            # Add ngrok URL to CORS_ALLOWED_ORIGINS
            if [ -n "$CORS_ALLOWED_ORIGINS" ]; then
                export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS},${NGROK_URL}"
            else
                export CORS_ALLOWED_ORIGINS="http://localhost:3000,${NGROK_URL}"
            fi
            
            echo -e "${GREEN}✅ Auto-detected ngrok tunnel: $NGROK_URL${NC}"
            echo -e "${GREEN}📝 Updated ALLOWED_HOSTS: $ALLOWED_HOSTS${NC}"
            echo -e "${GREEN}🌐 Updated CORS_ALLOWED_ORIGINS: $CORS_ALLOWED_ORIGINS${NC}"
        else
            echo -e "${YELLOW}⚠️  ngrok API responded but no HTTPS tunnel found${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ️  ngrok not accessible (this is normal if not using ngrok)${NC}"
    fi
}

# Function to check system health
check_system_health() {
    echo -e "${YELLOW}Checking system health...${NC}"
    if [ "$(id -u)" = "0" ]; then
        su -s /bin/sh appuser -c "python manage.py check --deploy"
    else
        python manage.py check --deploy
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}System health check passed!${NC}"
    else
        echo -e "${RED}System health check failed!${NC}"
        exit 1
    fi
}

# Main execution
main() {
    echo -e "${GREEN}=== Legal Backend Initialization ===${NC}"
    
    # Auto-detect ngrok tunnel first (so environment vars are set early)
    detect_ngrok
    
    # Ensure logs directory permissions
    ensure_logs_permissions
    
    # Wait for database
    wait_for_db
    
    # Run migrations
    run_migrations
    
    # Collect static files
    collect_static
    
    # Create demo users (development only)
    create_demo_users
    
    # Create superuser (production only)
    create_superuser
    
    # Check system health
    check_system_health
    
    echo -e "${GREEN}=== Initialization Complete ===${NC}"
    echo -e "${GREEN}Starting application...${NC}"
    
    # Execute the main command (switch to appuser if running as root)
    if [ "$(id -u)" = "0" ]; then
        echo -e "${YELLOW}Switching to appuser for Django application...${NC}"
        exec su -s /bin/sh appuser -c "$*"
    else
        exec "$@"
    fi
}

# Run main function
main "$@"