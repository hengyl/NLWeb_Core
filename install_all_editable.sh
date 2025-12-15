#!/bin/bash
# Script to install all NLWeb packages in editable mode for local testing

set -e  # Exit on error

PACKAGES_DIR="$(cd "$(dirname "$0")/packages" && pwd)"

echo "============================================"
echo "Installing NLWeb packages in editable mode"
echo "============================================"
echo ""

# Install core first (required by all others)
echo "1/6 Installing nlweb-core..."
cd "$PACKAGES_DIR/core"
pip install -e . --config-settings editable_mode=compat
echo "    ✓ nlweb-core installed"
echo ""

# Install bundles
echo "2/6 Installing nlweb-retrieval..."
cd "$PACKAGES_DIR/bundles/retrieval"
pip install -e . --config-settings editable_mode=compat
echo "    ✓ nlweb-retrieval installed"
echo ""

echo "3/6 Installing nlweb-models..."
cd "$PACKAGES_DIR/bundles/models"
pip install -e . --config-settings editable_mode=compat
echo "    ✓ nlweb-models installed"
echo ""

# Install Azure packages
echo "4/6 Installing nlweb-azure-vectordb..."
cd "$PACKAGES_DIR/providers/azure/vectordb"
pip install -e . --config-settings editable_mode=compat
echo "    ✓ nlweb-azure-vectordb installed"
echo ""

echo "5/6 Installing nlweb-azure-models..."
cd "$PACKAGES_DIR/providers/azure/models"
pip install -e . --config-settings editable_mode=compat
echo "    ✓ nlweb-azure-models installed"
echo ""

echo "6/6 Installing nlweb-network..."
cd "$PACKAGES_DIR/network"
pip install -e . --config-settings editable_mode=compat
echo "    ✓ nlweb-network installed"
echo ""



echo "============================================"
echo "✓ All packages installed successfully!"
echo "============================================"
echo ""
echo "Installed packages:"
pip list | grep nlweb
echo ""
echo "To test: cd examples/azure_hello_world && python hello_world.py"
