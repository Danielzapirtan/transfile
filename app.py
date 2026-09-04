#!/usr/bin/env python3
"""
universal_share.py - Cross-version file sharing server
Works on Python 3.8+ (including 3.12 and 3.13)
No deprecated modules, no external dependencies
"""

import http.server
import socketserver
import os
import json
import subprocess
import socket
import re
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime

PORT = 8000
DIRECTORY = Path.home() / "Shared"
#DIRECTORY = os.getcwd()
UPLOAD_DIR = os.path.join(DIRECTORY, "uploads")

# Create upload directory
Path(UPLOAD_DIR).mkdir(exist_ok=True)

class FileShareHandler(http.server.SimpleHTTPRequestHandler):
    """Modern file share handler - no cgi, no deprecated modules"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_POST(self):
        """Handle POST requests - file uploads (works on any Python 3.8+)"""
        content_type = self.headers.get('Content-Type', '')
        
        if 'multipart/form-data' in content_type:
            try:
                # Parse multipart form data using our own parser
                files = self.parse_multipart(content_type)
                
                if files:
                    results = []
                    for filename, file_data in files.items():
                        safe_filename = os.path.basename(filename)
                        filepath = os.path.join(UPLOAD_DIR, safe_filename)
                        
                        # Handle duplicate filenames
                        counter = 1
                        name, ext = os.path.splitext(safe_filename)
                        while os.path.exists(filepath):
                            filepath = os.path.join(UPLOAD_DIR, f"{name}_{counter}{ext}")
                            counter += 1
                        
                        # Save file
                        with open(filepath, 'wb') as f:
                            f.write(file_data)
                        
                        results.append({
                            'filename': os.path.basename(filepath),
                            'size': len(file_data)
                        })
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = json.dumps({
                        'success': True,
                        'files': results
                    })
                    self.wfile.write(response.encode())
                    return
                
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No file uploaded'}).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid content type'}).encode())
    
    def parse_multipart(self, content_type):
        """Parse multipart form data without cgi module"""
        # Extract boundary
        boundary_match = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type)
        if not boundary_match:
            return {}
        
        boundary = boundary_match.group(1) or boundary_match.group(2)
        boundary = boundary.strip()
        
        # Read the body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Parse multipart data
        files = {}
        delimiter = f'--{boundary}'.encode()
        
        # Split by boundary
        parts = body.split(delimiter)
        
        for part in parts:
            if not part or part in (b'--\r\n', b'--', b'\r\n'):
                continue
            
            # Remove leading/trailing CRLF
            if part.startswith(b'\r\n'):
                part = part[2:]
            if part.endswith(b'\r\n'):
                part = part[:-2]
            
            # Split headers from content
            if b'\r\n\r\n' in part:
                headers_part, content = part.split(b'\r\n\r\n', 1)
                
                # Parse headers
                headers_text = headers_part.decode('utf-8', errors='ignore')
                
                # Extract filename from Content-Disposition
                filename_match = re.search(r'filename="([^"]+)"', headers_text)
                if filename_match:
                    filename = filename_match.group(1)
                    files[filename] = content
        
        return files
    
    def do_GET(self):
        """Handle GET requests - file downloads and directory listing"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.generate_html().encode())
        else:
            # Serve files normally
            super().do_GET()
    
    def generate_html(self):
        """Generate a beautiful, mobile-friendly interface"""
        files = []
        for item in sorted(Path(DIRECTORY).iterdir(), key=lambda x: x.name.lower()):
            if item.is_file() and not item.name.endswith('.py'):
                files.append({
                    'name': item.name,
                    'size': self.format_size(item.stat().st_size),
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'url': f'/{urllib.parse.quote(item.name)}'
                })
        
        # Also list uploads
        uploads = []
        for item in sorted(Path(UPLOAD_DIR).iterdir(), key=lambda x: x.name.lower()):
            if item.is_file():
                uploads.append({
                    'name': item.name,
                    'size': self.format_size(item.stat().st_size),
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'url': f'/uploads/{urllib.parse.quote(item.name)}'
                })
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📁 File Share</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }}
                h1 {{ color: #333; margin-bottom: 10px; }}
                .subtitle {{ color: #666; margin-bottom: 30px; }}
                .upload-section {{
                    background: #f8f9fa;
                    border: 2px dashed #ddd;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .upload-btn {{
                    display: inline-block;
                    padding: 15px 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 50px;
                    font-size: 18px;
                    cursor: pointer;
                    border: none;
                    margin-top: 10px;
                }}
                .file-section {{ margin-bottom: 30px; }}
                .file-section h2 {{ color: #555; margin-bottom: 10px; }}
                .file-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    margin-bottom: 10px;
                }}
                .file-name {{
                    flex: 1;
                    color: #333;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .file-info {{ color: #999; font-size: 0.9em; }}
                .file-size {{ color: #764ba2; font-weight: bold; }}
                @media (max-width: 600px) {{
                    .file-item {{ flex-direction: column; align-items: flex-start; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 File Share</h1>
                <p class="subtitle">Transfer files between devices</p>
                
                <div class="upload-section">
                    <h2>📤 Upload to Computer</h2>
                    <form method="POST" enctype="multipart/form-data">
                        <input type="file" name="file" multiple style="margin: 20px 0;">
                        <br>
                        <button type="submit" class="upload-btn">Upload Files</button>
                    </form>
                </div>
                
                <div class="file-section">
                    <h2>📥 Files on Computer</h2>
        """
        
        if files:
            for file in files:
                html += f"""
                    <div class="file-item">
                        <a href="{file['url']}" class="file-name" download>📄 {file['name']}</a>
                        <span class="file-info">
                            <span class="file-size">{file['size']}</span> | {file['modified']}
                        </span>
                    </div>
                """
        else:
            html += "<p>No files to share</p>"
        
        if uploads:
            html += """
                </div>
                <div class="file-section">
                    <h2>📤 Uploaded from Device</h2>
            """
            for file in uploads:
                html += f"""
                    <div class="file-item">
                        <a href="{file['url']}" class="file-name" download>📄 {file['name']}</a>
                        <span class="file-info">
                            <span class="file-size">{file['size']}</span> | {file['modified']}
                        </span>
                    </div>
                """
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def format_size(self, bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"
    
    def log_message(self, format, *args):
        """Custom log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {self.client_address[0]} - {format % args}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Handle multiple connections simultaneously"""
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128

def get_ip_addresses():
    """Get all IP addresses - works on both Linux and macOS"""
    ips = []
    
    # Try Linux method first
    try:
        result = subprocess.run(['ip', '-4', 'addr', 'show'], 
                              capture_output=True, text=True, timeout=3)
        for line in result.stdout.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line:
                ip = line.strip().split()[1].split('/')[0]
                if not ip.startswith('169.254'):
                    ips.append(ip)
    except:
        pass
    
    # Try macOS method
    if not ips:
        try:
            for interface in ['en0', 'en1', 'en2']:
                result = subprocess.run(['ipconfig', 'getifaddr', interface],
                                      capture_output=True, text=True, timeout=2)
                ip = result.stdout.strip()
                if ip and ip != '127.0.0.1':
                    ips.append(ip)
        except:
            pass
    
    # Fallback to socket method
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ips.append(s.getsockname()[0])
            s.close()
        except:
            ips.append('127.0.0.1')
    
    return ips

def main():
    python_version = sys.version.split()[0]
    
    print(f"""
    ╔══════════════════════════════════════════╗
    ║     📁 Universal File Share Server       ║
    ╚══════════════════════════════════════════╝
    
    Python Version: {python_version}
    OS: {os.uname().sysname if hasattr(os, 'uname') else sys.platform}
    
    📂 Sharing directory: {DIRECTORY}
    📤 Upload directory: {UPLOAD_DIR}
    🔌 Port: {PORT}
    
    📱 Access from your Android device:
    """)
    
    ips = get_ip_addresses()
    for ip in ips:
        print(f"   http://{ip}:{PORT}")
    
    print("""
    ✨ Features:
       • Two-way file transfer
       • No deprecated modules
       • Works on Python 3.8+
       • No external dependencies
    
    Press Ctrl+C to stop
    """)
    
    server = ThreadedHTTPServer(("0.0.0.0", PORT), FileShareHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()
