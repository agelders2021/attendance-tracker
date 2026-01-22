"""
sv.py - StringVars and other Tkinter variables for the Training Attendance Tracker

This file contains all the Tkinter variables that will be used to connect
widgets to the database. Import this module where needed.
"""

import tkinter as tk
from tkinter import ttk


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
        
        # Emergency Contact
        self.emergency_contact_name = tk.StringVar()
        self.emergency_contact_phone = tk.StringVar()
        
        # Additional Information
        self.ham_callsign = tk.StringVar()
        self.mission_eligible = tk.BooleanVar(value=False)
        
        # Certification Dates (Treeview data)
        self.pack_check_date = tk.StringVar()
        self.online_base_medical_date = tk.StringVar()
        self.crime_scene_preservation_date = tk.StringVar()
        self.blood_borne_pathogens_date = tk.StringVar()
        self.nm_sar_field_certification_date = tk.StringVar()
        self.fitness_hike_date = tk.StringVar()
        
        # Currently selected member ID for editing
        self.selected_member_id = tk.IntVar(value=-1)
        
        # ============================================================
        # Training Sessions Tab Variables
        # ============================================================
        
        # Session Details
        self.session_location = tk.StringVar()
        self.session_date = tk.StringVar()
        self.session_type = tk.StringVar(value="Weekend")  # Default to Weekend
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
        self.emergency_contact_name.set("")
        self.emergency_contact_phone.set("")
        self.ham_callsign.set("")
        self.mission_eligible.set(False)
        self.pack_check_date.set("")
        self.online_base_medical_date.set("")
        self.crime_scene_preservation_date.set("")
        self.blood_borne_pathogens_date.set("")
        self.nm_sar_field_certification_date.set("")
        self.fitness_hike_date.set("")
        self.selected_member_id.set(-1)
        
    def clear_training_session(self):
        """Clear all training session fields."""
        self.session_location.set("")
        self.session_date.set("")
        self.session_type.set("Weekend")
        self.session_description.set("")
        self.selected_session_id.set(-1)
        
    def get_certification_dates_dict(self) -> dict:
        """Return certification dates as a dictionary.
        
        Returns:
            Dictionary with certification names as keys and dates as values
        """
        return {
            "Pack Check": self.pack_check_date.get(),
            "On-line Base Medical": self.online_base_medical_date.get(),
            "Crime Scene Preservation": self.crime_scene_preservation_date.get(),
            "Blood-borne Pathogens": self.blood_borne_pathogens_date.get(),
            "NM SAR Field Certification": self.nm_sar_field_certification_date.get(),
            "Fitness Hike": self.fitness_hike_date.get(),
        }
        
    def set_certification_dates_from_dict(self, dates: dict):
        """Set certification dates from a dictionary.
        
        Args:
            dates: Dictionary with certification names as keys and dates as values
        """
        self.pack_check_date.set(dates.get("Pack Check", ""))
        self.online_base_medical_date.set(dates.get("On-line Base Medical", ""))
        self.crime_scene_preservation_date.set(dates.get("Crime Scene Preservation", ""))
        self.blood_borne_pathogens_date.set(dates.get("Blood-borne Pathogens", ""))
        self.nm_sar_field_certification_date.set(dates.get("NM SAR Field Certification", ""))
        self.fitness_hike_date.set(dates.get("Fitness Hike", ""))


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
