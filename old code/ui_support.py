"""
ui_support.py - Support methods for the Training Attendance Tracker UI

This file contains helper methods, validation functions, and other support
code that doesn't directly relate to tkinter widget creation.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
import tkinter as tk
from tkinter import ttk, messagebox

# Try to import tkcalendar for datepicker
try:
    from tkcalendar import DateEntry, Calendar
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False


# ============================================================
# Date Validation and Formatting
# ============================================================

DATE_FORMAT = "%m/%d/%Y"
DATE_PATTERN = re.compile(r"^(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(\d{4})$")


def validate_date(date_str: str) -> Tuple[bool, str]:
    """Validate a date string and return normalized format.
    
    Args:
        date_str: Date string to validate (expected format: MM/DD/YYYY)
        
    Returns:
        Tuple of (is_valid, normalized_date_or_error_message)
    """
    if not date_str or date_str.strip() == "":
        return True, ""  # Empty dates are allowed
    
    date_str = date_str.strip()
    
    # Check basic format
    if not DATE_PATTERN.match(date_str):
        return False, "Invalid date format. Use MM/DD/YYYY"
    
    try:
        # Parse and validate the actual date
        parsed = datetime.strptime(date_str, DATE_FORMAT)
        
        # Check for reasonable date range (not in far future)
        if parsed > datetime.now() + timedelta(days=365):
            return False, "Date cannot be more than 1 year in the future"
        
        # Check for not too far in past (e.g., before 2000)
        if parsed.year < 2000:
            return False, "Date cannot be before year 2000"
        
        # Return normalized format
        return True, parsed.strftime(DATE_FORMAT)
        
    except ValueError as e:
        return False, f"Invalid date: {str(e)}"


def on_date_focus_out(event, stringvar: tk.StringVar, field_name: str):
    """Handle focus out event for date fields to validate and format.
    
    Args:
        event: The tkinter event
        stringvar: The StringVar associated with the field
        field_name: Name of the field for error messages
    """
    date_value = stringvar.get()
    if date_value:
        is_valid, result = validate_date(date_value)
        if is_valid:
            stringvar.set(result)
        else:
            messagebox.showwarning("Date Validation Error", 
                                   f"{field_name}: {result}")
            event.widget.focus_set()


# ============================================================
# Phone Number Formatting
# ============================================================

def format_phone_number(phone: str) -> str:
    """Format a phone number to (XXX) XXX-XXXX format.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Formatted phone number or original if invalid
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if can't format


def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate a phone number.
    
    Args:
        phone: Phone number string
        
    Returns:
        Tuple of (is_valid, formatted_phone_or_error_message)
    """
    if not phone or phone.strip() == "":
        return True, ""  # Empty phones are allowed
    
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        return True, format_phone_number(phone)
    elif len(digits) == 11 and digits[0] == '1':
        return True, format_phone_number(phone)
    else:
        return False, "Phone number must be 10 digits"


# ============================================================
# Email Validation
# ============================================================

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate an email address.
    
    Args:
        email: Email address string
        
    Returns:
        Tuple of (is_valid, email_or_error_message)
    """
    if not email or email.strip() == "":
        return True, ""  # Empty emails are allowed
    
    email = email.strip().lower()
    
    if EMAIL_PATTERN.match(email):
        return True, email
    else:
        return False, "Invalid email format"


# ============================================================
# Treeview Helper Functions
# ============================================================

def create_certification_treeview_data() -> List[Dict]:
    """Create the initial data structure for the certification treeview.
    
    Returns:
        List of dictionaries with certification row data
    """
    return [
        {"name": "Pack Check", "date": ""},
        {"name": "On-line Base Medical", "date": ""},
        {"name": "Crime Scene Preservation", "date": ""},
        {"name": "Blood-borne Pathogens", "date": ""},
        {"name": "NM SAR Field Certification", "date": ""},
        {"name": "Fitness Hike", "date": ""},
    ]


def get_certification_row_names() -> List[str]:
    """Get the list of certification row names.
    
    Returns:
        List of certification names
    """
    return [
        "Pack Check",
        "On-line Base Medical",
        "Crime Scene Preservation",
        "Blood-borne Pathogens",
        "NM SAR Field Certification",
        "Fitness Hike",
    ]


