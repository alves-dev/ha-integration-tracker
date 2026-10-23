"""Source-neutral results returned by automatic usage detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONFIDENCES = ("high", "medium", "low")


@dataclass(slots=True, frozen=True)
class DetectedUsage:
    """A single usage candidate returned by a detector."""

    item_id: str
    name: str
    type: str
    detection_key: str
    detector: str
    confidence: str
    url: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the detector result before it reaches the registry."""
        if not self.item_id.strip():
            raise ValueError("Detected usage item_id is required")
        if not self.name.strip():
            raise ValueError("Detected usage name is required")
        if not self.type.strip():
            raise ValueError("Detected usage type is required")
        if not self.detection_key.strip():
            raise ValueError("Detected usage detection_key is required")
        if not self.detector.strip():
            raise ValueError("Detected usage detector is required")
        if self.confidence not in CONFIDENCES:
            raise ValueError(f"Unsupported detection confidence: {self.confidence}")
