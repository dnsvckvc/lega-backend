#!/bin/bash
set -e

echo "🚀 Deploying Legal Practice Backend with ngrok..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: This script must be run from the Django project root directory"
    exit 1
fi

# Check if required files exist
if [ ! -f "fix_ngrok.py" ]; then
    echo "❌ Error: fix_ngrok.py not found. Make sure you're in the correct directory."
    exit 1
fi

if [ ! -f "docker-compose.remote.yml" ]; then
    echo "❌ Error: docker-compose.remote.yml not found."
    exit 1
fi

# Wait for ngrok to be ready
echo "⏳ Waiting for ngrok to start..."
timeout=60
elapsed=0
until curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Timeout waiting for ngrok. Please start ngrok manually:"
        echo "   ngrok http 8000"
        exit 1
    fi
    echo "   Waiting for ngrok API (${elapsed}s)..."
    sleep 2
    elapsed=$((elapsed + 2))
done

echo "✅ ngrok is running"

# Get current ngrok URL
echo "🔍 Detecting ngrok URL..."
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[] | select(.proto=="https") | .public_url' 2>/dev/null || echo "")

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo "❌ Error: Could not detect ngrok HTTPS URL."
    echo "   Make sure ngrok is running with: ngrok http 8000"
    exit 1
fi

echo "📍 Detected ngrok URL: $NGROK_URL"

# Update environment files with current ngrok URL
echo "📝 Updating environment configuration..."
if python3 fix_ngrok.py; then
    echo "✅ Environment files updated"
else
    echo "❌ Failed to update environment files"
    exit 1
fi

# Deploy containers
echo "🐳 Building and deploying Docker containers..."
if docker-compose -f docker-compose.remote.yml up -d --build; then
    echo "✅ Containers deployed successfully"
else
    echo "❌ Container deployment failed"
    exit 1
fi

# Wait for containers to be ready
echo "⏳ Waiting for containers to be ready..."
sleep 15

# Test the deployment
echo "🧪 Testing deployment..."
if curl -s -I "$NGROK_URL/docs/" | head -1 | grep -q "200\|302"; then
    echo "✅ Deployment test passed"
else
    echo "⚠️  Deployment test failed, but containers are running"
    echo "   Check logs: docker-compose -f docker-compose.remote.yml logs web"
fi

# Display container status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.remote.yml ps

echo ""
echo "🎉 Deployment Complete!"
echo "================================================"
echo "📍 Your API is available at: $NGROK_URL"
echo "📚 Documentation: $NGROK_URL/docs/"
echo "🔧 Admin Interface: $NGROK_URL/admin/"
echo "🔌 API Base: $NGROK_URL/api/"
echo ""
echo "📋 Next Steps:"
echo "  1. Visit $NGROK_URL/docs/ to test the API"
echo "  2. Update your frontend environment variables:"
echo "     NEXT_PUBLIC_API_URL=$NGROK_URL"
echo "     NEXT_PUBLIC_AUTH_URL=$NGROK_URL/auth"
echo "  3. Test authentication with demo users (see docs)"
echo ""
echo "🔧 Useful Commands:"
echo "  - View logs: docker-compose -f docker-compose.remote.yml logs web"
echo "  - Restart: docker-compose -f docker-compose.remote.yml restart web"
echo "  - Update code: git pull && ./deploy-with-ngrok.sh"
echo ""
echo "✅ Happy coding!"