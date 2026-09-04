#!/bin/bash
# Quick wireless share script

PORT=8000
DIR=${1:-$(pwd)}

cd "$DIR"
IP=$(hostname -I | awk '{print $1}')

echo "📁 Sharing: $HOME/Share"
echo "📱 On Android, open: http://$IP:$PORT"
echo ""
echo "To upload FROM Android:"
echo "  Use the upload button on the webpage"
echo ""
echo "Press Ctrl+C to stop"

# Run the enhanced server
python3 app.py
