"""
Player module for macro execution.
Reads the JSON macro file and executes it with anti-ban logic.
"""
import json
import time
import random
from typing import List, Dict, Any
import pyautogui
from .utils import random_offset, human_move_to

class Player:
    def __init__(self, window_manager):
        self.window_manager = window_manager
        self.macro: List[Dict[str, Any]] = []
        self.is_playing = False

    def load_macro(self, filename: str = "macro.json") -> bool:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.macro = json.load(f)
            return True
        except FileNotFoundError:
            print(f"[Player] Error: {filename} not found.")
            return False
        except Exception as e:
            print(f"[Player] Error loading macro: {e}")
            return False

    def play(self, check_stop_callback=None):
        if not self.macro:
            print("[Player] No macro loaded.")
            return

        self.is_playing = True
        print("[Player] Started playback.")

        for action in self.macro:
            if not self.is_playing or (check_stop_callback and check_stop_callback()):
                print("[Player] Playback interrupted.")
                break

            rect = self.window_manager.get_window_rect()
            if not rect:
                print("[Player] Emulator window not found. Halting playback.")
                break

            win_x, win_y, win_w, win_h = rect

            if action.get("action") == "click":
                # Wait for the recorded delay with added randomness
                delay = action.get("delay", 0.5)
                # Sleep in chunks to allow interruption
                self._safe_sleep(delay, check_stop_callback)
                
                if not self.is_playing or (check_stop_callback and check_stop_callback()):
                    break

                rel_x = action["rel_x"]
                rel_y = action["rel_y"]

                # Convert to absolute coordinates
                abs_x = win_x + rel_x
                abs_y = win_y + rel_y

                # Add anti-ban offset
                target_x, target_y = random_offset(abs_x, abs_y, max_offset=3)

                # Move and click
                human_move_to(target_x, target_y)
                pyautogui.click(target_x, target_y)
                print(f"[Player] Clicked at absolute ({target_x}, {target_y})")

        self.is_playing = False
        print("[Player] Playback finished.")

    def stop(self):
        self.is_playing = False

    def _safe_sleep(self, delay: float, check_stop_callback=None):
        """Sleeps in small chunks to allow for quick interruption and adds random extra time."""
        target_sleep = delay + random.uniform(0.05, 0.2)
        start = time.time()
        while time.time() - start < target_sleep:
            if not self.is_playing or (check_stop_callback and check_stop_callback()):
                break
            time.sleep(0.1)
