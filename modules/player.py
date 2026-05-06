"""
Player module for macro execution.
Reads the structured JSON macro file and executes all block types
with anti-ban logic. Supports recursive sub-macro execution.
"""
import os
import json
import time
import random
from typing import List, Dict, Any, Optional, Callable
import pyautogui
from .models import (
    Macro, Block, ClickBlock, DelayBlock, VisionScanBlock, SubMacroBlock, ScrollBlock, DragBlock, PeriodicBlock, ImageCheckBlock, LoopBlock,
    BLOCK_CLICK, BLOCK_DELAY, BLOCK_VISION_SCAN, BLOCK_SUB_MACRO, BLOCK_SCROLL, BLOCK_DRAG, BLOCK_PERIODIC, BLOCK_IMAGE_CHECK, BLOCK_LOOP,
)
from .utils import random_offset, human_move_to
from .vision import Vision
from .notifier import notifier


class ContinueLoopException(Exception):
    """Raised when a block (like ImageCheck) requests to skip the current loop iteration."""
    pass


class Player:
    def __init__(self, window_manager, vision: Optional[Vision] = None):
        self.window_manager = window_manager
        self.vision = vision or Vision()
        self.macro: Optional[Macro] = None
        self.is_playing = False
        self._max_recursion_depth = 5  # Prevent infinite sub-macro loops
        self.iteration_count = 0  # Tracks main loop iterations for periodic blocks

    def _get_valid_rect(self):
        """Returns the window rect only if the window is visible and on-screen."""
        rect = self.window_manager.get_window_rect()
        if not rect:
            return None
        left, top, width, height = rect
        # Windows uses -32000 for minimized windows
        if left <= -30000 or top <= -30000 or width <= 0 or height <= 0:
            print("[Player] Emulator window is minimized or off-screen. Skipping action.")
            return None
        return rect

    def load_macro(self, filename: str = "actions/macro.json") -> bool:
        """
        Loads a macro from a JSON file.
        Supports both legacy format (flat array) and new structured format.
        """
        try:
            self.macro = Macro.load(filename)
            print(f"[Player] Loaded macro '{self.macro.name}' with {len(self.macro.blocks)} blocks.")
            return True
        except FileNotFoundError:
            print(f"[Player] Error: {filename} not found.")
            return False
        except Exception as e:
            print(f"[Player] Error loading macro: {e}")
            return False

    def play(self, check_stop_callback: Optional[Callable[[], bool]] = None, on_abort_callback: Optional[Callable[[], None]] = None, _depth: int = 0):
        """
        Executes the loaded macro sequentially.

        Args:
            check_stop_callback: Function that returns True when playback should stop.
            on_abort_callback: Function called when a terminal failure occurs (e.g. image check fail).
            _depth: Internal recursion counter for sub-macros.
        """
        if not self.macro or not self.macro.blocks:
            print("[Player] No macro loaded.")
            return

        if _depth > self._max_recursion_depth:
            print(f"[Player] Max sub-macro recursion depth ({self._max_recursion_depth}) reached. Aborting.")
            return

        self.is_playing = True
        if _depth == 0:
            self.iteration_count += 1
            print(f"[Player] Started playback of '{self.macro.name}' (Iteration {self.iteration_count}).")
        else:
            print(f"[Player] {'  ' * _depth}Executing sub-macro '{self.macro.name}'...")

        try:
            for i, block in enumerate(self.macro.blocks):
                if not self.is_playing or (check_stop_callback and check_stop_callback()):
                    print(f"[Player] Playback interrupted at block {i + 1}.")
                    break

                self._execute_block(block, check_stop_callback, on_abort_callback, _depth)
        except ContinueLoopException:
            if _depth == 0:
                print(f"[Player] Macro run skipped (top-level skip).")
            else:
                # Re-raise so the parent loop can catch it
                raise

        if _depth == 0:
            self.is_playing = False
            print("[Player] Playback finished.")

    def _execute_block(
        self,
        block: Block,
        check_stop_callback: Optional[Callable[[], bool]],
        on_abort_callback: Optional[Callable[[], None]],
        depth: int,
    ):
        """Dispatches execution to the appropriate handler based on block type."""
        if block.type == BLOCK_CLICK:
            self._execute_click(block, check_stop_callback)
        elif block.type == BLOCK_DELAY:
            self._execute_delay(block, check_stop_callback)
        elif block.type == BLOCK_VISION_SCAN:
            self._execute_vision_scan(block, check_stop_callback)
        elif block.type == BLOCK_SUB_MACRO:
            self._execute_sub_macro(block, check_stop_callback, on_abort_callback, depth)
        elif block.type == BLOCK_SCROLL:
            self._execute_scroll(block, check_stop_callback)
        elif block.type == BLOCK_DRAG:
            self._execute_drag(block, check_stop_callback)
        elif block.type == BLOCK_PERIODIC:
            self._execute_periodic(block, check_stop_callback, on_abort_callback, depth)
        elif block.type == BLOCK_IMAGE_CHECK:
            self._execute_image_check(block, check_stop_callback, on_abort_callback)
        elif block.type == BLOCK_LOOP:
            self._execute_loop(block, check_stop_callback, on_abort_callback, depth)
        else:
            print(f"[Player] Unknown block type: {block.type}. Skipping.")

    def _execute_click(self, block: ClickBlock, check_stop_callback):
        """Executes a click block with anti-ban randomization."""
        # Wait for the recorded delay
        self._safe_sleep(block.delay, check_stop_callback)

        if not self.is_playing or (check_stop_callback and check_stop_callback()):
            return

        rect = self._get_valid_rect()
        if not rect:
            return

        win_x, win_y, win_w, win_h = rect

        # Convert to absolute coordinates
        abs_x = win_x + block.rel_x
        abs_y = win_y + block.rel_y

        try:
            human_move_to(abs_x, abs_y)
            pyautogui.click(abs_x, abs_y)
            print(f"[Player] Clicked at absolute ({abs_x}, {abs_y})")
        except pyautogui.FailSafeException:
            print(f"[Player] FailSafe triggered at ({abs_x}, {abs_y}). Skipping click.")

    def _execute_scroll(self, block: ScrollBlock, check_stop_callback):
        """Executes a scroll block."""
        # Wait for the recorded delay
        self._safe_sleep(block.delay, check_stop_callback)

        if not self.is_playing or (check_stop_callback and check_stop_callback()):
            return

        rect = self._get_valid_rect()
        if not rect:
            return

        win_x, win_y, win_w, win_h = rect

        # Convert to absolute coordinates
        abs_x = win_x + block.rel_x
        abs_y = win_y + block.rel_y

        try:
            human_move_to(abs_x, abs_y)
            pyautogui.scroll(block.amount, x=abs_x, y=abs_y)
            print(f"[Player] Scrolled {block.amount} at absolute ({abs_x}, {abs_y})")
        except pyautogui.FailSafeException:
            print(f"[Player] FailSafe triggered at ({abs_x}, {abs_y}). Skipping scroll.")

    def _execute_drag(self, block: DragBlock, check_stop_callback):
        """Executes a drag block."""
        # Wait for the recorded delay
        self._safe_sleep(block.delay, check_stop_callback)

        if not self.is_playing or (check_stop_callback and check_stop_callback()):
            return

        rect = self._get_valid_rect()
        if not rect:
            return

        win_x, win_y, win_w, win_h = rect

        # Convert to absolute coordinates
        abs_start_x = win_x + block.start_x
        abs_start_y = win_y + block.start_y
        abs_end_x = win_x + block.end_x
        abs_end_y = win_y + block.end_y

        try:
            human_move_to(abs_start_x, abs_start_y)
            pyautogui.dragTo(abs_end_x, abs_end_y, duration=block.duration, button='left')
            print(f"[Player] Dragged from absolute ({abs_start_x}, {abs_start_y}) to ({abs_end_x}, {abs_end_y})")
        except pyautogui.FailSafeException:
            print(f"[Player] FailSafe triggered during drag. Skipping.")

    def _execute_delay(self, block: DelayBlock, check_stop_callback):
        """Executes a delay block."""
        print(f"[Player] Waiting {block.duration:.1f}s...")
        self._safe_sleep(block.duration, check_stop_callback)

    def _execute_vision_scan(self, block: VisionScanBlock, check_stop_callback):
        """
        Executes a vision scan using a re-scan loop to handle layered/stacked popups.

        Strategy:
        1. Take a fresh screenshot
        2. Find ALL matching popup assets on screen
        3. Click every match found in this pass, one by one
        4. Wait briefly after each click for the popup to close
        5. Take a NEW screenshot and repeat from step 2
        6. Stop when no more matches are found

        This ensures ALL visible popups are dismissed before resuming the macro.
        After clicking everything visible, a re-scan catches any new popups
        that may have appeared underneath the ones we just closed.
        """
        MAX_PASSES = 20  # Safety limit to prevent infinite loops
        CLICK_SETTLE_TIME = 0.8  # Time to wait for a popup to close after clicking

        print(f"[Player] 👁️ Running vision scan (threshold={block.threshold})...")

        total_clicks = 0
        scan_pass = 0

        while scan_pass < MAX_PASSES:
            if not self.is_playing or (check_stop_callback and check_stop_callback()):
                print("[Player] Vision scan interrupted.")
                return

            scan_pass += 1

            # Fresh screenshot every pass
            rect = self._get_valid_rect()
            if not rect:
                break
            matches = self.vision.find_all_templates(
                assets_dir="assets/popups",
                region=rect,
                threshold=block.threshold,
            )

            if not matches:
                break  # Screen is clean — no more popups

            # Click ALL matches found in this pass, one by one
            clicks_this_pass = 0
            for abs_x, abs_y, asset_name in matches:
                if not self.is_playing or (check_stop_callback and check_stop_callback()):
                    print("[Player] Vision scan interrupted during clicking.")
                    return

                try:
                    human_move_to(abs_x, abs_y)
                    pyautogui.click(abs_x, abs_y)
                    total_clicks += 1
                    clicks_this_pass += 1
                    print(
                        f"[Player] Pass {scan_pass}: clicked '{asset_name}' "
                        f"at ({abs_x}, {abs_y})  "
                        f"[{clicks_this_pass}/{len(matches)} in this pass]"
                    )
                except pyautogui.FailSafeException:
                    print(f"[Player] FailSafe triggered during vision scan click. Stopping scan.")
                    break

                # Wait for the popup to close before clicking the next one
                self._safe_sleep(CLICK_SETTLE_TIME, check_stop_callback)

            # After clicking all matches, re-scan to check for new popups

        if total_clicks == 0:
            print("[Player] Vision scan: no popups found on screen.")
        else:
            print(
                f"[Player] Vision scan complete: {total_clicks} popup(s) dismissed "
                f"in {scan_pass} pass(es). Resuming macro."
            )

    def _execute_sub_macro(self, block: SubMacroBlock, check_stop_callback, on_abort_callback, depth: int):
        """Executes a sub-macro by loading and playing it recursively."""
        if not block.macro_file:
            print("[Player] Sub-macro block has no file specified. Skipping.")
            return

        print(f"[Player] Loading sub-macro: {block.macro_file}")

        # Create a temporary player for the sub-macro
        sub_player = Player(self.window_manager, self.vision)
        if sub_player.load_macro(block.macro_file):
            sub_player.is_playing = self.is_playing
            sub_player.play(check_stop_callback=check_stop_callback, on_abort_callback=on_abort_callback, _depth=depth + 1)
        else:
            print(f"[Player] Failed to load sub-macro: {block.macro_file}")

    def _execute_periodic(self, block: PeriodicBlock, check_stop_callback, on_abort_callback, depth: int):
        """Executes a sub-macro only every N iterations of the main loop."""
        if not block.macro_file:
            return

        # Check if we should execute this iteration
        # Using 1-indexed logic for user friendliness: Iteration 5, 10, 15...
        if self.iteration_count % block.n_iterations == 0:
            print(f"[Player] 🔄 Periodic trigger: iteration {self.iteration_count} is a multiple of {block.n_iterations}.")
            
            sub_player = Player(self.window_manager, self.vision)
            # Inherit iteration count so it stays consistent across sub-players if needed
            sub_player.iteration_count = self.iteration_count
            
            if sub_player.load_macro(block.macro_file):
                sub_player.is_playing = self.is_playing
                sub_player.play(check_stop_callback=check_stop_callback, on_abort_callback=on_abort_callback, _depth=depth + 1)
        else:
            print(f"[Player] 🔄 Periodic skip: iteration {self.iteration_count} is not a multiple of {block.n_iterations}.")

    # ── Recovery Constants ──
    RECOVERY_MAX_ATTEMPTS = 2
    RECOVERY_WAIT_SECONDS = 7

    def _attempt_recovery(self, block: ImageCheckBlock, check_stop_callback):
        """
        Attempts to recover from a failed image check by pressing ESC (LDPlayer Back)
        and waiting for the game to reload.

        Returns True if recovery succeeded (image found after retry), False otherwise.
        """
        for attempt in range(1, self.RECOVERY_MAX_ATTEMPTS + 1):
            if not self.is_playing or (check_stop_callback and check_stop_callback()):
                return False

            print(f"[Player] 🔧 Recovery attempt {attempt}/{self.RECOVERY_MAX_ATTEMPTS}: pressing ESC (Back)...")
            notifier.send_message(
                f"🔧 <b>Recovery Attempt {attempt}/{self.RECOVERY_MAX_ATTEMPTS}</b>\n"
                f"Image check failed. Pressing Back and waiting {self.RECOVERY_WAIT_SECONDS}s..."
            )

            # Bring LDPlayer to front and send Back key
            self.window_manager.bring_to_front()
            time.sleep(0.3)
            try:
                pyautogui.press('escape')
            except pyautogui.FailSafeException:
                print("[Player] 🔧 FailSafe triggered during recovery ESC press.")
                return False

            # Wait for the game to reload
            print(f"[Player] 🔧 Waiting {self.RECOVERY_WAIT_SECONDS}s for game to reload...")
            self._safe_sleep(self.RECOVERY_WAIT_SECONDS, check_stop_callback)

            if not self.is_playing or (check_stop_callback and check_stop_callback()):
                return False

            # Re-check the image
            rect = self._get_valid_rect()
            if not rect:
                print("[Player] 🔧 Recovery: window not visible. Retrying...")
                continue

            match = self.vision.find_template(
                template_path=block.image_path,
                region=rect,
                threshold=block.threshold,
            )

            if match:
                print(f"[Player] 🔧 Recovery SUCCESS! Image found at {match}.")
                notifier.send_message("✅ <b>Recovery Succeeded</b>\nGame is back. Resuming macro.")
                return True
            else:
                print(f"[Player] 🔧 Recovery attempt {attempt} failed: image still not found.")

        return False

    def _execute_image_check(self, block: ImageCheckBlock, check_stop_callback, on_abort_callback):
        """
        Executes an image check. If the image is not found within the threshold,
        behavior depends on on_fail:
        - 'continue_loop': skip current loop iteration
        - 'abort': attempt auto-recovery first, then abort if recovery fails
        """
        if not block.image_path:
            print("[Player] 🛡️ Image check: no image path specified. Skipping check.")
            return

        print(f"[Player] 🛡️ Checking for image: {os.path.basename(block.image_path)} (threshold={block.threshold:.2f})")

        rect = self._get_valid_rect()
        match = self.vision.find_template(
            template_path=block.image_path,
            region=rect,
            threshold=block.threshold,
        )

        if match:
            print(f"[Player] 🛡️ Image check passed: image found at {match}.")
            if block.click_if_found:
                abs_x, abs_y = match
                try:
                    human_move_to(abs_x, abs_y)
                    pyautogui.click(abs_x, abs_y)
                    print(f"[Player] 🛡️ Action: clicked on found image at ({abs_x}, {abs_y})")
                    # Settle time after click
                    time.sleep(0.5)
                except pyautogui.FailSafeException:
                    print(f"[Player] 🛡️ FailSafe triggered during image check click.")
        else:
            print(f"[Player] 🛡️ Image check FAILED: image NOT found.")
            if block.on_fail == "continue_loop":
                print("[Player] 🛡️ Action: skipping iteration (continue loop).")
                raise ContinueLoopException()
            else:
                # Attempt auto-recovery before aborting
                print("[Player] 🛡️ Attempting auto-recovery...")
                if self._attempt_recovery(block, check_stop_callback):
                    # Recovery succeeded — let the macro continue naturally
                    print("[Player] 🛡️ Recovery complete. Continuing macro.")
                    return
                else:
                    print("[Player] 🛡️ Recovery FAILED. Stopping macro.")
                    notifier.send_message(
                        "🛑 <b>Macro Aborted</b>\n"
                        f"Image check failed for <code>{os.path.basename(block.image_path)}</code>.\n"
                        f"Auto-recovery failed after {self.RECOVERY_MAX_ATTEMPTS} attempts."
                    )
                    if on_abort_callback:
                        on_abort_callback()
                    self.stop()

    def _execute_loop(self, block: LoopBlock, check_stop_callback, on_abort_callback, depth: int):
        """Executes child blocks N times."""
        if not block.children:
            print("[Player] 🔁 Loop has no children. Skipping.")
            return

        print(f"[Player] 🔁 Starting loop: {block.iterations} iterations, {len(block.children)} children.")

        for iteration in range(1, block.iterations + 1):
            if not self.is_playing or (check_stop_callback and check_stop_callback()):
                print(f"[Player] 🔁 Loop interrupted at iteration {iteration}.")
                break

            print(f"[Player] 🔁 Loop iteration {iteration}/{block.iterations}")

            try:
                for child_block in block.children:
                    if not self.is_playing or (check_stop_callback and check_stop_callback()):
                        break
                    self._execute_block(child_block, check_stop_callback, on_abort_callback, depth + 1)
            except ContinueLoopException:
                print(f"[Player] 🔁 Iteration {iteration} skipped.")
                continue

        print(f"[Player] 🔁 Loop completed.")

    def stop(self):
        """Signals playback to stop."""
        self.is_playing = False

    def _safe_sleep(self, delay: float, check_stop_callback=None):
        """Sleeps in small chunks to allow for quick interruption."""
        target_sleep = delay
        start = time.time()
        while time.time() - start < target_sleep:
            if not self.is_playing or (check_stop_callback and check_stop_callback()):
                break
            time.sleep(0.1)
