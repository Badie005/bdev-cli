"""
Cloud Plugin for B.DEV CLI.

Multi-cloud management for AWS, GCP, and Azure with unified interface.
"""

import subprocess
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors


class CloudProvider(Enum):
    """Cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class CloudPlugin(PluginBase):
    """Multi-cloud management plugin."""

    @property
    def name(self) -> str:
        return "cloud"

    @property
    def description(self) -> str:
        return "Multi-cloud management (AWS, GCP, Azure)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute cloud commands."""
        if not args:
            self._show_help()
            return

        provider = args[0].lower()
        sub_args = args[1:]

        if provider == "aws":
            self._handle_aws(*sub_args)
        elif provider == "gcp":
            self._handle_gcp(*sub_args)
        elif provider == "azure":
            self._handle_azure(*sub_args)
        elif provider in ["deploy", "cost", "inventory"]:
            self._handle_multicloud(provider, *sub_args)
        else:
            console.error(f"Unknown provider: {provider}")
            self._show_help()

    # ========================================================================
    # AWS Commands
    # ========================================================================

    def _handle_aws(self, *args: str) -> None:
        """Handle AWS commands."""
        if not args:
            self._aws_help()
            return

        command = args[0]
        sub_args = args[1:]

        try:
            if command == "s3":
                self._aws_s3(*sub_args)
            elif command == "ec2":
                self._aws_ec2(*sub_args)
            elif command == "lambda":
                self._aws_lambda(*sub_args)
            elif command == "rds":
                self._aws_rds(*sub_args)
            elif command == "cloudformation":
                self._aws_cloudformation(*sub_args)
            elif command == "secrets":
                self._aws_secrets(*sub_args)
            else:
                console.error(f"Unknown AWS command: {command}")
                self._aws_help()
        except Exception as e:
            console.error(f"AWS command failed: {e}")

    @handle_errors()
    def _aws_s3(self, *args: str) -> None:
        """Handle AWS S3 commands."""
        if not args:
            console.info("Usage: cloud aws s3 ls|upload|download|cp|sync|rm")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "ls":
            console.info("Listing S3 buckets...")
            result = self._run_aws(["s3", "ls"] + sub_args)
            console.print(result)
        elif command == "upload":
            if len(sub_args) < 2:
                console.error("Usage: cloud aws s3 upload <file> <bucket>")
                return
            console.info(f"Uploading {sub_args[0]} to {sub_args[1]}...")
            self._run_aws(
                ["s3", "cp", sub_args[0], f"s3://{sub_args[1]}"], capture=False
            )
            console.success("Upload complete")
        elif command == "download":
            if len(sub_args) < 2:
                console.error("Usage: cloud aws s3 download <key> <bucket>")
                return
            console.info(f"Downloading s3://{sub_args[1]}/{sub_args[0]}...")
            self._run_aws(
                [
                    "s3",
                    "cp",
                    f"s3://{sub_args[1]}/{sub_args[0]}",
                    sub_args[2] if len(sub_args) > 2 else ".",
                ],
                capture=False,
            )
            console.success("Download complete")
        elif command == "cp":
            self._run_aws(["s3", "cp"] + sub_args, capture=False)
        elif command == "sync":
            console.info("Syncing S3 bucket...")
            self._run_aws(["s3", "sync"] + sub_args, capture=False)
            console.success("Sync complete")
        elif command == "rm":
            console.info("Removing S3 object...")
            self._run_aws(["s3", "rm"] + sub_args, capture=False)
            console.success("Removed")
        else:
            console.error(f"Unknown S3 command: {command}")

    @handle_errors()
    def _aws_ec2(self, *args: str) -> None:
        """Handle AWS EC2 commands."""
        if not args:
            console.info("Usage: cloud aws ec2 list|start|stop|reboot|describe")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing EC2 instances...")
            result = self._run_aws(
                [
                    "ec2",
                    "describe-instances",
                    "--query",
                    "Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0]]",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        elif command == "start":
            if not sub_args:
                console.error("Usage: cloud aws ec2 start <instance-id>")
                return
            console.info(f"Starting EC2 instance {sub_args[0]}...")
            result = self._run_aws(
                ["ec2", "start-instances", "--instance-ids", sub_args[0]]
            )
            console.success("Instance started")
        elif command == "stop":
            if not sub_args:
                console.error("Usage: cloud aws ec2 stop <instance-id>")
                return
            console.warning(f"Stopping EC2 instance {sub_args[0]}...")
            result = self._run_aws(
                ["ec2", "stop-instances", "--instance-ids", sub_args[0]]
            )
            console.success("Instance stopped")
        elif command == "reboot":
            if not sub_args:
                console.error("Usage: cloud aws ec2 reboot <instance-id>")
                return
            console.info(f"Rebooting EC2 instance {sub_args[0]}...")
            self._run_aws(["ec2", "reboot-instances", "--instance-ids", sub_args[0]])
            console.success("Instance rebooted")
        elif command == "describe":
            if not sub_args:
                console.error("Usage: cloud aws ec2 describe <instance-id>")
                return
            console.info(f"Describing EC2 instance {sub_args[0]}...")
            result = self._run_aws(
                ["ec2", "describe-instances", "--instance-ids", sub_args[0]]
            )
            console.print(result)
        else:
            console.error(f"Unknown EC2 command: {command}")

    @handle_errors()
    def _aws_lambda(self, *args: str) -> None:
        """Handle AWS Lambda commands."""
        if not args:
            console.info("Usage: cloud aws lambda list|deploy|invoke|logs")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing Lambda functions...")
            result = self._run_aws(
                [
                    "lambda",
                    "list-functions",
                    "--query",
                    "Functions[*].[FunctionName,Runtime,LastModified,Handler]",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        elif command == "deploy":
            if len(sub_args) < 1:
                console.error(
                    "Usage: cloud aws lambda deploy <function-name> [zip-file]"
                )
                return
            function_name = sub_args[0]
            zip_file = sub_args[1] if len(sub_args) > 1 else None

            console.info(f"Deploying Lambda function: {function_name}")

            if zip_file:
                # Update function code
                self._run_aws(
                    [
                        "lambda",
                        "update-function-code",
                        "--function-name",
                        function_name,
                        "--zip-file",
                        f"fileb://{zip_file}",
                    ],
                    capture=False,
                )

            console.success("Lambda deployed")
        elif command == "invoke":
            if len(sub_args) < 1:
                console.error(
                    "Usage: cloud aws lambda invoke <function-name> [payload]"
                )
                return
            console.info(f"Invoking Lambda function: {sub_args[0]}")
            payload = sub_args[1] if len(sub_args) > 1 else "{}"
            result = self._run_aws(
                [
                    "lambda",
                    "invoke",
                    "--function-name",
                    sub_args[0],
                    "--payload",
                    payload,
                ]
            )
            console.print(result)
        elif command == "logs":
            if not sub_args:
                console.error("Usage: cloud aws lambda logs <function-name>")
                return
            console.info(f"Fetching logs for: {sub_args[0]}")
            result = self._run_aws(
                ["logs", "tail", "/aws/lambda/" + sub_args[0], "--follow"],
                capture=False,
            )
        else:
            console.error(f"Unknown Lambda command: {command}")

    @handle_errors()
    def _aws_rds(self, *args: str) -> None:
        """Handle AWS RDS commands."""
        if not args:
            console.info("Usage: cloud aws rds list|backup|restore|describe")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing RDS instances...")
            result = self._run_aws(
                [
                    "rds",
                    "describe-db-instances",
                    "--query",
                    "DBInstances[*].[DBInstanceIdentifier,DBInstanceClass,Engine,DBInstanceStatus]",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        elif command == "backup":
            if not sub_args:
                console.error("Usage: cloud aws rds backup <db-instance>")
                return
            console.info(f"Creating snapshot for: {sub_args[0]}")
            snapshot_id = f"{sub_args[0]}-snapshot-{self._timestamp()}"
            self._run_aws(
                [
                    "rds",
                    "create-db-snapshot",
                    "--db-instance-identifier",
                    sub_args[0],
                    "--db-snapshot-identifier",
                    snapshot_id,
                ]
            )
            console.success(f"Snapshot created: {snapshot_id}")
        elif command == "restore":
            if len(sub_args) < 2:
                console.error(
                    "Usage: cloud aws rds restore <snapshot-id> <new-instance>"
                )
                return
            console.info(f"Restoring from snapshot: {sub_args[0]}")
            self._run_aws(
                [
                    "rds",
                    "restore-db-instance-from-db-snapshot",
                    "--db-instance-identifier",
                    sub_args[1],
                    "--db-snapshot-identifier",
                    sub_args[0],
                ],
                capture=False,
            )
            console.success(f"Instance restored: {sub_args[1]}")
        elif command == "describe":
            if not sub_args:
                console.error("Usage: cloud aws rds describe <db-instance>")
                return
            console.info(f"Describing RDS instance: {sub_args[0]}")
            result = self._run_aws(
                [
                    "rds",
                    "describe-db-instances",
                    "--db-instance-identifier",
                    sub_args[0],
                ]
            )
            console.print(result)
        else:
            console.error(f"Unknown RDS command: {command}")

    @handle_errors()
    def _aws_cloudformation(self, *args: str) -> None:
        """Handle AWS CloudFormation commands."""
        if not args:
            console.info("Usage: cloud aws cloudformation deploy|list|describe|delete")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "deploy":
            if len(sub_args) < 1:
                console.error(
                    "Usage: cloud aws cloudformation deploy <stack-name> [template]"
                )
                return
            stack_name = sub_args[0]
            template = sub_args[1] if len(sub_args) > 1 else f"{stack_name}.yaml"

            console.info(f"Deploying CloudFormation stack: {stack_name}")
            self._run_aws(
                [
                    "cloudformation",
                    "deploy",
                    "--stack-name",
                    stack_name,
                    "--template-file",
                    template,
                    "--capabilities",
                    "CAPABILITY_IAM",
                ],
                capture=False,
            )
            console.success("Stack deployed")
        elif command == "list":
            console.info("Listing CloudFormation stacks...")
            result = self._run_aws(
                [
                    "cloudformation",
                    "list-stacks",
                    "--query",
                    "StackSummaries[*].[StackName,StackStatus,CreationTime]",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        elif command == "describe":
            if not sub_args:
                console.error("Usage: cloud aws cloudformation describe <stack-name>")
                return
            console.info(f"Describing stack: {sub_args[0]}")
            result = self._run_aws(
                ["cloudformation", "describe-stacks", "--stack-name", sub_args[0]]
            )
            console.print(result)
        elif command == "delete":
            if not sub_args:
                console.error("Usage: cloud aws cloudformation delete <stack-name>")
                return
            console.warning(f"Deleting stack: {sub_args[0]}")
            self._run_aws(
                ["cloudformation", "delete-stack", "--stack-name", sub_args[0]]
            )
            console.success("Stack deletion initiated")
        else:
            console.error(f"Unknown CloudFormation command: {command}")

    @handle_errors()
    def _aws_secrets(self, *args: str) -> None:
        """Handle AWS Secrets Manager commands."""
        if not args:
            console.info("Usage: cloud aws secrets get|list|create|delete")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "get":
            if not sub_args:
                console.error("Usage: cloud aws secrets get <secret-name>")
                return
            console.info(f"Getting secret: {sub_args[0]}")
            result = self._run_aws(
                [
                    "secretsmanager",
                    "get-secret-value",
                    "--secret-id",
                    sub_args[0],
                    "--query",
                    "SecretString",
                    "--output",
                    "text",
                ]
            )
            console.muted(result)
        elif command == "list":
            console.info("Listing secrets...")
            result = self._run_aws(
                [
                    "secretsmanager",
                    "list-secrets",
                    "--query",
                    "SecretList[*].[Name,LastChangedDate]",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        elif command == "create":
            if len(sub_args) < 2:
                console.error("Usage: cloud aws secrets create <name> <value>")
                return
            console.info(f"Creating secret: {sub_args[0]}")
            self._run_aws(
                [
                    "secretsmanager",
                    "create-secret",
                    "--name",
                    sub_args[0],
                    "--secret-string",
                    sub_args[1],
                ]
            )
            console.success("Secret created")
        elif command == "delete":
            if not sub_args:
                console.error("Usage: cloud aws secrets delete <secret-name>")
                return
            console.warning(f"Deleting secret: {sub_args[0]}")
            self._run_aws(
                ["secretsmanager", "delete-secret", "--secret-id", sub_args[0]]
            )
            console.success("Secret deleted")
        else:
            console.error(f"Unknown secrets command: {command}")

    # ========================================================================
    # GCP Commands
    # ========================================================================

    def _handle_gcp(self, *args: str) -> None:
        """Handle GCP commands."""
        if not args:
            self._gcp_help()
            return

        command = args[0]
        sub_args = args[1:]

        try:
            if command == "compute":
                self._gcp_compute(*sub_args)
            elif command == "storage":
                self._gcp_storage(*sub_args)
            elif command == "bigquery":
                self._gcp_bigquery(*sub_args)
            elif command == "pubsub":
                self._gcp_pubsub(*sub_args)
            elif command == "functions":
                self._gcp_functions(*sub_args)
            else:
                console.error(f"Unknown GCP command: {command}")
                self._gcp_help()
        except Exception as e:
            console.error(f"GCP command failed: {e}")

    @handle_errors()
    def _gcp_compute(self, *args: str) -> None:
        """Handle GCP Compute Engine commands."""
        if not args:
            console.info("Usage: cloud gcp compute list|start|stop|describe")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing GCE instances...")
            result = self._run_gcp(
                [
                    "compute",
                    "instances",
                    "list",
                    "--format",
                    "table(name,machineType,status,zone)",
                ]
            )
            console.print(result)
        elif command == "start":
            if not sub_args:
                console.error("Usage: cloud gcp compute start <instance-name> [zone]")
                return
            console.info(f"Starting instance: {sub_args[0]}")
            zone = sub_args[1] if len(sub_args) > 1 else "us-central1-a"
            self._run_gcp(
                ["compute", "instances", "start", sub_args[0], f"--zone={zone}"],
                capture=False,
            )
            console.success("Instance started")
        elif command == "stop":
            if not sub_args:
                console.error("Usage: cloud gcp compute stop <instance-name> [zone]")
                return
            console.warning(f"Stopping instance: {sub_args[0]}")
            zone = sub_args[1] if len(sub_args) > 1 else "us-central1-a"
            self._run_gcp(
                ["compute", "instances", "stop", sub_args[0], f"--zone={zone}"],
                capture=False,
            )
            console.success("Instance stopped")
        elif command == "describe":
            if not sub_args:
                console.error(
                    "Usage: cloud gcp compute describe <instance-name> [zone]"
                )
                return
            console.info(f"Describing instance: {sub_args[0]}")
            zone = sub_args[1] if len(sub_args) > 1 else "us-central1-a"
            result = self._run_gcp(
                ["compute", "instances", "describe", sub_args[0], f"--zone={zone}"]
            )
            console.print(result)
        else:
            console.error(f"Unknown compute command: {command}")

    @handle_errors()
    def _gcp_storage(self, *args: str) -> None:
        """Handle GCP Storage commands."""
        if not args:
            console.info("Usage: cloud gcp storage list|upload|download|ls|cp|rm")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing GCS buckets...")
            result = self._run_gcp(["storage", "ls"])
            console.print(result)
        elif command == "upload":
            if len(sub_args) < 2:
                console.error(
                    "Usage: cloud gcp storage upload <file> <gs://bucket/path>"
                )
                return
            console.info(f"Uploading {sub_args[0]}...")
            self._run_gcp(["storage", "cp", sub_args[0], sub_args[1]], capture=False)
            console.success("Upload complete")
        elif command == "download":
            if len(sub_args) < 2:
                console.error(
                    "Usage: cloud gcp storage download <gs://bucket/path> <local-path>"
                )
                return
            console.info(f"Downloading from GCS...")
            self._run_gcp(["storage", "cp", sub_args[0], sub_args[1]], capture=False)
            console.success("Download complete")
        elif command == "ls":
            if not sub_args:
                console.error("Usage: cloud gcp storage ls <gs://bucket/path>")
                return
            result = self._run_gcp(["storage", "ls", sub_args[0]])
            console.print(result)
        elif command == "cp":
            self._run_gcp(["storage", "cp"] + sub_args, capture=False)
        elif command == "rm":
            if not sub_args:
                console.error("Usage: cloud gcp storage rm <gs://bucket/path>")
                return
            console.warning(f"Removing: {sub_args[0]}")
            self._run_gcp(["storage", "rm", sub_args[0]], capture=False)
            console.success("Removed")
        else:
            console.error(f"Unknown storage command: {command}")

    @handle_errors()
    def _gcp_bigquery(self, *args: str) -> None:
        """Handle GCP BigQuery commands."""
        if not args:
            console.info("Usage: cloud gcp bigquery query|list")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "query":
            if not sub_args:
                console.error('Usage: cloud gcp bigquery query "<sql>"')
                return
            console.info("Executing BigQuery query...")
            sql = " ".join(sub_args)
            result = self._run_gcp(["bq", "query", "--use_legacy_sql=false", sql])
            console.print(result)
        elif command == "list":
            console.info("Listing BigQuery datasets...")
            result = self._run_gcp(["bq", "ls"])
            console.print(result)
        else:
            console.error(f"Unknown BigQuery command: {command}")

    @handle_errors()
    def _gcp_pubsub(self, *args: str) -> None:
        """Handle GCP Pub/Sub commands."""
        if not args:
            console.info("Usage: cloud gcp pubsub list|publish|create|delete")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing Pub/Sub topics...")
            result = self._run_gcp(["pubsub", "topics", "list"])
            console.print(result)
        elif command == "publish":
            if len(sub_args) < 2:
                console.error("Usage: cloud gcp pubsub publish <topic> <message>")
                return
            console.info(f"Publishing to {sub_args[0]}...")
            self._run_gcp(
                ["pubsub", "topics", "publish", sub_args[0], "--message", sub_args[1]]
            )
            console.success("Message published")
        elif command == "create":
            if not sub_args:
                console.error("Usage: cloud gcp pubsub create <topic-name>")
                return
            console.info(f"Creating topic: {sub_args[0]}")
            self._run_gcp(["pubsub", "topics", "create", sub_args[0]])
            console.success("Topic created")
        elif command == "delete":
            if not sub_args:
                console.error("Usage: cloud gcp pubsub delete <topic-name>")
                return
            console.warning(f"Deleting topic: {sub_args[0]}")
            self._run_gcp(["pubsub", "topics", "delete", sub_args[0]])
            console.success("Topic deleted")
        else:
            console.error(f"Unknown Pub/Sub command: {command}")

    @handle_errors()
    def _gcp_functions(self, *args: str) -> None:
        """Handle GCP Cloud Functions commands."""
        if not args:
            console.info("Usage: cloud gcp functions list|deploy|logs|call")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing Cloud Functions...")
            result = self._run_gcp(["functions", "list"])
            console.print(result)
        elif command == "deploy":
            if len(sub_args) < 1:
                console.error(
                    "Usage: cloud gcp functions deploy <name> --source=<source>"
                )
                return
            console.info(f"Deploying function: {sub_args[0]}")
            self._run_gcp(["functions", "deploy"] + sub_args, capture=False)
            console.success("Function deployed")
        elif command == "logs":
            if not sub_args:
                console.error("Usage: cloud gcp functions logs <function-name>")
                return
            console.info(f"Fetching logs for: {sub_args[0]}")
            self._run_gcp(["functions", "logs", "read", sub_args[0], "--limit", "50"])
        elif command == "call":
            if not sub_args:
                console.error("Usage: cloud gcp functions call <function-name> [data]")
                return
            console.info(f"Calling function: {sub_args[0]}")
            data = sub_args[1] if len(sub_args) > 1 else "{}"
            result = self._run_gcp(["functions", "call", sub_args[0], "--data", data])
            console.print(result)
        else:
            console.error(f"Unknown functions command: {command}")

    # ========================================================================
    # Azure Commands
    # ========================================================================

    def _handle_azure(self, *args: str) -> None:
        """Handle Azure commands."""
        if not args:
            self._azure_help()
            return

        command = args[0]
        sub_args = args[1:]

        try:
            if command == "vm":
                self._azure_vm(*sub_args)
            elif command == "function":
                self._azure_function(*sub_args)
            elif command == "storage":
                self._azure_storage(*sub_args)
            elif command == "database":
                self._azure_database(*sub_args)
            elif command == "keyvault":
                self._azure_keyvault(*sub_args)
            else:
                console.error(f"Unknown Azure command: {command}")
                self._azure_help()
        except Exception as e:
            console.error(f"Azure command failed: {e}")

    @handle_errors()
    def _azure_vm(self, *args: str) -> None:
        """Handle Azure VM commands."""
        if not args:
            console.info("Usage: cloud azure vm list|start|stop|scale")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing Azure VMs...")
            result = self._run_azure(
                [
                    "vm",
                    "list",
                    "--query",
                    "[].{Name:name,ResourceGroup:resourceGroup,Location:location,Size:hardwareProfile.vmSize}",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        elif command == "start":
            if not sub_args:
                console.error("Usage: cloud azure vm start <vm-name> [resource-group]")
                return
            console.info(f"Starting VM: {sub_args[0]}")
            rg = sub_args[1] if len(sub_args) > 1 else ""
            self._run_azure(
                ["vm", "start"]
                + (["--resource-group", rg] if rg else [])
                + [sub_args[0]],
                capture=False,
            )
            console.success("VM started")
        elif command == "stop":
            if not sub_args:
                console.error("Usage: cloud azure vm stop <vm-name> [resource-group]")
                return
            console.warning(f"Stopping VM: {sub_args[0]}")
            rg = sub_args[1] if len(sub_args) > 1 else ""
            self._run_azure(
                ["vm", "deallocate"]
                + (["--resource-group", rg] if rg else [])
                + [sub_args[0]],
                capture=False,
            )
            console.success("VM stopped")
        elif command == "scale":
            if len(sub_args) < 2:
                console.error("Usage: cloud azure vm scale <vmss-name> <count>")
                return
            console.info(f"Scaling VMSS to {sub_args[1]} instances...")
            self._run_azure(
                ["vmss", "scale", "-n", sub_args[0], "--new-capacity", sub_args[1]],
                capture=False,
            )
            console.success("Scaling initiated")
        else:
            console.error(f"Unknown VM command: {command}")

    @handle_errors()
    def _azure_function(self, *args: str) -> None:
        """Handle Azure Function commands."""
        if not args:
            console.info("Usage: cloud azure function list|deploy|logs")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing Azure Functions...")
            result = self._run_azure(["functionapp", "list"])
            console.print(result)
        elif command == "deploy":
            if not sub_args:
                console.error(
                    "Usage: cloud azure function deploy <function-name> [zip-file]"
                )
                return
            console.info(f"Deploying function: {sub_args[0]}")
            self._run_azure(
                [
                    "functionapp",
                    "deployment",
                    "source",
                    "config-zip",
                    "-g",
                    "DefaultResourceGroup",
                    "-n",
                    sub_args[0],
                    "--src",
                    sub_args[1] if len(sub_args) > 1 else "function.zip",
                ],
                capture=False,
            )
            console.success("Function deployed")
        elif command == "logs":
            if not sub_args:
                console.error("Usage: cloud azure function logs <function-name>")
                return
            console.info(f"Fetching logs for: {sub_args[0]}")
            self._run_azure(
                ["functionapp", "log", "tail", "-n", sub_args[0]], capture=False
            )
        else:
            console.error(f"Unknown function command: {command}")

    @handle_errors()
    def _azure_storage(self, *args: str) -> None:
        """Handle Azure Storage commands."""
        if not args:
            console.info("Usage: cloud azure storage list|upload|download|ls")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing Azure Storage accounts...")
            result = self._run_azure(["storage", "account", "list"])
            console.print(result)
        elif command == "upload":
            if len(sub_args) < 3:
                console.error(
                    "Usage: cloud azure storage upload <file> <container> <blob>"
                )
                return
            console.info(f"Uploading to Azure Storage...")
            self._run_azure(
                [
                    "storage",
                    "blob",
                    "upload",
                    "--container-name",
                    sub_args[1],
                    "--name",
                    sub_args[2],
                    "--file",
                    sub_args[0],
                ],
                capture=False,
            )
            console.success("Upload complete")
        elif command == "download":
            if len(sub_args) < 3:
                console.error(
                    "Usage: cloud azure storage download <container> <blob> <local-path>"
                )
                return
            console.info(f"Downloading from Azure Storage...")
            self._run_azure(
                [
                    "storage",
                    "blob",
                    "download",
                    "--container-name",
                    sub_args[0],
                    "--name",
                    sub_args[1],
                    "--file",
                    sub_args[2],
                ],
                capture=False,
            )
            console.success("Download complete")
        elif command == "ls":
            if not sub_args:
                console.error("Usage: cloud azure storage ls <container>")
                return
            result = self._run_azure(
                ["storage", "blob", "list", "--container-name", sub_args[0]]
            )
            console.print(result)
        else:
            console.error(f"Unknown storage command: {command}")

    @handle_errors()
    def _azure_database(self, *args: str) -> None:
        """Handle Azure Database commands."""
        if not args:
            console.info("Usage: cloud azure database list|backup")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            console.info("Listing Azure SQL databases...")
            result = self._run_azure(["sql", "db", "list"])
            console.print(result)
        elif command == "backup":
            if not sub_args:
                console.error("Usage: cloud azure database backup <server> <database>")
                return
            console.info(f"Creating backup for: {sub_args[1]}")
            self._run_azure(
                [
                    "sql",
                    "db",
                    "export",
                    "-s",
                    sub_args[0],
                    "-n",
                    sub_args[1],
                    "-g",
                    "DefaultResourceGroup",
                    "-p",
                    f"{sub_args[1]}-backup-{self._timestamp()}.bacpac",
                ]
            )
            console.success("Backup initiated")
        else:
            console.error(f"Unknown database command: {command}")

    @handle_errors()
    def _azure_keyvault(self, *args: str) -> None:
        """Handle Azure KeyVault commands."""
        if not args:
            console.info("Usage: cloud azure keyvault get|list|set")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "get":
            if len(sub_args) < 2:
                console.error(
                    "Usage: cloud azure keyvault get <vault-name> <secret-name>"
                )
                return
            console.info(f"Getting secret from KeyVault: {sub_args[1]}")
            result = self._run_azure(
                [
                    "keyvault",
                    "secret",
                    "show",
                    "--vault-name",
                    sub_args[0],
                    "--name",
                    sub_args[1],
                    "-o",
                    "tsv",
                    "--query",
                    "value",
                ]
            )
            console.muted(result)
        elif command == "list":
            if not sub_args:
                console.error("Usage: cloud azure keyvault list <vault-name>")
                return
            console.info(f"Listing secrets in KeyVault: {sub_args[0]}")
            result = self._run_azure(
                ["keyvault", "secret", "list", "--vault-name", sub_args[0]]
            )
            console.print(result)
        elif command == "set":
            if len(sub_args) < 3:
                console.error(
                    "Usage: cloud azure keyvault set <vault-name> <secret-name> <value>"
                )
                return
            console.info(f"Setting secret in KeyVault: {sub_args[1]}")
            self._run_azure(
                [
                    "keyvault",
                    "secret",
                    "set",
                    "--vault-name",
                    sub_args[0],
                    "--name",
                    sub_args[1],
                    "--value",
                    sub_args[2],
                ]
            )
            console.success("Secret set")
        else:
            console.error(f"Unknown KeyVault command: {command}")

    # ========================================================================
    # Multi-Cloud Commands
    # ========================================================================

    def _handle_multicloud(self, command: str, *args: str) -> None:
        """Handle multi-cloud commands."""
        if command == "deploy":
            self._multicloud_deploy(*args)
        elif command == "cost":
            self._multicloud_cost(*args)
        elif command == "inventory":
            self._multicloud_inventory(*args)

    @handle_errors()
    def _multicloud_deploy(self, *args: str) -> None:
        """Deploy using Terraform across clouds."""
        if not args:
            console.error("Usage: cloud deploy <stack> [vars]")
            return

        stack = args[0]
        console.info(f"Multi-cloud deployment: {stack}")

        # Check for Terraform
        result = self._run_command(["terraform", "version"])
        if result.returncode != 0:
            console.error("Terraform not found. Install it first.")
            return

        console.info("Running terraform apply...")
        self._run_command(["terraform", "init"], capture=False)
        self._run_command(
            ["terraform", "apply", "-auto-approve"] + list(args[1:]), capture=False
        )

        console.success("Deployment complete")

    @handle_errors()
    def _multicloud_cost(self, *args: str) -> None:
        """Analyze cloud costs across providers."""
        console.info("Cloud Cost Analysis")
        console.muted(
            "Note: Requires Cost Explorer (AWS), Billing Export (GCP), Cost Management (Azure)"
        )

        # AWS Cost
        console.rule("AWS")
        try:
            result = self._run_aws(
                [
                    "ce",
                    "get-cost-and-usage",
                    "--time-range",
                    "Start=2024-01-01,End=2024-01-31",
                    "--granularity",
                    "MONTHLY",
                    "--metrics",
                    "BlendedCost",
                ]
            )
            console.print(result)
        except Exception:
            console.muted("Cost Explorer not configured for AWS")

        # Note: GCP and Azure cost analysis would require additional setup
        console.muted("\nGCP/Azure cost: Requires billing export setup")

    @handle_errors()
    def _multicloud_inventory(self, *args: str) -> None:
        """List all resources across clouds."""
        console.info("Multi-Cloud Inventory")

        console.rule("AWS EC2")
        try:
            result = self._run_aws(
                [
                    "ec2",
                    "describe-instances",
                    "--query",
                    "Reservations[].Instances[].[InstanceId,InstanceType,State.Name]",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        except Exception:
            console.muted("No AWS EC2 resources")

        console.rule("GCE Instances")
        try:
            result = self._run_gcp(
                [
                    "compute",
                    "instances",
                    "list",
                    "--format",
                    "table(name,machineType,status)",
                ]
            )
            console.print(result)
        except Exception:
            console.muted("No GCE resources")

        console.rule("Azure VMs")
        try:
            result = self._run_azure(
                [
                    "vm",
                    "list",
                    "--query",
                    "[].{Name:name,Size:hardwareProfile.vmSize}",
                    "--output",
                    "table",
                ]
            )
            console.print(result)
        except Exception:
            console.muted("No Azure VM resources")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _run_aws(self, args: List[str], capture: bool = True) -> str:
        """Run AWS CLI command."""
        cmd = ["aws"] + args
        result = subprocess.run(cmd, capture_output=capture, text=capture, check=False)
        if capture and result.returncode != 0:
            console.error(f"AWS CLI error: {result.stderr}")
        return result.stdout if capture else ""

    def _run_gcp(self, args: List[str], capture: bool = True) -> str:
        """Run GCP CLI command."""
        cmd = ["gcloud"] + args
        result = subprocess.run(cmd, capture_output=capture, text=capture, check=False)
        if capture and result.returncode != 0:
            console.error(f"GCP CLI error: {result.stderr}")
        return result.stdout if capture else ""

    def _run_azure(self, args: List[str], capture: bool = True) -> str:
        """Run Azure CLI command."""
        cmd = ["az"] + args
        result = subprocess.run(cmd, capture_output=capture, text=capture, check=False)
        if capture and result.returncode != 0:
            console.error(f"Azure CLI error: {result.stderr}")
        return result.stdout if capture else ""

    def _run_command(
        self, cmd: List[str], capture: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a generic command."""
        return subprocess.run(cmd, capture_output=capture, text=capture, check=False)

    def _timestamp(self) -> str:
        """Generate timestamp."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d%H%M%S")

    def _show_help(self) -> None:
        """Show general help."""
        rows = [
            [
                "aws <command>",
                "AWS commands (s3, ec2, lambda, rds, cloudformation, secrets)",
            ],
            [
                "gcp <command>",
                "GCP commands (compute, storage, bigquery, pubsub, functions)",
            ],
            [
                "azure <command>",
                "Azure commands (vm, function, storage, database, keyvault)",
            ],
            ["deploy <stack>", "Multi-cloud deployment"],
            ["cost", "Cloud cost analysis"],
            ["inventory", "Multi-cloud resource inventory"],
        ]
        console.table("Cloud Commands", ["Command", "Description"], rows)

    def _aws_help(self) -> None:
        """Show AWS help."""
        rows = [
            ["aws s3 <cmd>", "S3 operations (ls, upload, download, cp, sync, rm)"],
            ["aws ec2 <cmd>", "EC2 operations (list, start, stop, reboot, describe)"],
            ["aws lambda <cmd>", "Lambda operations (list, deploy, invoke, logs)"],
            ["aws rds <cmd>", "RDS operations (list, backup, restore, describe)"],
            [
                "aws cloudformation <cmd>",
                "CloudFormation operations (deploy, list, describe, delete)",
            ],
            ["aws secrets <cmd>", "Secrets Manager (get, list, create, delete)"],
        ]
        console.table("AWS Commands", ["Command", "Description"], rows)

    def _gcp_help(self) -> None:
        """Show GCP help."""
        rows = [
            ["gcp compute <cmd>", "Compute Engine (list, start, stop, describe)"],
            ["gcp storage <cmd>", "Cloud Storage (list, upload, download, ls, cp, rm)"],
            ["gcp bigquery <cmd>", "BigQuery (query, list)"],
            ["gcp pubsub <cmd>", "Pub/Sub (list, publish, create, delete)"],
            ["gcp functions <cmd>", "Cloud Functions (list, deploy, logs, call)"],
        ]
        console.table("GCP Commands", ["Command", "Description"], rows)

    def _azure_help(self) -> None:
        """Show Azure help."""
        rows = [
            ["azure vm <cmd>", "Virtual Machines (list, start, stop, scale)"],
            ["azure function <cmd>", "Azure Functions (list, deploy, logs)"],
            ["azure storage <cmd>", "Storage (list, upload, download, ls)"],
            ["azure database <cmd>", "SQL Database (list, backup)"],
            ["azure keyvault <cmd>", "KeyVault (get, list, set)"],
        ]
        console.table("Azure Commands", ["Command", "Description"], rows)
