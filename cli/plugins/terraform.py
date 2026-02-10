"""
Terraform Plugin for B.DEV CLI

Provides Terraform infrastructure as code management including init, plan,
apply, destroy, state management, workspace, import, and more.
"""

import subprocess
import json
from typing import Any, List, Dict, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class TerraformBase(PluginBase):
    """Base class for Terraform plugins."""

    _is_base = True

    def _run_terraform(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run terraform command."""
        cmd = ["terraform"] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def _check_terraform(self) -> bool:
        """Check if terraform is installed."""
        result = self._run_terraform(["version"])
        return result.returncode == 0


# ============================================================================
# Basic Commands
# ============================================================================


class TerraformInitPlugin(TerraformBase):
    """Initialize Terraform working directory."""

    @property
    def name(self) -> str:
        return "tf_init"

    @property
    def description(self) -> str:
        return "Initialize Terraform configuration"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform init."""
        if not self._check_terraform():
            console.error(
                "Terraform is not installed. Install from https://www.terraform.io/"
            )
            return None

        console.info("Initializing Terraform...")

        cmd = ["init"]
        if args:
            cmd.extend(args)

        result = self._run_terraform(cmd)

        if result.stdout:
            console.success("Terraform initialized")
            console.muted(result.stdout)
        else:
            console.error("Init failed")


class TerraformPlanPlugin(TerraformBase):
    """Show Terraform execution plan."""

    @property
    def name(self) -> str:
        return "tf_plan"

    @property
    def description(self) -> str:
        return "Show Terraform execution plan"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform plan."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        console.info("Creating Terraform plan...")

        cmd = ["plan"]
        cmd.extend(args)

        result = self._run_terraform(cmd)

        if result.stdout:
            console.rule("Plan Output")
            console.muted(result.stdout)
        else:
            console.error("Plan failed")


class TerraformApplyPlugin(TerraformBase):
    """Apply Terraform changes."""

    @property
    def name(self) -> str:
        return "tf_apply"

    @property
    def description(self) -> str:
        return "Apply Terraform changes"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform apply."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        auto_approve = "--auto-approve" in args or "-auto" in args
        args_cleaned = [a for a in args if a not in ["--auto-approve", "-auto"]]

        if not auto_approve:
            console.warning("Review the plan before applying.")
            confirmation = input("Continue? (yes/no): ")
            if confirmation.lower() != "yes":
                console.info("Apply cancelled")
                return

        console.info("Applying Terraform changes...")

        cmd = ["apply", "--auto-approve"]
        cmd.extend(args_cleaned)

        result = self._run_terraform(cmd)

        if result.stdout:
            console.success("Apply completed")
            console.muted(result.stdout)
        else:
            console.error("Apply failed")


class TerraformDestroyPlugin(TerraformBase):
    """Destroy Terraform infrastructure."""

    @property
    def name(self) -> str:
        return "tf_destroy"

    @property
    def description(self) -> str:
        return "Destroy Terraform infrastructure"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform destroy."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        auto_approve = "--auto-approve" in args or "-auto" in args
        args_cleaned = [a for a in args if a not in ["--auto-approve", "-auto"]]

        if not auto_approve:
            console.warning("[!] This will DESTROY all infrastructure!")
            confirmation = input("Are you sure? (yes/no): ")
            if confirmation.lower() != "yes":
                console.info("Destroy cancelled")
                return

        console.warning("Destroying infrastructure...")

        cmd = ["destroy", "--auto-approve"]
        cmd.extend(args_cleaned)

        result = self._run_terraform(cmd)

        if result.stdout:
            console.success("Infrastructure destroyed")
            console.muted(result.stdout)
        else:
            console.error("Destroy failed")


# ============================================================================
# State Management
# ============================================================================


class TerraformStatePlugin(TerraformBase):
    """Terraform state management."""

    @property
    def name(self) -> str:
        return "tf_state"

    @property
    def description(self) -> str:
        return "Terraform state management (list, show, rm, mv, push, pull)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle state commands."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        if not args:
            self._list_state()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_state(*sub_args)
            elif command == "show":
                self._show_state(*sub_args)
            elif command == "rm":
                self._remove_state(*sub_args)
            elif command == "mv":
                self._move_state(*sub_args)
            elif command == "push":
                self._push_state(*sub_args)
            elif command == "pull":
                self._pull_state(*sub_args)
            elif command == "replace":
                self._replace_state(*sub_args)
            else:
                console.error(f"Unknown state command: {command}")
        except Exception as e:
            console.error(f"State command failed: {e}")

    def _list_state(self, *args: str) -> None:
        """List state resources."""
        console.info("Listing state resources...")

        result = self._run_terraform(["state", "list"])

        if result.stdout:
            console.rule("State Resources")
            console.muted(result.stdout)
        else:
            console.info("No state found")

    def _show_state(self, *args: str) -> None:
        """Show state details."""
        if not args:
            console.error("Usage: tf_state show <address>")
            return

        address = args[0]
        console.info(f"State for: {address}")

        result = self._run_terraform(["state", "show", address])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"No state found for {address}")

    def _remove_state(self, *args: str) -> None:
        """Remove resource from state."""
        if not args:
            console.error("Usage: tf_state rm <address>")
            return

        address = args[0]
        console.warning(f"Removing from state: {address}")

        result = self._run_terraform(["state", "rm", address])

        if result.returncode == 0:
            console.success(f"Removed {address} from state")
        else:
            console.error(f"Failed to remove: {result.stderr}")

    def _move_state(self, *args: str) -> None:
        """Move resource in state."""
        if len(args) < 2:
            console.error("Usage: tf_state mv <old_address> <new_address>")
            return

        old_address = args[0]
        new_address = args[1]

        console.info(f"Moving: {old_address} -> {new_address}")

        result = self._run_terraform(["state", "mv", old_address, new_address])

        if result.returncode == 0:
            console.success("State moved successfully")
        else:
            console.error(f"Failed to move: {result.stderr}")

    def _push_state(self, *args: str) -> None:
        """Push state to remote backend."""
        console.info("Pushing state to remote backend...")

        result = self._run_terraform(["state", "push"])

        if result.returncode == 0:
            console.success("State pushed to remote")
        else:
            console.error(f"Failed to push: {result.stderr}")

    def _pull_state(self, *args: str) -> None:
        """Pull state from remote backend."""
        console.info("Pulling state from remote backend...")

        result = self._run_terraform(["state", "pull"])

        if result.returncode == 0:
            console.success("State pulled from remote")
        else:
            console.error(f"Failed to pull: {result.stderr}")

    def _replace_state(self, *args: str) -> None:
        """Replace resource in state."""
        if len(args) < 1:
            console.error("Usage: tf_state replace <address> [options]")
            return

        address = args[0]
        options = args[1:]

        console.info(f"Replacing state for: {address}")

        cmd = ["state", "replace-provider", address] + list(options)
        result = self._run_terraform(cmd)

        if result.returncode == 0:
            console.success("State replaced")
        else:
            console.error(f"Failed to replace: {result.stderr}")


