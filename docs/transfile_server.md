Transfile minimal HTTP server (Python)

Overview

This small script provides an optional HTTP server for simple file transfers over a LAN (e.g., phone hotspot). It keeps backward compatibility (stdlib only) and provides:

- GET downloads using standard paths (curl http://PHONE_IP:8080/file -O)
- Optional POST uploads at /upload (curl -F "file=@local" http://PHONE_IP:8080/upload)
- Optional basic auth: --auth user:pass
- Optional TLS: --tls-cert cert.pem --tls-key key.pem

Quick examples

Start server (serve current directory, allow uploads):

  ./scripts/transfile_server.py --bind 0.0.0.0 --port 8080 --enable-upload

Download from laptop (phone hotspot IP example 192.168.43.1):

  curl http://192.168.43.1:8080/somefile -O

Upload to phone:

  curl -F "file=@myfile" http://192.168.43.1:8080/upload

If basic auth is enabled on the server (example user:pass):

  curl -u user:pass -F "file=@myfile" http://192.168.43.1:8080/upload

Notes

- Typical phone hotspot IP ranges vary by vendor; common Android hotspot gateway is 192.168.43.1. Verify with ifconfig/ipconfig on each device.
- Ensure the phone's hotspot allows client-to-client connections or that the receiving device listens on the hotspot network.
- Firewall: allow the chosen port (default 8080) on the receiving device.
- For stronger security in production, use TLS and strong credentials or use a more featureful tool.
