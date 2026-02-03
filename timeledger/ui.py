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


class ModernConfirmDialog(tk.Toplevel):
    """Custom premium-styled confirmation dialog."""
    def __init__(self, parent, title, message, colors):
        super().__init__(parent)
        self.result = False
        self.colors = colors
        
        self.title(title)
        self.geometry("380x200")
        self.resizable(False, False)
        self.configure(bg=colors['bg'])
        
        # Center in parent
        self.transient(parent)
        self.grab_set()
        
        # UI components
        container = tk.Frame(self, bg=colors['bg'], padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            container, text=message, font=('Segoe UI', 11), 
            fg=colors['text'], bg=colors['bg'], wraplength=320, justify='center'
        ).pack(pady=(0, 25))
        
        btns = tk.Frame(container, bg=colors['bg'])
        btns.pack(fill=tk.X)
        btns.columnconfigure(0, weight=1, uniform='b')
        btns.columnconfigure(1, weight=1, uniform='b')
        
        # Styling buttons
        tk.Button(
            btns, text="Cancel", font=('Segoe UI', 10, 'bold'),
            bg=colors['border'], fg=colors['muted'], activebackground=colors['border'],
            activeforeground=colors['muted'], relief=tk.FLAT,
            padx=20, pady=8, cursor='hand2', command=self._cancel
        ).grid(row=0, column=0, padx=(0, 10), sticky='ew')
        
        tk.Button(
            btns, text="Confirm", font=('Segoe UI', 10, 'bold'),
            bg=colors['primary'], fg='white', activebackground=colors['primary'],
            activeforeground='white', relief=tk.FLAT,
            padx=20, pady=8, cursor='hand2', command=self._confirm
        ).grid(row=0, column=1, padx=(10, 0), sticky='ew')
        
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.wait_window()

    def _confirm(self):
        self.result = True
        self.destroy()

    def _cancel(self):
        self.result = False
        self.destroy()


class ModernInfoDialog(tk.Toplevel):
    """Custom premium-styled information dialog."""
    def __init__(self, parent, title, message, colors):
        super().__init__(parent)
        self.colors = colors
        
        self.title(title)
        self.geometry("400x220")
        self.resizable(False, False)
        self.configure(bg=colors['bg'])
        
        self.transient(parent)
        self.grab_set()
        
        container = tk.Frame(self, bg=colors['bg'], padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            container, text="🎉 Success!", font=('Segoe UI', 14, 'bold'), 
            fg=colors['success'], bg=colors['bg']
        ).pack(pady=(0, 15))
        
        tk.Label(
            container, text=message, font=('Segoe UI', 10), 
            fg=colors['text'], bg=colors['bg'], wraplength=340, justify='center'
        ).pack(pady=(0, 25))
        
        tk.Button(
            container, text="Excellent", font=('Segoe UI', 10, 'bold'),
            bg=colors['primary'], fg='white', relief=tk.FLAT,
            padx=30, pady=8, cursor='hand2', command=self.destroy
        ).pack(fill=tk.X)
        
        self.wait_window()


class ModernErrorDialog(tk.Toplevel):
    """Custom premium-styled error dialog."""
    def __init__(self, parent, title, message, colors):
        super().__init__(parent)
        self.colors = colors
        
        self.title(title)
        self.geometry("400x220")
        self.resizable(False, False)
        self.configure(bg=colors['bg'])
        
        self.transient(parent)
        self.grab_set()
        
        container = tk.Frame(self, bg=colors['bg'], padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            container, text="⚠️ Attention", font=('Segoe UI', 14, 'bold'), 
            fg=colors['danger'], bg=colors['bg']
        ).pack(pady=(0, 15))
        
        tk.Label(
            container, text=message, font=('Segoe UI', 10), 
            fg=colors['text'], bg=colors['bg'], wraplength=340, justify='center'
        ).pack(pady=(0, 25))
        
        tk.Button(
            container, text="Close", font=('Segoe UI', 10, 'bold'),
            bg=colors['border'], fg=colors['muted'], relief=tk.FLAT,
            padx=30, pady=8, cursor='hand2', command=self.destroy
        ).pack(fill=tk.X)
        
        self.wait_window()


