from dataclasses import dataclass


@dataclass
class BBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height

    def intersects(self, other: "BBox") -> bool:
        return not (
            self.x2 < other.x or other.x2 < self.x
            or self.y2 < other.y or other.y2 < self.y
        )

    def intersection_area(self, other: "BBox") -> float:
        x_overlap = max(0, min(self.x2, other.x2) - max(self.x, other.x))
        y_overlap = max(0, min(self.y2, other.y2) - max(self.y, other.y))
        return x_overlap * y_overlap

    def iou(self, other: "BBox") -> float:
        inter = self.intersection_area(other)
        area_a = self.width * self.height
        area_b = other.width * other.height
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def contains(self, other: "BBox") -> bool:
        return (
            self.x <= other.x and self.y <= other.y
            and self.x2 >= other.x2 and self.y2 >= other.y2
        )

    @classmethod
    def from_dict(cls, d: dict) -> "BBox":
        return cls(x=d["x"], y=d["y"], width=d["width"], height=d["height"])

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}
