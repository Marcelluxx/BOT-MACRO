"""
Window Manager module.
Handles finding the emulator window and getting its dimensions.
"""
import win32gui
import win32con
from typing import Tuple, Optional

class WindowManager:
    """
    Manages the interaction with the target application window.
    """
    def __init__(self, window_title: str):
        """
        Initializes the WindowManager.
        
        Args:
            window_title (str): The exact or partial title of the window to target.
        """
        self.window_title = window_title
        self.hwnd = None

    def find_window(self) -> bool:
        """
        Attempts to find the window by its title.
        
        Returns:
            bool: True if the window was found, False otherwise.
        """
        self.hwnd = win32gui.FindWindow(None, self.window_title)
        return self.hwnd != 0

    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Gets the bounding box of the window.
        
        Returns:
            Optional[Tuple[int, int, int, int]]: A tuple of (left, top, width, height) 
                                                 or None if the window is not found.
        """
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            if not self.find_window():
                return None
        
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            left = rect[0]
            top = rect[1]
            right = rect[2]
            bottom = rect[3]
            width = right - left
            height = bottom - top
            return (left, top, width, height)
        except Exception:
            return None

    def bring_to_front(self) -> bool:
        """
        Brings the window to the foreground.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.hwnd:
            if not self.find_window():
                return False
        try:
            # If the window is minimized, restore it
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            
            win32gui.SetForegroundWindow(self.hwnd)
            return True
        except Exception:
            return False
