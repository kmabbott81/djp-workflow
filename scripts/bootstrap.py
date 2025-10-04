#!/usr/bin/env python3
"""
Bootstrap script for provisioning initial admin user and role bindings.

This script creates the foundational security setup for the system:
- Admin user with Admin role
- Default team with admin as member
- Initial workspace for the team
- Audit events for all operations

Usage:
    # Using environment variables
    export BOOTSTRAP_ADMIN_USER=admin@example.com
    export BOOTSTRAP_TENANT=acme-corp
    python scripts/bootstrap.py

    # Using CLI flags
    python scripts/bootstrap.py --user admin@example.com --tenant acme-corp

    # Using both (flags override environment)
    export BOOTSTRAP_ADMIN_USER=default@example.com
    python scripts/bootstrap.py --user admin@example.com --tenant acme-corp

Features:
    - Idempotent: safe to re-run, won't create duplicates
    - Audit logging: all operations are logged for compliance
    - Clear status messages: progress and results clearly communicated
    - Validation: checks for required configuration before proceeding

Sprint 34A: Collaborative governance bootstrap.
"""

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from security.audit import AuditAction, get_audit_logger  # noqa: E402
from security.teams import get_team_role, upsert_team_member  # noqa: E402
from security.workspaces import get_workspace_role, upsert_workspace_member  # noqa: E402


class BootstrapError(Exception):
    """Raised when bootstrap process fails."""

    pass


