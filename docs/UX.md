# User Experience Guide

World-class UX patterns for keyboard-first navigation, mobile support, and offline access.

## Command Palette (Ctrl/Cmd+K)

### Overview

The command palette provides keyboard-first access to all major actions without leaving the keyboard.

**Shortcut:** `Ctrl+K` (Windows/Linux) or `Cmd+K` (Mac)

### Features

- **Fuzzy search**: Type partial matches (e.g., "run temp" finds "Run Template")
- **Categorized actions**: Organized by Navigation, Actions, Search, Utilities
- **Keyboard shortcuts**: Each action displays its shortcut for direct access
- **Contextual actions**: Actions adapt based on current page and permissions

### Available Actions

#### Navigation
- `Ctrl+H`: Go to Home
- `Ctrl+1`: Go to Templates
- `Ctrl+2`: Go to Chat
- `Ctrl+3`: Go to Batch
- `Ctrl+4`: Go to Observability
- `Ctrl+5`: Go to Admin (admin only)

#### Actions
- `Ctrl+Enter`: Run Template
- `Ctrl+Shift+A`: Approve Artifact (editor/admin)
- `Ctrl+Shift+R`: Reject Artifact (editor/admin)
- `Ctrl+N`: Create Template (admin)
- `Ctrl+E`: Export Artifact
- `Ctrl+D`: Favorite/Unfavorite Template

#### Search
- `Ctrl+F`: Search Templates
- `Ctrl+O`: Open Artifact by ID

#### Utilities
- `Ctrl+Shift+T`: Toggle Theme (light/dark)
- `F1`: Show Help

### Custom Actions

Add custom actions to the palette:

```python
from dashboards.command_palette import register_custom_action

def my_custom_action(context):
    artifact_id = context.get("selected_artifact_id")
    # Do something with artifact
    print(f"Custom action on {artifact_id}")

register_custom_action(
    action_id="my_custom",
    label="My Custom Action",
    description="Does something custom",
    callback=my_custom_action,
    keyboard_shortcut="Ctrl+Shift+C",
    category="Custom",
    icon="⚡"
)
```

## Home Dashboard

**Feature Flag:** `FEATURE_HOME=true`

The Home tab provides a personalized dashboard with quick access to favorites, recent activity, and budget status.

### Dashboard Cards

#### Favorite Templates
- Displays top 5 favorited templates with quick Run buttons
- Click ⭐ icon on any template to add/remove from favorites
- Keyboard shortcut: `Ctrl+D` when template selected
- Favorites persist per user, per tenant

#### Recent Artifacts
- Shows last 10 artifacts with status (approved/pending/rejected)
- Displays cost estimate for each artifact
- Click "View" to open artifact details
- Filtered by current tenant

#### Recent Chats
- Shows last 10 chat sessions with timestamps
- Click "Resume" to continue chat
- Chat history isolated per tenant

#### Budget Usage
- Daily and monthly budget progress bars
- Warning indicator at 90% usage (⚠️ orange)
- Error indicator at 100% usage (⚠️ red)
- Real-time budget tracking with cost estimates

#### Quick Actions
- One-click navigation to major sections
- Browse Templates, New Chat, Batch Jobs, Observability
- Equivalent to keyboard shortcuts

### Multi-Tenant Support

Users with access to multiple tenants can:
- Switch tenant using dropdown selector (top-right)
- View tenant-specific favorites and recent activity
- Budget usage per tenant

### Privacy & Isolation

- User preferences are isolated per tenant
- Viewers can read own preferences (read-only)
- Editors/admins can write own preferences
- Admins can write any user's preferences (for delegation)
- Cross-tenant access is blocked by RBAC

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl/Cmd+K` | Open Command Palette | Universal search |
| `Esc` | Close modal/palette | Cancel operation |
| `F1` | Show Help | Keyboard shortcuts reference |

### Navigation Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+H` | Home Tab | Personalized dashboard |
| `Ctrl+1` | Templates Tab | Browse templates |
| `Ctrl+2` | Chat Tab | Interactive chat |
| `Ctrl+3` | Batch Tab | Batch jobs |
| `Ctrl+4` | Observability | Metrics dashboard |
| `Ctrl+5` | Admin Panel | Admin only |

