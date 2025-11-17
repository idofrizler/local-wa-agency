"""
GUI display for WhatsApp Padel Match Tracker with Hebrew RTL support.
"""
import tkinter as tk
from tkinter import ttk
from typing import List, Literal
from datetime import datetime, timedelta
from src.models import Match

class MatchDisplayWindow:
    """GUI window to display matches in a Hebrew RTL table."""
    
    def __init__(self, title: str = "תוצאות סריקה"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1300x700")
        
        # Configure RTL support
        self.root.option_add('*font', 'Arial 11')
        
        # Store matches
        self.matches: List[Match] = []
        
        # Privacy setting
        self.show_private_info = tk.BooleanVar(value=False)
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title and privacy checkbox frame
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame,
            text="התאמות פוטנציאליות למשחקי פאדל",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(side=tk.RIGHT, padx=10)
        
        # Privacy checkbox
        privacy_check = ttk.Checkbutton(
            header_frame,
            text="הצג שמות וטלפונים",
            variable=self.show_private_info,
            command=self._toggle_privacy
        )
        privacy_check.pack(side=tk.RIGHT)
        
        # Create frame for treeview and scrollbar
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Create treeview with scrollbar (added match_datetime and location columns)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('confidence', 'match_datetime', 'location', 'phone', 'sender', 'group', 'time'),
            show='headings',
            height=20
        )
        
        # Define RTL columns (right to left)
        self.tree.heading('confidence', text='רמת התאמה')
        self.tree.heading('match_datetime', text='תאריך ושעה')
        self.tree.heading('location', text='מיקום')
        self.tree.heading('phone', text='טלפון')
        self.tree.heading('sender', text='שולח')
        self.tree.heading('group', text='קבוצה')
        self.tree.heading('time', text='שעת שליחה')
        
        # Column widths
        self.tree.column('confidence', width=90, anchor='center')
        self.tree.column('match_datetime', width=130, anchor='center')
        self.tree.column('location', width=120, anchor='e')
        self.tree.column('phone', width=110, anchor='e')
        self.tree.column('sender', width=120, anchor='e')
        self.tree.column('group', width=180, anchor='e')
        self.tree.column('time', width=70, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Details text box
        details_label = ttk.Label(main_frame, text="פרטי ההודעה:", font=('Arial', 12, 'bold'))
        details_label.grid(row=2, column=0, pady=(10, 5), sticky=tk.E)
        
        details_frame = ttk.Frame(main_frame)
        details_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        
        self.details_text = tk.Text(
            details_frame,
            height=8,
            wrap=tk.WORD,
            font=('Arial', 10),
            state=tk.DISABLED
        )
        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        details_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure row weights for resizing
        main_frame.rowconfigure(3, weight=1)
        
        # Summary label
        self.summary_label = ttk.Label(
            main_frame,
            text="",
            font=('Arial', 10)
        )
        self.summary_label.grid(row=4, column=0, pady=(10, 0))
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        
        # Configure tags for colors with dark text
        self.tree.tag_configure('HIGH', background='#90EE90', foreground='#000000')  # Light green with black text
        self.tree.tag_configure('MEDIUM', background='#FFE5B4', foreground='#000000')  # Light orange with black text
        self.tree.tag_configure('LOW', background='#FFB6C6', foreground='#000000')  # Light red with black text
    
    def add_match(self, match: Match):
        """Add a match to the display."""
        self.matches.append(match)
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the entire display with current privacy settings."""
        # Clear current display
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Re-add all matches
        for match in reversed(self.matches):  # Reversed so newest is first
            self._add_match_to_tree(match)
        
        # Update summary
        self._update_summary()
    
    def _add_match_to_tree(self, match: Match):
        """Add a single match to the tree with current privacy settings."""
        # Get confidence symbol
        symbol = self._get_confidence_symbol(match.confidence)
        confidence_text = f"{match.confidence} {symbol}"
        
        # Format match date/time with actual dates
        match_datetime = self._format_match_datetime_with_actual_date(match)
        
        # Get location
        location = match.analysis.location if match.analysis and match.analysis.location else "-"
        
        # Apply privacy redaction if needed
        show_private = self.show_private_info.get()
        phone_display = match.phone_number if show_private else "***"
        sender_display = match.sender if show_private else "***"
        
        # Insert into treeview
        self.tree.insert(
            '',
            'end',
            values=(
                confidence_text,
                match_datetime,
                location,
                phone_display,
                sender_display,
                match.group_name,
                match.timestamp
            ),
            tags=(match.confidence,)
        )
    
    def _format_match_datetime_with_actual_date(self, match: Match) -> str:
        """
        Format the match date and time, converting relative dates to actual dates.
        Uses the message timestamp to calculate actual dates from relative terms.
        """
        if not match.analysis:
            return "לא ידוע"
        
        date_str = match.analysis.match_date or ""
        time_str = match.analysis.match_time or ""
        
        # Convert relative date to actual date
        actual_date = self._convert_relative_to_actual_date(date_str, match.timestamp)
        
        # Combine date and time
        if actual_date and time_str:
            return f"{actual_date} {time_str}"
        elif actual_date:
            return actual_date
        elif time_str:
            return time_str
        else:
            return "לא ידוע"
    
    def _convert_relative_to_actual_date(self, date_str: str, message_timestamp: str) -> str:
        """
        Convert relative date (today, tomorrow) to actual date.
        
        Args:
            date_str: The date string from AI (e.g., "today", "tomorrow", "Sunday")
            message_timestamp: The timestamp when the message was sent (HH:MM format)
            
        Returns:
            Formatted date string (DD/MM or day name)
        """
        if not date_str:
            return ""
        
        date_lower = date_str.lower()
        now = datetime.now()
        
        # Handle "today" / "היום"
        if date_lower in ["today", "היום", "tod", "tdy"]:
            return now.strftime("%d/%m")
        
        # Handle "tomorrow" / "מחר"
        elif date_lower in ["tomorrow", "מחר", "tmrw", "tmr"]:
            tomorrow = now + timedelta(days=1)
            return tomorrow.strftime("%d/%m")
        
        # Handle day of week names (English)
        day_names = {
            "monday": 0, "mon": 0,
            "tuesday": 1, "tue": 1,
            "wednesday": 2, "wed": 2,
            "thursday": 3, "thu": 3,
            "friday": 4, "fri": 4,
            "saturday": 5, "sat": 5,
            "sunday": 6, "sun": 6
        }
        
        # Handle day of week names (Hebrew)
        hebrew_days = {
            "ראשון": 6, "יום ראשון": 6,
            "שני": 0, "יום שני": 0,
            "שלישי": 1, "יום שלישי": 1,
            "רביעי": 2, "יום רביעי": 2,
            "חמישי": 3, "יום חמישי": 3,
            "שישי": 4, "יום שישי": 4,
            "שבת": 5, "יום שבת": 5
        }
        
        # Check for day names
        for day_name, day_num in day_names.items():
            if day_name in date_lower:
                days_ahead = (day_num - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next occurrence
                target_date = now + timedelta(days=days_ahead)
                return target_date.strftime("%d/%m")
        
        for day_name, day_num in hebrew_days.items():
            if day_name in date_str:
                days_ahead = (day_num - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next occurrence
                target_date = now + timedelta(days=days_ahead)
                return target_date.strftime("%d/%m")
        
        # If it's already a specific date format, return as is
        return date_str
    
    def _toggle_privacy(self):
        """Toggle privacy mode and refresh display."""
        self._refresh_display()
    
    def clear_matches(self):
        """Clear all matches from the display."""
        self.matches.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._update_summary()
        self._clear_details()
    
    def _get_confidence_symbol(self, confidence: str) -> str:
        """Get symbol for confidence level."""
        if confidence == "HIGH":
            return "✓"
        elif confidence == "MEDIUM":
            return "~"
        else:
            return "✗"
    
    def _on_select(self, event):
        """Handle row selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get the index from the item
        item = selection[0]
        index = self.tree.index(item)
        
        # Get the match (reversed because we insert at beginning)
        match = self.matches[len(self.matches) - 1 - index]
        
        # Display details
        self._show_details(match)
    
    def _show_details(self, match: Match):
        """Show match details in the text box."""
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        # Build details text (RTL)
        details = f"הודעה מקורית:\n{match.message}\n\n"
        
        if match.analysis:
            details += f"ניתוח:\n{match.analysis.reasoning}\n\n"
            details += "התאמות:\n"
            details += f"  רמה: {'✓' if match.analysis.level_match else '✗'}\n"
            details += f"  זמן: {'✓' if match.analysis.time_match else '✗'}\n"
            details += f"  מספר שחקנים: {'✓' if match.analysis.player_count_match else '✗'}\n"
        
        self.details_text.insert(1.0, details)
        self.details_text.configure(state=tk.DISABLED)
    
    def _clear_details(self):
        """Clear the details text box."""
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.configure(state=tk.DISABLED)
    
    def _update_summary(self):
        """Update the summary label."""
        total = len(self.matches)
        high = sum(1 for m in self.matches if m.confidence == "HIGH")
        medium = sum(1 for m in self.matches if m.confidence == "MEDIUM")
        low = sum(1 for m in self.matches if m.confidence == "LOW")
        
        summary = f"סה\"כ התאמות: {total} (גבוה: {high}, בינוני: {medium}, נמוך: {low})"
        self.summary_label.config(text=summary)
    
    def show(self):
        """Show the window."""
        self.root.mainloop()
    
    def update(self):
        """Update the window (for non-blocking updates)."""
        self.root.update()
    
    def destroy(self):
        """Destroy the window."""
        self.root.destroy()
