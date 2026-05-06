"""
Main entry point for the automation bot.
- Default: launches the visual GUI editor.
- With --cli flag: runs the original CLI game loop.
"""
import sys
import os

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def run_gui():
    """Launches the PyQt6 visual macro editor."""
    from PyQt6.QtWidgets import QApplication
    from gui.main_window import MainWindow
    from gui.styles import GLOBAL_STYLESHEET

    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    app.setStyle("Fusion")  # Consistent cross-platform look

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def run_cli():
    """Runs the original CLI-based game loop (legacy mode)."""
    import threading
    import time
    import keyboard
    import pyautogui
    from modules.window_manager import WindowManager
    from modules.recorder import Recorder
    from modules.player import Player
    from modules.vision import Vision
    from modules.notifier import notifier

    # PyAutoGUI fail-safe (moving mouse to a corner will abort)
    pyautogui.FAILSAFE = True

    # Configuration
    WINDOW_TITLE = "LDPlayer"

    # Global state
    stop_event = threading.Event()
    app_state = {"value": "IDLE"}  # IDLE, RECORDING, PLAYING

    def game_loop(window_manager, player, vision):
        while not stop_event.is_set():
            try:
                if app_state["value"] == "PLAYING":
                    window_manager.bring_to_front()
                    time.sleep(0.5)

                    rect = window_manager.get_window_rect()
                    if rect:
                        # Re-scan loop: click one popup at a time, re-screenshot after each
                        popup_cleared = False
                        for _ in range(20):  # Safety limit
                            matches = vision.find_all_templates(assets_dir="assets", region=rect)
                            if not matches:
                                break
                            abs_x, abs_y, name = matches[0]
                            print(f"[Main] Found popup ({name}) at ({abs_x}, {abs_y}). Clicking...")
                            pyautogui.click(abs_x, abs_y)
                            time.sleep(0.8)
                            popup_cleared = True
                        if popup_cleared:
                            continue

                    # Play macro
                    if player.load_macro("actions/macro.json"):
                        player.play(check_stop_callback=lambda: stop_event.is_set() or app_state["value"] != "PLAYING")
                    else:
                        print("[Main] Failed to load macro. Switching to IDLE.")
                        app_state["value"] = "IDLE"
                else:
                    time.sleep(0.5)
            except Exception as e:
                import html
                error_text = html.escape(str(e))
                print(f"[Main] Exception in game loop: {e}")
                notifier.send_message(f"⚠️ <b>Exception in Bot Loop</b>\n<pre>{error_text}</pre>")
                app_state["value"] = "IDLE"
                time.sleep(1)

    def toggle_record(recorder):
        if app_state["value"] == "PLAYING":
            print("[Hotkey] Cannot record while playing.")
            return
        if app_state["value"] == "RECORDING":
            recorder.stop()
            app_state["value"] = "IDLE"
        else:
            recorder.start()
            app_state["value"] = "RECORDING"

    def toggle_play():
        if app_state["value"] == "RECORDING":
            print("[Hotkey] Cannot play while recording.")
            return
        if app_state["value"] == "PLAYING":
            app_state["value"] = "IDLE"
            print("[Hotkey] Stopped playback.")
            notifier.send_message("⏹ <b>Playback Stopped</b>\nBot playback was stopped manually.")
        else:
            app_state["value"] = "PLAYING"
            print("[Hotkey] Started playback.")

    def insert_flag(recorder):
        if app_state["value"] == "RECORDING":
            recorder.insert_flag()

    def emergency_stop():
        print("\n[EMERGENCY STOP] Stopping all operations!")
        notifier.send_message("🛑 <b>Emergency Stop</b>\nBot was terminated via emergency stop (CLI).")
        stop_event.set()
        sys.exit(0)

    print("Initializing Desktop Automation Bot (CLI Mode)...")

    window_manager = WindowManager(WINDOW_TITLE)
    recorder = Recorder(window_manager)
    player = Player(window_manager)
    vision = Vision()

    keyboard.add_hotkey('F7', insert_flag, args=(recorder,))
    keyboard.add_hotkey('F8', toggle_record, args=(recorder,))
    keyboard.add_hotkey('F9', toggle_play)
    keyboard.add_hotkey('F12', emergency_stop)

    print("\n" + "=" * 40)
    print("Bot is ready! (CLI Mode)")
    print("Hotkeys:")
    print("  [F7]  - Insert Vision Scan Flag (during recording)")
    print("  [F8]  - Toggle Record Macro")
    print("  [F9]  - Toggle Play Macro Loop")
    print("  [F12] - Emergency Stop / Exit")
    print("=" * 40 + "\n")

    game_thread = threading.Thread(target=game_loop, args=(window_manager, player, vision))
    game_thread.daemon = True
    game_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        emergency_stop()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()
