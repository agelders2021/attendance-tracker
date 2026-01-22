"""
config.py - Configuration Management for Training Attendance Tracker

This module handles loading and saving application configuration
to attendance.json in the user's home folder, and manages backups.
"""

import json
import os
import glob
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path


# Default configuration values
DEFAULT_CONFIG = {
    "primary_storage_folder": "",
    "secondary_backup_folder": "",
    "excel_participation_folder": "",
    "window_geometry": "",
    "last_tab": 0,
    "last_backup_cleanup_date": "",
    "last_email_month": "",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "",
    "sender_email": "",
    "sender_password_encrypted": "",
    "smtp_encryption": "TLS",  # TLS, SSL, or None
}

# Simple XOR encryption key (not highly secure, but obfuscates the password)
_ENCRYPTION_KEY = b'Tr41n1ngTr4ck3r2024!'

def _encrypt_password(password: str) -> str:
    """Encrypt a password using XOR with base64 encoding.
    
    Args:
        password: Plain text password
        
    Returns:
        Base64 encoded encrypted password
    """
    if not password:
        return ""
    import base64
    key = _ENCRYPTION_KEY
    encrypted = bytes([ord(c) ^ key[i % len(key)] for i, c in enumerate(password)])
    return base64.b64encode(encrypted).decode('utf-8')

def _decrypt_password(encrypted: str) -> str:
    """Decrypt a password that was encrypted with _encrypt_password.
    
    Args:
        encrypted: Base64 encoded encrypted password
        
    Returns:
        Plain text password
    """
    if not encrypted:
        return ""
    import base64
    try:
        key = _ENCRYPTION_KEY
        decoded = base64.b64decode(encrypted.encode('utf-8'))
        decrypted = ''.join([chr(b ^ key[i % len(key)]) for i, b in enumerate(decoded)])
        return decrypted
    except Exception:
        return ""


def get_config_path() -> str:
    """Get the path to the configuration file.
    
    Returns:
        Full path to attendance.json in user's home folder
    """
    home_folder = Path.home()
    return str(home_folder / "attendance.json")


def load_config() -> Dict[str, Any]:
    """Load configuration from attendance.json.
    
    Returns:
        Dictionary containing configuration values
    """
    config_path = get_config_path()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            return merged
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to attendance.json.
    
    Args:
        config: Dictionary containing configuration values
        
    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
        
    except IOError as e:
        print(f"Error saving config: {e}")
        return False


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a single configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> bool:
    """Set a single configuration value and save.
    
    Args:
        key: Configuration key
        value: Value to set
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    config[key] = value
    return save_config(config)


# ============================================================
# Backup Functions
# ============================================================

BACKUP_FILENAME_FORMAT = "attendance-backup-{timestamp}.json"
BACKUP_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def get_backup_filename(timestamp: datetime = None) -> str:
    """Generate a backup filename with timestamp.
    
    Args:
        timestamp: Datetime to use, defaults to now
        
    Returns:
        Backup filename
    """
    if timestamp is None:
        timestamp = datetime.now()
    ts_str = timestamp.strftime(BACKUP_TIMESTAMP_FORMAT)
    return f"attendance-backup-{ts_str}.json"


def parse_backup_timestamp(filename: str) -> Optional[datetime]:
    """Parse timestamp from backup filename.
    
    Args:
        filename: Backup filename
        
    Returns:
        Datetime or None if parsing fails
    """
    try:
        # Extract timestamp part: attendance-backup-YYYYMMDD_HHMMSS.json
        basename = os.path.basename(filename)
        if basename.startswith("attendance-backup-") and basename.endswith(".json"):
            ts_str = basename[18:-5]  # Remove prefix and .json
            return datetime.strptime(ts_str, BACKUP_TIMESTAMP_FORMAT)
    except (ValueError, IndexError):
        pass
    return None


def get_backup_files(backup_folder: str) -> List[Tuple[str, datetime]]:
    """Get list of backup files sorted by timestamp (newest first).
    
    Args:
        backup_folder: Path to backup folder
        
    Returns:
        List of (filepath, timestamp) tuples sorted newest first
    """
    if not backup_folder or not os.path.exists(backup_folder):
        return []
        
    pattern = os.path.join(backup_folder, "attendance-backup-*.json")
    files = glob.glob(pattern)
    
    result = []
    for filepath in files:
        timestamp = parse_backup_timestamp(filepath)
        if timestamp:
            result.append((filepath, timestamp))
            
    # Sort by timestamp descending (newest first)
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def get_most_recent_backup(backup_folder: str) -> Optional[Tuple[str, datetime]]:
    """Get the most recent backup file.
    
    Args:
        backup_folder: Path to backup folder
        
    Returns:
        Tuple of (filepath, timestamp) or None if no backups
    """
    backups = get_backup_files(backup_folder)
    return backups[0] if backups else None


def create_backup(backup_folder: str, data: Dict) -> Optional[str]:
    """Create a backup file with the given data.
    
    Args:
        backup_folder: Path to backup folder
        data: Dictionary containing all data to backup
        
    Returns:
        Path to created backup file, or None if failed
    """
    if not backup_folder:
        return None
        
    # Create folder if it doesn't exist
    if not os.path.exists(backup_folder):
        try:
            os.makedirs(backup_folder)
        except OSError:
            return None
            
    filename = get_backup_filename()
    filepath = os.path.join(backup_folder, filename)
    
    try:
        # Add metadata to backup
        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)
        return filepath
        
    except (IOError, TypeError) as e:
        print(f"Error creating backup: {e}")
        return None


def load_backup(filepath: str) -> Optional[Dict]:
    """Load data from a backup file.
    
    Args:
        filepath: Path to backup file
        
    Returns:
        Dictionary containing backup data, or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        return backup_data.get("data", backup_data)
        
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading backup: {e}")
        return None


