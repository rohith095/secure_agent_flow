#!/bin/bash

# Script to build Lambda dependencies layer for secure agent flow using uv

set -e

echo "🔧 Building Lambda dependencies layer with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create a temporary directory for building the layer
TEMP_DIR=$(mktemp -d)
LAYER_DIR="$TEMP_DIR/python"

echo "📁 Creating layer structure in $TEMP_DIR"
mkdir -p "$LAYER_DIR"

# Create a temporary requirements file for Lambda dependencies
TEMP_REQUIREMENTS="$TEMP_DIR/lambda_requirements.txt"
cat > "$TEMP_REQUIREMENTS" << EOF
crewai>=0.186.1
crewai-tools>=0.1.0
python-dotenv>=1.0.0
pydantic>=2.0.0
boto3>=1.34.0
botocore>=1.34.0
requests>=2.31.0
PyYAML>=6.0
langchain>=0.1.0
langchain-openai>=0.1.0
EOF

# Install dependencies using uv
echo "📦 Installing Python dependencies with uv..."
uv pip install --target "$LAYER_DIR" --requirement "$TEMP_REQUIREMENTS" --python python3.11

# Create the zip file
echo "🗜️ Creating dependencies.zip..."
cd "$TEMP_DIR"
zip -r9 "${OLDPWD}/dependencies.zip" python/

# Clean up
echo "🧹 Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "✅ Dependencies layer created successfully: dependencies.zip"
echo "📏 Layer size: $(du -h dependencies.zip | cut -f1)"

# Verify the layer contents
echo "📋 Layer contents preview:"
unzip -l dependencies.zip | head -20
