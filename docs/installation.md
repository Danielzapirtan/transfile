Installing transfile as a pseudo-native CLI

Recommended (isolated, cross-platform): pipx

  python3 -m pip install --user pipx
  python3 -m pipx ensurepath
  pipx install .

This installs a `transfile` command in the user's PATH.

Alternative: pip

  python3 -m pip install --user .

System integration examples

- systemd (Linux, user service)

Create ~/.config/systemd/user/transfile.service:

[Unit]
Description=Transfile HTTP server (user)
After=network-online.target

[Service]
Type=simple
ExecStart=%h/.local/bin/transfile --directory /path/to/serve --enable-upload
Restart=on-failure

[Install]
WantedBy=default.target

Enable and start:

  systemctl --user enable --now transfile

- Desktop shortcut (.desktop) (Linux/GNOME)

Create ~/.local/share/applications/transfile.desktop:

[Desktop Entry]
Name=Transfile
Comment=Run Transfile HTTP server
Exec=transfile --directory /path/to/serve --enable-upload
Terminal=false
Type=Application
Categories=Utility;

- LaunchAgent (macOS user)

Create ~/Library/LaunchAgents/com.example.transfile.plist with appropriate ExecProgram pointing to the transfile executable and load with:

  launchctl load ~/Library/LaunchAgents/com.example.transfile.plist

Notes

- Using pipx provides best isolation and creates a native-feeling CLI on macOS and Linux.
- For GUI shortcuts, adapt the Exec line to include the full path to transfile if needed.
- Keep firewall and hotspot notes from docs/transfile_server.md in mind.
