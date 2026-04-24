import time
import pyautogui
from modules.window_manager import WindowManager
from modules.vision import Vision

def test_red_x_click():
    """
    Test script to verify if the bot can find the LDPlayer window,
    locate the red x image, and click on it.
    """
    print("Initializing test for Red X Click...")
    
    window_title = "LDPlayer"
    template_path = "assets/red_x.png"
    
    window_manager = WindowManager(window_title)
    vision = Vision()
    
    print(f"Bringing '{window_title}' to front...")
    if not window_manager.bring_to_front():
        print(f"Failed to find or focus window '{window_title}'. Please ensure LDPlayer is running.")
        return

    time.sleep(1) # Give it a moment to bring to front
    
    rect = window_manager.get_window_rect()
    if not rect:
        print(f"Could not get coordinates for '{window_title}'.")
        return
        
    print(f"Window bounds: {rect}. Searching for '{template_path}'...")
    match_pos = vision.find_template(template_path, region=rect)
    
    if match_pos:
        print(f"Found Red X at screen coordinates {match_pos}! Clicking...")
        # Move mouse smoothly to position and click
        pyautogui.moveTo(match_pos[0], match_pos[1], duration=0.5)
        pyautogui.click()
        print("Click performed successfully. Test passed.")
    else:
        print("Could not find the Red X on the screen.")
        print("Make sure the red x is visible inside the LDPlayer window and the template matches.")

if __name__ == "__main__":
    test_red_x_click()