class ModernInputDialog(tk.Toplevel):
    """Custom premium-styled input dialog."""
    def __init__(self, parent, title, prompt, colors):
        super().__init__(parent)
        self.result = None
        self.colors = colors
        
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(bg=colors['bg'])
        
        self.transient(parent)
        self.grab_set()
        
        container = tk.Frame(self, bg=colors['bg'], padx=30, pady=25)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            container, text=prompt, font=('Segoe UI', 11), 
            fg=colors['text'], bg=colors['bg']
        ).pack(anchor='w', pady=(0, 10))
        
        self.entry = tk.Entry(
            container, font=('Segoe UI', 11), bg=colors['card'],
            relief=tk.FLAT, highlightbackground=colors['border'],
            highlightthickness=1, insertbackground=colors['primary']
        )
        self.entry.pack(fill=tk.X, ipady=8, pady=(0, 20))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._submit())
        
        btns = tk.Frame(container, bg=colors['bg'])
        btns.pack(fill=tk.X)
        btns.columnconfigure(0, weight=1, uniform='b')
        btns.columnconfigure(1, weight=1, uniform='b')
        
        tk.Button(
            btns, text="Cancel", font=('Segoe UI', 10, 'bold'),
            bg=colors['border'], fg=colors['muted'], relief=tk.FLAT,
            padx=20, pady=8, cursor='hand2', command=self._cancel
        ).grid(row=0, column=0, padx=(0, 10), sticky='ew')
        
        tk.Button(
            btns, text="Confirm", font=('Segoe UI', 10, 'bold'),
            bg=colors['primary'], fg='white', relief=tk.FLAT,
            padx=20, pady=8, cursor='hand2', command=self._submit
        ).grid(row=0, column=1, padx=(10, 0), sticky='ew')
        
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.wait_window()

    def _submit(self):
        val = self.entry.get().strip()
        if val:
            self.result = val
            self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class TimeLedgerApp:
    """Main application class for TimeLedger GUI with modern overhaul."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TimeLedger")
        self.root.geometry("510x720")
        self.root.resizable(False, False)
        
        # Modern Color Palette
        self.colors = {
            'bg': '#F8FAFC',
            'card': '#FFFFFF',
            'primary': '#3B82F6',
            'success': '#10B981',
            'warning': '#F59E0B',
            'danger': '#EF4444',
            'text': '#1E293B',
            'muted': '#64748B',
            'border': '#E2E8F0'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Initialize tracker
        self.tracker: Optional[WorkTracker] = None
        self.db_connected = False
        self._timer_id: Optional[str] = None
        
        self._build_ui()
        self._connect_to_db()
        self._update_timer()
        
    def _build_ui(self):
        """Build the dashboard-style UI."""
        # Main container with padding
        self.main_container = tk.Frame(self.root, bg=self.colors['bg'], padx=30, pady=25)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # --- Header ---
        header_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(
            header_frame, 
            text="TimeLedger", 
            font=('Segoe UI Variable Display', 26, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
        
        self.date_label = tk.Label(
            header_frame,
            text=datetime.now().strftime("%A, %B %d"),
            font=('Segoe UI', 10),
            fg=self.colors['muted'],
            bg=self.colors['bg']
        )
        self.date_label.pack(side=tk.RIGHT, pady=(12, 0))
        
        # --- Status Banner ---
        self.status_banner = tk.Frame(self.main_container, bg=self.colors['card'], padx=15, pady=12, highlightbackground=self.colors['border'], highlightthickness=1)
        self.status_banner.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(self.status_banner, text="Status:", font=('Segoe UI', 10), fg=self.colors['muted'], bg=self.colors['card']).pack(side=tk.LEFT)
        self.status_text = tk.Label(self.status_banner, text="Connecting...", font=('Segoe UI', 10, 'bold'), fg=self.colors['text'], bg=self.colors['card'])
        self.status_text.pack(side=tk.LEFT, padx=8)
        
        self.status_dot_container = tk.Frame(self.status_banner, bg=self.colors['card'])
        self.status_dot_container.pack(side=tk.RIGHT)
        self.status_dot = tk.Canvas(self.status_dot_container, width=12, height=12, bg=self.colors['card'], highlightthickness=0)
        self.status_dot.pack(padx=2)
        self._draw_status_dot('#94A3B8')

        # --- Dashboard Grid (2x2) ---
        grid_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        grid_frame.pack(fill=tk.X, pady=(0, 25))
        grid_frame.columnconfigure(0, weight=1, uniform='card_col')
        grid_frame.columnconfigure(1, weight=1, uniform='card_col')
        
        self.cards = {}
        # Changed icons to common emojis for better compatibility
        card_info = [
            ('session', 'Current Session', '🕒', 0, 0),
            ('today', 'Today Total', '📅', 0, 1),
            ('week', 'This Week', '🗓️', 1, 0),
            ('month', 'This Month', '📊', 1, 1)
        ]
        
        for key, title, icon, r, c in card_info:
            card = self._create_stat_card(grid_frame, title, icon)
            padx = (0, 8) if c == 0 else (8, 0)
            card['frame'].grid(row=r, column=c, padx=padx, pady=8, sticky='nsew')
            self.cards[key] = card

        # --- Primary Controls ---
        btns_container = tk.Frame(self.main_container, bg=self.colors['bg'])
        btns_container.pack(fill=tk.X)
        btns_container.columnconfigure(0, weight=1, uniform='btn_col')
        btns_container.columnconfigure(1, weight=1, uniform='btn_col')
        
        self.start_btn = self._create_modern_button(btns_container, "▶ Start Work", self.colors['success'], self._on_start)
        self.start_btn.grid(row=0, column=0, padx=(0, 6), pady=6, sticky='ew')
        
        self.pause_btn = self._create_modern_button(btns_container, "⏸ Pause", self.colors['warning'], self._on_pause, fg='black')
        self.pause_btn.grid(row=0, column=1, padx=(6, 0), pady=6, sticky='ew')
        
        self.resume_btn = self._create_modern_button(btns_container, "🔄 Resume", self.colors['primary'], self._on_resume)
        self.resume_btn.grid(row=1, column=0, padx=(0, 6), pady=6, sticky='ew')
        
        self.end_btn = self._create_modern_button(btns_container, "⏹ End Day", self.colors['danger'], self._on_end)
        self.end_btn.grid(row=1, column=1, padx=(6, 0), pady=6, sticky='ew')
        
        # Report Button
        report_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        report_frame.pack(fill=tk.X, pady=(20, 0))
        self.report_btn = self._create_modern_button(report_frame, "📊 Generate Detailed Report", self.colors['muted'], self._on_generate_report)
        self.report_btn.pack(fill=tk.X)

    def _create_stat_card(self, parent, title, icon):
        """Create a styled stat card."""
        f = tk.Frame(parent, bg=self.colors['card'], padx=18, pady=18, highlightbackground=self.colors['border'], highlightthickness=1)
        
        tk.Label(f, text=f"{icon} {title}", font=('Segoe UI', 9), fg=self.colors['muted'], bg=self.colors['card']).pack(anchor='w')
        val = tk.Label(f, text="0m", font=('Segoe UI Variable Display', 20, 'bold'), fg=self.colors['text'], bg=self.colors['card'])
        val.pack(anchor='w', pady=(8, 0))
        
        return {'frame': f, 'label': val}

    def _create_modern_button(self, parent, text, color, command, fg='white'):
        """Create a premium styled button."""
        btn = tk.Button(
            parent,
            text=text,
            font=('Segoe UI', 10, 'bold'),
            bg=color,
            fg=fg,
            activebackground=color,
            activeforeground=fg,
            relief=tk.FLAT,
            cursor='hand2',
            command=command,
            pady=10
        )
        return btn

    def _draw_status_dot(self, color):
        self.status_dot.delete('all')
        self.status_dot.create_oval(1, 1, 9, 9, fill=color, outline='')

    def _connect_to_db(self):
        try:
            if test_connection():
                self.db_connected = True
                self.tracker = WorkTracker()
                if self.tracker.has_active_session():
                    self._prompt_session_choice()
                else:
                    self._update_status()
            else:
                raise DatabaseConnectionError("Conn failed")
        except Exception:
            self.db_connected = False
            self.status_text.configure(text="Disconnected", fg=self.colors['danger'])
            self._draw_status_dot(self.colors['danger'])

    def _update_status(self):
        if not self.tracker: return
        
        text = self.tracker.get_status_text()
        self.status_text.configure(text=text)
        
        cmap = {
            State.IDLE: '#94A3B8',
            State.WORKING: self.colors['success'],
            State.PAUSED: self.colors['warning'],
            State.ENDED: self.colors['danger']
        }
        self._draw_status_dot(cmap.get(self.tracker.state, '#94A3B8'))
        self._update_button_states()

    def _update_button_states(self):
        db_bg = '#E2E8F0'
        db_fg = '#94A3B8'
        
        configs = [
            (self.start_btn, self.tracker.can_start(), self.colors['success'], 'white'),
            (self.pause_btn, self.tracker.can_pause(), self.colors['warning'], 'black'),
            (self.resume_btn, self.tracker.can_resume(), self.colors['primary'], 'white'),
            (self.end_btn, self.tracker.can_end(), self.colors['danger'], 'white')
        ]
        
        for btn, enabled, bg, fg in configs:
            if enabled:
                btn.configure(state=tk.NORMAL, bg=bg, fg=fg)
            else:
                btn.configure(state=tk.DISABLED, bg=db_bg, fg=db_fg)

    def _format_seconds(self, s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        return f"{h:02d}:{m:02d}:{sec:02d}"

    def _update_timer(self):
        if self.tracker and self.db_connected:
            # Current Session (Interval since last Start/Resume)
            session_elapsed = self.tracker.get_current_session_time()
            self.cards['session']['label'].configure(text=self._format_seconds(session_elapsed))
            
            # Today Total (Cumulative for the day)
            today_elapsed = self.tracker.get_elapsed_work_time()
            self.cards['today']['label'].configure(text=self._format_seconds(today_elapsed))
            
            # Week & Month (maybe only update every 10s to be efficient)
            if not hasattr(self, '_long_update_counter'): self._long_update_counter = 0
            self._long_update_counter += 1
            
            if self._long_update_counter >= 10:
                self._long_update_counter = 0
                week_stats = self.tracker.get_weekly_stats()
                month_stats = self.tracker.get_monthly_stats()
                self.cards['week']['label'].configure(text=self._format_seconds(week_stats.work_seconds))
                self.cards['month']['label'].configure(text=self._format_seconds(month_stats.work_seconds))
        
        self._timer_id = self.root.after(1000, self._update_timer)

    # ... keeping event handlers similar but updated for new UI ...
    def _prompt_session_choice(self):
        diag = ModernConfirmDialog(
            self.root, "Resume Session?", 
            "You have an active session. Would you like to resume it?", 
            self.colors
        )
        if not diag.result: self.tracker.reset_state()
        self._update_status()

    def _on_start(self):
        try:
            self.tracker.start_work()
            self._update_status()
        except Exception as e: 
            ModernErrorDialog(self.root, "Error", str(e), self.colors)

    def _on_pause(self):
        diag = ModernInputDialog(
            self.root, "Pause Reason", 
            "Please enter the reason for your break:", 
            self.colors
        )
        if diag.result:
            try:
                self.tracker.pause_work(diag.result)
                self._update_status()
            except Exception as e: 
                ModernErrorDialog(self.root, "Error", str(e), self.colors)

    def _on_resume(self):
        try:
            self.tracker.resume_work()
            self._update_status()
        except Exception as e: 
            ModernErrorDialog(self.root, "Error", str(e), self.colors)

    def _on_end(self):
        diag = ModernConfirmDialog(
            self.root, "End Day", 
            "Are you sure you want to end your work day?", 
            self.colors
        )
        if diag.result:
            try:
                self.tracker.end_day()
                self._update_status()
                
                rep_diag = ModernConfirmDialog(
                    self.root, "Generate Report", 
                    "Day ended! Would you like to generate today's report?", 
                    self.colors
                )
                if rep_diag.result: self._on_generate_report()
            except Exception as e: 
                ModernErrorDialog(self.root, "Error", str(e), self.colors)

    def _on_generate_report(self):
        try:
            path = generate_today_report()
            ModernInfoDialog(self.root, "Success", f"Report saved:\n{path}", self.colors)
        except Exception as e: 
            ModernErrorDialog(self.root, "Error", str(e), self.colors)

    def on_closing(self):
        if self._timer_id: self.root.after_cancel(self._timer_id)
        self.root.destroy()



def create_app() -> tk.Tk:
    """Create and return the main application window."""
    root = tk.Tk()
    app = TimeLedgerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    return root
