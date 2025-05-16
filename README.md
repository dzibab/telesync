# TeleSync

TeleSync is a utility that automatically synchronizes media files from your Telegram Saved Messages to a specified SMB network share. It runs as a scheduled service that connects to Telegram, retrieves your saved media files, and uploads them directly to your SMB share without storing them locally.

## Features

- Automatic synchronization of media files from Telegram Saved Messages
- Direct streaming from Telegram to SMB without using local storage
- Duplicate file detection to prevent redundant uploads
- Support for photos and documents
- Scheduled daily synchronization
- Secure SMB connectivity with credentials

## Prerequisites

- Python 3.10+ with `uv` package manager
- Telegram API credentials (`API_ID` and `API_HASH`)
- SMB/CIFS network share access credentials

## Installation

### 1. Clone the repository

```sh
git clone https://github.com/dzibab/telesync.git
cd telesync
```

### 2. Environment Configuration

Create a `.env` file in the project root with the following variables:

```sh
# Telegram API credentials
# Get these from https://my.telegram.org/apps
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash

# SMB Configuration
SMB_HOST=your_smb_server_ip_or_hostname
SMB_SHARE=your_share_name
SMB_USER=your_username
SMB_PASSWORD=your_password
SMB_PATH=optional/subfolder/path
```

## Running TeleSync

### Initial Setup (First Time Only)

Before running the application in Docker, you must initialize the Telegram session interactively:

1. Ensure your `.env` file contains valid `API_ID` and `API_HASH` values.
2. Install dependencies and run locally:

```sh
pip install uv
uv sync  # Install dependencies
uv run main.py
```

3. Follow the interactive prompts:
   - Enter your phone number (international format)
   - Enter the verification code sent to your Telegram
   - Enter your two-factor authentication password (if enabled)

This creates a `telesync_session.session` file that stores your authenticated session.

### Running with Docker (Recommended)

After the initial authentication:

```sh
docker compose up --build
```

TeleSync will:
- Run immediately when started
- Schedule automatic synchronization daily at 2 AM
- Maintain the session file persistently via Docker volume

### Running Locally (Development)

```sh
uv run main.py
```

## How It Works

1. TeleSync connects to Telegram's API using your credentials
2. It retrieves your Saved Messages containing media
3. For each media file:
   - Checks if the file already exists on the SMB share
   - If not, streams the file directly from Telegram to the SMB share
4. The connection to SMB is maintained throughout the process for efficiency
5. The process repeats on schedule (daily at 2 AM) or can be run manually

## Troubleshooting

- **Authentication Issues**: Delete the `telesync_session.session` file and perform the initial setup again
- **SMB Connection Problems**: Verify your SMB credentials and network connectivity
- **File Permissions**: Ensure the SMB user has write access to the share
