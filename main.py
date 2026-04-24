"""
Main entry point for the automation bot.
Manages global hotkeys, orchestrates the components, and runs the game loop.
"""
import sys
import threading
import time
import keyboard
import pyautogui
from modules.window_manager import WindowManager
from modules.recorder import Recorder
from modules.player import Player
from modules.vision import Vision

# PyAutoGUI fail-safe (moving mouse to a corner will abort)
pyautogui.FAILSAFE = True

# Configuration
WINDOW_TITLE = "LDPlayer"  # Set to LDPlayer
TEMPLATE_PATH = "assets/red_x.png"  # Image for popups

# Global state
stop_event = threading.Event()
app_state = "IDLE" # IDLE, RECORDING, PLAYING

def game_loop(window_manager: WindowManager, player: Player, vision: Vision):
    """
    The main game loop executed when playing.
    """
    global app_state
    
    while not stop_event.is_set():
        if app_state == "PLAYING":
            # 1. Bring window to front
            window_manager.bring_to_front()
            time.sleep(0.5)

            # 2. Check for popups (e.g. a red X)
            rect = window_manager.get_window_rect()
            if rect:
                # Utilizzo della vision per trovare e cliccare la X rossa
                match_pos = vision.find_template(TEMPLATE_PATH, region=rect)
                if match_pos:
                    print(f"[Main] Trovato popup a {match_pos}. Clicco...")
                    pyautogui.click(*match_pos)
                    time.sleep(1)
                    continue # Ricomincia il loop

            # 3. Play macro
            if player.load_macro("actions/macro.json"):
                player.play(check_stop_callback=lambda: stop_event.is_set() or app_state != "PLAYING")
            else:
                print("[Main] Failed to load macro. Switching to IDLE.")
                app_state = "IDLE"
                
        else:
            # When IDLE or RECORDING, just sleep to prevent high CPU usage
            time.sleep(0.5)

def toggle_record(recorder: Recorder):
    global app_state
    if app_state == "PLAYING":
        print("[Hotkey] Cannot record while playing. Stop playback first.")
        return
        
    if app_state == "RECORDING":
        recorder.stop()
        app_state = "IDLE"
    else:
        recorder.start()
        app_state = "RECORDING"

def toggle_play():
    global app_state
    if app_state == "RECORDING":
        print("[Hotkey] Cannot play while recording. Stop recording first.")
        return
        
    if app_state == "PLAYING":
        app_state = "IDLE"
        print("[Hotkey] Stopped playback. Now IDLE.")
    else:
        app_state = "PLAYING"
        print("[Hotkey] Started playback.")

def emergency_stop():
    print("\n[EMERGENCY STOP] Stopping all operations immediately!")
    stop_event.set()
    sys.exit(0)

def main():
    print("Initializing Desktop Automation Bot...")
    
    window_manager = WindowManager(WINDOW_TITLE)
    recorder = Recorder(window_manager)
    player = Player(window_manager)
    vision = Vision()

    # Set up global hotkeys
    keyboard.add_hotkey('F8', toggle_record, args=(recorder,))
    keyboard.add_hotkey('F9', toggle_play)
    keyboard.add_hotkey('esc', emergency_stop)
    
    print("\n" + "="*40)
    print("Bot is ready!")
    print("Hotkeys:")
    print("  [F8]  - Toggle Record Macro")
    print("  [F9]  - Toggle Play Macro Loop")
    print("  [ESC] - Emergency Stop / Exit")
    print("Note: PyAutoGUI Fail-Safe is active. Move mouse to any corner to abort.")
    print("="*40 + "\n")

    # Start the game loop thread
    game_thread = threading.Thread(target=game_loop, args=(window_manager, player, vision))
    game_thread.daemon = True
    game_thread.start()

    # Keep main thread alive to listen to hotkeys
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        emergency_stop()

if __name__ == "__main__":
    main()
