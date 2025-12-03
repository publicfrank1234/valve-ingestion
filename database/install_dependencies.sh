#!/bin/bash
# Install Python dependencies for the API server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${PARENT_DIR}/venv"

echo "🔍 Checking for virtual environment..."
echo "   Script directory: $SCRIPT_DIR"
echo "   Parent directory: $PARENT_DIR"
echo "   Looking for venv at: $VENV_PATH"

# Check for virtual environment (same logic as start_api_server.sh)
if [ -d "$VENV_PATH" ]; then
    PIP_CMD="${VENV_PATH}/bin/pip"
    PYTHON_CMD="${VENV_PATH}/bin/python"
    echo "✅ Found virtual environment: $VENV_PATH"
    
    # Verify the venv is valid
    if [ ! -f "$PIP_CMD" ]; then
        echo "⚠️  Warning: venv directory exists but pip not found. Recreating venv..."
        rm -rf "$VENV_PATH"
        python3 -m venv "$VENV_PATH"
    fi
else
    echo "⚠️  Virtual environment not found at: $VENV_PATH"
    echo "📦 Creating virtual environment..."
    
    # Create venv if it doesn't exist
    if python3 -m venv "$VENV_PATH"; then
        PIP_CMD="${VENV_PATH}/bin/pip"
        PYTHON_CMD="${VENV_PATH}/bin/python"
        echo "✅ Virtual environment created: $VENV_PATH"
    else
        echo "❌ Failed to create virtual environment. Using system Python (may require --break-system-packages)"
        PIP_CMD="pip3"
        PYTHON_CMD="python3"
    fi
fi

echo ""
echo "📦 Installing Python dependencies..."
echo "   Using: $PIP_CMD"

# Install required packages
if [ "$PIP_CMD" = "pip3" ]; then
    # System pip - may need --break-system-packages on newer Python
    $PIP_CMD install --break-system-packages flask flask-cors psycopg2-binary python-dotenv redis || {
        echo "❌ Installation failed. Please create a virtual environment manually:"
        echo "   cd $PARENT_DIR && python3 -m venv venv"
        exit 1
    }
else
    # Venv pip - no special flags needed
    $PIP_CMD install flask flask-cors psycopg2-binary python-dotenv redis || {
        echo "❌ Installation failed"
        exit 1
    }
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."
if $PYTHON_CMD -c "import flask; import flask_cors; import psycopg2; from dotenv import load_dotenv; import redis; print('✅ All dependencies installed successfully!')" 2>/dev/null; then
    echo "✅ Verification passed"
else
    echo "❌ Some dependencies failed to install"
    exit 1
fi

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "You can now start the server with:"
echo "  ./start_api_server.sh start"




