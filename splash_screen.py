#!/usr/bin/env python3
"""
SPDX-License-Identifier: GPL-3.0-or-later

Copyright (C) 2026 Al Gelders

This file is part of the attendance logging programs

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
Splash Screen for Training Tracker Applications
Copyright (C) 2025 Al Gelders

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import tkinter as tk
from tkinter import ttk
import time

# Default values for airscenting (backward compatible)
DEFAULT_APP_TITLE = "Air-scent Training Tracker"
DEFAULT_GITHUB_URL = "github.com/agelders2021/airscent_tracker"

class SplashScreen:
    """Display a splash screen while the application loads"""
    
    def __init__(self, parent, version="1.0.0-alpha", app_title=None, github_url=None, main_window_geometry=None):
        self.version = version
        self.app_title = app_title or DEFAULT_APP_TITLE
        self.github_url = github_url or DEFAULT_GITHUB_URL
        self.start_time = time.time()
        self.root = tk.Toplevel(parent)
        self.root.title("Loading...")
        self.closed = False  # Track if splash has been closed
        self.auto_close_timer = None
        
        # Remove window decorations
        self.root.overrideredirect(True)
        
        # Keep splash on top
        self.root.lift()
        self.root.attributes('-topmost', True)
        
        # Set size
        width = 500
        height = 500
        
        # Center on main window if geometry provided, otherwise center on screen
        if main_window_geometry:
            try:
                import re
                match = re.match(r'(\d+)x(\d+)([+-]\d+)([+-]\d+)', main_window_geometry)
                if match:
                    main_w, main_h, main_x, main_y = match.groups()
                    main_w, main_h = int(main_w), int(main_h)
                    main_x, main_y = int(main_x), int(main_y)
                    # Center splash over main window
                    x = main_x + (main_w - width) // 2
                    y = main_y + (main_h - height) // 2
                else:
                    # Fallback to screen center
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    x = (screen_width - width) // 2
                    y = (screen_height - height) // 2
            except Exception:
                # Fallback to screen center
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
        else:
            # Center on screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create frame with border
        frame = tk.Frame(self.root, bg='white', relief='raised', borderwidth=2)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            frame, 
            text=self.app_title,
            font=('Arial', 20, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(40, 10))
        
        # Version
        version_label = tk.Label(
            frame,
            text=f"Version {self.version}",
            font=('Arial', 10),
            bg='white',
            fg='#7f8c8d'
        )
        version_label.pack()
        
        # Copyright
        copyright_label = tk.Label(
            frame,
            text="Â© 2025 Al Gelders",
            font=('Arial', 11),
            bg='white',
            fg='#34495e'
        )
        copyright_label.pack(pady=(30, 5))
        
        # License info
        license_text = (
            "This program is free software licensed under\n"
            "the GNU General Public License v3.0\n\n"
            "You are free to use, modify, and distribute this software."
        )
        license_label = tk.Label(
            frame,
            text=license_text,
            font=('Arial', 9),
            bg='white',
            fg='#7f8c8d',
            justify='center'
        )
        license_label.pack(pady=5)
        
        # GitHub repository
        github_label = tk.Label(
            frame,
            text=self.github_url,
            font=('Arial', 8),
            bg='white',
            fg='#95a5a6',
            justify='center'
        )
        github_label.pack(pady=5)
        
        # Loading message
        loading_label = tk.Label(
            frame,
            text="Loading application...",
            font=('Arial', 9, 'italic'),
            bg='white',
            fg='#95a5a6'
        )
        loading_label.pack(pady=(30, 5))
        
        # Countdown text
        self.countdown_var = tk.StringVar(value="Auto-closing in 5 seconds...")
        countdown_label = tk.Label(
            frame,
            textvariable=self.countdown_var,
            font=('Arial', 9),
            bg='white',
            fg='#7f8c8d'
        )
        countdown_label.pack(pady=5)
        
        # Progress bar (counts down from full to empty, in tenths)
        self.progress = ttk.Progressbar(
            frame,
            mode='determinate',
            length=300,
            maximum=50  # 5 seconds * 10 tenths per second
        )
        self.progress['value'] = 50  # Start at full
        self.progress.pack(pady=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(frame, bg='white')
        buttons_frame.pack(pady=15)
        
        # Stop Countdown button
        stop_button = ttk.Button(
            buttons_frame,
            text="Stop Countdown",
            command=self.stop_countdown,
            width=18
        )
        stop_button.pack(side='left', padx=5)
        
        # Close button
        close_button = ttk.Button(
            buttons_frame,
            text="Close This Screen",
            command=self.destroy,
            width=18
        )
        close_button.pack(side='left', padx=5)
        
        # Update display
        self.root.update()
        
        # Start countdown updates
        self.remaining_tenths = 50  # 5 seconds * 10 tenths
        self.update_countdown()
    
    def stop_countdown(self):
        """Stop the countdown timer"""
        if self.auto_close_timer:
            self.root.after_cancel(self.auto_close_timer)
            self.auto_close_timer = None
        self.countdown_var.set("Countdown stopped")
    
    def update_countdown(self):
        """Update countdown timer every tenth of a second"""
        if self.closed:
            return
        
        if self.remaining_tenths > 0:
            # Update progress bar
            self.progress['value'] = self.remaining_tenths
            
            # Update text only on whole seconds
            seconds = self.remaining_tenths // 10
            if self.remaining_tenths % 10 == 0:  # Only update text on whole seconds
                if seconds > 0:
                    self.countdown_var.set(f"Auto-closing in {seconds} seconds...")
                else:
                    self.countdown_var.set("Auto-closing now...")
            
            self.remaining_tenths -= 1
            self.auto_close_timer = self.root.after(100, self.update_countdown)  # Update every 0.1 seconds
        else:
            # Time's up, close the splash
            self.destroy()
    
    def destroy(self):
        """Close the splash screen (called by Continue button, timer, or initialization complete)"""
        if self.closed:
            return  # Already closed
        
        self.closed = True
        
        # Cancel auto-close timer if it's still running
        if self.auto_close_timer:
            self.root.after_cancel(self.auto_close_timer)
            self.auto_close_timer = None
        
        # Destroy the window
        self.root.destroy()
