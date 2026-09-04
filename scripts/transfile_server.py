#!/usr/bin/env python3
"""Minimal HTTP file transfer server with optional upload, basic auth and TLS.

Usage examples:
  ./scripts/transfile_server.py --bind 0.0.0.0 --port 8080 --enable-upload
  curl http://PHONE_IP:8080/somefile -O
  curl -F "file=@localfile" http://PHONE_IP:8080/upload

This is intentionally dependency-free (stdlib only) for backward compatibility.
"""

import argparse
import base64
import http.server
import io
import os
import ssl
import sys
from http import HTTPStatus
import cgi

class TransferHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "Transfile/0.1"

    def do_POST(self):
        if not getattr(self.server, "enable_upload", False):
            self.send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Uploads disabled")
            return

        if self.path != "/upload":
            self.send_error(HTTPStatus.NOT_FOUND, "Only /upload is supported for POST")
            return

        if not self.check_auth():
            return

        content_type = self.headers.get("Content-Type")
        if not content_type:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing Content-Type")
            return

        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': content_type,
        }
        fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)
        field = fs['file'] if 'file' in fs else None
        if not field or not getattr(field, 'file', None):
            self.send_error(HTTPStatus.BAD_REQUEST, "No file field in form (use 'file')")
            return

        filename = os.path.basename(field.filename) if field.filename else 'upload'
        dest = os.path.join(self.server.directory, filename)
        try:
            with open(dest, 'wb') as out:
                data = field.file.read()
                out.write(data)
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to save: {e}")
            return

        self.send_response(HTTPStatus.CREATED)
        self.end_headers()
        self.wfile.write(f"Saved {filename}\n".encode('utf-8'))

    def check_auth(self):
        expected = getattr(self.server, 'auth', None)
        if not expected:
            return True
        auth = self.headers.get('Authorization')
        if not auth or not auth.startswith('Basic '):
            self.send_response(HTTPStatus.UNAUTHORIZED)
            self.send_header('WWW-Authenticate', 'Basic realm="Transfile"')
            self.end_headers()
            return False
        try:
            b64 = auth.split(' ', 1)[1].strip()
            decoded = base64.b64decode(b64).decode('utf-8')
        except Exception:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Invalid auth header')
            return False
        if decoded != expected:
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return False
        return True

    # For GET/HEAD, delegate to SimpleHTTPRequestHandler which uses self.server.directory


def run():
    parser = argparse.ArgumentParser(description='Minimal IP file transfer HTTP server (download + optional upload)')
    parser.add_argument('--bind', default='0.0.0.0', help='Bind address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen (default: 8080)')
    parser.add_argument('--directory', default='.', help='Directory to serve (default: current dir)')
    parser.add_argument('--enable-upload', action='store_true', help='Allow uploads via POST /upload')
    parser.add_argument('--auth', help='Enable basic auth in the form user:pass')
    parser.add_argument('--tls-cert', help='Path to TLS certificate (PEM)')
    parser.add_argument('--tls-key', help='Path to TLS key (PEM)')
    args = parser.parse_args()

    os.chdir(args.directory)

    handler = TransferHandler
    httpd = http.server.ThreadingHTTPServer((args.bind, args.port), handler)
    # attach simple attributes for handler access
    httpd.enable_upload = args.enable_upload
    httpd.auth = args.auth
    httpd.directory = os.path.abspath(args.directory)

    proto = 'http'
    if args.tls_cert and args.tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=args.tls_cert, keyfile=args.tls_key)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        proto = 'https'

    print(f"Serving {httpd.directory} on {proto}://{args.bind}:{args.port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down')
        httpd.server_close()


if __name__ == '__main__':
    run()
