#!/bin/bash
# Railway Streamlit Startup Script

# Start Streamlit on Railway's PORT
streamlit run streamlit_app_auth.py \
  --server.port=$PORT \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
