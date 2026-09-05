# Transfile

Transfile is a small, dependency-free file sharing server for transferring files between a computer and devices on the same local network. It provides a mobile-friendly web interface for downloading files from the computer and uploading files from a phone or tablet.

## Requirements

- Python 3.8 or newer
- A computer and the device you want to transfer files to on the same Wi-Fi or local network

No third-party Python packages are required.

## Quick start

Start the server with:

```bash
./lau.sh
```

If the script is not executable, run:

```bash
bash lau.sh
```

Alternatively, start the server directly:

```bash
python3 app.py
```

The server creates and shares the following directories automatically:

- `~/Shared` — files available to download
- `~/Shared/uploads` — files uploaded from another device

When the server starts, it prints one or more local network addresses. Open one of these URLs on the other device, for example:

```text
http://192.168.1.100:8000
```

The default port is `8000`. Stop the server with `Ctrl+C`.

## Using the web interface

1. Put files you want to share in `~/Shared`.
2. Open the displayed server URL on the device receiving the files.
3. Select a listed file to download it.
4. Use the upload form to send files to the computer. Uploaded files appear in `~/Shared/uploads`.

Duplicate upload names are preserved by adding a numeric suffix, such as `photo_1.jpg`.

## Launcher page

`index.html` is a standalone launcher page that stores a server IP address in the browser and opens the server on port `8000`. It can be opened directly in a browser when you want a reusable shortcut to a known server address.

## Configuration

The server settings are defined near the top of `app.py`:

```python
PORT = 8000
DIRECTORY = Path.home() / "Shared"
```

Change these values before starting the server if you need a different port or sharing directory.

## Network and security notes

Transfile is intended for trusted local networks. The server listens on all network interfaces and does not provide authentication or encryption. Anyone who can reach the server address may be able to view shared files or upload files, so avoid exposing port `8000` to the public internet and stop the server when it is no longer needed.

Depending on your operating system, you may need to allow Python through the firewall for devices on your local network.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Threaded HTTP server, directory listing, downloads, and multipart uploads |
| `lau.sh` | Creates the sharing directory and starts the server |
| `index.html` | Optional browser-based launcher for a saved server IP |

