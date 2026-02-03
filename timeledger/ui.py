"""
UI module for TimeLedger - Tkinter desktop GUI.
Provides controls for work tracking with live elapsed time display.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional

from .tracker import WorkTracker, InvalidTransitionError, State
from .report import generate_today_report
from .db import DatabaseConnectionError, test_connection


class PauseReasonDialog(simpledialog.Dialog):
    """Custom dialog for entering pause reason."""
    
    def __init__(self, parent, title="Pause Work"):
        self.reason = None
        super().__init__(parent, title)
    
    def body(self, master):
        """Create dialog body."""
        ttk.Label(
            master,
            text="Please enter the reason for your break:",
            font=('Segoe UI', 10)
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky='w')
        
        self.reason_entry = ttk.Entry(master, width=40, font=('Segoe UI', 10))
        self.reason_entry.grid(row=1, column=0, padx=10, pady=5)
        self.reason_entry.focus_set()
        
        return self.reason_entry
    
    def apply(self):
        """Process the input."""
        self.reason = self.reason_entry.get().strip()


class TimeLedgerApp:
    """Main application class for TimeLedger GUI."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TimeLedger - Work Hours Tracker")
        self.root.geometry("450x380")
        self.root.resizable(False, False)
        
        # Set app icon colors
        self.root.configure(bg='#f0f4f8')
        
        # Initialize tracker
        self.tracker: Optional[WorkTracker] = None
        self.db_connected = False
        
        # Timer update ID
        self._timer_id: Optional[str] = None
        
        # Build UI
        self._create_styles()
        self._build_ui()
        
        # Try to connect to database
        self._connect_to_db()
        
        # Start timer updates
        self._update_timer()
    
    def _create_styles(self):
        """Create custom ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure frame style
        style.configure('Card.TFrame', background='white')
        style.configure('App.TFrame', background='#f0f4f8')
        
        # Configure button styles
        style.configure(
            'Start.TButton',
            font=('Segoe UI', 11, 'bold'),
            padding=(20, 10)
        )
        style.map('Start.TButton',
            background=[('active', '#28a745'), ('!disabled', '#28a745')],
            foreground=[('!disabled', 'white')]
        )
        
        style.configure(
            'Pause.TButton',
            font=('Segoe UI', 11, 'bold'),
            padding=(20, 10)
        )
        style.map('Pause.TButton',
            background=[('active', '#ffc107'), ('!disabled', '#ffc107')],
            foreground=[('!disabled', 'black')]
        )
        
        style.configure(
            'Resume.TButton',
            font=('Segoe UI', 11, 'bold'),
            padding=(20, 10)
        )
        style.map('Resume.TButton',
            background=[('active', '#17a2b8'), ('!disabled', '#17a2b8')],
            foreground=[('!disabled', 'white')]
        )
        
        style.configure(
            'End.TButton',
            font=('Segoe UI', 11, 'bold'),
            padding=(20, 10)
        )
        style.map('End.TButton',
            background=[('active', '#dc3545'), ('!disabled', '#dc3545')],
            foreground=[('!disabled', 'white')]
        )
        
        style.configure(
            'Report.TButton',
            font=('Segoe UI', 10),
            padding=(15, 8)
        )
        
        # Label styles
        style.configure(
            'Title.TLabel',
            font=('Segoe UI', 18, 'bold'),
            background='#f0f4f8',
            foreground='#1a365d'
        )
        
        style.configure(
            'Status.TLabel',
            font=('Segoe UI', 14),
            background='white',
            padding=(10, 5)
        )
        
        style.configure(
            'Timer.TLabel',
            font=('Consolas', 32, 'bold'),
            background='white',
            foreground='#2c5282'
        )
        
        style.configure(
            'Date.TLabel',
            font=('Segoe UI', 10),
            background='#f0f4f8',
            foreground='#4a5568'
        )
    
    def _build_ui(self):
        """Build the main user interface."""
        main_frame = ttk.Frame(self.root, style='App.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title and date
        title_frame = ttk.Frame(main_frame, style='App.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            title_frame,
            text="⏱️ TimeLedger",
            style='Title.TLabel'
        ).pack(side=tk.LEFT)
        
        self.date_label = ttk.Label(
            title_frame,
            text=datetime.now().strftime("%A, %B %d, %Y"),
            style='Date.TLabel'
        )
        self.date_label.pack(side=tk.RIGHT, pady=(8, 0))
        
        # Status card
        status_card = ttk.Frame(main_frame, style='Card.TFrame')
        status_card.pack(fill=tk.X, pady=(0, 15))
        
        # Add padding inside card
        card_inner = ttk.Frame(status_card, style='Card.TFrame')
        card_inner.pack(fill=tk.X, padx=20, pady=15)
        
        # Status indicator
        status_row = ttk.Frame(card_inner, style='Card.TFrame')
        status_row.pack(fill=tk.X)
        
        ttk.Label(
            status_row,
            text="Status:",
            font=('Segoe UI', 11),
            background='white'
        ).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(
            status_row,
            text="Connecting...",
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Status indicator dot
        self.status_dot = tk.Canvas(
            status_row,
            width=16,
            height=16,
            bg='white',
            highlightthickness=0
        )
        self.status_dot.pack(side=tk.RIGHT)
        self._draw_status_dot('#9ca3af')  # Gray initially
        
        # Timer display
        timer_frame = ttk.Frame(card_inner, style='Card.TFrame')
        timer_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(
            timer_frame,
            text="Work Time:",
            font=('Segoe UI', 10),
            background='white',
            foreground='#4a5568'
        ).pack()
        
        self.timer_label = ttk.Label(
            timer_frame,
            text="00:00:00",
            style='Timer.TLabel'
        )
        self.timer_label.pack(pady=(5, 0))
        
        # Action buttons
        buttons_frame = ttk.Frame(main_frame, style='App.TFrame')
        buttons_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Configure grid
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        self.start_btn = tk.Button(
            buttons_frame,
            text="▶ Start Work",
            font=('Segoe UI', 11, 'bold'),
            bg='#28a745',
            fg='white',
            activebackground='#218838',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_start
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 5), pady=5, sticky='ew')
        
        self.pause_btn = tk.Button(
            buttons_frame,
            text="⏸ Pause",
            font=('Segoe UI', 11, 'bold'),
            bg='#ffc107',
            fg='black',
            activebackground='#e0a800',
            activeforeground='black',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_pause
        )
        self.pause_btn.grid(row=0, column=1, padx=(5, 0), pady=5, sticky='ew')
        
        self.resume_btn = tk.Button(
            buttons_frame,
            text="▶ Resume",
            font=('Segoe UI', 11, 'bold'),
            bg='#17a2b8',
            fg='white',
            activebackground='#138496',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_resume
        )
        self.resume_btn.grid(row=1, column=0, padx=(0, 5), pady=5, sticky='ew')
        
        self.end_btn = tk.Button(
            buttons_frame,
            text="⏹ End Day",
            font=('Segoe UI', 11, 'bold'),
            bg='#dc3545',
            fg='white',
            activebackground='#c82333',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_end
        )
        self.end_btn.grid(row=1, column=1, padx=(5, 0), pady=5, sticky='ew')
        
        # Generate Report button
        self.report_btn = tk.Button(
            main_frame,
            text="📊 Generate Report",
            font=('Segoe UI', 10),
            bg='#6c757d',
            fg='white',
            activebackground='#5a6268',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_generate_report
        )
        self.report_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Connection status
        self.connection_label = ttk.Label(
            main_frame,
            text="",
            font=('Segoe UI', 9),
            background='#f0f4f8',
            foreground='#718096'
        )
        self.connection_label.pack()
        
        # Initial button states
        self._update_button_states()
    
    def _draw_status_dot(self, color: str):
        """Draw the status indicator dot."""
        self.status_dot.delete('all')
        self.status_dot.create_oval(2, 2, 14, 14, fill=color, outline='')
    
    def _connect_to_db(self):
        """Attempt to connect to the database."""
        try:
            if test_connection():
                self.db_connected = True
                self.tracker = WorkTracker()
                self.connection_label.configure(
                    text="✓ Connected to MongoDB Atlas",
                    foreground='#38a169'
                )
                
                # Check if there's an active session and prompt user
                if self.tracker.has_active_session():
                    self._prompt_session_choice()
                else:
                    self._update_status()
            else:
                raise DatabaseConnectionError("Connection test failed")
        except DatabaseConnectionError as e:
            self.db_connected = False
            self.connection_label.configure(
                text="✗ Database connection failed",
                foreground='#e53e3e'
            )
            self.status_label.configure(text="Disconnected")
            self._draw_status_dot('#e53e3e')
            
            messagebox.showerror(
                "Connection Error",
                f"Failed to connect to MongoDB Atlas.\n\n"
                f"Please ensure:\n"
                f"1. Your .env file contains a valid MONGODB_URI\n"
                f"2. Your IP is whitelisted in MongoDB Atlas\n"
                f"3. Your internet connection is working\n\n"
                f"Error: {str(e)}"
            )
    
    def _prompt_session_choice(self):
        """Prompt the user to choose between resuming previous session or starting fresh."""
        status = "working" if self.tracker.is_working else "on a break"
        
        choice = messagebox.askyesno(
            "Previous Session Detected",
            f"You have an active session from earlier today.\n\n"
            f"Current status: {status.title()}\n\n"
            f"Would you like to RESUME your previous session?\n\n"
            f"• Click 'Yes' to continue where you left off\n"
            f"• Click 'No' to start fresh (previous session data is preserved)"
        )
        
        if choice:
            # User wants to resume - keep the restored state
            self._update_status()
        else:
            # User wants to start fresh - reset the state
            self.tracker.reset_state()
            self._update_status()
            messagebox.showinfo(
                "Fresh Start",
                "Starting fresh! Your previous session data is still saved in the database.\n\n"
                "Click 'Start Work' when you're ready to begin."
            )
    
    def _update_status(self):
        """Update the status display based on tracker state."""
        if not self.tracker:
            return
        
        status_text = self.tracker.get_status_text()
        self.status_label.configure(text=status_text)
        
        # Update status dot color
        color_map = {
            State.IDLE: '#9ca3af',      # Gray
            State.WORKING: '#38a169',   # Green
            State.PAUSED: '#f6ad55',    # Orange
            State.ENDED: '#e53e3e'      # Red
        }
        self._draw_status_dot(color_map.get(self.tracker.state, '#9ca3af'))
        
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button enabled/disabled states and colors."""
        # Disabled styling
        disabled_bg = '#cccccc'
        disabled_fg = '#666666'
        
        if not self.tracker or not self.db_connected:
            for btn in [self.start_btn, self.pause_btn, self.resume_btn, self.end_btn]:
                btn.configure(state=tk.DISABLED, bg=disabled_bg, fg=disabled_fg)
            return
        
        # Define enabled colors for each button
        button_config = {
            'start': (self.start_btn, self.tracker.can_start(), '#28a745', 'white'),
            'pause': (self.pause_btn, self.tracker.can_pause(), '#ffc107', 'black'),
            'resume': (self.resume_btn, self.tracker.can_resume(), '#17a2b8', 'white'),
            'end': (self.end_btn, self.tracker.can_end(), '#dc3545', 'white'),
        }
        
        for name, (btn, can_act, enabled_bg, enabled_fg) in button_config.items():
            if can_act:
                btn.configure(state=tk.NORMAL, bg=enabled_bg, fg=enabled_fg)
            else:
                btn.configure(state=tk.DISABLED, bg=disabled_bg, fg=disabled_fg)
    
    def _update_timer(self):
        """Update the elapsed time display."""
        if self.tracker and self.db_connected:
            elapsed = self.tracker.get_elapsed_work_time()
            
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            self.timer_label.configure(
                text=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            )
        
        # Schedule next update
        self._timer_id = self.root.after(1000, self._update_timer)
    
    def _on_start(self):
        """Handle Start Work button click."""
        if not self.tracker:
            return
        
        try:
            self.tracker.start_work()
            self._update_status()
        except InvalidTransitionError as e:
            messagebox.showwarning("Cannot Start", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start work: {e}")
    
    def _on_pause(self):
        """Handle Pause button click."""
        if not self.tracker:
            return
        
        # Show reason dialog
        dialog = PauseReasonDialog(self.root)
        
        if dialog.reason:
            try:
                self.tracker.pause_work(dialog.reason)
                self._update_status()
            except (InvalidTransitionError, ValueError) as e:
                messagebox.showwarning("Cannot Pause", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to pause: {e}")
    
    def _on_resume(self):
        """Handle Resume button click."""
        if not self.tracker:
            return
        
        try:
            self.tracker.resume_work()
            self._update_status()
        except InvalidTransitionError as e:
            messagebox.showwarning("Cannot Resume", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to resume: {e}")
    
    def _on_end(self):
        """Handle End Day button click."""
        if not self.tracker:
            return
        
        # Confirm action
        if not messagebox.askyesno(
            "End Day",
            "Are you sure you want to end your work day?\n\n"
            "This action cannot be undone and will lock today's records."
        ):
            return
        
        try:
            self.tracker.end_day()
            self._update_status()
            
            # Offer to generate report
            if messagebox.askyesno(
                "Generate Report",
                "Day ended successfully!\n\n"
                "Would you like to generate today's CSV report?"
            ):
                self._on_generate_report()
                
        except InvalidTransitionError as e:
            messagebox.showwarning("Cannot End Day", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to end day: {e}")
    
    def _on_generate_report(self):
        """Handle Generate Report button click."""
        try:
            filepath = generate_today_report()
            messagebox.showinfo(
                "Report Generated",
                f"Report saved successfully!\n\n📁 {filepath}"
            )
        except Exception as e:
            messagebox.showerror(
                "Report Error",
                f"Failed to generate report:\n\n{e}"
            )
    
    def on_closing(self):
        """Handle window close event."""
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
        self.root.destroy()


def create_app() -> tk.Tk:
    """Create and return the main application window."""
    root = tk.Tk()
    app = TimeLedgerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    return root