### Action Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+Enter` | Run/Submit | Execute template/chat |
| `Ctrl+N` | New Template | Admin only |
| `Ctrl+E` | Export | Export artifact |
| `Ctrl+D` | Favorite/Unfavorite Template | Toggle favorite status |
| `Ctrl+F` | Search | Find templates |
| `Ctrl+O` | Open | Open artifact by ID |

### Approval Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+Shift+A` | Approve | Editor/admin only |
| `Ctrl+Shift+R` | Reject | Editor/admin only |

### Utilities

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+Shift+T` | Toggle Theme | Light/dark mode |
| `Ctrl+,` | Settings | User preferences (future) |

## PWA Mobile Support

### Installation

#### iOS (Safari)
1. Open site in Safari
2. Tap Share button (box with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" to confirm
5. App icon appears on home screen

#### Android (Chrome)
1. Open site in Chrome
2. Tap menu (three dots)
3. Tap "Install app" or "Add to Home Screen"
4. Tap "Install" to confirm
5. App icon appears in app drawer

#### Desktop (Chrome/Edge)
1. Open site in Chrome or Edge
2. Look for install icon in address bar
3. Click "Install" button
4. App opens in standalone window

### Offline Mode

**Feature Flag:** `FEATURE_PWA_OFFLINE=true`

#### What Works Offline
- ✅ View cached artifacts
- ✅ Browse templates (cached)
- ✅ Read documentation
- ✅ View metrics snapshots

#### What Requires Connection
- ❌ Run workflows
- ❌ Approve/reject artifacts
- ❌ Upload files
- ❌ Real-time chat

#### Offline Indicator

When offline, banner appears at top:
```
⚠️ Offline Mode — Viewing cached content only
```

#### Cache Management

Clear PWA cache:
```javascript
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(reg => reg.unregister());
});
```

### Manifest Configuration

PWA manifest at `/pwa/manifest.json`:

```json
{
  "name": "DJP Workflows",
  "short_name": "DJP",
  "display": "standalone",
  "theme_color": "#4A90E2",
  "background_color": "#ffffff",
  "start_url": "/",
  "icons": [...]
}
```

### App Shortcuts (Android)

Long-press app icon for quick actions:
- Templates
- Chat
- Batch

## Accessibility

### Keyboard Navigation
- All actions accessible via keyboard
- Focus indicators visible
- Tab order logical

### Screen Readers
- ARIA labels on all interactive elements
- Semantic HTML structure
- Alt text on images

### Color Contrast
- WCAG AA compliant (4.5:1 minimum)
- Theme toggle for low vision users

## Feature Flags

Control UX features via environment variables:

```bash
# Command Palette
FEATURE_COMMAND_PALETTE=true  # Enable command palette (default: true)

# PWA Offline
FEATURE_PWA_OFFLINE=true      # Enable offline support (default: true)

# PWA Cache Directory
PWA_CACHE_DIR=data/pwa_cache  # Cache location (default)
```

## Performance

### Command Palette
- Opens in <50ms
- Fuzzy search: <10ms for 100 actions
- Zero network calls

### PWA
- Service worker caches static assets on install
- Artifacts cached on first view
- Cache size limit: 50 MB (configurable)

## Troubleshooting

### Command Palette Not Opening

1. Check feature flag: `FEATURE_COMMAND_PALETTE=true`
2. Clear browser cache
3. Check browser console for JS errors

### PWA Not Installable

1. Must be served over HTTPS (or localhost)
2. Must have valid manifest.json
3. Must have service worker
4. Check browser support (Chrome, Edge, Safari 16.4+)

### Offline Mode Not Working

1. Check feature flag: `FEATURE_PWA_OFFLINE=true`
2. Ensure service worker registered
3. Check cache storage in DevTools
4. Try clearing and re-caching

## Best Practices

### For Users
- Learn 3-5 key shortcuts (Ctrl+K, Ctrl+Enter, Ctrl+1-5)
- Install PWA for app-like experience
- Use offline mode for viewing artifacts on the go

### For Developers
- Register custom actions with clear labels
- Test keyboard navigation paths
- Provide meaningful shortcuts (avoid conflicts)
- Cache only essential data for offline use

## Next Steps

1. Install PWA on mobile device
2. Practice command palette shortcuts
3. Customize shortcuts for your workflow
4. Enable offline mode for travel

## Future Enhancements

- Voice commands ("Hey DJP, run template X")
- Gesture navigation (swipe between tabs)
- Customizable keyboard shortcuts
- Offline editing with sync on reconnect
