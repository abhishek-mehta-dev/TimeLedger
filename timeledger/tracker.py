"""
Tracker module for TimeLedger - State management and time calculations.
Enforces valid state transitions and computes work/break durations.
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass

from .db import insert_event, get_events_for_date, get_today_events, get_events_for_range


class State(Enum):
    """Possible tracker states."""
    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    ENDED = "ended"


class Action(Enum):
    """Possible user actions."""
    START = "START"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    END = "END"


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


@dataclass
class TimeStats:
    """Statistics for a work day."""
    total_span_seconds: float
    break_seconds: float
    work_seconds: float
    break_count: int
    break_reasons: List[str]
    first_start: Optional[datetime]
    last_end: Optional[datetime]


class WorkTracker:
    """
    Manages work session state and time tracking.
    
    State transitions:
    - IDLE -> WORKING (Start)
    - WORKING -> PAUSED (Pause)
    - PAUSED -> WORKING (Resume)
    - WORKING -> ENDED (End Day)
    - PAUSED -> ENDED (End Day)
    """
    
    def __init__(self):
        self._state = State.IDLE
        self._current_date = datetime.now().strftime("%Y-%m-%d")
        self._work_start_time: Optional[datetime] = None
        self._work_end_time: Optional[datetime] = None
        self._pause_start_time: Optional[datetime] = None
        self._interval_start_time: Optional[datetime] = None
        self._total_break_seconds: float = 0.0
        self._break_reasons: List[str] = []
        
        # Restore state from database on startup
        self._restore_state()
    
    def _restore_state(self):
        """Restore state from today's events in the database."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # If it's a new day, reset state
        if self._current_date != today:
            self._current_date = today
            self._state = State.IDLE
            self._work_start_time = None
            self._work_end_time = None
            self._pause_start_time = None
            self._interval_start_time = None
            self._total_break_seconds = 0.0
            self._break_reasons = []
            return
        
        events = get_today_events()
        
        if not events:
            return
        
        # Process events to restore state
        pause_time = None
        
        for event in events:
            action = event.get("action")
            timestamp = datetime.fromisoformat(
                event.get("timestamp", "").replace("Z", "+00:00")
            )
            
            if action == Action.START.value:
                self._work_start_time = timestamp
                self._state = State.WORKING
            
            elif action == Action.PAUSE.value:
                pause_time = timestamp
                self._state = State.PAUSED
                reason = event.get("reason", "No reason")
                self._break_reasons.append(reason)
            
            elif action == Action.RESUME.value:
                if pause_time:
                    self._total_break_seconds += (timestamp - pause_time).total_seconds()
                    pause_time = None
                self._state = State.WORKING
                self._interval_start_time = timestamp
            
            elif action == Action.END.value:
                if pause_time:
                    self._total_break_seconds += (timestamp - pause_time).total_seconds()
                self._state = State.ENDED
                self._work_end_time = timestamp
                self._interval_start_time = None
    
    @property
    def state(self) -> State:
        """Get current state."""
        return self._state
    
    @property
    def is_working(self) -> bool:
        """Check if currently working."""
        return self._state == State.WORKING
    
    @property
    def is_paused(self) -> bool:
        """Check if currently on break."""
        return self._state == State.PAUSED
    
    @property
    def is_ended(self) -> bool:
        """Check if day has ended."""
        return self._state == State.ENDED
    
    @property
    def is_idle(self) -> bool:
        """Check if no session started."""
        return self._state == State.IDLE
    
    def _get_today(self) -> str:
        """Get today's date string."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def start_work(self) -> str:
        """
        Start a new work session.
        
        Returns:
            The event ID
        
        Raises:
            InvalidTransitionError: If not in IDLE state
        """
        if self._state != State.IDLE:
            raise InvalidTransitionError(
                f"Cannot start work from {self._state.value} state. "
                "Work can only be started from idle state."
            )
        
        self._current_date = self._get_today()
        event_id = insert_event(Action.START.value, self._current_date)
        
        self._state = State.WORKING
        self._work_start_time = datetime.now(timezone.utc)
        self._interval_start_time = self._work_start_time
        self._work_end_time = None
        
        return event_id
    
    def pause_work(self, reason: str) -> str:
        """
        Pause work with a reason.
        
        Args:
            reason: The reason for the pause
        
        Returns:
            The event ID
        
        Raises:
            InvalidTransitionError: If not in WORKING state
            ValueError: If reason is empty
        """
        if self._state != State.WORKING:
            raise InvalidTransitionError(
                f"Cannot pause from {self._state.value} state. "
                "Can only pause while working."
            )
        
        if not reason or not reason.strip():
            raise ValueError("Pause reason is required.")
        
        reason = reason.strip()
        event_id = insert_event(Action.PAUSE.value, self._current_date, reason)
        
        self._state = State.PAUSED
        self._pause_start_time = datetime.now(timezone.utc)
        self._interval_start_time = None
        self._break_reasons.append(reason)
        
        return event_id
    
    def resume_work(self) -> str:
        """
        Resume work after a pause.
        
        Returns:
            The event ID
        
        Raises:
            InvalidTransitionError: If not in PAUSED state
        """
        if self._state != State.PAUSED:
            raise InvalidTransitionError(
                f"Cannot resume from {self._state.value} state. "
                "Can only resume after a pause."
            )
        
        event_id = insert_event(Action.RESUME.value, self._current_date)
        
        # Calculate break duration
        if self._pause_start_time:
            break_duration = (datetime.now(timezone.utc) - self._pause_start_time).total_seconds()
            self._total_break_seconds += break_duration
        
        self._state = State.WORKING
        self._pause_start_time = None
        self._interval_start_time = datetime.now(timezone.utc)
        
        return event_id
    
    def end_day(self) -> str:
        """
        End the work day. Locks the day from further edits.
        
        Returns:
            The event ID
        
        Raises:
            InvalidTransitionError: If not in WORKING or PAUSED state
        """
        if self._state not in (State.WORKING, State.PAUSED):
            raise InvalidTransitionError(
                f"Cannot end day from {self._state.value} state. "
                "Can only end day while working or paused."
            )
        
        # If paused, count remaining break time
        if self._state == State.PAUSED and self._pause_start_time:
            break_duration = (datetime.now(timezone.utc) - self._pause_start_time).total_seconds()
            self._total_break_seconds += break_duration
        
        event_id = insert_event(Action.END.value, self._current_date)
        
        self._state = State.ENDED
        self._work_end_time = datetime.now(timezone.utc)
        self._interval_start_time = None
        
        return event_id
    
    def get_elapsed_work_time(self) -> float:
        """
        Get the elapsed working time in seconds (excluding breaks).
        
        Returns:
            Elapsed work time in seconds
        """
        if self._state == State.IDLE:
            return 0.0
        
        if self._work_start_time is None:
            return 0.0
            
        # Determine the end time for calculation
        if self._state == State.ENDED and self._work_end_time:
            end_time = self._work_end_time
        else:
            end_time = datetime.now(timezone.utc)
        
        total_elapsed = (end_time - self._work_start_time).total_seconds()
        
        # Subtract completed breaks
        work_time = total_elapsed - self._total_break_seconds
        
        # If currently paused, subtract current break time
        if self._state == State.PAUSED and self._pause_start_time:
            current_break = (end_time - self._pause_start_time).total_seconds()
            work_time -= current_break
        
        return max(0.0, work_time)
    
    def get_current_session_time(self) -> float:
        """
        Get the elapsed time in the CURRENT interval (since last start/resume).
        
        Returns:
            Elapsed session time in seconds
        """
        if self._state != State.WORKING or self._interval_start_time is None:
            return 0.0
            
        now = datetime.now(timezone.utc)
        return (now - self._interval_start_time).total_seconds()
    
    def get_stats_for_date(self, date: str) -> TimeStats:
        """
        Calculate time statistics for a given date from stored events.
        
        Args:
            date: The date in YYYY-MM-DD format
        
        Returns:
            TimeStats dataclass with calculated values
        """
        events = get_events_for_date(date)
        
        if not events:
            return TimeStats(
                total_span_seconds=0,
                break_seconds=0,
                work_seconds=0,
                break_count=0,
                break_reasons=[],
                first_start=None,
                last_end=None
            )
        
        first_start: Optional[datetime] = None
        last_end: Optional[datetime] = None
        pause_time: Optional[datetime] = None
        total_break_seconds = 0.0
        break_count = 0
        break_reasons = []
        
        for event in events:
            action = event.get("action")
            timestamp = datetime.fromisoformat(
                event.get("timestamp", "").replace("Z", "+00:00")
            )
            
            if action == Action.START.value:
                first_start = timestamp
            
            elif action == Action.PAUSE.value:
                pause_time = timestamp
                break_count += 1
                reason = event.get("reason", "No reason")
                break_reasons.append(reason)
            
            elif action == Action.RESUME.value:
                if pause_time:
                    total_break_seconds += (timestamp - pause_time).total_seconds()
                    pause_time = None
            
            elif action == Action.END.value:
                last_end = timestamp
                if pause_time:
                    total_break_seconds += (timestamp - pause_time).total_seconds()
        
        # Calculate total span
        total_span_seconds = 0.0
        if first_start and last_end:
            total_span_seconds = (last_end - first_start).total_seconds()
        
        # Calculate work time
        work_seconds = total_span_seconds - total_break_seconds
        
        return TimeStats(
            total_span_seconds=total_span_seconds,
            break_seconds=total_break_seconds,
            work_seconds=max(0, work_seconds),
            break_count=break_count,
            break_reasons=break_reasons,
            first_start=first_start,
            last_end=last_end
        )
    
    def get_stats_for_range(self, start_date: str, end_date: str) -> TimeStats:
        """
        Calculate aggregate time statistics for a date range.
        
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            
        Returns:
            TimeStats object with aggregated values
        """
        events = get_events_for_range(start_date, end_date)
        
        if not events:
            return TimeStats(0, 0, 0, 0, [], None, None)
            
        # Group events by date
        events_by_date = {}
        for event in events:
            date = event.get("date")
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(event)
            
        total_work_seconds = 0.0
        total_break_seconds = 0.0
        total_break_count = 0
        all_reasons = []
        first_start = None
        last_end = None
        
        for date, date_events in events_by_date.items():
            # For each date, calculate stats
            # This logic is similar to get_stats_for_date but we aggregate
            d_first_start = None
            d_last_end = None
            d_pause_time = None
            d_break_seconds = 0.0
            d_break_count = 0
            
            for event in date_events:
                action = event.get("action")
                ts = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
                
                if action == Action.START.value:
                    if not d_first_start: d_first_start = ts
                    if not first_start or ts < first_start: first_start = ts
                elif action == Action.PAUSE.value:
                    d_pause_time = ts
                    d_break_count += 1
                    all_reasons.append(event.get("reason", "No reason"))
                elif action == Action.RESUME.value:
                    if d_pause_time:
                        d_break_seconds += (ts - d_pause_time).total_seconds()
                        d_pause_time = None
                elif action == Action.END.value:
                    d_last_end = ts
                    if not last_end or ts > last_end: last_end = ts
                    if d_pause_time:
                        d_break_seconds += (ts - d_pause_time).total_seconds()
            
            if d_first_start and d_last_end:
                span = (d_last_end - d_first_start).total_seconds()
                total_work_seconds += max(0, span - d_break_seconds)
                total_break_seconds += d_break_seconds
                total_break_count += d_break_count
                
        return TimeStats(
            total_span_seconds=total_work_seconds + total_break_seconds,
            break_seconds=total_break_seconds,
            work_seconds=total_work_seconds,
            break_count=total_break_count,
            break_reasons=all_reasons,
            first_start=first_start,
            last_end=last_end
        )

    def get_weekly_stats(self) -> TimeStats:
        """Get stats for the current week (Mon-Sun)."""
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        return self.get_stats_for_range(
            start_of_week.strftime("%Y-%m-%d"),
            end_of_week.strftime("%Y-%m-%d")
        )
        
    def get_monthly_stats(self) -> TimeStats:
        """Get stats for the current month."""
        now = datetime.now()
        start_of_month = now.replace(day=1)
        # End of month is tricky, but we can just use end_date = now for current activity
        # or calculate last day of month. For stats display, "This Month" usually means up to now.
        import calendar
        last_day = calendar.monthrange(now.year, now.month)[1]
        end_of_month = now.replace(day=last_day)
        
        return self.get_stats_for_range(
            start_of_month.strftime("%Y-%m-%d"),
            end_of_month.strftime("%Y-%m-%d")
        )

    def get_today_stats(self) -> TimeStats:
        """Get statistics for today."""
        return self.get_stats_for_date(self._get_today())
    
    def get_status_text(self) -> str:
        """Get human-readable status text."""
        status_map = {
            State.IDLE: "Ready to Start",
            State.WORKING: "Working",
            State.PAUSED: "On Break",
            State.ENDED: "Day Ended"
        }
        return status_map.get(self._state, "Unknown")
    
    def can_start(self) -> bool:
        """Check if Start action is available."""
        return self._state == State.IDLE
    
    def can_pause(self) -> bool:
        """Check if Pause action is available."""
        return self._state == State.WORKING
    
    def can_resume(self) -> bool:
        """Check if Resume action is available."""
        return self._state == State.PAUSED
    
    def can_end(self) -> bool:
        """Check if End Day action is available."""
        return self._state in (State.WORKING, State.PAUSED)
    
    def has_active_session(self) -> bool:
        """Check if there's an active session that was restored."""
        return self._state in (State.WORKING, State.PAUSED)
    
    def reset_state(self):
        """
        Reset the tracker state to IDLE for a fresh start.
        This does NOT delete any database records - it only resets the in-memory state.
        """
        self._state = State.IDLE
        self._work_start_time = None
        self._work_end_time = None
        self._pause_start_time = None
        self._interval_start_time = None
        self._total_break_seconds = 0.0
        self._break_reasons = []
