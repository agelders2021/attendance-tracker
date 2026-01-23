#!/usr/bin/env python3
"""
migrate_session_types.py - Database Migration Script

This script updates an existing Training Attendance Tracker database
to use the new session type terminology:
    - "Weekend" → "Qualifying Training"
    - "Weekday" → "Optional Training"

Usage:
    python migrate_session_types.py <path_to_database>
    
Example:
    python migrate_session_types.py /path/to/training_tracker.db
    
The script will:
1. Create a backup of the database before making changes
2. Update all session_type values in the training_sessions table
3. Report the number of records updated

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 Al Gelders
"""

import sqlite3
import sys
import os
import shutil
from datetime import datetime


def create_backup(db_path: str) -> str:
    """Create a backup of the database before migration.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Path to the backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def get_session_type_counts(cursor) -> dict:
    """Get counts of each session type in the database.
    
    Args:
        cursor: Database cursor
        
    Returns:
        Dictionary with session types as keys and counts as values
    """
    cursor.execute("""
        SELECT session_type, COUNT(*) as count 
        FROM training_sessions 
        GROUP BY session_type
    """)
    return {row[0]: row[1] for row in cursor.fetchall()}


def migrate_database(db_path: str) -> bool:
    """Migrate the database to use new session type terminology.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        True if migration was successful, False otherwise
    """
    # Verify database exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
    
    # Create backup
    print(f"Creating backup of database...")
    try:
        backup_path = create_backup(db_path)
        print(f"Backup created: {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Show current state
        print("\n--- Current Session Type Distribution ---")
        before_counts = get_session_type_counts(cursor)
        if not before_counts:
            print("No training sessions found in database.")
        else:
            for session_type, count in sorted(before_counts.items()):
                print(f"  {session_type}: {count} sessions")
        
        # Check if migration is needed
        needs_migration = 'Weekend' in before_counts or 'Weekday' in before_counts
        already_migrated = 'Qualifying Training' in before_counts or 'Optional Training' in before_counts
        
        if not needs_migration and already_migrated:
            print("\nDatabase appears to already be migrated (no 'Weekend' or 'Weekday' entries found).")
            print("No changes made.")
            conn.close()
            # Remove unnecessary backup
            os.remove(backup_path)
            print(f"Removed unnecessary backup: {backup_path}")
            return True
        
        if not needs_migration and not already_migrated:
            print("\nNo session records found that need migration.")
            conn.close()
            os.remove(backup_path)
            print(f"Removed unnecessary backup: {backup_path}")
            return True
        
        # Perform migration
        print("\n--- Performing Migration ---")
        
        # Update "Weekend" to "Qualifying Training"
        cursor.execute("""
            UPDATE training_sessions 
            SET session_type = 'Qualifying Training' 
            WHERE session_type = 'Weekend'
        """)
        weekend_updated = cursor.rowcount
        print(f"Updated {weekend_updated} 'Weekend' sessions to 'Qualifying Training'")
        
        # Update "Weekday" to "Optional Training"
        cursor.execute("""
            UPDATE training_sessions 
            SET session_type = 'Optional Training' 
            WHERE session_type = 'Weekday'
        """)
        weekday_updated = cursor.rowcount
        print(f"Updated {weekday_updated} 'Weekday' sessions to 'Optional Training'")
        
        # Commit changes
        conn.commit()
        
        # Show final state
        print("\n--- Updated Session Type Distribution ---")
        after_counts = get_session_type_counts(cursor)
        for session_type, count in sorted(after_counts.items()):
            print(f"  {session_type}: {count} sessions")
        
        # Summary
        total_updated = weekend_updated + weekday_updated
        print(f"\n--- Migration Summary ---")
        print(f"Total records updated: {total_updated}")
        print(f"Backup file preserved at: {backup_path}")
        print("\nMigration completed successfully!")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        print(f"Restoring from backup...")
        try:
            shutil.copy2(backup_path, db_path)
            print("Database restored from backup.")
        except Exception as restore_error:
            print(f"Error restoring backup: {restore_error}")
            print(f"Manual restoration may be needed from: {backup_path}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    """Main entry point for the migration script."""
    print("=" * 60)
    print("Training Attendance Tracker - Session Type Migration Tool")
    print("=" * 60)
    print()
    print("This script updates session types:")
    print("  'Weekend' → 'Qualifying Training'")
    print("  'Weekday' → 'Optional Training'")
    print()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        # Try to find database in common locations
        print("Usage: python migrate_session_types.py <path_to_database>")
        print()
        print("Example paths:")
        print("  python migrate_session_types.py ./training_tracker.db")
        print("  python migrate_session_types.py ~/Documents/training_tracker.db")
        print()
        
        # Check if there's a database in the current directory
        if os.path.exists("training_tracker.db"):
            print("Found 'training_tracker.db' in current directory.")
            response = input("Would you like to migrate this database? (yes/no): ").strip().lower()
            if response in ('yes', 'y'):
                db_path = "training_tracker.db"
            else:
                print("Migration cancelled.")
                sys.exit(0)
        else:
            sys.exit(1)
    else:
        db_path = sys.argv[1]
    
    # Confirm before proceeding
    print(f"\nDatabase to migrate: {os.path.abspath(db_path)}")
    print()
    response = input("Proceed with migration? (yes/no): ").strip().lower()
    
    if response not in ('yes', 'y'):
        print("Migration cancelled.")
        sys.exit(0)
    
    print()
    
    # Run migration
    success = migrate_database(db_path)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