class BootstrapRunner:
    """Bootstrap runner for provisioning initial admin and resources."""

    def __init__(self, admin_user: str, tenant: str, verbose: bool = True):
        """
        Initialize bootstrap runner.

        Args:
            admin_user: Admin user identifier (e.g., email or username)
            tenant: Tenant identifier
            verbose: Print status messages
        """
        self.admin_user = admin_user
        self.tenant = tenant
        self.verbose = verbose
        self.audit_logger = get_audit_logger()

        # Default IDs
        self.default_team_id = f"team-{tenant}-default"
        self.default_team_name = f"{tenant} Default Team"
        self.default_workspace_id = f"ws-{tenant}-default"
        self.default_workspace_name = f"{tenant} Default Workspace"

    def log(self, message: str) -> None:
        """Print status message if verbose."""
        if self.verbose:
            print(f"[BOOTSTRAP] {message}")

    def log_success(self, message: str) -> None:
        """Print success message if verbose."""
        if self.verbose:
            print(f"[BOOTSTRAP] SUCCESS: {message}")

    def log_error(self, message: str) -> None:
        """Print error message."""
        print(f"[BOOTSTRAP] ERROR: {message}", file=sys.stderr)

    def validate_config(self) -> None:
        """
        Validate configuration before proceeding.

        Raises:
            BootstrapError: If configuration is invalid
        """
        if not self.admin_user:
            raise BootstrapError("Admin user is required (set BOOTSTRAP_ADMIN_USER or use --user)")

        if not self.tenant:
            raise BootstrapError("Tenant is required (set BOOTSTRAP_TENANT or use --tenant)")

        # Validate user format (basic check)
        if not self.admin_user.strip():
            raise BootstrapError("Admin user cannot be empty or whitespace")

        # Validate tenant format (basic check)
        if not self.tenant.strip():
            raise BootstrapError("Tenant cannot be empty or whitespace")

        if " " in self.tenant:
            raise BootstrapError("Tenant ID cannot contain spaces")

        self.log(f"Configuration validated: user={self.admin_user}, tenant={self.tenant}")

    def create_admin_user(self) -> bool:
        """
        Create or update admin user with Admin role in default team.

        Returns:
            True if user was created, False if already existed

        Raises:
            BootstrapError: If creation fails
        """
        try:
            self.log(f"Creating admin user '{self.admin_user}' in team '{self.default_team_id}'...")

            # Check if user already exists in team
            existing_role = get_team_role(self.admin_user, self.default_team_id)
            was_existing = existing_role is not None

            if was_existing:
                self.log(f"User already exists with role: {existing_role}")
                if existing_role == "Admin":
                    self.log("User already has Admin role, skipping creation")
                    return False
                else:
                    self.log(f"Upgrading user role from {existing_role} to Admin")

            # Create or update user
            upsert_team_member(
                team_id=self.default_team_id,
                user=self.admin_user,
                role="Admin",
                team_name=self.default_team_name,
            )

            # Log audit event
            self.audit_logger.log_success(
                tenant_id=self.tenant,
                user_id="system",
                action=AuditAction.LOGIN if not was_existing else AuditAction.UPDATE_CONFIG,
                resource_type="user",
                resource_id=self.admin_user,
                metadata={
                    "operation": "bootstrap_admin_user",
                    "team_id": self.default_team_id,
                    "role": "Admin",
                    "was_existing": was_existing,
                    "upgraded": was_existing and existing_role != "Admin",
                },
            )

            if was_existing:
                self.log_success(f"Admin user updated: {self.admin_user}")
            else:
                self.log_success(f"Admin user created: {self.admin_user}")

            return not was_existing

        except Exception as e:
            self.log_error(f"Failed to create admin user: {e}")
            self.audit_logger.log_failure(
                tenant_id=self.tenant,
                user_id="system",
                action=AuditAction.LOGIN,
                resource_type="user",
                resource_id=self.admin_user,
                reason=str(e),
                metadata={"operation": "bootstrap_admin_user"},
            )
            raise BootstrapError(f"Failed to create admin user: {e}") from e

    def create_default_team(self) -> bool:
        """
        Create default team with admin as member.

        Returns:
            True if team was created, False if already existed

        Note:
            Team creation is handled automatically by upsert_team_member
            in create_admin_user(), so this verifies the team exists.
        """
        try:
            self.log(f"Verifying default team '{self.default_team_id}'...")

            # Check if admin is in team (implies team exists)
            existing_role = get_team_role(self.admin_user, self.default_team_id)

            if existing_role:
                self.log_success(f"Default team exists with admin as {existing_role}")
                return False
            else:
                # This shouldn't happen if create_admin_user ran successfully
                self.log_error("Team verification failed: admin not in team")
                raise BootstrapError("Default team verification failed")

        except Exception as e:
            self.log_error(f"Failed to verify default team: {e}")
            raise BootstrapError(f"Failed to verify default team: {e}") from e

    def create_default_workspace(self) -> bool:
        """
        Create initial workspace for the default team.

        Returns:
            True if workspace was created, False if already existed

        Raises:
            BootstrapError: If creation fails
        """
        try:
            self.log(f"Creating default workspace '{self.default_workspace_id}'...")

            # Check if workspace already exists
            existing_role = get_workspace_role(self.admin_user, self.default_workspace_id)
            was_existing = existing_role is not None

            if was_existing:
                self.log(f"Workspace already exists, admin has role: {existing_role}")
                if existing_role == "Admin":
                    self.log("Admin already has Admin role in workspace, skipping creation")
                    return False
                else:
                    self.log(f"Upgrading admin role from {existing_role} to Admin")

            # Create or update workspace
            upsert_workspace_member(
                workspace_id=self.default_workspace_id,
                user=self.admin_user,
                role="Admin",
                workspace_name=self.default_workspace_name,
                team_id=self.default_team_id,
            )

            # Log audit event
            self.audit_logger.log_success(
                tenant_id=self.tenant,
                user_id="system",
                action=AuditAction.CREATE_TEMPLATE if not was_existing else AuditAction.UPDATE_TEMPLATE,
                resource_type="workspace",
                resource_id=self.default_workspace_id,
                metadata={
                    "operation": "bootstrap_workspace",
                    "workspace_name": self.default_workspace_name,
                    "team_id": self.default_team_id,
                    "admin_user": self.admin_user,
                    "was_existing": was_existing,
                    "upgraded": was_existing and existing_role != "Admin",
                },
            )

            if was_existing:
                self.log_success(f"Default workspace updated: {self.default_workspace_id}")
            else:
                self.log_success(f"Default workspace created: {self.default_workspace_id}")

            return not was_existing

        except Exception as e:
            self.log_error(f"Failed to create default workspace: {e}")
            self.audit_logger.log_failure(
                tenant_id=self.tenant,
                user_id="system",
                action=AuditAction.CREATE_TEMPLATE,
                resource_type="workspace",
                resource_id=self.default_workspace_id,
                reason=str(e),
                metadata={"operation": "bootstrap_workspace"},
            )
            raise BootstrapError(f"Failed to create default workspace: {e}") from e

    def run(self) -> dict:
        """
        Run the complete bootstrap process.

        Returns:
            Dict with bootstrap results

        Raises:
            BootstrapError: If bootstrap fails
        """
        self.log("=" * 60)
        self.log("Starting bootstrap process...")
        self.log("=" * 60)

        start_time = datetime.now(UTC)

        try:
            # Validate configuration
            self.validate_config()

            # Create admin user and team
            user_created = self.create_admin_user()

            # Verify team (created implicitly)
            self.create_default_team()

            # Create default workspace
            workspace_created = self.create_default_workspace()

            # Calculate duration
            duration = (datetime.now(UTC) - start_time).total_seconds()

            # Prepare results
            results = {
                "success": True,
                "tenant": self.tenant,
                "admin_user": self.admin_user,
                "team_id": self.default_team_id,
                "workspace_id": self.default_workspace_id,
                "user_created": user_created,
                "workspace_created": workspace_created,
                "duration_seconds": duration,
            }

            # Print summary
            self.log("=" * 60)
            self.log_success("Bootstrap completed successfully!")
            self.log("=" * 60)
            self.log(f"Tenant:      {self.tenant}")
            self.log(f"Admin User:  {self.admin_user}")
            self.log(f"Team:        {self.default_team_id}")
            self.log(f"Workspace:   {self.default_workspace_id}")
            self.log(f"Duration:    {duration:.2f}s")
            self.log("=" * 60)

            if not user_created and not workspace_created:
                self.log("Note: All resources already existed (idempotent re-run)")

            return results

        except BootstrapError:
            # Re-raise bootstrap errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            self.log_error(f"Unexpected error during bootstrap: {e}")
            raise BootstrapError(f"Unexpected error: {e}") from e


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Bootstrap initial admin user and role bindings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables
  export BOOTSTRAP_ADMIN_USER=admin@example.com
  export BOOTSTRAP_TENANT=acme-corp
  python scripts/bootstrap.py

  # Using CLI flags
  python scripts/bootstrap.py --user admin@example.com --tenant acme-corp

  # Quiet mode
  python scripts/bootstrap.py --user admin@example.com --tenant acme-corp --quiet

