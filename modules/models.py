"""
Data models for macro blocks.
Defines the block types and provides serialization/deserialization utilities.
"""
import json
import os
import glob
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


# ── Block Type Constants ────────────────────────────────────────────
BLOCK_CLICK = "click"
BLOCK_DELAY = "delay"
BLOCK_VISION_SCAN = "vision_scan"
BLOCK_SUB_MACRO = "sub_macro"
BLOCK_SCROLL = "scroll"
BLOCK_DRAG = "drag"
BLOCK_PERIODIC = "periodic"
BLOCK_IMAGE_CHECK = "image_check"
BLOCK_LOOP = "loop"

ALL_BLOCK_TYPES = [BLOCK_CLICK, BLOCK_DELAY, BLOCK_VISION_SCAN, BLOCK_SUB_MACRO, BLOCK_SCROLL, BLOCK_DRAG, BLOCK_PERIODIC, BLOCK_IMAGE_CHECK, BLOCK_LOOP]

BLOCK_COLORS = {
    BLOCK_CLICK:       "#3B82F6",  # Blue
    BLOCK_DELAY:       "#F59E0B",  # Amber
    BLOCK_VISION_SCAN: "#10B981",  # Emerald
    BLOCK_SUB_MACRO:   "#8B5CF6",  # Violet
    BLOCK_SCROLL:      "#EC4899",  # Pink
    BLOCK_DRAG:        "#F97316",  # Orange
    BLOCK_PERIODIC:    "#06B6D4",  # Cyan
    BLOCK_IMAGE_CHECK: "#EF4444",  # Red
    BLOCK_LOOP:        "#14B8A6",  # Teal
}

BLOCK_ICONS = {
    BLOCK_CLICK:       "🖱️",
    BLOCK_DELAY:       "⏱️",
    BLOCK_VISION_SCAN: "👁️",
    BLOCK_SUB_MACRO:   "📂",
    BLOCK_SCROLL:      "↕️",
    BLOCK_DRAG:        "🤚",
    BLOCK_PERIODIC:    "🔄",
    BLOCK_IMAGE_CHECK: "🛡️",
    BLOCK_LOOP:        "🔁",
}

BLOCK_LABELS = {
    BLOCK_CLICK:       "Click",
    BLOCK_DELAY:       "Delay",
    BLOCK_VISION_SCAN: "Vision Scan",
    BLOCK_SUB_MACRO:   "Sub-Macro",
    BLOCK_SCROLL:      "Scroll",
    BLOCK_DRAG:        "Drag",
    BLOCK_PERIODIC:    "Periodic",
    BLOCK_IMAGE_CHECK: "Image Check",
    BLOCK_LOOP:        "Loop",
}


# ── Block Data Classes ──────────────────────────────────────────────
@dataclass
class Block:
    """Base class for all macro blocks."""
    type: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Block":
        block_type = data.get("type", BLOCK_CLICK)
        if block_type == BLOCK_CLICK:
            return ClickBlock(
                rel_x=data.get("rel_x", 0),
                rel_y=data.get("rel_y", 0),
                delay=data.get("delay", 0.5),
            )
        elif block_type == BLOCK_DELAY:
            return DelayBlock(duration=data.get("duration", 1.0))
        elif block_type == BLOCK_VISION_SCAN:
            return VisionScanBlock(threshold=data.get("threshold", 0.8))
        elif block_type == BLOCK_SUB_MACRO:
            return SubMacroBlock(macro_file=data.get("macro_file", ""))
        elif block_type == BLOCK_SCROLL:
            return ScrollBlock(
                rel_x=data.get("rel_x", 0),
                rel_y=data.get("rel_y", 0),
                amount=data.get("amount", 0),
                delay=data.get("delay", 0.5),
            )
        elif block_type == BLOCK_DRAG:
            return DragBlock(
                start_x=data.get("start_x", 0),
                start_y=data.get("start_y", 0),
                end_x=data.get("end_x", 0),
                end_y=data.get("end_y", 0),
                duration=data.get("duration", 0.5),
                delay=data.get("delay", 0.5),
            )
        elif block_type == BLOCK_PERIODIC:
            return PeriodicBlock(
                n_iterations=data.get("n_iterations", 5),
                macro_file=data.get("macro_file", ""),
            )
        elif block_type == BLOCK_IMAGE_CHECK:
            return ImageCheckBlock(
                image_path=data.get("image_path", ""),
                threshold=data.get("threshold", 0.8),
                on_fail=data.get("on_fail", "abort"),
            )
        elif block_type == BLOCK_LOOP:
            children = [Block.from_dict(c) for c in data.get("children", [])]
            return LoopBlock(
                iterations=data.get("iterations", 3),
                children=children,
            )
        else:
            # Fallback: treat unknown as click
            return ClickBlock(
                rel_x=data.get("rel_x", 0),
                rel_y=data.get("rel_y", 0),
                delay=data.get("delay", 0.5),
            )