# ============================================================
# Training Session Helper Functions
# ============================================================

def get_session_types() -> List[str]:
    """Get the list of session types.
    
    Returns:
        List of session type names
    """
    return ["Weekend", "Weekday", "Mission", "Other"]


def calculate_weekend_sessions_count(sessions: List[Dict], member_id: int) -> int:
    """Calculate the number of weekend sessions a member attended in the last 6 months.
    
    Args:
        sessions: List of session dictionaries with attendance data
        member_id: ID of the member to check
        
    Returns:
        Count of weekend sessions attended
    """
    six_months_ago = datetime.now() - timedelta(days=180)
    count = 0
    
    for session in sessions:
        if session.get("type") == "Weekend":
            try:
                session_date = datetime.strptime(session.get("date", ""), DATE_FORMAT)
                if session_date >= six_months_ago:
                    # Check if member attended
                    attendance = session.get("attendance", {})
                    if attendance.get(member_id) == "Yes":
                        count += 1
            except (ValueError, TypeError):
                continue
    
    return count


# ============================================================
# Member List Helper Functions
# ============================================================

def sort_members_by_last_name(members: List[Dict]) -> List[Dict]:
    """Sort a list of members by last name.
    
    Args:
        members: List of member dictionaries with 'last_name' key
        
    Returns:
        Sorted list of members
    """
    return sorted(members, key=lambda x: x.get("last_name", "").lower())


def format_member_display_name(first_name: str, last_name: str) -> str:
    """Format a member's name for display (Last, First).
    
    Args:
        first_name: Member's first name
        last_name: Member's last name
        
    Returns:
        Formatted name string
    """
    return f"{last_name}, {first_name}"


# ============================================================
# Combobox Values
# ============================================================

def get_attendance_options() -> List[str]:
    """Get the attendance dropdown options.
    
    Returns:
        List of attendance options
    """
    return ["No", "Yes"]


# ============================================================
# Form Validation
# ============================================================

def validate_required_field(value: str, field_name: str) -> Tuple[bool, str]:
    """Validate that a required field is not empty.
    
    Args:
        value: Field value
        field_name: Name of the field for error messages
        
    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    if not value or value.strip() == "":
        return False, f"{field_name} is required"
    return True, ""


def validate_demographics_form(vars_dict: Dict) -> Tuple[bool, List[str]]:
    """Validate the demographics form.
    
    Args:
        vars_dict: Dictionary of field names to values
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = [
        ("first_name", "First Name"),
        ("last_name", "Last Name"),
    ]
    
    for field, name in required_fields:
        is_valid, error = validate_required_field(vars_dict.get(field, ""), name)
        if not is_valid:
            errors.append(error)
    
    # Email validation (if provided)
    email = vars_dict.get("email", "")
    if email:
        is_valid, error = validate_email(email)
        if not is_valid:
            errors.append(f"Email: {error}")
    
    alt_email = vars_dict.get("alternate_email", "")
    if alt_email:
        is_valid, error = validate_email(alt_email)
        if not is_valid:
            errors.append(f"Alternate Email: {error}")
    
    # Phone validation (if provided)
    cell_phone = vars_dict.get("cell_phone", "")
    if cell_phone:
        is_valid, error = validate_phone(cell_phone)
        if not is_valid:
            errors.append(f"Cell Phone: {error}")
    
    home_phone = vars_dict.get("home_phone", "")
    if home_phone:
        is_valid, error = validate_phone(home_phone)
        if not is_valid:
            errors.append(f"Home Phone: {error}")
    
    emergency_phone = vars_dict.get("emergency_contact_phone", "")
    if emergency_phone:
        is_valid, error = validate_phone(emergency_phone)
        if not is_valid:
            errors.append(f"Emergency Contact Phone: {error}")
    
    return len(errors) == 0, errors