# ============================================================================
# Workspace Management
# ============================================================================


class TerraformWorkspacePlugin(TerraformBase):
    """Terraform workspace management."""

    @property
    def name(self) -> str:
        return "tf_workspace"

    @property
    def description(self) -> str:
        return "Workspace management (list, show, new, select, delete)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle workspace commands."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_workspaces()
            elif command == "show":
                self._show_workspace()
            elif command == "new":
                self._new_workspace(*sub_args)
            elif command == "select":
                self._select_workspace(*sub_args)
            elif command == "delete":
                self._delete_workspace(*sub_args)
            elif command == "new-state":
                self._new_state_workspace(*sub_args)
            else:
                console.error(f"Unknown workspace command: {command}")
        except Exception as e:
            console.error(f"Workspace command failed: {e}")

    def _list_workspaces(self) -> None:
        """List workspaces."""
        console.info("Listing workspaces...")

        result = self._run_terraform(["workspace", "list"])

        if result.stdout:
            console.rule("Workspaces")
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.startswith("*"):
                    console.success(f"  {line}")
                else:
                    console.muted(f"  {line}")
        else:
            console.info("No workspaces found")

    def _show_workspace(self) -> None:
        """Show current workspace."""
        result = self._run_terraform(["workspace", "show"])

        if result.stdout:
            console.rule("Current Workspace")
            console.muted(result.stdout)
        else:
            console.info("No workspace set")

    def _new_workspace(self, *args: str) -> None:
        """Create new workspace."""
        if not args:
            console.error("Usage: tf_workspace new <name>")
            return

        name = args[0]
        console.info(f"Creating workspace: {name}")

        result = self._run_terraform(["workspace", "new", name])

        if result.returncode == 0:
            console.success(f"Workspace {name} created and selected")
        else:
            console.error(f"Failed to create: {result.stderr}")

    def _select_workspace(self, *args: str) -> None:
        """Select workspace."""
        if not args:
            console.error("Usage: tf_workspace select <name>")
            return

        name = args[0]
        console.info(f"Selecting workspace: {name}")

        result = self._run_terraform(["workspace", "select", name])

        if result.returncode == 0:
            console.success(f"Selected workspace: {name}")
        else:
            console.error(f"Failed to select: {result.stderr}")

    def _delete_workspace(self, *args: str) -> None:
        """Delete workspace."""
        if not args:
            console.error("Usage: tf_workspace delete <name>")
            return

        name = args[0]
        console.warning(f"Deleting workspace: {name}")

        result = self._run_terraform(["workspace", "delete", name])

        if result.returncode == 0:
            console.success(f"Workspace {name} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _new_state_workspace(self, *args: str) -> None:
        """Create new state from existing state."""
        if not args:
            console.error("Usage: tf_workspace new-state <name>")
            return

        name = args[0]
        console.info(f"Creating workspace from state: {name}")

        result = self._run_terraform(["workspace", "new-state", name])

        if result.returncode == 0:
            console.success(f"Workspace {name} created from existing state")
        else:
            console.error(f"Failed to create from state: {result.stderr}")

    def _show_help(self) -> None:
        rows = [
            ["list", "List all workspaces"],
            ["show", "Show current workspace"],
            ["new <name>", "Create new workspace"],
            ["select <name>", "Select workspace"],
            ["delete <name>", "Delete workspace"],
            ["new-state <name>", "Create workspace from existing state"],
        ]
        console.table("Workspace Commands", ["Command", "Description"], rows)


# ============================================================================
# Import & Output
# ============================================================================


class TerraformImportPlugin(TerraformBase):
    """Import existing resources into Terraform state."""

    @property
    def name(self) -> str:
        return "tf_import"

    @property
    def description(self) -> str:
        return "Import existing resources into Terraform state"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform import."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        if len(args) < 2:
            console.error("Usage: tf_import <address> <id>")
            return

        address = args[0]
        resource_id = args[1]

        console.info(f"Importing {resource_id} as {address}...")

        result = self._run_terraform(["import", address, resource_id])

        if result.stdout:
            console.success("Resource imported")
            console.muted(result.stdout)
        else:
            console.error(f"Import failed: {result.stderr}")


class TerraformOutputPlugin(TerraformBase):
    """Show Terraform outputs."""

    @property
    def name(self) -> str:
        return "tf_output"

    @property
    def description(self) -> str:
        return "Show Terraform output values"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show outputs."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        output_name = args[0] if args else None

        console.info("Fetching outputs...")

        if output_name:
            result = self._run_terraform(["output", "-raw", output_name])
        else:
            result = self._run_terraform(["output"])

        if result.stdout:
            console.rule("Outputs")
            console.muted(result.stdout)
        else:
            console.info("No outputs found")


# ============================================================================
# Validation & Formatting
# ============================================================================


class TerraformValidatePlugin(TerraformBase):
    """Validate Terraform configuration."""

    @property
    def name(self) -> str:
        return "tf_validate"

    @property
    def description(self) -> str:
        return "Validate Terraform configuration files"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform validate."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        console.info("Validating configuration...")

        result = self._run_terraform(["validate"])

        if result.returncode == 0:
            console.success("Configuration is valid")
            console.muted(result.stdout)
        else:
            console.error("Validation failed")
            console.muted(result.stderr)


class TerraformFmtPlugin(TerraformBase):
    """Format Terraform configuration."""

    @property
    def name(self) -> str:
        return "tf_fmt"

    @property
    def description(self) -> str:
        return "Format Terraform configuration files"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform fmt."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        check = "--check" in args or "-c" in args
        recursive = "--recursive" in args or "-r" in args
        args_cleaned = [
            a for a in args if a not in ["--check", "-c", "--recursive", "-r"]
        ]

        console.info("Formatting configuration...")

        cmd = ["fmt"]
        if check:
            cmd.append("--check")
        if recursive:
            cmd.append("--recursive")
        cmd.extend(args_cleaned)

        result = self._run_terraform(cmd)

        if result.stdout:
            if check:
                if result.returncode == 0:
                    console.success("All files are formatted")
                else:
                    console.warning("Some files need formatting")
                    console.muted(result.stdout)
            else:
                console.success("Formatting completed")
                console.muted(result.stdout)
        elif result.returncode != 0:
            console.error("Format failed")


class TerraformTaintPlugin(TerraformBase):
    """Mark resource for recreation."""

    @property
    def name(self) -> str:
        return "tf_taint"

    @property
    def description(self) -> str:
        return "Mark resource for recreation on next apply"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform taint."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        if len(args) < 1:
            console.error("Usage: tf_taint <address>")
            return

        address = args[0]
        console.warning(f"Tainting: {address}")

        result = self._run_terraform(["taint", address])

        if result.returncode == 0:
            console.success(f"Resource {address} tainted")
        else:
            console.error(f"Failed to taint: {result.stderr}")


class TerraformUntaintPlugin(TerraformBase):
    """Untaint resource."""

    @property
    def name(self) -> str:
        return "tf_untaint"

    @property
    def description(self) -> str:
        return "Remove taint from resource"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform untaint."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        if len(args) < 1:
            console.error("Usage: tf_untaint <address>")
            return

        address = args[0]
        console.info(f"Untainting: {address}")

        result = self._run_terraform(["untaint", address])

        if result.returncode == 0:
            console.success(f"Resource {address} untainted")
        else:
            console.error(f"Failed to untaint: {result.stderr}")


# ============================================================================
# Graph & Visualization
# ============================================================================


class TerraformGraphPlugin(TerraformBase):
    """Visualize Terraform configuration."""

    @property
    def name(self) -> str:
        return "tf_graph"

    @property
    def description(self) -> str:
        return "Visualize Terraform configuration as graph"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform graph."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        plan = "--plan" in args or "-p" in args
        type_arg = args[0] if args and not args[0].startswith("-") else None

        console.info("Generating graph...")

        cmd = ["graph"]
        if plan:
            cmd.append("-plan=terraform.tfplan")
        if type_arg:
            cmd.extend(["-type", type_arg])

        result = self._run_terraform(cmd)

        if result.stdout:
            console.rule("Graph Output (DOT format)")
            console.muted(result.stdout)
            console.muted(
                "Use online DOT viewers like https://dreampuf.github.io/Gravizo/ to visualize"
            )
        else:
            console.info("No graph output")


# ============================================================================
# Refresh & Lock
# ============================================================================


class TerraformRefreshPlugin(TerraformBase):
    """Refresh Terraform state."""

    @property
    def name(self) -> str:
        return "tf_refresh"

    @property
    def description(self) -> str:
        return "Refresh Terraform state with real infrastructure"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run terraform refresh."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        console.info("Refreshing state...")

        result = self._run_terraform(["refresh"])

        if result.stdout:
            console.success("State refreshed")
            console.muted(result.stdout)
        else:
            console.error("Refresh failed")


class TerraformLockPlugin(TerraformBase):
    """Manage state lock."""

    @property
    def name(self) -> str:
        return "tf_lock"

    @property
    def description(self) -> str:
        return "Manage state lock (status, force-unlock)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle lock commands."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        if not args:
            console.error("Usage: tf_lock <status|force-unlock> [ID]")
            return

        action = args[0].lower()

        if action == "status":
            result = self._run_terraform(["force-unlock"])
            if result.returncode != 0:
                console.success("No lock held")
            else:
                console.muted(result.stdout)
        elif action == "force-unlock":
            lock_id = args[1] if len(args) > 1 else None

            console.warning("Force unlocking state...")
            cmd = ["force-unlock"]
            if lock_id:
                cmd.append(lock_id)

            result = self._run_terraform(cmd)

            if result.returncode == 0:
                console.success("State unlocked")
            else:
                console.error(f"Failed to unlock: {result.stderr}")
        else:
            console.error(f"Unknown lock action: {action}")


# ============================================================================
# Providers & Modules
# ============================================================================


class TerraformProvidersPlugin(TerraformBase):
    """Provider management."""

    @property
    def name(self) -> str:
        return "tf_providers"

    @property
    def description(self) -> str:
        return "Provider management (init, lock, mirror, schema)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle provider commands."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "init":
                self._providers_init(*sub_args)
            elif command == "lock":
                self._providers_lock(*sub_args)
            elif command == "mirror":
                self._providers_mirror(*sub_args)
            elif command == "schema":
                self._providers_schema(*sub_args)
            elif command == "validate":
                self._providers_validate(*sub_args)
            else:
                console.error(f"Unknown provider command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Provider command failed: {e}")

    def _providers_init(self, *args: str) -> None:
        """Initialize providers."""
        console.info("Initializing providers...")

        cmd = ["init"]
        if "-upgrade" in args:
            cmd.append("-upgrade")

        result = self._run_terraform(cmd)

        if result.returncode == 0:
            console.success("Providers initialized")
        else:
            console.error("Provider init failed")

    def _providers_lock(self, *args: str) -> None:
        """Lock provider versions."""
        if not args:
            console.error("Usage: tf_providers lock [provider]")
            return

        provider = args[0]
        console.info(f"Locking provider: {provider}")

        result = self._run_terraform(["providers", "lock", "-platform"] + list(args))

        if result.returncode == 0:
            console.success(f"Provider {provider} locked")
        else:
            console.error("Lock failed")

    def _providers_mirror(self, *args: str) -> None:
        """Configure provider mirrors."""
        if not args:
            self._show_help()
            return

        console.info("Configuring provider mirrors...")

        result = self._run_terraform(["providers", "mirror"] + list(args))

        if result.returncode == 0:
            console.success("Mirror configured")
        else:
            console.error("Mirror configuration failed")

    def _providers_schema(self, *args: str) -> None:
        """Show provider schema."""
        provider = args[0] if args else "aws"

        console.info(f"Schema for provider: {provider}")

        result = self._run_terraform(["providers", "schema", "-json", provider])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"No schema found for {provider}")

    def _providers_validate(self, *args: str) -> None:
        """Validate provider configuration."""
        console.info("Validating provider configuration...")

        result = self._run_terraform(["providers", "validate"])

        if result.returncode == 0:
            console.success("Provider configuration is valid")
        else:
            console.error("Validation failed")

    def _show_help(self) -> None:
        rows = [
            ["init", "Initialize providers"],
            ["lock <provider>", "Lock provider version"],
            ["mirror", "Configure mirrors"],
            ["schema <provider>", "Show provider schema"],
            ["validate", "Validate provider config"],
        ]
        console.table("Provider Commands", ["Command", "Description"], rows)


# ============================================================================
# Miscellaneous
# ============================================================================


class TerraformVersionPlugin(TerraformBase):
    """Show Terraform version."""

    @property
    def name(self) -> str:
        return "tf_version"

    @property
    def description(self) -> str:
        return "Show Terraform version"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show version."""
        if not self._check_terraform():
            console.error("Terraform is not installed")
            return None

        result = self._run_terraform(["version"])

        if result.stdout:
            console.rule("Terraform Version")
            console.muted(result.stdout)
        else:
            console.error("Version check failed")
