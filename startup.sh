#!/bin/bash
# Startup script for Azure Web App

# Install all dependencies from PyPI
pip install -r requirements.txt

# Copy query_analysis.xml to the installed package location
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
cp packages/core/nlweb_core/query_analysis/query_analysis.xml $SITE_PACKAGES/nlweb_core/query_analysis/

# Start the NLWeb server
python -m nlweb_network.server