def validate_training_session_form(vars_dict: Dict) -> Tuple[bool, List[str]]:
    """Validate the training session form.
    
    Args:
        vars_dict: Dictionary of field names to values
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = [
        ("location", "Location"),
        ("date", "Date"),
        ("type", "Session Type"),
    ]
    
    for field, name in required_fields:
        is_valid, error = validate_required_field(vars_dict.get(field, ""), name)
        if not is_valid:
            errors.append(error)
    
    # Date validation
    date = vars_dict.get("date", "")
    if date:
        is_valid, error = validate_date(date)
        if not is_valid:
            errors.append(f"Date: {error}")
    
    return len(errors) == 0, errors


# ============================================================
# UI State Management
# ============================================================

class UIState:
    """Class to manage UI state that isn't tied to database fields."""
    
    def __init__(self):
        self.is_editing_member = False
        self.is_editing_session = False
        self.members_list: List[Dict] = []
        self.sessions_list: List[Dict] = []
        self.current_session_attendance: Dict[int, str] = {}
        
        # Session change tracking
        self.session_has_unsaved_changes = False
        self.last_saved_session_data: Dict = {}
        
    def reset(self):
        """Reset all state."""
        self.is_editing_member = False
        self.is_editing_session = False
        self.members_list = []
        self.sessions_list = []
        self.current_session_attendance = {}
        self.session_has_unsaved_changes = False
        self.last_saved_session_data = {}
        
    def mark_session_saved(self, session_data: Dict):
        """Mark session as saved with current data.
        
        Args:
            session_data: Dictionary of current session field values
        """
        self.last_saved_session_data = session_data.copy()
        self.session_has_unsaved_changes = False
        
    def mark_session_clean(self):
        """Mark session as having no unsaved changes."""
        self.session_has_unsaved_changes = False
        self.last_saved_session_data = {}
        
    def check_session_changed(self, current_data: Dict) -> bool:
        """Check if session data has changed from last saved state.
        
        Args:
            current_data: Dictionary of current session field values
            
        Returns:
            True if data has changed, False otherwise
        """
        # If no saved state and form is essentially empty, no changes
        if not self.last_saved_session_data:
            # Check if any meaningful fields have values (ignore type which has a default)
            location = current_data.get('location', '').strip()
            date = current_data.get('date', '').strip()
            description = current_data.get('description', '').strip()
            
            # Only consider it changed if location or date has a value
            if location or date:
                return True
            return False
            
        # Compare with saved state
        for key, value in current_data.items():
            saved_value = self.last_saved_session_data.get(key, "")
            if str(value).strip() != str(saved_value).strip():
                return True
        return False


# Global UI state instance
ui_state = UIState()


def get_ui_state() -> UIState:
    """Get the global UI state instance.
    
    Returns:
        The UIState instance
    """
    return ui_state


# ============================================================
# Custom DateEntry with Session Highlighting
# ============================================================

# Session type colors for calendar highlighting
SESSION_COLORS = {
    "Weekend": "#FFFF00",    # Yellow
    "Weekday": "#87CEEB",    # Light Blue
    "Mission": "#FF6B6B",    # Red
    "Other": "#90EE90",      # Light Green
}


