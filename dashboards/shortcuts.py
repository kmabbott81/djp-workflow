"""Centralized keyboard shortcuts and action registry."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class ActionType(str, Enum):
    """Types of actions available in command palette."""

    RUN_TEMPLATE = "run_template"
    APPROVE_ARTIFACT = "approve_artifact"
    REJECT_ARTIFACT = "reject_artifact"
    OPEN_ARTIFACT = "open_artifact"
    SEARCH_TEMPLATES = "search_templates"
    GO_TO_HOME = "go_to_home"
    GO_TO_TEMPLATES = "go_to_templates"
    GO_TO_CHAT = "go_to_chat"
    GO_TO_BATCH = "go_to_batch"
    GO_TO_OBSERVABILITY = "go_to_observability"
    GO_TO_ADMIN = "go_to_admin"
    CREATE_TEMPLATE = "create_template"
    EXPORT_ARTIFACT = "export_artifact"
    TOGGLE_THEME = "toggle_theme"
    SHOW_HELP = "show_help"
    FAVORITE_TEMPLATE = "favorite_template"


@dataclass
class ShortcutAction:
    """Represents a keyboard shortcut action."""

    action_id: str
    action_type: ActionType
    label: str
    description: str
    keyboard_shortcut: Optional[str] = None  # e.g., "Ctrl+K", "Cmd+Enter"
    category: str = "General"
    icon: Optional[str] = None  # Emoji or icon name
    enabled: bool = True
    callback: Optional[Callable[[Any], Any]] = None


class ShortcutRegistry:
    """Central registry for keyboard shortcuts and command palette actions."""

    def __init__(self):
        self._actions: dict[str, ShortcutAction] = {}
        self._register_default_actions()

    def _register_default_actions(self):
        """Register default system actions."""
        # Feature flag for command palette
        if not os.getenv("FEATURE_COMMAND_PALETTE", "true").lower() == "true":
            return

        default_actions = [
            # Navigation
            ShortcutAction(
                action_id="go_to_home",
                action_type=ActionType.GO_TO_HOME,
                label="Go to Home",
                description="Navigate to Home dashboard",
                keyboard_shortcut="Ctrl+H",
                category="Navigation",
                icon="🏠",
            ),
            ShortcutAction(
                action_id="go_to_templates",
                action_type=ActionType.GO_TO_TEMPLATES,
                label="Go to Templates",
                description="Navigate to Templates tab",
                keyboard_shortcut="Ctrl+1",
                category="Navigation",
                icon="📝",
            ),
            ShortcutAction(
                action_id="go_to_chat",
                action_type=ActionType.GO_TO_CHAT,
                label="Go to Chat",
                description="Navigate to Chat tab",
                keyboard_shortcut="Ctrl+2",
                category="Navigation",
                icon="💬",
            ),
            ShortcutAction(
                action_id="go_to_batch",
                action_type=ActionType.GO_TO_BATCH,
                label="Go to Batch",
                description="Navigate to Batch tab",
                keyboard_shortcut="Ctrl+3",
                category="Navigation",
                icon="📦",
            ),
            ShortcutAction(
                action_id="go_to_observability",
                action_type=ActionType.GO_TO_OBSERVABILITY,
                label="Go to Observability",
                description="Navigate to Observability dashboard",
                keyboard_shortcut="Ctrl+4",
                category="Navigation",
                icon="📊",
            ),
            ShortcutAction(
                action_id="go_to_admin",
                action_type=ActionType.GO_TO_ADMIN,
                label="Go to Admin",
                description="Navigate to Admin panel (requires admin role)",
                keyboard_shortcut="Ctrl+5",
                category="Navigation",
                icon="⚙️",
            ),
            # Actions
            ShortcutAction(
                action_id="run_template",
                action_type=ActionType.RUN_TEMPLATE,
                label="Run Template",
                description="Execute selected template",
                keyboard_shortcut="Ctrl+Enter",
                category="Actions",
                icon="▶️",
            ),
            ShortcutAction(
                action_id="approve_artifact",
                action_type=ActionType.APPROVE_ARTIFACT,
                label="Approve Artifact",
                description="Approve selected artifact (requires editor role)",
                keyboard_shortcut="Ctrl+Shift+A",
                category="Actions",
                icon="✅",
            ),
            ShortcutAction(
                action_id="reject_artifact",
                action_type=ActionType.REJECT_ARTIFACT,
                label="Reject Artifact",
                description="Reject selected artifact (requires editor role)",
                keyboard_shortcut="Ctrl+Shift+R",
                category="Actions",
                icon="❌",
            ),
            ShortcutAction(
                action_id="create_template",
                action_type=ActionType.CREATE_TEMPLATE,
                label="Create Template",
                description="Create new template (requires admin role)",
                keyboard_shortcut="Ctrl+N",
                category="Actions",
                icon="➕",
            ),
            ShortcutAction(
                action_id="export_artifact",
                action_type=ActionType.EXPORT_ARTIFACT,
                label="Export Artifact",
                description="Export selected artifact to PDF/Excel",
                keyboard_shortcut="Ctrl+E",
                category="Actions",
                icon="📤",
            ),
            ShortcutAction(
                action_id="favorite_template",
                action_type=ActionType.FAVORITE_TEMPLATE,
                label="Favorite/Unfavorite Template",
                description="Toggle favorite status for selected template",
                keyboard_shortcut="Ctrl+D",
                category="Actions",
                icon="⭐",
            ),
            # Search
            ShortcutAction(
                action_id="search_templates",
                action_type=ActionType.SEARCH_TEMPLATES,
                label="Search Templates",
                description="Search and filter templates",
                keyboard_shortcut="Ctrl+F",
                category="Search",
                icon="🔍",
            ),
            ShortcutAction(
                action_id="open_artifact",
                action_type=ActionType.OPEN_ARTIFACT,
                label="Open Artifact",
                description="Open artifact by ID",
                keyboard_shortcut="Ctrl+O",
                category="Search",
                icon="📄",
            ),
            # Utilities
            ShortcutAction(
                action_id="toggle_theme",
                action_type=ActionType.TOGGLE_THEME,
                label="Toggle Theme",
                description="Switch between light and dark mode",
                keyboard_shortcut="Ctrl+Shift+T",
                category="Utilities",
                icon="🌓",
            ),
            ShortcutAction(
                action_id="show_help",
                action_type=ActionType.SHOW_HELP,
                label="Show Help",
                description="Display keyboard shortcuts and help",
                keyboard_shortcut="F1",
                category="Utilities",
                icon="❓",
            ),
        ]

        for action in default_actions:
            self.register(action)

    def register(self, action: ShortcutAction):
        """Register an action in the registry."""
        self._actions[action.action_id] = action

    def unregister(self, action_id: str):
        """Unregister an action."""
        self._actions.pop(action_id, None)

    def get_action(self, action_id: str) -> Optional[ShortcutAction]:
        """Get action by ID."""
        return self._actions.get(action_id)

    def get_all_actions(self) -> list[ShortcutAction]:
        """Get all registered actions."""
        return list(self._actions.values())

    def get_actions_by_category(self, category: str) -> list[ShortcutAction]:
        """Get actions by category."""
        return [action for action in self._actions.values() if action.category == category]

    def get_enabled_actions(self) -> list[ShortcutAction]:
        """Get all enabled actions."""
        return [action for action in self._actions.values() if action.enabled]

    def search_actions(self, query: str) -> list[ShortcutAction]:
        """Fuzzy search actions by label or description."""
        query_lower = query.lower()
        results = []

        for action in self.get_enabled_actions():
            # Simple fuzzy matching
            label_match = query_lower in action.label.lower()
            desc_match = query_lower in action.description.lower()
            category_match = query_lower in action.category.lower()

            if label_match or desc_match or category_match:
                # Calculate relevance score (simple heuristic)
                score = 0
                if label_match:
                    score += 10
                if action.label.lower().startswith(query_lower):
                    score += 5
                if desc_match:
                    score += 3
                if category_match:
                    score += 1

                results.append((score, action))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [action for _, action in results]

    def execute_action(self, action_id: str, context: Optional[dict[str, Any]] = None) -> Any:
        """Execute action callback if registered."""
        action = self.get_action(action_id)
        if not action:
            raise ValueError(f"Action not found: {action_id}")

        if not action.enabled:
            raise ValueError(f"Action disabled: {action_id}")

        if action.callback:
            return action.callback(context or {})

        return None

    def get_shortcuts_by_key(self, key: str) -> list[ShortcutAction]:
        """Get actions bound to a specific keyboard shortcut."""
        return [action for action in self._actions.values() if action.keyboard_shortcut == key]


# Global registry singleton
_global_registry: Optional[ShortcutRegistry] = None


def get_shortcut_registry() -> ShortcutRegistry:
    """Get global shortcut registry singleton."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ShortcutRegistry()
    return _global_registry
