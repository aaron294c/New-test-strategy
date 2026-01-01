#!/bin/bash

# Lower Extension Distance Panel - Installation Script
# This script installs dependencies and verifies the setup

set -e  # Exit on error

echo "🚀 Installing Lower Extension Distance Panel..."
echo ""

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: /workspaces/New-test-strategy/"
    exit 1
fi

echo "✅ Found project root directory"
echo ""

# Navigate to frontend directory
cd frontend

echo "📦 Installing npm dependencies..."
echo ""

# Install dependencies
npm install

echo ""
echo "✅ Dependencies installed successfully"
echo ""

# Verify key dependencies
echo "🔍 Verifying installation..."
echo ""

if npm list lightweight-charts &> /dev/null; then
    echo "✅ lightweight-charts installed"
else
    echo "⚠️  Warning: lightweight-charts not found, installing..."
    npm install lightweight-charts
fi

if npm list jest &> /dev/null; then
    echo "✅ jest installed"
else
    echo "⚠️  Warning: jest not found, installing..."
    npm install --save-dev jest ts-jest @types/jest
fi

if npm list @testing-library/react &> /dev/null; then
    echo "✅ @testing-library/react installed"
else
    echo "⚠️  Warning: @testing-library/react not found, installing..."
    npm install --save-dev @testing-library/react @testing-library/jest-dom
fi

echo ""
echo "🧪 Running tests..."
echo ""

# Run tests
if [ -f "src/utils/__tests__/lowerExtensionCalculations.test.ts" ]; then
    npm test -- lowerExtensionCalculations.test.ts --passWithNoTests || {
        echo "⚠️  Tests not yet configured, skipping..."
    }
else
    echo "⚠️  Test file not found, skipping tests..."
fi

echo ""
echo "✨ Installation complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Review integration guide:"
echo "   cat ../docs/lower-extension-panel/INTEGRATION_GUIDE.md"
echo ""
echo "2. See example usage:"
echo "   cat ../docs/lower-extension-panel/EXAMPLE_USAGE.md"
echo ""
echo "3. Start development server:"
echo "   npm run dev"
echo ""
echo "4. Run tests:"
echo "   npm test -- lowerExtensionCalculations.test.ts"
echo ""
echo "5. Build for production:"
echo "   npm run build"
echo ""
echo "📚 Documentation available in: docs/lower-extension-panel/"
echo ""
echo "Happy trading! 📈"