def get_backup_timestamp_from_file(filepath: str) -> Optional[datetime]:
    """Get the timestamp from inside a backup file.
    
    Args:
        filepath: Path to backup file
        
    Returns:
        Datetime or None if not found
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        ts_str = backup_data.get("backup_timestamp")
        if ts_str:
            return datetime.fromisoformat(ts_str)
    except (IOError, json.JSONDecodeError, ValueError):
        pass
    return None


def get_old_backups(backup_folder: str, months: int = 6) -> List[Tuple[str, datetime]]:
    """Get list of backup files older than specified months.
    
    Args:
        backup_folder: Path to backup folder
        months: Number of months (default 6)
        
    Returns:
        List of (filepath, timestamp) tuples for old backups
    """
    cutoff = datetime.now() - timedelta(days=months * 30)
    backups = get_backup_files(backup_folder)
    
    return [(fp, ts) for fp, ts in backups if ts < cutoff]


def delete_backup(filepath: str) -> bool:
    """Delete a backup file.
    
    Args:
        filepath: Path to backup file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.remove(filepath)
        return True
    except OSError:
        return False


def should_cleanup_backups(last_cleanup_date: str) -> bool:
    """Check if backup cleanup should be performed (once per month).
    
    Args:
        last_cleanup_date: ISO format date string of last cleanup
        
    Returns:
        True if cleanup should be done, False otherwise
    """
    if not last_cleanup_date:
        return True
        
    try:
        last_cleanup = datetime.fromisoformat(last_cleanup_date)
        # Check if it's been at least 30 days
        return (datetime.now() - last_cleanup).days >= 30
    except ValueError:
        return True


class ConfigManager:
    """Class to manage application configuration."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._config: Dict[str, Any] = {}
        self.load()
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        self._config = load_config()
        return self._config
        
    def save(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        return save_config(self._config)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            auto_save: Whether to automatically save after setting
            
        Returns:
            True if successful (or auto_save is False), False otherwise
        """
        self._config[key] = value
        if auto_save:
            return self.save()
        return True
        
    @property
    def primary_storage_folder(self) -> str:
        """Get the primary storage folder path."""
        return self._config.get("primary_storage_folder", "")
        
    @primary_storage_folder.setter
    def primary_storage_folder(self, value: str):
        """Set the primary storage folder path."""
        self._config["primary_storage_folder"] = value
        
    @property
    def secondary_backup_folder(self) -> str:
        """Get the secondary backup folder path."""
        return self._config.get("secondary_backup_folder", "")
        
    @secondary_backup_folder.setter
    def secondary_backup_folder(self, value: str):
        """Set the secondary backup folder path."""
        self._config["secondary_backup_folder"] = value
        
    @property
    def window_geometry(self) -> str:
        """Get the saved window geometry."""
        return self._config.get("window_geometry", "")
        
    @window_geometry.setter
    def window_geometry(self, value: str):
        """Set the window geometry."""
        self._config["window_geometry"] = value
        
    @property
    def last_backup_cleanup_date(self) -> str:
        """Get the last backup cleanup date."""
        return self._config.get("last_backup_cleanup_date", "")
        
    @last_backup_cleanup_date.setter
    def last_backup_cleanup_date(self, value: str):
        """Set the last backup cleanup date."""
        self._config["last_backup_cleanup_date"] = value
        
    @property
    def excel_participation_folder(self) -> str:
        """Get the excel participation folder path."""
        return self._config.get("excel_participation_folder", "")
        
    @excel_participation_folder.setter
    def excel_participation_folder(self, value: str):
        """Set the excel participation folder path."""
        self._config["excel_participation_folder"] = value
        
    @property
    def last_email_month(self) -> str:
        """Get the last month emails were sent."""
        return self._config.get("last_email_month", "")
        
    @last_email_month.setter
    def last_email_month(self, value: str):
        """Set the last month emails were sent."""
        self._config["last_email_month"] = value
        
    @property
    def smtp_server(self) -> str:
        """Get the SMTP server."""
        return self._config.get("smtp_server", "smtp.gmail.com")
        
    @smtp_server.setter
    def smtp_server(self, value: str):
        """Set the SMTP server."""
        self._config["smtp_server"] = value
        
    @property
    def smtp_port(self) -> int:
        """Get the SMTP port."""
        return self._config.get("smtp_port", 587)
        
    @smtp_port.setter
    def smtp_port(self, value: int):
        """Set the SMTP port."""
        self._config["smtp_port"] = value
        
    @property
    def smtp_username(self) -> str:
        """Get the SMTP username."""
        return self._config.get("smtp_username", "")
        
    @smtp_username.setter
    def smtp_username(self, value: str):
        """Set the SMTP username."""
        self._config["smtp_username"] = value
        
    @property
    def sender_email(self) -> str:
        """Get the sender email address."""
        return self._config.get("sender_email", "")
        
    @sender_email.setter
    def sender_email(self, value: str):
        """Set the sender email address."""
        self._config["sender_email"] = value
        
    @property
    def sender_password(self) -> str:
        """Get the sender email password (decrypted)."""
        encrypted = self._config.get("sender_password_encrypted", "")
        return _decrypt_password(encrypted)
        
    @sender_password.setter
    def sender_password(self, value: str):
        """Set the sender email password (encrypts before storing)."""
        self._config["sender_password_encrypted"] = _encrypt_password(value)
        
    @property
    def smtp_encryption(self) -> str:
        """Get the SMTP encryption type (TLS, SSL, or None)."""
        return self._config.get("smtp_encryption", "TLS")
        
    @smtp_encryption.setter
    def smtp_encryption(self, value: str):
        """Set the SMTP encryption type."""
        self._config["smtp_encryption"] = value


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
