"""
Computer Vision module for popup detection using OpenCV and MSS.
"""
import cv2
import numpy as np
import mss
from typing import Tuple, Optional

class Vision:
    """
    Handles template matching to find objects on the screen.
    """
    def __init__(self):
        self.sct = mss.mss()

    def find_template(self, template_path: str, region: Optional[Tuple[int, int, int, int]] = None, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Finds an image template on the screen.
        
        Args:
            template_path (str): Path to the template image file.
            region (Optional[Tuple[int, int, int, int]]): The region to search in (left, top, width, height).
                                                          If None, searches the whole screen.
            threshold (float): The confidence threshold for matching (0.0 to 1.0).
            
        Returns:
            Optional[Tuple[int, int]]: The (x, y) center coordinates of the match if found, None otherwise.
        """
        # Load the template image
        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                print(f"[Vision] Error: Template not found at {template_path}")
                return None
        except Exception as e:
            print(f"[Vision] Exception loading template: {e}")
            return None
        
        template_w, template_h = template.shape[::-1]

        # Capture screen
        if region:
            # MSS uses dictionaries for monitor areas
            monitor = {"left": region[0], "top": region[1], "width": region[2], "height": region[3]}
        else:
            # Default to primary monitor if no region
            monitor = self.sct.monitors[1]
            
        sct_img = self.sct.grab(monitor)
        # Convert to numpy array and grayscale
        img = np.array(sct_img)
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

        # Perform template matching
        res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        print(f"[Vision] '{template_path}' -> Max Similarity: {max_val:.2%}")

        # If match found
        if max_val >= threshold:
            match_x, match_y = max_loc
            
            # Calcola il centro
            center_x = match_x + template_w // 2
            center_y = match_y + template_h // 2
            
            # Convert to absolute screen coordinates
            if region:
                abs_x = region[0] + center_x
                abs_y = region[1] + center_y
            else:
                abs_x = monitor["left"] + center_x
                abs_y = monitor["top"] + center_y
                
            return (abs_x, abs_y)
            
        return None
