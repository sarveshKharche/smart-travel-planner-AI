#!/bin/bash
# Build script for Smart Travel Planner AI

set -e

echo "🚀 Building Smart Travel Planner AI..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -f *.zip

# Create build directory
mkdir -p build/lambda

# Copy source code
echo "📁 Copying source code..."
cp -r src/* build/lambda/
cp lambda_function.py build/lambda/

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -t build/lambda/ --quiet

# Create deployment package
echo "📦 Creating deployment package..."
cd build/lambda
zip -r ../../lambda_deployment.zip . -q
cd ../..

echo "✅ Build complete! Package: lambda_deployment.zip"
echo "📊 Package size: $(du -h lambda_deployment.zip | cut -f1)"
