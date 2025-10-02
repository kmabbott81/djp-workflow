"""PWA helper functions for mobile support and offline mode."""

import os
from pathlib import Path


def get_pwa_html_head() -> str:
    """
    Generate HTML head tags for PWA support.

    Returns HTML string with manifest link, meta tags, and service worker registration.
    """
    # Feature flag
    if not os.getenv("FEATURE_PWA_OFFLINE", "true").lower() == "true":
        return ""

    pwa_html = """
    <!-- PWA Manifest -->
    <link rel="manifest" href="/pwa/manifest.json">

    <!-- iOS Meta Tags -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="DJP Workflows">
    <link rel="apple-touch-icon" href="/pwa/icons/icon-192x192.png">

    <!-- Android Meta Tags -->
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#4A90E2">

    <!-- Splash Screens (iOS) -->
    <link rel="apple-touch-startup-image" href="/pwa/splash/splash-2048x2732.png" media="(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2)">
    <link rel="apple-touch-startup-image" href="/pwa/splash/splash-1668x2388.png" media="(device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2)">
    <link rel="apple-touch-startup-image" href="/pwa/splash/splash-1536x2048.png" media="(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2)">
    <link rel="apple-touch-startup-image" href="/pwa/splash/splash-1242x2688.png" media="(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3)">
    <link rel="apple-touch-startup-image" href="/pwa/splash/splash-1125x2436.png" media="(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3)">
    <link rel="apple-touch-startup-image" href="/pwa/splash/splash-750x1334.png" media="(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)">

    <!-- Service Worker Registration -->
    <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/pwa/service_worker.js')
          .then(function(registration) {
            console.log('[PWA] Service Worker registered:', registration.scope);
          })
          .catch(function(error) {
            console.log('[PWA] Service Worker registration failed:', error);
          });
      });
    }
    </script>

    <!-- PWA Install Prompt -->
    <script>
    let deferredPrompt;

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;

      // Show install button or banner
      const installBanner = document.getElementById('pwa-install-banner');
      if (installBanner) {
        installBanner.style.display = 'block';
      }
    });

    function installPWA() {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('[PWA] User accepted install');
          } else {
            console.log('[PWA] User dismissed install');
          }
          deferredPrompt = null;
        });
      }
    }

    window.addEventListener('appinstalled', (evt) => {
      console.log('[PWA] App installed');
      const installBanner = document.getElementById('pwa-install-banner');
      if (installBanner) {
        installBanner.style.display = 'none';
      }
    });
    </script>
    """

    return pwa_html


def render_pwa_install_banner() -> str:
    """Generate HTML for PWA install banner."""
    if not os.getenv("FEATURE_PWA_OFFLINE", "true").lower() == "true":
        return ""

    banner_html = """
    <div id="pwa-install-banner" style="display:none; position: fixed; bottom: 0; left: 0; right: 0;
         background: #4A90E2; color: white; padding: 16px; text-align: center; z-index: 9999;">
      <p style="margin: 0 0 8px 0; font-weight: 500;">Install DJP Workflows for offline access</p>
      <button onclick="installPWA()" style="background: white; color: #4A90E2; border: none;
              padding: 8px 16px; border-radius: 4px; font-weight: 500; cursor: pointer;">
        Install App
      </button>
      <button onclick="document.getElementById('pwa-install-banner').style.display='none'"
              style="background: transparent; color: white; border: 1px solid white;
              padding: 8px 16px; border-radius: 4px; margin-left: 8px; cursor: pointer;">
        Maybe Later
      </button>
    </div>
    """

    return banner_html


def is_offline_mode() -> bool:
    """Check if app is running in offline mode (via service worker)."""
    # This would need to be checked via JavaScript in the browser
    # For server-side, we can check feature flag
    return os.getenv("FEATURE_PWA_OFFLINE", "true").lower() == "true"


def get_cached_artifacts_path() -> Path:
    """Get path to cached artifacts for offline viewing."""
    cache_dir = Path(os.getenv("PWA_CACHE_DIR", "data/pwa_cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
