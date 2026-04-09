#!/bin/bash
# Post-build script: injects PWA assets into the Expo web export.
# Run after: npx expo export --platform web
# Works on both macOS and Linux (Render).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$SCRIPT_DIR/../dist"
WEB_DIR="$SCRIPT_DIR/../web"
ASSETS_DIR="$SCRIPT_DIR/../assets"

echo "==> Injecting PWA assets into dist/"

# 1. Copy service worker, offline page, and registration script
cp "$WEB_DIR/service-worker.js" "$DIST_DIR/service-worker.js"
cp "$WEB_DIR/offline.html" "$DIST_DIR/offline.html"
cp "$WEB_DIR/register-sw.js" "$DIST_DIR/register-sw.js"

# 2. Copy PWA icons
cp "$ASSETS_DIR/icon-192.png" "$DIST_DIR/icon-192.png"
cp "$ASSETS_DIR/icon-512.png" "$DIST_DIR/icon-512.png"

# 3. Generate manifest.json
cat > "$DIST_DIR/manifest.json" << 'MANIFEST'
{
  "name": "Nowhere",
  "short_name": "Nowhere",
  "description": "Find spontaneous local gatherings. Ephemeral. Anonymous. 24 hours.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#111827",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
MANIFEST

# 4. Inject manifest link + SW registration into index.html
# Use Node.js (guaranteed available on Render static site builds)
node -e "
const fs = require('fs');
const p = '$DIST_DIR/index.html';
let html = fs.readFileSync(p, 'utf8');
html = html.replace('</head>', '<link rel=\"manifest\" href=\"/manifest.json\" />\\n<link rel=\"apple-touch-icon\" href=\"/icon-192.png\" />\\n<meta name=\"apple-mobile-web-app-capable\" content=\"yes\" />\\n<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"default\" />\\n</head>');
html = html.replace('</body>', '<script src=\"/register-sw.js\" defer></script>\\n</body>');
fs.writeFileSync(p, html);
console.log('==> index.html injected successfully');
"

echo "==> PWA injection complete."
ls -la "$DIST_DIR"
