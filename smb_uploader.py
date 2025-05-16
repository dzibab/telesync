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

    def __init__(self):
        """Initialize the SMB uploader."""
        self.conn = None
        self.client_name = socket.gethostname()

    def connect(self):
        """
        Establish a connection to the SMB server.

        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not (config.SMB_HOST and config.SMB_SHARE and config.SMB_USER and config.SMB_PASSWORD):
            logger.debug("SMB config not provided, cannot connect.")
            return False

        try:
            self.conn = SMBConnection(
                config.SMB_USER, config.SMB_PASSWORD,
                self.client_name, config.SMB_HOST,
                domain=config.SMB_DOMAIN, use_ntlm_v2=True
            )

            if self.conn.connect(config.SMB_HOST, 139):
                logger.debug("SMB connection established")
                return True
            else:
                logger.error("Failed to connect to SMB server")
                return False
        except Exception as e:
            logger.error(f"SMB connection error: {e}")
            return False

    def close(self):
        """Close the SMB connection if it's open."""
        if self.conn:
            try:
                self.conn.close()
                logger.debug("SMB connection closed")
            except Exception as e:
                logger.error(f"Error closing SMB connection: {e}")
            finally:
                self.conn = None

    def _get_clean_folder_path(self, folder):
        """
        Process and clean the SMB folder path.

        Args:
            folder: The raw folder path to clean

        Returns:
            str: Clean folder path
        """
        folder = folder.strip().lstrip('/').lstrip('\\') if folder else ''

        if folder.lower().startswith(config.SMB_SHARE.lower() + '/'):
            folder = folder[len(config.SMB_SHARE)+1:]
        elif folder.lower().startswith(config.SMB_SHARE.lower() + '\\'):
            folder = folder[len(config.SMB_SHARE)+1:]
        elif folder.lower() == config.SMB_SHARE.lower():
            folder = ''

        return folder

    def _ensure_directory_exists(self, folder):
        """
        Ensures that a directory path exists on the SMB share, creating it if needed.

        Args:
            folder: Path to ensure exists

        Returns:
            bool: True if directory exists or was created, False on failure
        """
        if not folder:
            return True

        # Split and create each part if needed
        current = ''
        for part in folder.replace('\\', '/').split('/'):
            if not part:
                continue
            current = f"{current}/{part}" if current else part
            try:
                self.conn.listPath(config.SMB_SHARE, current)
            except Exception:
                try:
                    self.conn.createDirectory(config.SMB_SHARE, current)
                    logger.info(f"Created SMB directory: {current}")
                except Exception as e:
                    logger.error(f"Failed to create SMB directory {current}: {e}")
                    return False
        return True

    def ensure_connected(self):
        """
        Ensure there is an active connection to the SMB server.
        Attempt to reconnect if the connection is closed.

        Returns:
            bool: True if connection is active, False otherwise
        """
        if self.conn and hasattr(self.conn, 'sock') and self.conn.sock:
            # Connection exists and has an active socket
            return True

        # Try to establish a new connection
        return self.connect()

    def file_exists(self, remote_name):
        """
        Check if a file already exists on the SMB share.

        Args:
            remote_name (str): Filename to check on the remote share

        Returns:
            bool: True if file exists, False otherwise
        """
        if not self.ensure_connected():
            logger.error("No active SMB connection")
            return False

        try:
            folder = self._get_clean_folder_path(config.SMB_PATH)
            remote_path = f"{folder}/{remote_name}" if folder else remote_name

            # Try to get file info - if successful, file exists
            file_info = self.conn.getAttributes(config.SMB_SHARE, remote_path)
            return True
        except Exception as e:
            # File doesn't exist or error occurred
            logger.debug(f"File check for {remote_name}: {str(e)}")
            return False

    def upload_file(self, file_stream, remote_name, check_exists=True):
        """
        Upload a file to the connected SMB share.

        Args:
            file_stream: File-like object to upload
            remote_name (str): Filename to use on the remote share
            check_exists (bool): Whether to check if file already exists before uploading

        Returns:
            bool: True if successful or file already exists, False otherwise
        """
        if not self.ensure_connected():
            logger.error("No active SMB connection")
            return False

        try:
            # Process the path
            folder = self._get_clean_folder_path(config.SMB_PATH)

            # Ensure directories exist
            if not self._ensure_directory_exists(folder):
                return False

            # Build final remote path
            remote_path = f"{folder}/{remote_name}" if folder else remote_name

            # Check if file already exists
            if check_exists and self.file_exists(remote_name):
                logger.info(f"File already exists on SMB: {remote_path}, skipping upload")
                return True

            # Upload the file
            self.conn.storeFile(config.SMB_SHARE, remote_path, file_stream)
            logger.info(f"Uploaded to SMB: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"SMB upload failed for {remote_name}: {e}")
            return False

    def upload_multiple_files(self, file_data_list):
        """
        Upload multiple files in a single SMB connection.

        Args:
            file_data_list: List of (file_stream, remote_name) tuples to upload

        Returns:
            int: Count of successfully uploaded files
        """
        if not self.ensure_connected():
            return 0

        success_count = 0
        try:
            for file_stream, remote_name in file_data_list:
                if self.upload_file(file_stream, remote_name):
                    success_count += 1
        finally:
            self.close()

        return success_count

    @staticmethod
    def upload_from_stream(file_stream, remote_name):
        """
        Upload a file stream to the configured SMB share without saving locally.
        Legacy method maintained for backwards compatibility.

        Args:
            file_stream: File-like object to upload
            remote_name (str): Filename to use on the remote share

        Returns:
            bool: True if upload was successful, False otherwise
        """
        uploader = SMBUploader()

        # Use ensure_connected which will try to connect if needed
        if not uploader.ensure_connected():
            return False

        try:
            # Already checks for duplicates by default
            result = uploader.upload_file(file_stream, remote_name)
            return result
        finally:
            uploader.close()

    @staticmethod
    def upload(local_path, remote_name):
        """
        Upload a file to the configured SMB share.
        Legacy method maintained for backwards compatibility.

        Args:
            local_path (str): Path to the local file to upload
            remote_name (str): Filename to use on the remote share

        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            with open(local_path, 'rb') as f:
                return SMBUploader.upload_from_stream(f, remote_name)
        except Exception as e:
            logger.error(f"SMB upload failed for {remote_name}: {e}")
            return False