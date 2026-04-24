"""
Recorder module for macro generation.
Listens for mouse events, calculates relative coordinates based on the emulator's window,
and saves the macro to a JSON file.
"""
import time
import json
from pynput import mouse
from typing import List, Dict, Any, Optional

class Recorder:
    def __init__(self, window_manager):
        self.window_manager = window_manager
        self.macro: List[Dict[str, Any]] = []
        self.last_time: Optional[float] = None
        self.listener: Optional[mouse.Listener] = None
        self.is_recording = False

    def on_click(self, x: float, y: float, button: mouse.Button, pressed: bool):
        if not pressed or not self.is_recording:
            return

        if button != mouse.Button.left:
            return

        rect = self.window_manager.get_window_rect()
        if not rect:
            print("[Recorder] Emulator window not found. Skipping click.")
            return

        win_x, win_y, win_w, win_h = rect

        # Check if click is inside the window
        if win_x <= x <= win_x + win_w and win_y <= y <= win_y + win_h:
            rel_x = int(x - win_x)
            rel_y = int(y - win_y)

            current_time = time.time()
            if self.last_time is None:
                delay = 0.5 # Default start delay
            else:
                delay = current_time - self.last_time
            self.last_time = current_time

            action = {
                "action": "click",
                "rel_x": rel_x,
                "rel_y": rel_y,
                "delay": round(delay, 3)
            }
            self.macro.append(action)
            print(f"[Recorder] Recorded click at relative ({rel_x}, {rel_y}) after {delay:.2f}s delay.")
        else:
            print("[Recorder] Click outside emulator window. Ignored.")

    def start(self):
        self.macro = []
        self.last_time = None
        self.is_recording = True
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        print("[Recorder] Started recording.")

    def stop(self, filename: str = "macro.json"):
        self.is_recording = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.macro, f, indent=4)
        print(f"[Recorder] Stopped recording. Macro saved to {filename}.")
