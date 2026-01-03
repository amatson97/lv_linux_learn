"""
TimerManager - Centralized timer management for async operations

Eliminates 20+ duplicate GLib.timeout_add calls with magic numbers
"""
from typing import Callable, Any
from gi.repository import GLib


class TimerManager:
    """
    Centralized timer management for GLib async operations
    
    Provides semantic delay types instead of magic numbers, making
    timing intent clear and maintainable.
    """
    
    # Standard delays (milliseconds)
    IMMEDIATE = 50      # For very quick operations
    FAST = 100          # For UI refresh operations
    NORMAL = 500        # For standard async operations
    SLOW = 1500         # For completion delays
    
    @staticmethod
    def schedule(
        callback: Callable,
        delay_ms: int = None,
        delay_type: str = 'normal'
    ) -> int:
        """
        Schedule callback with semantic delay
        
        Args:
            callback: Function to call after delay
            delay_ms: Explicit delay in ms (overrides delay_type if provided)
            delay_type: Semantic delay type: 'immediate', 'fast', 'normal', 'slow'
        
        Returns:
            Timer ID (can be used with GLib.source_remove to cancel)
        """
        if delay_ms is None:
            delays = {
                'immediate': TimerManager.IMMEDIATE,
                'fast': TimerManager.FAST,
                'normal': TimerManager.NORMAL,
                'slow': TimerManager.SLOW,
            }
            delay_ms = delays.get(delay_type.lower(), TimerManager.NORMAL)
        
        return GLib.timeout_add(delay_ms, callback)
    
    @staticmethod
    def schedule_immediate(callback: Callable) -> int:
        """
        Schedule callback for immediate execution (50ms)
        
        Args:
            callback: Function to call
            
        Returns:
            Timer ID
        """
        return TimerManager.schedule(callback, delay_type='immediate')
    
    @staticmethod
    def schedule_ui_refresh(callback: Callable) -> int:
        """
        Schedule UI refresh operation (100ms - fast)
        
        Args:
            callback: Function to call
            
        Returns:
            Timer ID
        """
        return TimerManager.schedule(callback, delay_type='fast')
    
    @staticmethod
    def schedule_operation(callback: Callable) -> int:
        """
        Schedule standard async operation (500ms - normal)
        
        Args:
            callback: Function to call
            
        Returns:
            Timer ID
        """
        return TimerManager.schedule(callback, delay_type='normal')
    
    @staticmethod
    def schedule_completion(callback: Callable) -> int:
        """
        Schedule operation completion callback (1500ms - slow)
        
        Args:
            callback: Function to call
            
        Returns:
            Timer ID
        """
        return TimerManager.schedule(callback, delay_type='slow')
    
    @staticmethod
    def cancel(timer_id: int) -> bool:
        """
        Cancel a scheduled timer
        
        Args:
            timer_id: Timer ID returned from schedule methods
            
        Returns:
            True if timer was found and removed
        """
        return GLib.source_remove(timer_id)
