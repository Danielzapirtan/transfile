#!/bin/bash
# Quick wireless share script

DIR=$HOME/Shared
PORT=8000
IP=$(hostname -I | awk '{print $1}')

mkdir -p $DIR
echo "📁 Sharing: $DIR"
echo "📱 On Android, open: http://$IP:$PORT"
echo ""
echo "To upload FROM Android:"
echo "  Use the upload button on the webpage"
echo ""
echo "Press Ctrl+C to stop"

# Run the enhanced server
python3 app.py
