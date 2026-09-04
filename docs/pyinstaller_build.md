Building standalone executables with PyInstaller (CI + local)

This project includes a GitHub Actions workflow (.github/workflows/pyinstaller-build.yml)
that builds single-file executables for Linux and macOS when changes are pushed to the
feature branch (danielzapirtan-transfer-fisiere-ip). Artifacts are attached to the workflow run.

Local build (Linux/macOS)

  ./scripts/pyinstaller_build.sh

Options:
  --name <name>        Set executable name (default: transfile)
  --no-onefile         Build directory style instead of single file
  --entry <script>     Use a different entry script

Notes

- CI builds run on GitHub-hosted runners (ubuntu-latest and macos-latest). macOS artifacts require the macos runner and cannot be cross-built from Linux.
- For distribution on macOS, notarization/signing may be required to avoid Gatekeeper warnings; that is not automated here.
- To produce Windows binaries, add a windows job using windows-latest in the workflow (PyInstaller on Windows produces .exe).
