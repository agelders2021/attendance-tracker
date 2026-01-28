"""
SPDX-License-Identifier: GPL-3.0-or-later

Copyright (C) 2026 Al Gelders

This file is part of the attendance logging program

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
database.py - SQLite Database Module for Training Attendance Tracker

This module handles all database operations including initialization,
CRUD operations for members, sessions, attendance, and training locations.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Any


# Date format used throughout the application
DATE_FORMAT = "%m/%d/%Y"


class DatabaseManager:
    """Manages SQLite database operations for the training tracker."""
    
    def __init__(self, db_path: str = None):
        """Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        
    def set_db_path(self, db_path: str):
        """Set the database path.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        
    def get_db_path(self) -> Optional[str]:
        """Get the current database path.
        
        Returns:
            The database path or None if not set
        """
        return self.db_path
        
    def database_exists(self) -> bool:
        """Check if the database file exists.
        
        Returns:
            True if database file exists, False otherwise
        """
        if not self.db_path:
            return False
        return os.path.exists(self.db_path)
        
    def connect(self) -> sqlite3.Connection:
        """Connect to the database.
        
        Returns:
            SQLite connection object
            
        Raises:
            ValueError: If db_path is not set
        """
        if not self.db_path:
            raise ValueError("Database path not set")
            
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        # Ensure all tables exist (for databases created before updates)
        self._ensure_tables_exist()
        
        return self.connection
        
    def _ensure_tables_exist(self):
        """Ensure all required tables exist (for backward compatibility)."""
        if not self.connection:
            return
            
        cursor = self.connection.cursor()
        
        # Check and create certification_types table if missing
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='certification_types'
        """)
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certification_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    certification_name TEXT NOT NULL UNIQUE,
                    sort_order INTEGER DEFAULT 0
                )
            ''')
            
            # Insert default certification types
            default_certs = [
                "Pack Check",
                "On-line Base Medical",
                "Crime Scene Preservation",
                "Blood-borne Pathogens",
                "NM SAR Field Certification",
                "Fitness Hike 1",
                "Fitness Hike 2",
                "Fitness Hike 3",
            ]
            for i, cert in enumerate(default_certs):
                cursor.execute(
                    "INSERT OR IGNORE INTO certification_types (certification_name, sort_order) VALUES (?, ?)",
                    (cert, i)
                )
            self.connection.commit()
        
        # Check if attendance table has updated_at column, add if missing
        cursor.execute("PRAGMA table_info(attendance)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'updated_at' not in columns:
            try:
                # SQLite doesn't allow non-constant defaults in ALTER TABLE, so use NULL
                cursor.execute("ALTER TABLE attendance ADD COLUMN updated_at TEXT")
                self.connection.commit()
            except sqlite3.Error:
                pass  # Column might already exist or table doesn't exist yet
        
        # Check if members table has member_status column, add if missing
        cursor.execute("PRAGMA table_info(members)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'member_status' not in columns:
            try:
                cursor.execute("ALTER TABLE members ADD COLUMN member_status TEXT DEFAULT 'Member'")
                self.connection.commit()
            except sqlite3.Error:
                pass  # Column might already exist or table doesn't exist yet
        
        # Check if members table has member_role column, add if missing
        cursor.execute("PRAGMA table_info(members)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'member_role' not in columns:
            try:
                cursor.execute("ALTER TABLE members ADD COLUMN member_role TEXT DEFAULT 'None'")
                self.connection.commit()
            except sqlite3.Error:
                pass  # Column might already exist or table doesn't exist yet
        
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection.
        
        Returns:
            SQLite connection object
        """
        if self.connection is None:
            self.connect()
        return self.connection
        
    # ============================================================
    # Database Initialization
    # ============================================================
    
    def initialize_database(self, replace_existing: bool = False) -> bool:
        """Initialize the database with all required tables.
        
        Args:
            replace_existing: If True, delete existing database first
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_path:
            raise ValueError("Database path not set")
            
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        # Handle existing database
        if self.database_exists():
            if replace_existing:
                self.close()
                os.remove(self.db_path)
            else:
                return False
                
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Create Members table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    address TEXT,
                    cell_phone TEXT,
                    home_phone TEXT,
                    email TEXT,
                    alternate_email TEXT,
                    emergency_contact_name TEXT,
                    emergency_contact_phone TEXT,
                    ham_callsign TEXT,
                    mission_eligible INTEGER DEFAULT 0,
                    member_status TEXT DEFAULT 'Member',
                    member_role TEXT DEFAULT 'None',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(first_name, last_name)
                )
            ''')
            
            # Create Certifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    certification_name TEXT NOT NULL,
                    date_completed TEXT,
                    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
                    UNIQUE(member_id, certification_name)
                )
            ''')
            
            # Create Training Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    session_date TEXT NOT NULL,
                    session_type TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(location, session_date)
                )
            ''')
            
            # Create Attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    member_id INTEGER NOT NULL,
                    attended INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES training_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
                    UNIQUE(session_id, member_id)
                )
            ''')
            
            # Create Training Locations table (for default locations)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT NOT NULL UNIQUE
                )
            ''')
            
            # Create Users table (for the user dropdown)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create Certification Types table (for configurable certifications)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certification_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    certification_name TEXT NOT NULL UNIQUE,
                    sort_order INTEGER DEFAULT 0
                )
            ''')
            
            # Insert default user if none exists
            cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", ("default",))
            
            # Insert default certification types
            default_certs = [
                "Pack Check",
                "On-line Base Medical",
                "Crime Scene Preservation",
                "Blood-borne Pathogens",
                "NM SAR Field Certification",
                "Fitness Hike 1",
                "Fitness Hike 2",
                "Fitness Hike 3",
            ]
            for i, cert in enumerate(default_certs):
                cursor.execute(
                    "INSERT OR IGNORE INTO certification_types (certification_name, sort_order) VALUES (?, ?)",
                    (cert, i)
                )
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            return False
            
    # ============================================================
    # Training Locations Operations
    # ============================================================
    
    def add_training_location(self, location_name: str) -> bool:
        """Add a training location.
        
        Args:
            location_name: Name of the location
            
        Returns:
            True if successful, False if already exists or error
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO training_locations (location_name) VALUES (?)",
                (location_name.strip(),)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists
        except sqlite3.Error as e:
            print(f"Error adding training location: {e}")
            return False
            
    def remove_training_location(self, location_name: str) -> bool:
        """Remove a training location.
        
        Args:
            location_name: Name of the location to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM training_locations WHERE location_name = ?",
                (location_name,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error removing training location: {e}")
            return False
            
    def get_training_locations(self) -> List[str]:
        """Get all training locations.
        
        Returns:
            List of location names sorted alphabetically
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT location_name FROM training_locations ORDER BY location_name")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting training locations: {e}")
            return []
            
    # ============================================================
    # Member Operations
    # ============================================================
    
    def save_member(self, member_data: Dict) -> Tuple[bool, int, str]:
        """Save a member (insert or update).
        
        Args:
            member_data: Dictionary containing member fields
            
        Returns:
            Tuple of (success, member_id, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            member_id = member_data.get('id', -1)
            first_name = member_data.get('first_name', '').strip()
            last_name = member_data.get('last_name', '').strip()
            
            if not first_name or not last_name:
                return False, -1, "First name and last name are required"
                
            if member_id > 0:
                # Update existing member
                cursor.execute('''
                    UPDATE members SET
                        first_name = ?,
                        last_name = ?,
                        address = ?,
                        cell_phone = ?,
                        home_phone = ?,
                        email = ?,
                        alternate_email = ?,
                        emergency_contact_name = ?,
                        emergency_contact_phone = ?,
                        ham_callsign = ?,
                        mission_eligible = ?,
                        member_status = ?,
                        member_role = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    first_name,
                    last_name,
                    member_data.get('address', ''),
                    member_data.get('cell_phone', ''),
                    member_data.get('home_phone', ''),
                    member_data.get('email', ''),
                    member_data.get('alternate_email', ''),
                    member_data.get('emergency_contact_name', ''),
                    member_data.get('emergency_contact_phone', ''),
                    member_data.get('ham_callsign', ''),
                    1 if member_data.get('mission_eligible', False) else 0,
                    member_data.get('member_status', 'Member'),
                    member_data.get('member_role', 'None'),
                    member_id
                ))
                conn.commit()
                message = "Member updated successfully"
            else:
                # Check if member already exists by name
                cursor.execute(
                    "SELECT id FROM members WHERE first_name = ? AND last_name = ?",
                    (first_name, last_name)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing member found by name
                    member_id = existing[0]
                    cursor.execute('''
                        UPDATE members SET
                            address = ?,
                            cell_phone = ?,
                            home_phone = ?,
                            email = ?,
                            alternate_email = ?,
                            emergency_contact_name = ?,
                            emergency_contact_phone = ?,
                            ham_callsign = ?,
                            mission_eligible = ?,
                            member_status = ?,
                            member_role = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        member_data.get('address', ''),
                        member_data.get('cell_phone', ''),
                        member_data.get('home_phone', ''),
                        member_data.get('email', ''),
                        member_data.get('alternate_email', ''),
                        member_data.get('emergency_contact_name', ''),
                        member_data.get('emergency_contact_phone', ''),
                        member_data.get('ham_callsign', ''),
                        1 if member_data.get('mission_eligible', False) else 0,
                        member_data.get('member_status', 'Member'),
                        member_data.get('member_role', 'None'),
                        member_id
                    ))
                    conn.commit()
                    message = "Existing member updated successfully"
                else:
                    # Insert new member
                    cursor.execute('''
                        INSERT INTO members (
                            first_name, last_name, address, cell_phone, home_phone,
                            email, alternate_email, emergency_contact_name,
                            emergency_contact_phone, ham_callsign, mission_eligible, member_status, member_role
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        first_name,
                        last_name,
                        member_data.get('address', ''),
                        member_data.get('cell_phone', ''),
                        member_data.get('home_phone', ''),
                        member_data.get('email', ''),
                        member_data.get('alternate_email', ''),
                        member_data.get('emergency_contact_name', ''),
                        member_data.get('emergency_contact_phone', ''),
                        member_data.get('ham_callsign', ''),
                        1 if member_data.get('mission_eligible', False) else 0,
                        member_data.get('member_status', 'Member'),
                        member_data.get('member_role', 'None')
                    ))
                    member_id = cursor.lastrowid
                    conn.commit()
                    message = "New member added successfully"
                    
            # Save certifications
            self._save_member_certifications(member_id, member_data.get('certifications', {}))
            
            return True, member_id, message
            
        except sqlite3.Error as e:
            return False, -1, f"Database error: {e}"
            
    def _save_member_certifications(self, member_id: int, certifications: Dict[str, str]):
        """Save member certifications.
        
        Args:
            member_id: ID of the member
            certifications: Dictionary of certification_name -> date_completed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for cert_name, date_completed in certifications.items():
                cursor.execute('''
                    INSERT INTO certifications (member_id, certification_name, date_completed)
                    VALUES (?, ?, ?)
                    ON CONFLICT(member_id, certification_name) 
                    DO UPDATE SET date_completed = excluded.date_completed
                ''', (member_id, cert_name, date_completed))
                
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving certifications: {e}")
            
    def delete_member(self, member_id: int) -> Tuple[bool, str]:
        """Delete a member.
        
        Args:
            member_id: ID of the member to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete certifications first (should cascade, but being explicit)
            cursor.execute("DELETE FROM certifications WHERE member_id = ?", (member_id,))
            
            # Delete attendance records
            cursor.execute("DELETE FROM attendance WHERE member_id = ?", (member_id,))
            
            # Delete member
            cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Member deleted successfully"
            else:
                return False, "Member not found"
                
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
            
    def get_member(self, member_id: int) -> Optional[Dict]:
        """Get a member by ID.
        
        Args:
            member_id: ID of the member
            
        Returns:
            Member dictionary or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
            row = cursor.fetchone()
            
            if row:
                member = dict(row)
                member['mission_eligible'] = bool(member['mission_eligible'])
                # Ensure member_status has a default value
                if 'member_status' not in member or member['member_status'] is None:
                    member['member_status'] = 'Member'
                # Ensure member_role has a default value
                if 'member_role' not in member or member['member_role'] is None:
                    member['member_role'] = 'None'
                member['certifications'] = self._get_member_certifications(member_id)
                return member
            return None
            
        except sqlite3.Error as e:
            print(f"Error getting member: {e}")
            return None
            
    def get_member_by_name(self, first_name: str, last_name: str) -> Optional[Dict]:
        """Get a member by name.
        
        Args:
            first_name: Member's first name
            last_name: Member's last name
            
        Returns:
            Member dictionary or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM members WHERE first_name = ? AND last_name = ?",
                (first_name.strip(), last_name.strip())
            )
            row = cursor.fetchone()
            
            if row:
                member = dict(row)
                member['mission_eligible'] = bool(member['mission_eligible'])
                # Ensure member_status has a default value
                if 'member_status' not in member or member['member_status'] is None:
                    member['member_status'] = 'Member'
                # Ensure member_role has a default value
                if 'member_role' not in member or member['member_role'] is None:
                    member['member_role'] = 'None'
                member['certifications'] = self._get_member_certifications(member['id'])
                return member
            return None
            
        except sqlite3.Error as e:
            print(f"Error getting member by name: {e}")
            return None
            
    def _get_member_certifications(self, member_id: int) -> Dict[str, str]:
        """Get certifications for a member.
        
        Args:
            member_id: ID of the member
            
        Returns:
            Dictionary of certification_name -> date_completed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT certification_name, date_completed FROM certifications WHERE member_id = ?",
                (member_id,)
            )
            return {row[0]: row[1] or "" for row in cursor.fetchall()}
            
        except sqlite3.Error as e:
            print(f"Error getting certifications: {e}")
            return {}
            
    def get_all_members(self) -> List[Dict]:
        """Get all members.
        
        Returns:
            List of member dictionaries sorted by last name
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM members ORDER BY last_name, first_name")
            members = []
            
            for row in cursor.fetchall():
                member = dict(row)
                member['mission_eligible'] = bool(member['mission_eligible'])
                # Ensure member_status has a default value
                if 'member_status' not in member or member['member_status'] is None:
                    member['member_status'] = 'Member'
                # Ensure member_role has a default value
                if 'member_role' not in member or member['member_role'] is None:
                    member['member_role'] = 'None'
                member['certifications'] = self._get_member_certifications(member['id'])
                members.append(member)
                
            return members
            
        except sqlite3.Error as e:
            print(f"Error getting all members: {e}")
            return []
            
    def get_unique_last_names(self) -> List[str]:
        """Get unique last names for the combobox.
        
        Returns:
            List of unique last names sorted alphabetically
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT last_name FROM members ORDER BY last_name")
            return [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error getting last names: {e}")
            return []
            
    # ============================================================
    # Training Session Operations
    # ============================================================
    
    def save_session(self, session_data: Dict) -> Tuple[bool, int, str]:
        """Save a training session (insert or update).
        
        Args:
            session_data: Dictionary containing session fields
            
        Returns:
            Tuple of (success, session_id, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            session_id = session_data.get('id', -1)
            location = session_data.get('location', '').strip()
            session_date = session_data.get('date', '').strip()
            session_type = session_data.get('type', 'Weekend Training')
            description = session_data.get('description', '')
            
            if not location or not session_date:
                return False, -1, "Location and date are required"
                
            if session_id > 0:
                # Update existing session
                cursor.execute('''
                    UPDATE training_sessions SET
                        location = ?,
                        session_date = ?,
                        session_type = ?,
                        description = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (location, session_date, session_type, description, session_id))
                conn.commit()
                
                # Verify the update was successful
                if cursor.rowcount == 0:
                    return False, session_id, f"No session found with id {session_id}"
                    
                message = "Session updated successfully"
            else:
                # Check if session already exists
                cursor.execute(
                    "SELECT id FROM training_sessions WHERE location = ? AND session_date = ?",
                    (location, session_date)
                )
                existing = cursor.fetchone()
                
                if existing:
                    session_id = existing[0]
                    cursor.execute('''
                        UPDATE training_sessions SET
                            session_type = ?,
                            description = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (session_type, description, session_id))
                    conn.commit()
                    message = "Existing session updated successfully"
                else:
                    # Insert new session
                    cursor.execute('''
                        INSERT INTO training_sessions (location, session_date, session_type, description)
                        VALUES (?, ?, ?, ?)
                    ''', (location, session_date, session_type, description))
                    session_id = cursor.lastrowid
                    conn.commit()
                    
                    # Initialize attendance records for all members
                    self._initialize_attendance_for_session(session_id)
                    message = "New session added successfully"
                    
            return True, session_id, message
            
        except sqlite3.Error as e:
            return False, -1, f"Database error: {e}"
            
    def _initialize_attendance_for_session(self, session_id: int):
        """Initialize attendance records for all members for a session.
        
        Args:
            session_id: ID of the session
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all member IDs
            cursor.execute("SELECT id FROM members")
            member_ids = [row[0] for row in cursor.fetchall()]
            
            # Insert attendance records (default to not attended)
            for member_id in member_ids:
                cursor.execute('''
                    INSERT OR IGNORE INTO attendance (session_id, member_id, attended)
                    VALUES (?, ?, 0)
                ''', (session_id, member_id))
                
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error initializing attendance: {e}")
            
    def delete_session(self, session_id: int) -> Tuple[bool, str]:
        """Delete a training session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete attendance records first
            cursor.execute("DELETE FROM attendance WHERE session_id = ?", (session_id,))
            
            # Delete session
            cursor.execute("DELETE FROM training_sessions WHERE id = ?", (session_id,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Session deleted successfully"
            else:
                return False, "Session not found"
                
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
            
    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get a session by ID.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session dictionary or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM training_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                session = dict(row)
                session['date'] = session.pop('session_date')
                session['type'] = session.pop('session_type')
                return session
            return None
            
        except sqlite3.Error as e:
            print(f"Error getting session: {e}")
            return None
            
    def get_session_by_date_location(self, session_date: str, location: str) -> Optional[Dict]:
        """Get a session by date and location.
        
        Args:
            session_date: Session date
            location: Session location
            
        Returns:
            Session dictionary or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM training_sessions WHERE session_date = ? AND location = ?",
                (session_date, location)
            )
            row = cursor.fetchone()
            
            if row:
                session = dict(row)
                session['date'] = session.pop('session_date')
                session['type'] = session.pop('session_type')
                return session
            return None
            
        except sqlite3.Error as e:
            print(f"Error getting session: {e}")
            return None
            
    def get_all_sessions(self) -> List[Dict]:
        """Get all training sessions.
        
        Returns:
            List of session dictionaries sorted by date descending
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM training_sessions ORDER BY session_date DESC")
            sessions = []
            
            for row in cursor.fetchall():
                session = dict(row)
                session['date'] = session.pop('session_date')
                session['type'] = session.pop('session_type')
                sessions.append(session)
                
            return sessions
            
        except sqlite3.Error as e:
            print(f"Error getting all sessions: {e}")
            return []
            
    def get_sessions_by_date(self, session_date: str) -> List[Dict]:
        """Get all sessions on a specific date.
        
        Args:
            session_date: Session date
            
        Returns:
            List of session dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM training_sessions WHERE session_date = ?",
                (session_date,)
            )
            sessions = []
            
            for row in cursor.fetchall():
                session = dict(row)
                session['date'] = session.pop('session_date')
                session['type'] = session.pop('session_type')
                sessions.append(session)
                
            return sessions
            
        except sqlite3.Error as e:
            print(f"Error getting sessions by date: {e}")
            return []
            
    # ============================================================
    # Attendance Operations
    # ============================================================
    
    def update_attendance(self, session_id: int, member_id: int, attended: bool) -> bool:
        """Update attendance for a member at a session.
        
        Args:
            session_id: ID of the session
            member_id: ID of the member
            attended: Whether the member attended
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Try with updated_at column first
            try:
                cursor.execute('''
                    INSERT INTO attendance (session_id, member_id, attended, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(session_id, member_id)
                    DO UPDATE SET attended = excluded.attended, updated_at = CURRENT_TIMESTAMP
                ''', (session_id, member_id, 1 if attended else 0))
            except sqlite3.OperationalError as e:
                if "no column named updated_at" in str(e):
                    # Column doesn't exist, add it (with NULL default, SQLite limitation)
                    cursor.execute("ALTER TABLE attendance ADD COLUMN updated_at TEXT")
                    conn.commit()
                    # Retry the insert
                    cursor.execute('''
                        INSERT INTO attendance (session_id, member_id, attended, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(session_id, member_id)
                        DO UPDATE SET attended = excluded.attended, updated_at = CURRENT_TIMESTAMP
                    ''', (session_id, member_id, 1 if attended else 0))
                else:
                    raise
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error updating attendance: {e}")
            return False
            
    def get_session_attendance(self, session_id: int) -> Dict[int, bool]:
        """Get attendance for all members at a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary of member_id -> attended (bool)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT member_id, attended FROM attendance WHERE session_id = ?",
                (session_id,)
            )
            return {row[0]: bool(row[1]) for row in cursor.fetchall()}
            
        except sqlite3.Error as e:
            print(f"Error getting session attendance: {e}")
            return {}
            
    def get_attendance_status(self, session_id: int, member_id: int) -> bool:
        """Get attendance status for a specific member at a specific session.
        
        Args:
            session_id: ID of the session
            member_id: ID of the member
            
        Returns:
            True if member attended, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT attended FROM attendance WHERE session_id = ? AND member_id = ?",
                (session_id, member_id)
            )
            row = cursor.fetchone()
            return bool(row[0]) if row else False
            
        except sqlite3.Error as e:
            print(f"Error getting attendance status: {e}")
            return False
            
    def get_weekend_attendance_count(self, member_id: int, months: int = 6) -> int:
        """Get count of weekend training sessions attended by a member in the last N months.
        
        Args:
            member_id: ID of the member
            months: Number of months to look back (default 6)
            
        Returns:
            Count of weekend training sessions attended
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            
            # We need to filter by date in Python since date format is MM/DD/YYYY
            # Check for both old and new session type names
            cursor.execute('''
                SELECT ts.session_date FROM attendance a
                JOIN training_sessions ts ON a.session_id = ts.id
                WHERE a.member_id = ?
                AND a.attended = 1
                AND (ts.session_type = 'Weekend Training' OR ts.session_type = 'Qualifying Training')
            ''', (member_id,))
            
            count = 0
            for row in cursor.fetchall():
                try:
                    session_date = datetime.strptime(row[0], DATE_FORMAT)
                    if session_date >= cutoff_date:
                        count += 1
                except (ValueError, TypeError):
                    continue
                    
            return count
            
        except sqlite3.Error as e:
            print(f"Error getting weekend attendance count: {e}")
            return 0
            
    def get_member_attendance_summary(self, session_id: int) -> List[Dict]:
        """Get attendance summary for all members for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of dictionaries with member info and attendance
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all members with their attendance for this session
            cursor.execute('''
                SELECT m.id, m.first_name, m.last_name, m.member_status,
                       COALESCE(a.attended, 0) as attended
                FROM members m
                LEFT JOIN attendance a ON m.id = a.member_id AND a.session_id = ?
                ORDER BY m.last_name, m.first_name
            ''', (session_id,))
            
            results = []
            for row in cursor.fetchall():
                member_id = row[0]
                # Commented out weekend_count as per requirements
                # weekend_count = self.get_weekend_attendance_count(member_id)
                member_status = row[3] if row[3] else 'Member'
                results.append({
                    'id': member_id,
                    'first_name': row[1],
                    'last_name': row[2],
                    'member_status': member_status,
                    'attended': bool(row[4]),
                    # 'weekend_count': weekend_count  # Commented out
                })
                
            return results
            
        except sqlite3.Error as e:
            print(f"Error getting attendance summary: {e}")
            return []
            
    # ============================================================
    # User Operations
    # ============================================================
    
    def get_users(self) -> List[str]:
        """Get all users.
        
        Returns:
            List of usernames
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT username FROM users ORDER BY username")
            return [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error getting users: {e}")
            return []
            
    def add_user(self, username: str) -> bool:
        """Add a new user.
        
        Args:
            username: Username to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            return False  # Already exists
        except sqlite3.Error as e:
            print(f"Error adding user: {e}")
            return False
            
    # ============================================================
    # Certification Types Operations
    # ============================================================
    
    def get_certification_types(self) -> List[str]:
        """Get all certification types.
        
        Returns:
            List of certification type names
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT certification_name FROM certification_types ORDER BY sort_order, certification_name")
            return [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error getting certification types: {e}")
            # Return default list if table doesn't exist
            return [
                "Pack Check",
                "On-line Base Medical",
                "Crime Scene Preservation",
                "Blood-borne Pathogens",
                "NM SAR Field Certification",
                "Fitness Hike 1",
                "Fitness Hike 2",
                "Fitness Hike 3",
            ]
            
    def add_certification_type(self, cert_name: str) -> bool:
        """Add a certification type.
        
        Args:
            cert_name: Name of the certification
            
        Returns:
            True if successful, False if already exists or error
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get max sort_order
            cursor.execute("SELECT MAX(sort_order) FROM certification_types")
            max_order = cursor.fetchone()[0] or 0
            
            cursor.execute(
                "INSERT INTO certification_types (certification_name, sort_order) VALUES (?, ?)",
                (cert_name.strip(), max_order + 1)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists
        except sqlite3.Error as e:
            print(f"Error adding certification type: {e}")
            return False
            
    def remove_certification_type(self, cert_name: str) -> bool:
        """Remove a certification type.
        
        Args:
            cert_name: Name of the certification to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM certification_types WHERE certification_name = ?",
                (cert_name,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error removing certification type: {e}")
            return False
            
    # ============================================================
    # Export/Import for Backup
    # ============================================================
    
    def export_all_data(self) -> Dict:
        """Export all database data to a dictionary for backup.
        
        Returns:
            Dictionary containing all data
        """
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "members": [],
            "training_sessions": [],
            "attendance": [],
            "training_locations": [],
            "certification_types": [],
        }
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Export members with certifications
            cursor.execute("SELECT * FROM members")
            for row in cursor.fetchall():
                member = dict(row)
                member['certifications'] = self._get_member_certifications(member['id'])
                data["members"].append(member)
                
            # Export training sessions
            cursor.execute("SELECT * FROM training_sessions")
            for row in cursor.fetchall():
                data["training_sessions"].append(dict(row))
                
            # Export attendance
            cursor.execute("SELECT * FROM attendance")
            for row in cursor.fetchall():
                data["attendance"].append(dict(row))
                
            # Export training locations
            cursor.execute("SELECT location_name FROM training_locations")
            data["training_locations"] = [row[0] for row in cursor.fetchall()]
            
            # Export certification types
            cursor.execute("SELECT certification_name FROM certification_types ORDER BY sort_order")
            data["certification_types"] = [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error exporting data: {e}")
            
        return data
        
    def import_all_data(self, data: Dict) -> Tuple[bool, str]:
        """Import all data from a backup dictionary.
        
        Args:
            data: Dictionary containing backup data
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM attendance")
            cursor.execute("DELETE FROM certifications")
            cursor.execute("DELETE FROM training_sessions")
            cursor.execute("DELETE FROM members")
            cursor.execute("DELETE FROM training_locations")
            cursor.execute("DELETE FROM certification_types")
            
            # Import certification types
            for i, cert_name in enumerate(data.get("certification_types", [])):
                cursor.execute(
                    "INSERT INTO certification_types (certification_name, sort_order) VALUES (?, ?)",
                    (cert_name, i)
                )
                
            # Import training locations
            for loc in data.get("training_locations", []):
                cursor.execute(
                    "INSERT INTO training_locations (location_name) VALUES (?)",
                    (loc,)
                )
                
            # Import members
            member_id_map = {}  # old_id -> new_id
            for member in data.get("members", []):
                old_id = member.get("id")
                cursor.execute('''
                    INSERT INTO members (
                        first_name, last_name, address, cell_phone, home_phone,
                        email, alternate_email, emergency_contact_name,
                        emergency_contact_phone, ham_callsign, mission_eligible, member_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    member.get("first_name", ""),
                    member.get("last_name", ""),
                    member.get("address", ""),
                    member.get("cell_phone", ""),
                    member.get("home_phone", ""),
                    member.get("email", ""),
                    member.get("alternate_email", ""),
                    member.get("emergency_contact_name", ""),
                    member.get("emergency_contact_phone", ""),
                    member.get("ham_callsign", ""),
                    member.get("mission_eligible", 0),
                    member.get("member_status", "Member")
                ))
                new_id = cursor.lastrowid
                member_id_map[old_id] = new_id
                
                # Import certifications for this member
                for cert_name, date_completed in member.get("certifications", {}).items():
                    cursor.execute('''
                        INSERT INTO certifications (member_id, certification_name, date_completed)
                        VALUES (?, ?, ?)
                    ''', (new_id, cert_name, date_completed))
                    
            # Import training sessions
            session_id_map = {}  # old_id -> new_id
            for session in data.get("training_sessions", []):
                old_id = session.get("id")
                cursor.execute('''
                    INSERT INTO training_sessions (location, session_date, session_type, description)
                    VALUES (?, ?, ?, ?)
                ''', (
                    session.get("location", ""),
                    session.get("session_date", ""),
                    session.get("session_type", "Weekend Training"),
                    session.get("description", "")
                ))
                session_id_map[old_id] = cursor.lastrowid
                
            # Import attendance
            for att in data.get("attendance", []):
                old_session_id = att.get("session_id")
                old_member_id = att.get("member_id")
                new_session_id = session_id_map.get(old_session_id)
                new_member_id = member_id_map.get(old_member_id)
                
                if new_session_id and new_member_id:
                    cursor.execute('''
                        INSERT INTO attendance (session_id, member_id, attended)
                        VALUES (?, ?, ?)
                    ''', (new_session_id, new_member_id, att.get("attended", 0)))
                    
            conn.commit()
            return True, "Data imported successfully"
            
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
        except Exception as e:
            return False, f"Import error: {e}"
            
    def get_last_modified_time(self) -> Optional[datetime]:
        """Get the most recent modification time from the database.
        
        Returns:
            Datetime of most recent update, or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check members table
            cursor.execute("SELECT MAX(updated_at) FROM members")
            member_time = cursor.fetchone()[0]
            
            # Check sessions table
            cursor.execute("SELECT MAX(updated_at) FROM training_sessions")
            session_time = cursor.fetchone()[0]
            
            # Check attendance table
            attendance_time = None
            try:
                cursor.execute("SELECT MAX(updated_at) FROM attendance")
                attendance_time = cursor.fetchone()[0]
            except sqlite3.Error:
                # Column may not exist in older databases
                pass
            
            times = []
            if member_time:
                times.append(member_time)
            if session_time:
                times.append(session_time)
            if attendance_time:
                times.append(attendance_time)
                
            if times:
                latest = max(times)
                # Parse the timestamp
                try:
                    return datetime.fromisoformat(latest.replace('Z', '+00:00'))
                except ValueError:
                    return datetime.strptime(latest, "%Y-%m-%d %H:%M:%S")
            return None
            
        except sqlite3.Error as e:
            print(f"Error getting last modified time: {e}")
            return None


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager


def init_db_manager(db_path: str) -> DatabaseManager:
    """Initialize the global database manager with a path.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        DatabaseManager instance
    """
    global db_manager
    db_manager = DatabaseManager(db_path)
    return db_manager
