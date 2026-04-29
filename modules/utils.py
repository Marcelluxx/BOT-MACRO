"""
Utility functions for the desktop automation bot.
Includes anti-ban randomization methods like random offsets and easing.
"""
import time
import random
from typing import Tuple
import pyautogui

def random_sleep(base_time: float, min_extra: float = 0.05, max_extra: float = 0.2) -> None:
    """
    Sleeps for a base amount of time plus a random extra delay.
    
    Args:
        base_time (float): The base time to sleep in seconds.
        min_extra (float): Minimum extra random time.
        max_extra (float): Maximum extra random time.
    """
    sleep_time = base_time + random.uniform(min_extra, max_extra)
    time.sleep(sleep_time)

def random_offset(x: int, y: int, max_offset: int = 3) -> Tuple[int, int]:
    """
    Adds a random offset to x and y coordinates to simulate human inaccuracy.
    
    Args:
        x (int): Original X coordinate.
        y (int): Original Y coordinate.
        max_offset (int): Maximum absolute offset in pixels.
        
    Returns:
        Tuple[int, int]: The modified coordinates.
    """
    offset_x = random.randint(-max_offset, max_offset)
    offset_y = random.randint(-max_offset, max_offset)
    return x + offset_x, y + offset_y

def human_move_to(x: int, y: int, min_duration: float = 0.1, max_duration: float = 0.4) -> None:
    """
    Moves the mouse to the specified coordinates with a human-like easing.
    
    Args:
        x (int): Target X coordinate.
        y (int): Target Y coordinate.
        min_duration (float): Minimum time the movement should take.
        max_duration (float): Maximum time the movement should take.
    """
    duration = 0.2  # Fixed duration for deterministic behavior
    # Use easeOutQuad for a human-like deceleration towards the target
    pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)
