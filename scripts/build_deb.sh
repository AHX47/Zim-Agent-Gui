#!/usr/bin/env bash
# =============================================================
# build_deb.sh  –  Build ZimAgent Desktop .deb package (Linux)
# Requirements: dpkg-deb, fakeroot  (sudo apt install fakeroot)
# =============================================================

set -euo pipefail

APP_NAME="zimagent"
VERSION="1.0.0"
ARCH="amd64"
DEB_DIR="${APP_NAME}_${VERSION}_${ARCH}"

echo "[ZimAgent] Building .deb package…"

# ── 1. Freeze application ──────────────────────────────────
pip install pyinstaller --quiet
pyinstaller \
    --onefile \
    --windowed \
    --name "zimagent" \
    --add-data "zimagent/resources:zimagent/resources" \
    --add-data "models:models" \
    --hidden-import "PyQt5.QtWebEngineWidgets" \
    --hidden-import "psutil" \
    run_app.py

# ── 2. Create .deb directory structure ────────────────────
rm -rf "${DEB_DIR}"
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/pixmaps"

# Copy binary
cp dist/zimagent "${DEB_DIR}/usr/bin/zimagent"
chmod +x "${DEB_DIR}/usr/bin/zimagent"

# .desktop entry
cat > "${DEB_DIR}/usr/share/applications/zimagent.desktop" <<EOF
[Desktop Entry]
Name=ZimAgent Desktop
Comment=Offline CRUD + Semantic Search for Wikipedia ZIM archives
Exec=/usr/bin/zimagent
Icon=zimagent
Terminal=false
Type=Application
Categories=Education;Science;
Keywords=wikipedia;offline;zim;search;ai;
EOF

# Control file
cat > "${DEB_DIR}/DEBIAN/control" <<EOF
Package: zimagent
Version: ${VERSION}
Section: education
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.9), python3-pyqt5, python3-psutil
Maintainer: ZimAgent <hello@zimagent.local>
Description: ZimAgent Desktop
 Offline CRUD + semantic search desktop application
 for Wikipedia ZIM archives. Supports TurboRag RAG
 engine, local LLM inference, and MCP server.
EOF

# Post-install script
cat > "${DEB_DIR}/DEBIAN/postinst" <<'EOF'
#!/bin/sh
update-desktop-database /usr/share/applications || true
EOF
chmod 755 "${DEB_DIR}/DEBIAN/postinst"

# ── 3. Build the .deb ──────────────────────────────────────
fakeroot dpkg-deb --build "${DEB_DIR}"

echo ""
echo "✅  Built: ${DEB_DIR}.deb"
echo ""
echo "Install with:"
echo "  sudo dpkg -i ${DEB_DIR}.deb"
echo "  sudo apt-get install -f   # fix any missing deps"