@dataclass
class ClickBlock(Block):
    type: str = field(default=BLOCK_CLICK, init=False)
    rel_x: int = 0
    rel_y: int = 0
    delay: float = 0.5


@dataclass
class DelayBlock(Block):
    type: str = field(default=BLOCK_DELAY, init=False)
    duration: float = 1.0


@dataclass
class VisionScanBlock(Block):
    type: str = field(default=BLOCK_VISION_SCAN, init=False)
    threshold: float = 0.8


@dataclass
class SubMacroBlock(Block):
    type: str = field(default=BLOCK_SUB_MACRO, init=False)
    macro_file: str = ""


@dataclass
class ScrollBlock(Block):
    type: str = field(default=BLOCK_SCROLL, init=False)
    rel_x: int = 0
    rel_y: int = 0
    amount: int = 0  # Positive for up, negative for down
    delay: float = 0.5


@dataclass
class DragBlock(Block):
    type: str = field(default=BLOCK_DRAG, init=False)
    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0
    duration: float = 0.5
    delay: float = 0.5


@dataclass
class PeriodicBlock(Block):
    type: str = field(default=BLOCK_PERIODIC, init=False)
    n_iterations: int = 5
    macro_file: str = ""

@dataclass
class ImageCheckBlock(Block):
    type: str = field(default=BLOCK_IMAGE_CHECK, init=False)
    image_path: str = ""
    threshold: float = 0.8
    on_fail: str = "abort"  # "abort" or "continue_loop"

@dataclass
class LoopBlock(Block):
    type: str = field(default=BLOCK_LOOP, init=False)
    iterations: int = 3
    children: List["Block"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "iterations": self.iterations,
            "children": [c.to_dict() for c in self.children],
        }

# ── Macro Container ─────────────────────────────────────────────────
@dataclass
class Macro:
    """Top-level macro container with metadata and a list of blocks."""
    name: str = "Untitled"
    description: str = ""
    blocks: List[Block] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "blocks": [b.to_dict() for b in self.blocks],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Macro":
        return Macro(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            blocks=[Block.from_dict(b) for b in data.get("blocks", [])],
        )

    def save(self, filepath: str) -> None:
        """Saves the macro to a JSON file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)

    @staticmethod
    def load(filepath: str) -> "Macro":
        """
        Loads a macro from a JSON file.
        Supports both the new format (dict with 'blocks') and the legacy format (flat array of clicks).
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Legacy format: plain array of click actions
        if isinstance(data, list):
            blocks = []
            for item in data:
                block_data = dict(item)
                if "type" not in block_data:
                    block_data["type"] = BLOCK_CLICK
                blocks.append(Block.from_dict(block_data))
            return Macro(
                name=os.path.splitext(os.path.basename(filepath))[0],
                description="Imported from legacy format",
                blocks=blocks,
            )

        return Macro.from_dict(data)


def list_saved_macros(actions_dir: str = "actions") -> List[str]:
    """Returns a list of all .json macro files in the actions directory."""
    if not os.path.isdir(actions_dir):
        return []
    return sorted(glob.glob(os.path.join(actions_dir, "*.json")))
