#!/bin/bash
# Install Python dependencies for the API server

echo "Installing Python dependencies..."

# Install required packages
pip3 install flask flask-cors psycopg2-binary python-dotenv redis

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "import flask; import flask_cors; import psycopg2; from dotenv import load_dotenv; import redis; print('✅ All dependencies installed successfully!')" && echo "✅ Verification passed" || echo "❌ Some dependencies failed to install"

echo ""
echo "Dependencies installed. You can now start the server with:"
echo "  ./start_api_server.sh start"