Environment Variables:
  BOOTSTRAP_ADMIN_USER  Admin user identifier (email or username)
  BOOTSTRAP_TENANT      Tenant identifier
  AUDIT_LOG_DIR         Directory for audit logs (default: audit)
  TEAMS_PATH            Path to teams JSONL file (default: logs/teams.jsonl)
  WORKSPACES_PATH       Path to workspaces JSONL file (default: logs/workspaces.jsonl)
        """,
    )

    parser.add_argument(
        "--user",
        "-u",
        help="Admin user identifier (overrides BOOTSTRAP_ADMIN_USER)",
        default=None,
    )

    parser.add_argument(
        "--tenant",
        "-t",
        help="Tenant identifier (overrides BOOTSTRAP_TENANT)",
        default=None,
    )

    parser.add_argument(
        "--quiet",
        "-q",
        help="Suppress status messages (only show errors)",
        action="store_true",
    )

    parser.add_argument(
        "--dry-run",
        help="Validate configuration without making changes",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Get user and tenant from args or environment
    admin_user = args.user or os.getenv("BOOTSTRAP_ADMIN_USER")
    tenant = args.tenant or os.getenv("BOOTSTRAP_TENANT")

    try:
        # Create bootstrap runner
        runner = BootstrapRunner(
            admin_user=admin_user or "",
            tenant=tenant or "",
            verbose=not args.quiet,
        )

        if args.dry_run:
            runner.log("DRY RUN: Validating configuration only...")
            runner.validate_config()
            runner.log_success("Configuration is valid")
            return 0

        # Run bootstrap
        runner.run()

        return 0

    except BootstrapError as e:
        print(f"[BOOTSTRAP] FAILED: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[BOOTSTRAP] INTERRUPTED: Bootstrap interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[BOOTSTRAP] ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
