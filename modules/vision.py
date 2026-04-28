"""
Computer Vision module for popup detection using OpenCV and MSS.
Enhanced with multi-template matching: scans ALL assets and finds ALL occurrences.
"""
import os
import glob
import cv2
import numpy as np
import mss
from typing import List, Tuple, Optional


class Vision:
    """
    Handles template matching to find objects on the screen.
    Supports finding multiple instances of multiple templates simultaneously.
    """
    def __init__(self):
        self.sct = mss.mss()
        self._template_cache: dict = {}  # Cache loaded templates

    def _load_template(self, template_path: str) -> Optional[np.ndarray]:
        """Loads a template image, using cache to avoid repeated disk reads."""
        if template_path in self._template_cache:
            return self._template_cache[template_path]

        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                print(f"[Vision] Error: Template not found at {template_path}")
                return None
            self._template_cache[template_path] = template
            return template
        except Exception as e:
            print(f"[Vision] Exception loading template: {e}")
            return None

    def _capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[np.ndarray, dict]:
        """Captures a screenshot, returns grayscale image and monitor dict."""
        if region:
            monitor = {"left": region[0], "top": region[1], "width": region[2], "height": region[3]}
        else:
            monitor = self.sct.monitors[1]

        sct_img = self.sct.grab(monitor)
        img = np.array(sct_img)
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        return gray_img, monitor

    def find_template(
        self,
        template_path: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8,
    ) -> Optional[Tuple[int, int]]:
        """
        Finds the best match of a single image template on the screen.

        Args:
            template_path: Path to the template image file.
            region: The region to search in (left, top, width, height).
            threshold: The confidence threshold for matching (0.0 to 1.0).

        Returns:
            The (x, y) center coordinates of the match if found, None otherwise.
        """
        template = self._load_template(template_path)
        if template is None:
            return None

        template_w, template_h = template.shape[::-1]
        gray_img, monitor = self._capture_screen(region)

        res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        print(f"[Vision] '{template_path}' -> Max Similarity: {max_val:.2%}")

        if max_val >= threshold:
            match_x, match_y = max_loc
            center_x = match_x + template_w // 2
            center_y = match_y + template_h // 2

            abs_x = monitor["left"] + center_x
            abs_y = monitor["top"] + center_y
            return (abs_x, abs_y)

        return None

    @staticmethod
    def discover_assets(assets_dir: str = "assets") -> List[str]:
        """
        Auto-discovers all .png template files in the assets directory.

        Returns:
            Sorted list of absolute paths to all .png files found.
        """
        if not os.path.isdir(assets_dir):
            print(f"[Vision] Assets directory '{assets_dir}' not found.")
            return []
        patterns = ["*.png", "*.jpg", "*.jpeg", "*.bmp"]
        found = []
        for pat in patterns:
            found.extend(glob.glob(os.path.join(assets_dir, pat)))
        result = sorted(set(found))
        print(f"[Vision] Discovered {len(result)} asset(s) in '{assets_dir}': {[os.path.basename(f) for f in result]}")
        return result

    def find_all_matches_for_template(
        self,
        gray_img: np.ndarray,
        template: np.ndarray,
        threshold: float = 0.8,
    ) -> List[Tuple[int, int, int, int]]:
        """
        Finds ALL positions of a template in a grayscale image above the threshold.
        Uses Non-Maximum Suppression to avoid overlapping detections.

        Returns:
            List of (x, y, w, h) bounding boxes in image-local coordinates.
        """
        template_w, template_h = template.shape[::-1]
        img_h, img_w = gray_img.shape

        # Prevent OpenCV crash if template is larger than search region
        if template_w > img_w or template_h > img_h:
            print(f"[Vision] Warning: Template ({template_w}x{template_h}) is larger than search region ({img_w}x{img_h}). Skipping.")
            return []

        res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)

        # Find all locations above threshold
        locations = np.where(res >= threshold)
        if len(locations[0]) == 0:
            return []

        # Build bounding boxes
        boxes = []
        scores = []
        for pt_y, pt_x in zip(*locations):
            boxes.append((int(pt_x), int(pt_y), int(pt_x + template_w), int(pt_y + template_h)))
            scores.append(float(res[pt_y, pt_x]))

        # Apply Non-Maximum Suppression
        nms_boxes = self._nms(boxes, scores, iou_threshold=0.3)

        # Convert back to (x, y, w, h) centered
        results = []
        for (x1, y1, x2, y2) in nms_boxes:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            results.append((cx, cy, template_w, template_h))

        return results

    @staticmethod
    def _nms(
        boxes: List[Tuple[int, int, int, int]],
        scores: List[float],
        iou_threshold: float = 0.3,
    ) -> List[Tuple[int, int, int, int]]:
        """
        Non-Maximum Suppression to eliminate overlapping detections.
        boxes: list of (x1, y1, x2, y2)
        """
        if not boxes:
            return []

        indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        keep = []

        while indices:
            current = indices.pop(0)
            keep.append(current)
            remaining = []
            for idx in indices:
                if Vision._iou(boxes[current], boxes[idx]) < iou_threshold:
                    remaining.append(idx)
            indices = remaining

        return [boxes[i] for i in keep]

    @staticmethod
    def _iou(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> float:
        """Compute Intersection over Union between two boxes (x1, y1, x2, y2)."""
        x1 = max(box_a[0], box_b[0])
        y1 = max(box_a[1], box_b[1])
        x2 = min(box_a[2], box_b[2])
        y2 = min(box_a[3], box_b[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
        area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def find_all_templates(
        self,
        assets_dir: str = "assets",
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8,
    ) -> List[Tuple[int, int, str]]:
        """
        Scans ALL template images in the assets directory against the current screen
        and returns ALL match positions above threshold.

        This is the core method called by 'vision_scan' blocks.
        It captures the screen ONCE and matches every asset against it.

        Args:
            assets_dir: Directory containing template images.
            region: Screen region to scan (left, top, width, height).
            threshold: Confidence threshold.

        Returns:
            List of (abs_x, abs_y, template_name) for every match found.
        """
        asset_files = self.discover_assets(assets_dir)
        if not asset_files:
            print("[Vision] No assets found. Skipping scan.")
            return []

        # Capture screen ONCE for efficiency
        gray_img, monitor = self._capture_screen(region)

        all_matches: List[Tuple[int, int, str]] = []

        for asset_path in asset_files:
            template = self._load_template(asset_path)
            if template is None:
                continue

            matches = self.find_all_matches_for_template(gray_img, template, threshold)
            asset_name = os.path.basename(asset_path)

            for (cx, cy, tw, th) in matches:
                abs_x = monitor["left"] + cx
                abs_y = monitor["top"] + cy
                all_matches.append((abs_x, abs_y, asset_name))
                print(f"[Vision] Found '{asset_name}' at screen ({abs_x}, {abs_y})")

        print(f"[Vision] Total matches found: {len(all_matches)}")
        return all_matches

    def clear_cache(self) -> None:
        """Clears the template image cache."""
        self._template_cache.clear()
