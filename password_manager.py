"""
SPDX-License-Identifier: GPL-3.0-or-later

Copyright (C) 2026 Al Gelders

This file is part of the airscenting an trailing logging programs

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""
Password encryption utilities for Air-Scenting Logger
Uses Fernet symmetric encryption with machine-specific key
"""
import base64
import hashlib
import os
from pathlib import Path
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("WARNING: cryptography library not installed. Password encryption disabled.")
    print("Install with: pip install cryptography")


def get_machine_key():
    """
    Generate a machine-specific encryption key
    Uses username + machine name to create unique key per machine
    """
    if not CRYPTO_AVAILABLE:
        return None
    
    try:
        # Get machine-specific identifiers
        import getpass
        import socket
        
        username = getpass.getuser()
        hostname = socket.gethostname()
        
        # Combine identifiers
        machine_id = f"{username}@{hostname}".encode()
        
        # Generate key using SHA256 hash
        key_material = hashlib.sha256(machine_id).digest()
        
        # Fernet requires 32 bytes base64-encoded
        key = base64.urlsafe_b64encode(key_material)
        
        return key
    except Exception as e:
        print(f"Error generating machine key: {e}")
        return None


def encrypt_password(password):
    """
    Encrypt a password using machine-specific key
    
    Args:
        password (str): Plain text password
    
    Returns:
        str: Encrypted password (base64 string) or None if encryption fails
    """
    if not CRYPTO_AVAILABLE:
        return None
    
    if not password:
        return None
    
    try:
        key = get_machine_key()
        if not key:
            return None
        
        f = Fernet(key)
        encrypted = f.encrypt(password.encode())
        
        # Return as string for JSON storage
        return encrypted.decode()
    except Exception as e:
        print(f"Error encrypting password: {e}")
        return None


def decrypt_password(encrypted_password):
    """
    Decrypt a password using machine-specific key
    
    Args:
        encrypted_password (str): Encrypted password (base64 string)
    
    Returns:
        str: Decrypted password or None if decryption fails
    """
    if not CRYPTO_AVAILABLE:
        return None
    
    if not encrypted_password:
        return None
    
    try:
        key = get_machine_key()
        if not key:
            return None
        
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        
        return decrypted.decode()
    except Exception as e:
        print(f"Error decrypting password: {e}")
        return None


def save_encrypted_password(config, db_type, password):
    """
    Encrypt and save password to config dictionary
    
    Args:
        config (dict): Configuration dictionary
        db_type (str): Database type ('postgres' or 'supabase')
        password (str): Plain text password to encrypt and save
    
    Returns:
        bool: True if successful, False otherwise
    """
    encrypted = encrypt_password(password)
    if encrypted:
        if 'encrypted_db_passwords' not in config:
            config['encrypted_db_passwords'] = {}
        config['encrypted_db_passwords'][db_type] = encrypted
        return True
    return False


def get_decrypted_password(config, db_type):
    """
    Retrieve and decrypt password from config
    
    Args:
        config (dict): Configuration dictionary
        db_type (str): Database type ('postgres' or 'supabase')
    
    Returns:
        str: Decrypted password or None if not found or decryption fails
    """
    if 'encrypted_db_passwords' not in config:
        return None
    
    encrypted = config['encrypted_db_passwords'].get(db_type)
    if not encrypted:
        return None
    
    return decrypt_password(encrypted)


def clear_saved_password(config, db_type):
    """
    Remove saved password from config
    
    Args:
        config (dict): Configuration dictionary
        db_type (str): Database type ('postgres' or 'supabase')
    """
    if 'encrypted_db_passwords' in config:
        if db_type in config['encrypted_db_passwords']:
            del config['encrypted_db_passwords'][db_type]


def check_crypto_available():
    """
    Check if cryptography library is available
    
    Returns:
        bool: True if available, False otherwise
    """
    return CRYPTO_AVAILABLE
