#!/usr/bin/env python
"""
Quick fix script for ngrok configuration
This script will update your .env file with the current ngrok URL
"""

import re
import requests
import os
from pathlib import Path

def get_ngrok_url():
    """Get the current ngrok URL from the local API"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        data = response.json()
        
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                return tunnel.get('public_url')
    except:
        pass
    
    return None

def update_env_file(ngrok_url):
    """Update the .env file with the new ngrok URL"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"❌ {env_file} not found. Creating from .env.remote template...")
        if os.path.exists('.env.remote'):
            with open('.env.remote', 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
        else:
            print("❌ No .env.remote template found either!")
            return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Extract domain from ngrok URL
    domain_match = re.search(r'https://([^/]+)', ngrok_url)
    if not domain_match:
        print("❌ Could not extract domain from ngrok URL")
        return False
    
    domain = domain_match.group(1)
    
    # Update ALLOWED_HOSTS
    allowed_hosts_pattern = r'ALLOWED_HOSTS=([^\n]+)'
    if re.search(allowed_hosts_pattern, content):
        # Replace existing ALLOWED_HOSTS, ensuring ngrok domain is included
        def replace_allowed_hosts(match):
            hosts = match.group(1)
            # Remove old ngrok domains
            hosts = re.sub(r',[^,]*\.ngrok-free\.app', '', hosts)
            # Add new ngrok domain
            return f'ALLOWED_HOSTS={hosts},{domain}'
        
        content = re.sub(allowed_hosts_pattern, replace_allowed_hosts, content)
    else:
        # Add ALLOWED_HOSTS if not present
        content += f'\nALLOWED_HOSTS=localhost,127.0.0.1,{domain}\n'
    
    # Update CORS_ALLOWED_ORIGINS
    cors_pattern = r'CORS_ALLOWED_ORIGINS=([^\n]+)'
    if re.search(cors_pattern, content):
        # Replace existing CORS_ALLOWED_ORIGINS, ensuring ngrok URL is included
        def replace_cors_origins(match):
            origins = match.group(1)
            # Remove old ngrok URLs
            origins = re.sub(r',https://[^,]*\.ngrok-free\.app', '', origins)
            # Add new ngrok URL
            return f'CORS_ALLOWED_ORIGINS={origins},{ngrok_url}'
        
        content = re.sub(cors_pattern, replace_cors_origins, content)
    else:
        # Add CORS_ALLOWED_ORIGINS if not present
        content += f'\nCORS_ALLOWED_ORIGINS=http://localhost:3000,{ngrok_url}\n'
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {env_file} with ngrok URL: {ngrok_url}")
    return True

def main():
    print("=== NGROK FIX SCRIPT ===")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ This script must be run from the Django project root directory")
        return
    
    # Get current ngrok URL
    print("1. Getting current ngrok URL...")
    ngrok_url = get_ngrok_url()
    
    if not ngrok_url:
        print("❌ Could not get ngrok URL. Make sure ngrok is running on port 4040")
        print("   Try: ngrok http 8000")
        return
    
    print(f"   Found ngrok URL: {ngrok_url}")
    
    # Update .env file
    print("2. Updating .env file...")
    if update_env_file(ngrok_url):
        print("3. ✅ Done! Now restart your Django service:")
        print("   docker-compose restart web")
        print()
        print("4. Update your Vercel environment variables:")
        print(f"   NEXT_PUBLIC_API_URL={ngrok_url}/api")
        print(f"   NEXT_PUBLIC_AUTH_URL={ngrok_url}/auth")
    else:
        print("❌ Failed to update .env file")

if __name__ == "__main__":
    main()