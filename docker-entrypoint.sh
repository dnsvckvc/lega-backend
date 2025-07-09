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
    python manage.py migrate --noinput
    
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
    python manage.py collectstatic --noinput
    
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
        python manage.py create_demo_users --clear
        
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
        python manage.py createsuperuser \
            --noinput \
            --email="${DJANGO_SUPERUSER_EMAIL}" \
            --first_name="${DJANGO_SUPERUSER_FIRST_NAME:-Admin}" \
            --last_name="${DJANGO_SUPERUSER_LAST_NAME:-User}" \
            --role=admin \
            || echo -e "${YELLOW}Superuser already exists or creation failed${NC}"
    fi
}

# Function to ensure logs directory permissions
ensure_logs_permissions() {
    echo -e "${YELLOW}Ensuring logs directory permissions...${NC}"
    
    # Create logs directory if it doesn't exist
    mkdir -p /app/logs
    
    # Check if we can write to the logs directory
    if [ -w /app/logs ]; then
        echo -e "${GREEN}Logs directory is writable!${NC}"
    else
        echo -e "${RED}Logs directory is not writable! Attempting to fix...${NC}"
        # Try to fix permissions (this might not work in all environments)
        chmod 755 /app/logs 2>/dev/null || true
        
        if [ -w /app/logs ]; then
            echo -e "${GREEN}Logs directory permissions fixed!${NC}"
        else
            echo -e "${RED}Cannot fix logs directory permissions. Logging may fail.${NC}"
        fi
    fi
    
    # Test if we can create a log file
    touch /app/logs/test.log 2>/dev/null && rm -f /app/logs/test.log
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Log file creation test passed!${NC}"
    else
        echo -e "${RED}Cannot create log files in /app/logs directory!${NC}"
        exit 1
    fi
}

# Function to check system health
check_system_health() {
    echo -e "${YELLOW}Checking system health...${NC}"
    python manage.py check --deploy
    
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
    
    # Execute the main command
    exec "$@"
}

# Run main function
main "$@"