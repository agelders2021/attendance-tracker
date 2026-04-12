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
sv.py - StringVars and other Tkinter variables for the Training Attendance Tracker

This file contains all the Tkinter variables that will be used to connect
widgets to the database. Import this module where needed.
"""

import tkinter as tk
from tkinter import ttk
import ui_support


class AppVariables:
    """Container for all application variables."""
    
    def __init__(self, root: tk.Tk):
        """Initialize all StringVars and other Tkinter variables.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        
        # ============================================================
        # Demographics Tab Variables
        # ============================================================
        
        # Personal Information
        self.first_name = tk.StringVar()
        self.last_name = tk.StringVar()
        self.address = tk.StringVar()
        self.cell_phone = tk.StringVar()
        self.home_phone = tk.StringVar()
        self.email = tk.StringVar()
        self.alternate_email = tk.StringVar()
        
        # Member Status (Member, Candidate, Affiliate, or Pre-Candidate)
        self.member_status = tk.StringVar(value="")  # Start empty, no default
        
        # Member Role (Canine Handler, Field Support, Base Support, Provisional Field Support, None)
        self.member_role = tk.StringVar(value="None")  # Default to 'None'
        
        # Emergency Contact
        self.emergency_contact_name = tk.StringVar()
        self.emergency_contact_phone = tk.StringVar()
        
        # Additional Information
        self.ham_callsign = tk.StringVar()
        self.mission_eligible = tk.BooleanVar(value=False)
        
        # Certification Dates (Treeview data) — keyed by certification name
        self.cert_dates: dict = {
            name: tk.StringVar()
            for name in ui_support.load_certification_names()
        }
        
        # Currently selected member ID for editing
        self.selected_member_id = tk.IntVar(value=-1)
        
        # ============================================================
        # Training Sessions Tab Variables
        # ============================================================
        
        # Session Details
        self.session_location = tk.StringVar()
        self.session_date = tk.StringVar()
        self.session_type = tk.StringVar(value="Weekend Training")  # Default to Weekend Training
        self.session_description = tk.StringVar()  # For Mission/Other description
        
        # Currently selected session ID
        self.selected_session_id = tk.IntVar(value=-1)
        
        # ============================================================
        # Setup Tab Variables (to be defined later)
        # ============================================================
        
        # Storage paths
        self.primary_storage_folder = tk.StringVar()
        self.secondary_backup_folder = tk.StringVar()
        self.excel_participation_folder = tk.StringVar()
        
        # Email settings
        self.smtp_server = tk.StringVar(value="smtp.gmail.com")
        self.smtp_port = tk.StringVar(value="587")
        self.smtp_username = tk.StringVar()
        self.sender_email = tk.StringVar()
        self.sender_password = tk.StringVar()
        self.smtp_encryption = tk.StringVar(value="TLS")
        
        # Email PDF settings
        self.pdf_months_to_review = tk.IntVar(value=1)
        
        # Placeholder for future setup variables
        self.setup_placeholder = tk.StringVar()
        
    def clear_demographics(self):
        """Clear all demographics fields."""
        self.first_name.set("")
        self.last_name.set("")
        self.address.set("")
        self.cell_phone.set("")
        self.home_phone.set("")
        self.email.set("")
        self.alternate_email.set("")
        self.member_status.set("")  # No default status when clearing
        self.member_role.set("None")  # Reset to 'None' when clearing
        self.emergency_contact_name.set("")
        self.emergency_contact_phone.set("")
        self.ham_callsign.set("")
        self.mission_eligible.set(False)
        for var in self.cert_dates.values():
            var.set("")
        self.selected_member_id.set(-1)
        
    def clear_training_session(self):
        """Clear all training session fields."""
        self.session_location.set("")
        self.session_date.set("")
        self.session_type.set("Weekend Training")
        self.session_description.set("")
        self.selected_session_id.set(-1)
        
    def get_certification_dates_dict(self) -> dict:
        """Return certification dates as a dictionary.

        Returns:
            Dictionary with certification names as keys and dates as values
        """
        return {name: var.get() for name, var in self.cert_dates.items()}

    def set_certification_dates_from_dict(self, dates: dict):
        """Set certification dates from a dictionary.

        Args:
            dates: Dictionary with certification names as keys and dates as values
        """
        for name, var in self.cert_dates.items():
            var.set(dates.get(name, ""))


# Global instance - will be initialized when the app starts
app_vars: AppVariables = None


def init_variables(root: tk.Tk) -> AppVariables:
    """Initialize the global AppVariables instance.
    
    Args:
        root: The root Tkinter window
        
    Returns:
        The initialized AppVariables instance
    """
    global app_vars
    app_vars = AppVariables(root)
    return app_vars


def get_variables() -> AppVariables:
    """Get the global AppVariables instance.
    
    Returns:
        The AppVariables instance
        
    Raises:
        RuntimeError: If variables haven't been initialized
    """
    if app_vars is None:
        raise RuntimeError("Variables not initialized. Call init_variables() first.")
    return app_vars
