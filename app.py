#!/usr/bin/env python3
"""
wireless_share.py - Two-way file sharing between Linux/Mac and Android
No cables needed! Works over WiFi or hotspot.
"""

import http.server
import socketserver
import os
import cgi
import json
import subprocess
import socket
from pathlib import Path
from datetime import datetime
import urllib.parse

PORT = 8000
DIRECTORY = os.getcwd()
UPLOAD_DIR = os.path.join(DIRECTORY, "uploads")  # Files from Android go here

# Create upload directory
Path(UPLOAD_DIR).mkdir(exist_ok=True)

class FileShareHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        """Handle GET requests - file downloads and directory listing"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.generate_html().encode())
        else:
            # Serve files normally
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests - file uploads from Android"""
        content_type = self.headers.get('Content-Type', '')
        
        if 'multipart/form-data' in content_type:
            try:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                if 'file' in form:
                    file_item = form['file']
                    if file_item.filename:
                        # Sanitize filename
                        filename = os.path.basename(file_item.filename)
                        filepath = os.path.join(UPLOAD_DIR, filename)
                        
                        # Handle duplicate filenames
                        counter = 1
                        name, ext = os.path.splitext(filename)
                        while os.path.exists(filepath):
                            filepath = os.path.join(UPLOAD_DIR, f"{name}_{counter}{ext}")
                            counter += 1
                        
                        # Save file
                        with open(filepath, 'wb') as f:
                            f.write(file_item.file.read())
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        response = json.dumps({
                            'success': True,
                            'filename': os.path.basename(filepath),
                            'size': os.path.getsize(filepath)
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
    
    def do_PUT(self):
        """Handle PUT requests for large file uploads (alternative to POST)"""
        try:
            # Get filename from URL
            filename = os.path.basename(urllib.parse.unquote(self.path))
            if not filename:
                filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            # Get file size
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Save file in chunks (for large files)
            with open(filepath, 'wb') as f:
                remaining = content_length
                while remaining > 0:
                    chunk = self.rfile.read(min(8192, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'filename': filename,
                'size': content_length
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
    
    def generate_html(self):
        """Generate a beautiful, mobile-friendly interface"""
        files = []
        for item in sorted(Path(DIRECTORY).iterdir(), key=lambda x: x.name.lower()):
            if item.is_file() and item.name != 'wireless_share.py':
                files.append({
                    'name': item.name,
                    'size': self.format_size(item.stat().st_size),
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'url': f'/{item.name}'
                })
        
        # Also list uploads
        uploads = []
        for item in sorted(Path(UPLOAD_DIR).iterdir(), key=lambda x: x.name.lower()):
            if item.is_file():
                uploads.append({
                    'name': item.name,
                    'size': self.format_size(item.stat().st_size),
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'url': f'/uploads/{item.name}'
                })
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📁 Wireless File Share</title>
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
                h1 {{
                    color: #333;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    color: #666;
                    margin-bottom: 30px;
                }}
                .upload-section {{
                    background: #f8f9fa;
                    border: 2px dashed #ddd;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                    transition: all 0.3s;
                }}
                .upload-section:hover {{
                    border-color: #764ba2;
                    background: #f0e6ff;
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
                .file-list {{
                    margin-top: 20px;
                }}
                .file-section {{
                    margin-bottom: 30px;
                }}
                .file-section h2 {{
                    color: #555;
                    margin-bottom: 10px;
                    font-size: 1.2em;
                }}
                .file-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    transition: transform 0.2s;
                }}
                .file-item:hover {{
                    transform: translateX(5px);
                    background: #e9ecef;
                }}
                .file-name {{
                    flex: 1;
                    color: #333;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .file-info {{
                    color: #999;
                    font-size: 0.9em;
                    margin-left: 20px;
                }}
                .file-size {{
                    color: #764ba2;
                    font-weight: bold;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 10px;
                    background: #f0f0f0;
                    border-radius: 5px;
                    overflow: hidden;
                    margin-top: 10px;
                    display: none;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    transition: width 0.3s;
                }}
                @media (max-width: 600px) {{
                    .file-item {{
                        flex-direction: column;
                        align-items: flex-start;
                    }}
                    .file-info {{
                        margin-left: 0;
                        margin-top: 5px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 Wireless File Share</h1>
                <p class="subtitle">Transfer files between devices without cables</p>
                
                <div class="upload-section">
                    <h2>📤 Upload to Computer</h2>
                    <p>Select files from your device to upload</p>
                    <form id="upload-form" enctype="multipart/form-data">
                        <input type="file" id="file-input" name="file" multiple style="display:none;">
                        <button type="button" class="upload-btn" onclick="document.getElementById('file-input').click()">
                            Choose Files
                        </button>
                    </form>
                    <div class="progress-bar" id="upload-progress">
                        <div class="progress-fill" id="upload-progress-fill"></div>
                    </div>
                    <div id="upload-status"></div>
                </div>
                
                <div class="file-section">
                    <h2>📥 Files on Computer (Click to Download)</h2>
                    <div class="file-list">
        """
        
        for file in files:
            html += f"""
                        <div class="file-item">
                            <a href="{file['url']}" class="file-name" download>📄 {file['name']}</a>
                            <span class="file-info">
                                <span class="file-size">{file['size']}</span> | {file['modified']}
                            </span>
                        </div>
            """
        
        if uploads:
            html += """
                    </div>
                </div>
                
                <div class="file-section">
                    <h2>📤 Uploaded from Device</h2>
                    <div class="file-list">
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
            </div>
            
            <script>
                const fileInput = document.getElementById('file-input');
                const uploadForm = document.getElementById('upload-form');
                const progressBar = document.getElementById('upload-progress');
                const progressFill = document.getElementById('upload-progress-fill');
                const uploadStatus = document.getElementById('upload-status');
                
                fileInput.addEventListener('change', async () => {
                    const files = fileInput.files;
                    if (files.length === 0) return;
                    
                    const formData = new FormData();
                    for (let i = 0; i < files.length; i++) {
                        formData.append('file', files[i]);
                    }
                    
                    progressBar.style.display = 'block';
                    uploadStatus.innerHTML = 'Uploading...';
                    
                    try {
                        const response = await fetch('/', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            uploadStatus.innerHTML = `✅ Uploaded: ${result.filename} (${formatSize(result.size)})`;
                            setTimeout(() => location.reload(), 2000);
                        } else {
                            uploadStatus.innerHTML = '❌ Upload failed';
                        }
                    } catch (error) {
                        uploadStatus.innerHTML = '❌ Upload failed: ' + error.message;
                    }
                    
                    progressBar.style.display = 'none';
                    progressFill.style.width = '0%';
                });
                
                function formatSize(bytes) {
                    const units = ['B', 'KB', 'MB', 'GB'];
                    let size = bytes;
                    let unit = 0;
                    while (size >= 1024 && unit < units.length - 1) {
                        size /= 1024;
                        unit++;
                    }
                    return `${size.toFixed(1)} ${units[unit]}`;
                }
            </script>
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
    """Get all IP addresses"""
    ips = []
    try:
        # Try using ip command (Linux)
        result = subprocess.run(['ip', '-4', 'addr', 'show'], 
                              capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line:
                ip = line.strip().split()[1].split('/')[0]
                if not ip.startswith('169.254'):
                    ips.append(ip)
    except:
        pass
    
    if not ips:
        # Fallback to socket method
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ips.append(s.getsockname()[0])
            s.close()
        except:
            ips.append('127.0.0.1')
    
    return ips

def main():
    print("""
    ╔══════════════════════════════════════════╗
    ║     📁 Wireless File Share Server        ║
    ╚══════════════════════════════════════════╝
    """)
    
    print(f"📂 Sharing directory: {DIRECTORY}")
    print(f"📤 Upload directory: {UPLOAD_DIR}")
    print(f"🔌 Port: {PORT}")
    print("\n📱 Access from your Android device:\n")
    
    ips = get_ip_addresses()
    for ip in ips:
        print(f"   http://{ip}:{PORT}")
    
    print("\n✨ Features:")
    print("   • Download files from computer")
    print("   • Upload files from Android")
    print("   • No file size limits (practical)")
    print("   • Multiple files at once")
    print("\nPress Ctrl+C to stop\n")
    
    server = ThreadedHTTPServer(("0.0.0.0", PORT), FileShareHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()
