#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pydrive2", "python-dotenv", "rich"]
# ///
"""
Upload a docx file to Google Drive and return a shareable link.

Usage:
    uv run upload_to_drive.py --input FILE.docx [--title "Document Title"]

Requirements:
    - GOOGLE_SERVICE_ACCOUNT_JSON environment variable with service account JSON
    - Or a credentials JSON file in the current directory

Example:
    uv run upload_to_drive.py --input proposal.docx --title "Syngenta Proposal"
"""

import argparse
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from rich import print

load_dotenv()


def get_credentials_path():
    """Get credentials from environment or file."""
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if creds_json:
        fpath = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        fpath.write(creds_json)
        fpath.close()
        return fpath.name

    local_creds = Path.cwd() / "credentials.json"
    if local_creds.exists():
        return str(local_creds)

    raise ValueError(
        "No credentials found. Set GOOGLE_SERVICE_ACCOUNT_JSON or provide credentials.json"
    )


def upload_to_drive(input_path: str, title: str | None = None, share: bool = True):
    """Upload a file to Google Drive and return shareable link."""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[red]Error: File not found: {input_path}[/red]")
        return None

    if not title:
        title = input_file.stem

    creds_path = get_credentials_path()
    cleanup_needed = "GOOGLE_SERVICE_ACCOUNT_JSON" in os.environ

    try:
        settings = {
            "client_config_backend": "service",
            "service_config": {"client_json_file_path": creds_path},
        }
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)

        print(f"[blue]Uploading {input_file.name} to Google Drive...[/blue]")

        gfile = drive.CreateFile(
            {
                "title": title,
                "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }
        )
        gfile.SetContentFile(str(input_file))
        gfile.Upload()

        if share:
            gfile.InsertPermission(
                {"type": "anyone", "role": "writer", "value": "anyone"}
            )

        print(f"[green]✓ Uploaded successfully![/green]")
        print(f"[green]Link: {gfile['alternateLink']}[/green]")
        return gfile["alternateLink"]

    finally:
        if cleanup_needed:
            os.unlink(creds_path)


def main():
    parser = argparse.ArgumentParser(description="Upload docx to Google Drive")
    parser.add_argument("--input", "-i", required=True, help="Path to the docx file")
    parser.add_argument("--title", "-t", help="Document title (default: filename)")
    parser.add_argument(
        "--no-share",
        action="store_true",
        help="Don't make the document publicly editable",
    )

    args = parser.parse_args()

    result = upload_to_drive(args.input, args.title, share=not args.no_share)
    return 0 if result else 1


if __name__ == "__main__":
    exit(main())
