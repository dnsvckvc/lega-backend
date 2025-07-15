#!/usr/bin/env python
"""
Debug script to check Django settings for ngrok configuration
Run this on your server to see what Django is actually loading
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_backend.settings')
django.setup()

from django.conf import settings
from decouple import config

print("=== NGROK DEBUG INFORMATION ===")
print()

# Check environment variables
print("1. ENVIRONMENT VARIABLES:")
print(f"   ALLOWED_HOSTS env var: {os.getenv('ALLOWED_HOSTS', 'NOT SET')}")
print(f"   CORS_ALLOWED_ORIGINS env var: {os.getenv('CORS_ALLOWED_ORIGINS', 'NOT SET')}")
print(f"   DEBUG env var: {os.getenv('DEBUG', 'NOT SET')}")
print()

# Check Django settings
print("2. DJANGO SETTINGS:")
print(f"   DEBUG: {settings.DEBUG}")
print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"   CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
print(f"   CORS_ALLOWED_ORIGIN_REGEXES: {settings.CORS_ALLOWED_ORIGIN_REGEXES}")
print()

# Test ngrok URL matching
print("3. NGROK URL TESTING:")
ngrok_url = "https://714bd790aa57.ngrok-free.app"
print(f"   Testing URL: {ngrok_url}")

# Check if URL is in ALLOWED_HOSTS
host_domain = "714bd790aa57.ngrok-free.app"
if host_domain in settings.ALLOWED_HOSTS:
    print(f"   ✅ {host_domain} is in ALLOWED_HOSTS")
else:
    print(f"   ❌ {host_domain} is NOT in ALLOWED_HOSTS")

# Check if URL is in CORS_ALLOWED_ORIGINS
if ngrok_url in settings.CORS_ALLOWED_ORIGINS:
    print(f"   ✅ {ngrok_url} is in CORS_ALLOWED_ORIGINS")
else:
    print(f"   ❌ {ngrok_url} is NOT in CORS_ALLOWED_ORIGINS")

# Test regex patterns
import re
print()
print("4. REGEX PATTERN TESTING:")
for pattern in settings.CORS_ALLOWED_ORIGIN_REGEXES:
    if re.match(pattern, ngrok_url):
        print(f"   ✅ {ngrok_url} matches pattern: {pattern}")
    else:
        print(f"   ❌ {ngrok_url} does NOT match pattern: {pattern}")

print()
print("5. TROUBLESHOOTING STEPS:")
print("   - Make sure your .env file is in the correct location")
print("   - Check that Docker is loading the .env file properly")
print("   - Verify the ngrok URL is correct and accessible")
print("   - Try setting CORS_ALLOW_ALL_ORIGINS=True temporarily for testing")
print()

# Check if .env file exists and show its contents
env_files = ['.env', '.env.remote', '.env.docker']
print("6. ENVIRONMENT FILES:")
for env_file in env_files:
    if os.path.exists(env_file):
        print(f"   ✅ {env_file} exists")
        with open(env_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'ALLOWED_HOSTS' in line or 'CORS_ALLOWED_ORIGINS' in line:
                    print(f"      {line.strip()}")
    else:
        print(f"   ❌ {env_file} does not exist")

print()
print("=== END DEBUG INFO ===")