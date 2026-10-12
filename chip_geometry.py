"""Uniform tixel geometry; ROI corners mark the outside capture-array edges."""
from dataclasses import dataclass
import math

PRESETS = {10: (10, 15), 15: (15, 10), 25: (25, 25), 50: (50, 50)}


@dataclass(frozen=True)
class ChipGeometry:
    size_um: int = 25
    width_um: float = 25
    gap_um: float = 25

    def __post_init__(self):
        if self.size_um not in PRESETS:
            raise ValueError("Select a tixel size of 10, 15, 25 or 50 µm.")
        if not math.isfinite(self.width_um) or self.width_um <= 0:
            raise ValueError("Capture width must be a positive number.")
        if not math.isfinite(self.gap_um) or self.gap_um < 0:
            raise ValueError("Gap must be a nonnegative number.")

    @classmethod
    def preset(cls, size):
        return cls(size, *PRESETS[size])

    @classmethod
    def from_metadata(cls, metadata):
        size = int(str(metadata.get("chip_resolution", "25um")).replace("um", "").replace("µm", "").strip())
        preset = cls.preset(size)
        custom = metadata.get("tixel_geometry", {})
        return cls(size, float(custom.get("width_um", preset.width_um)), float(custom.get("gap_um", preset.gap_um)))

    def metadata(self):
        return {"chip_resolution": "{}um".format(self.size_um),
                "tixel_geometry": {"width_um": self.width_um, "gap_um": self.gap_um}}

    def vectors(self, start, end, n):
        if not isinstance(n, int) or n < 1:
            raise ValueError("Channel count must be a positive integer.")
        span = n * self.width_um + (n - 1) * self.gap_um
        edge = [end[i] - start[i] for i in range(2)]
        return ([v * self.width_um / span for v in edge],
                [v * (self.width_um + self.gap_um) / span for v in edge])

    def slopes(self, points, n):
        horizontal, horizontal_pitch = self.vectors(points[:2], points[2:4], n)
        vertical, vertical_pitch = self.vectors(points[:2], points[6:8], n)
        # Existing drawing loops store vectors in (dy, dx) order.
        return vertical[::-1], horizontal[::-1], vertical_pitch[::-1], horizontal_pitch[::-1]

    def diameters(self, points, n):
        vertical, horizontal, _, _ = self.slopes(points, n)
        p = math.hypot(horizontal[0] - vertical[0], horizontal[1] - vertical[1])
        q = math.hypot(horizontal[0] + vertical[0], horizontal[1] + vertical[1])
        diameter = math.sqrt(p * q)
        return diameter, diameter * 1.6153846
