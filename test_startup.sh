#!/bin/bash
# Test the exact startup command that runs on Azure

set -e

echo "Testing Azure startup command..."
echo ""

# Use the test virtual environment we created
source /tmp/nlweb_test_env/bin/activate

# Set up environment (Azure does this automatically)
export NLWEB_CONFIG_DIR=/Users/rvguha/code/NLWeb_Core

# Source environment variables (Azure has these configured in app settings)
source set_keys.sh

echo "Environment configured:"
echo "  NLWEB_CONFIG_DIR: $NLWEB_CONFIG_DIR"
echo "  Python: $(which python)"
echo "  Gunicorn: $(which gunicorn)"
echo ""
echo "Starting gunicorn..."
echo ""

# Run the EXACT command from startup.sh
gunicorn nlweb_core.simple_server:create_app \
  --bind=0.0.0.0:${PORT:-8000} \
  --worker-class aiohttp.GunicornWebWorker \
  --workers 1 \
  --timeout 600 \
  --access-logfile - \
  --error-logfile -
