#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pydrive2", "rich"]
# ///
"""
Upload a docx file to Google Drive using OAuth2 user authentication.

Usage:
    uv run upload_to_drive.py --input FILE.docx [--title "Document Title"]

On first run, opens a browser for you to log in to Google and authorize.
Saves credentials locally for future use.

Setup:
    1. Go to https://console.cloud.google.com/apis/credentials
    2. Create an OAuth 2.0 Client ID (Desktop app)
    3. Set environment variables:
       export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
       export GOOGLE_CLIENT_SECRET="your-client-secret"

Example:
    uv run upload_to_drive.py --input proposal.docx --title "My Proposal"
"""

import argparse
import os
from pathlib import Path

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from rich import print


def get_credentials_dir():
    """Get or create the credentials directory."""
    creds_dir = Path.home() / ".config" / "markdown-to-docx"
    creds_dir.mkdir(parents=True, exist_ok=True)
    return creds_dir


def authenticate():
    """Authenticate with Google using OAuth2 user flow."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("[red]Error: OAuth client credentials not found.[/red]")
        print("[yellow]Setup instructions:[/yellow]")
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("  2. Create an OAuth 2.0 Client ID (Desktop app)")
        print("  3. Set environment variables:")
        print(
            "     export GOOGLE_CLIENT_ID='your-client-id.apps.googleusercontent.com'"
        )
        print("     export GOOGLE_CLIENT_SECRET='your-client-secret'")
        raise ValueError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")

    creds_dir = get_credentials_dir()

    # Create settings for pydrive2
    import json

    settings = {
        "client_config_backend": "settings",
        "client_config": {
            "client_id": client_id,
            "client_secret": client_secret,
        },
        "save_credentials": True,
        "save_credentials_backend": "file",
        "save_credentials_file": str(creds_dir / "credentials.json"),
        "get_refresh_token": True,
        "oauth_scope": [
            "https://www.googleapis.com/auth/drive.file",
        ],
    }

    settings_file = creds_dir / "settings.yaml"
    with open(settings_file, "w") as f:
        json.dump(settings, f)

    gauth = GoogleAuth(settings_file=str(settings_file))

    # Try to load saved credentials
    gauth.LoadCredentialsFile(str(creds_dir / "credentials.json"))

    if gauth.credentials is None:
        # Authenticate if no valid credentials
        print("[blue]Opening browser for Google login...[/blue]")
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh if expired
        print("[blue]Refreshing Google credentials...[/blue]")
        gauth.Refresh()
    else:
        # Use saved credentials
        gauth.Authorize()

    # Save credentials for next run
    gauth.SaveCredentialsFile(str(creds_dir / "credentials.json"))

    return gauth


def upload_to_drive(input_path: str, title: str | None = None, share: bool = True):
    """Upload a file to Google Drive and return shareable link."""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[red]Error: File not found: {input_path}[/red]")
        return None

    if not title:
        title = input_file.stem

    try:
        gauth = authenticate()
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

    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        return None


def logout():
    """Remove saved credentials."""
    creds_dir = get_credentials_dir()
    creds_file = creds_dir / "credentials.json"
    settings_file = creds_dir / "settings.yaml"

    removed = False
    if creds_file.exists():
        creds_file.unlink()
        removed = True
    if settings_file.exists():
        settings_file.unlink()
        removed = True

    if removed:
        print("[green]Logged out successfully.[/green]")
    else:
        print("[yellow]No saved credentials found.[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="Upload docx to Google Drive")
    parser.add_argument("--input", "-i", help="Path to the docx file")
    parser.add_argument("--title", "-t", help="Document title (default: filename)")
    parser.add_argument(
        "--no-share",
        action="store_true",
        help="Don't make the document publicly editable",
    )
    parser.add_argument(
        "--logout", action="store_true", help="Remove saved Google credentials"
    )

    args = parser.parse_args()

    if args.logout:
        logout()
        return 0

    if not args.input:
        parser.error("--input is required (unless using --logout)")

    result = upload_to_drive(args.input, args.title, share=not args.no_share)
    return 0 if result else 1


if __name__ == "__main__":
    exit(main())
