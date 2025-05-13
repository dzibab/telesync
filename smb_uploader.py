"""
SMB file upload functionality for TeleSync application.
"""
import socket

from smb.SMBConnection import SMBConnection

from logger import get_logger
import config

logger = get_logger('smb_uploader')


class SMBUploader:
    """Handles file uploads to SMB/CIFS network shares."""

    @staticmethod
    def upload(local_path, remote_name):
        """
        Upload a file to the configured SMB share.

        Args:
            local_path (str): Path to the local file to upload
            remote_name (str): Filename to use on the remote share

        Returns:
            bool: True if upload was successful, False otherwise
        """
        if not (config.SMB_HOST and config.SMB_SHARE and config.SMB_USER and config.SMB_PASSWORD):
            logger.debug("SMB config not provided, skipping SMB upload.")
            return False

        try:
            client_name = socket.gethostname()
            conn = SMBConnection(
                config.SMB_USER, config.SMB_PASSWORD,
                client_name, config.SMB_HOST,
                domain=config.SMB_DOMAIN, use_ntlm_v2=True
            )

            assert conn.connect(config.SMB_HOST, 139)

            # Clean up SMB_PATH: remove share name if present, and any leading/trailing slashes/spaces
            folder = config.SMB_PATH.strip().lstrip('/').lstrip('\\') if config.SMB_PATH else ''

            if folder.lower().startswith(config.SMB_SHARE.lower() + '/'):
                folder = folder[len(config.SMB_SHARE)+1:]
            elif folder.lower().startswith(config.SMB_SHARE.lower() + '\\'):
                folder = folder[len(config.SMB_SHARE)+1:]
            elif folder.lower() == config.SMB_SHARE.lower():
                folder = ''

            # Recursively create folders if they don't exist
            remote_path = remote_name
            if folder:
                # Split and create each part if needed
                current = ''
                for part in folder.replace('\\', '/').split('/'):
                    if not part:
                        continue
                    current = f"{current}/{part}" if current else part
                    try:
                        conn.listPath(config.SMB_SHARE, current)
                    except Exception:
                        try:
                            conn.createDirectory(config.SMB_SHARE, current)
                            logger.info(f"Created SMB directory: {current}")
                        except Exception as e:
                            logger.error(f"Failed to create SMB directory {current}: {e}")
                            conn.close()
                            return False
                remote_path = f"{folder}/{remote_name}"

            with open(local_path, 'rb') as f:
                conn.storeFile(config.SMB_SHARE, remote_path, f)

            conn.close()
            logger.info(f"Uploaded to SMB: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"SMB upload failed for {remote_name}: {e}")
            return False