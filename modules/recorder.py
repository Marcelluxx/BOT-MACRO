"""
Recorder module for macro generation.
Listens for mouse events, calculates relative coordinates based on the emulator's window,
and saves the macro in the new structured format.
Supports F7 flag insertion for vision_scan checkpoints.
"""
import time
import json
import os
import winsound
from pynput import mouse
from typing import List, Dict, Any, Optional
from .models import (
    Macro, Block, ClickBlock, VisionScanBlock, ScrollBlock, DragBlock,
    BLOCK_CLICK, BLOCK_VISION_SCAN, BLOCK_SCROLL, BLOCK_DRAG,
)
import math


class Recorder:
    def __init__(self, window_manager):
        self.window_manager = window_manager
        self.blocks: List[Block] = []
        self.last_time: Optional[float] = None
        self.listener: Optional[mouse.Listener] = None
        self.is_recording = False
        self.drag_start_pos = None
        self.drag_start_time = None
        self.delay_before_action = 0.5

    def on_click(self, x: float, y: float, button: mouse.Button, pressed: bool):
        """Handles mouse click events during recording."""
        if not self.is_recording:
            return

        if button != mouse.Button.left:
            return

        rect = self.window_manager.get_window_rect()
        if not rect:
            print("[Recorder] Emulator window not found. Skipping click.")
            return

        win_x, win_y, win_w, win_h = rect
        current_time = time.time()

        if pressed:
            # Check if click started inside the window
            if win_x <= x <= win_x + win_w and win_y <= y <= win_y + win_h:
                self.drag_start_pos = (x, y)
                self.drag_start_time = current_time
                if self.last_time is None:
                    self.delay_before_action = 0.5
                else:
                    self.delay_before_action = current_time - self.last_time
                self.last_time = current_time
            else:
                self.drag_start_pos = None
                print("[Recorder] Click start outside emulator window. Ignored.")
        else:
            if self.drag_start_pos is None:
                return  # Ignored start

            start_x, start_y = self.drag_start_pos
            rel_start_x = int(start_x - win_x)
            rel_start_y = int(start_y - win_y)

            rel_end_x = int(x - win_x)
            rel_end_y = int(y - win_y)

            distance = math.hypot(rel_end_x - rel_start_x, rel_end_y - rel_start_y)

            if distance > 10:  # Threshold for drag
                duration = current_time - self.drag_start_time
                block = DragBlock(
                    start_x=rel_start_x, start_y=rel_start_y,
                    end_x=rel_end_x, end_y=rel_end_y,
                    duration=round(duration, 3),
                    delay=round(self.delay_before_action, 3)
                )
                self.blocks.append(block)
                print(f"[Recorder] Recorded drag from ({rel_start_x}, {rel_start_y}) to ({rel_end_x}, {rel_end_y}) duration={duration:.2f}s after {self.delay_before_action:.2f}s delay.")
            else:
                block = ClickBlock(rel_x=rel_start_x, rel_y=rel_start_y, delay=round(self.delay_before_action, 3))
                self.blocks.append(block)
                print(f"[Recorder] Recorded click at relative ({rel_start_x}, {rel_start_y}) after {self.delay_before_action:.2f}s delay.")

            self.drag_start_pos = None
            self.last_time = current_time

    def on_scroll(self, x: float, y: float, dx: float, dy: float):
        """Handles mouse scroll events during recording."""
        if not self.is_recording:
            return

        rect = self.window_manager.get_window_rect()
        if not rect:
            return

        win_x, win_y, win_w, win_h = rect

        # Check if scroll is inside the window
        if win_x <= x <= win_x + win_w and win_y <= y <= win_y + win_h:
            rel_x = int(x - win_x)
            rel_y = int(y - win_y)

            current_time = time.time()
            if self.last_time is None:
                delay = 0.5
            else:
                delay = current_time - self.last_time
            self.last_time = current_time

            # dy is the scroll amount (usually 1 or -1 per notch)
            # We multiply by a factor if needed, but pynput's dy is standard
            block = ScrollBlock(
                rel_x=rel_x,
                rel_y=rel_y,
                amount=int(dy * 120),  # Normalize to Windows wheel units (120 per notch)
                delay=round(delay, 3)
            )
            self.blocks.append(block)
            print(f"[Recorder] Recorded scroll at ({rel_x}, {rel_y}) amount={dy} after {delay:.2f}s delay.")

    def insert_flag(self, threshold: float = 0.8):
        """
        Inserts a vision_scan flag/checkpoint at the current position in the recording.
        Called when the user presses F7 during recording.
        Emits an audible beep as feedback.
        """
        if not self.is_recording:
            print("[Recorder] Not recording. Cannot insert flag.")
            return

        block = VisionScanBlock(threshold=threshold)
        self.blocks.append(block)

        # Audible feedback: short beep
        try:
            winsound.Beep(1000, 200)  # 1000 Hz for 200ms
        except Exception:
            pass  # Silently ignore if beep fails (e.g., no audio device)

        print(f"[Recorder] 🚩 Flag inserted: vision_scan (threshold={threshold})")

    def start(self):
        """Starts recording mouse events."""
        self.blocks = []
        self.last_time = None
        self.is_recording = True
        self.listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        self.listener.start()
        print("[Recorder] Started recording. Press F7 to insert vision scan flags.")

    def stop(self, filename: str = "actions/macro.json", name: str = "Recorded Macro"):
        """
        Stops recording and saves the macro in the new structured format.

        Args:
            filename: Path to save the macro JSON file.
            name: Human-readable name for the macro.
        """
        self.is_recording = False
        if self.listener:
            self.listener.stop()
            self.listener = None

        macro = Macro(
            name=name,
            description=f"Recorded on {time.strftime('%Y-%m-%d %H:%M:%S')}",
            blocks=self.blocks,
        )
        macro.save(filename)
        print(f"[Recorder] Stopped recording. Macro saved to {filename} ({len(self.blocks)} blocks).")

    def get_blocks(self) -> List[Block]:
        """Returns the current list of recorded blocks."""
        return list(self.blocks)