class TrainingDateEntry(DateEntry if TKCALENDAR_AVAILABLE else object):
    """Custom DateEntry that highlights past training sessions by type.
    
    - Weekend sessions: Yellow
    - Weekday sessions: Blue
    - Mission sessions: Red
    - Other sessions: Green
    """
    
    def __init__(self, master=None, sessions_callback=None, **kw):
        """Initialize the custom DateEntry.
        
        Args:
            master: Parent widget
            sessions_callback: Callback function that returns list of session dicts
                              with 'date' and 'type' keys
            **kw: Additional keyword arguments for DateEntry
        """
        if not TKCALENDAR_AVAILABLE:
            raise ImportError("tkcalendar is required for TrainingDateEntry")
            
        self.sessions_callback = sessions_callback
        
        # Set default options
        kw.setdefault('date_pattern', 'mm/dd/yyyy')
        kw.setdefault('width', 12)
        
        super().__init__(master, **kw)
        
        # Bind to calendar display to update highlighting
        self.bind("<<DateEntrySelected>>", self._on_date_selected)
        
    def _on_date_selected(self, event=None):
        """Handle date selection event."""
        pass  # Can be overridden or bound externally
        
    def drop_down(self):
        """Override drop_down to add session highlighting to calendar."""
        super().drop_down()
        # Schedule highlighting after the calendar is displayed
        self.after(10, self._highlight_sessions)
        
    def _get_calendar_widget(self):
        """Get the actual Calendar widget from the dropdown.
        
        Returns:
            Calendar widget or None if not found
        """
        try:
            # The _top_cal is a Toplevel window containing the calendar
            top = self._top_cal
            if top and top.winfo_exists():
                # Find the Calendar widget inside the Toplevel
                for child in top.winfo_children():
                    if isinstance(child, Calendar):
                        return child
        except (AttributeError, tk.TclError):
            pass
        return None
        
    def _highlight_sessions(self):
        """Highlight dates with past training sessions."""
        if not self.sessions_callback:
            return
            
        # Get the calendar widget
        cal = self._get_calendar_widget()
        if cal is None:
            return
            
        # Clear existing tags
        for tag in SESSION_COLORS.keys():
            try:
                cal.calevent_remove('all', tag)
            except Exception:
                pass
            
        # Get sessions from callback
        sessions = self.sessions_callback()
        
        # Add events for each session
        for session in sessions:
            date_str = session.get('date', '')
            session_type = session.get('type', '')
            
            if date_str and session_type in SESSION_COLORS:
                try:
                    session_date = datetime.strptime(date_str, DATE_FORMAT).date()
                    cal.calevent_create(session_date, session_type, session_type)
                except (ValueError, TypeError):
                    continue
                    
        # Configure tag colors
        for session_type, color in SESSION_COLORS.items():
            try:
                cal.tag_config(session_type, background=color, foreground='black')
            except Exception:
                pass


def get_day_of_week(date_str: str) -> Optional[str]:
    """Get the day of week for a date string.
    
    Args:
        date_str: Date in MM/DD/YYYY format
        
    Returns:
        Day name (e.g., 'Monday') or None if invalid
    """
    try:
        date_obj = datetime.strptime(date_str, DATE_FORMAT)
        return date_obj.strftime('%A')
    except (ValueError, TypeError):
        return None


def is_weekend_date(date_str: str) -> Optional[bool]:
    """Check if a date falls on a weekend.
    
    Args:
        date_str: Date in MM/DD/YYYY format
        
    Returns:
        True if Saturday or Sunday, False if weekday, None if invalid
    """
    day = get_day_of_week(date_str)
    if day is None:
        return None
    return day in ('Saturday', 'Sunday')


def suggest_session_type(date_str: str) -> str:
    """Suggest a session type based on the date.
    
    Args:
        date_str: Date in MM/DD/YYYY format
        
    Returns:
        'Weekend' or 'Weekday' based on the date
    """
    is_weekend = is_weekend_date(date_str)
    if is_weekend is None:
        return "Weekend"  # Default
    return "Weekend" if is_weekend else "Weekday"


def get_unique_locations(sessions: List[Dict]) -> List[str]:
    """Get unique locations from sessions, sorted alphabetically.
    
    Args:
        sessions: List of session dictionaries
        
    Returns:
        Sorted list of unique location names
    """
    locations = set()
    for session in sessions:
        loc = session.get('location', '').strip()
        if loc:
            locations.add(loc)
    return sorted(locations, key=str.lower)


def find_session_by_date_and_location(sessions: List[Dict], 
                                       date_str: str, 
                                       location: str) -> Optional[Dict]:
    """Find a session by date and location.
    
    Args:
        sessions: List of session dictionaries
        date_str: Date in MM/DD/YYYY format
        location: Location name
        
    Returns:
        Session dictionary if found, None otherwise
    """
    for session in sessions:
        if (session.get('date', '') == date_str and 
            session.get('location', '').lower() == location.lower()):
            return session
    return None


def find_sessions_by_date(sessions: List[Dict], date_str: str) -> List[Dict]:
    """Find all sessions on a specific date.
    
    Args:
        sessions: List of session dictionaries
        date_str: Date in MM/DD/YYYY format
        
    Returns:
        List of matching session dictionaries
    """
    return [s for s in sessions if s.get('date', '') == date_str]
