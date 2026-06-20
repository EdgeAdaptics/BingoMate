from __future__ import annotations

import base64
import io
import statistics
import time
from dataclasses import asdict, dataclass
from importlib.util import find_spec
from typing import Any


@dataclass(frozen=True)
class VisionDetection:
    label: str
    confidence: float
    box: list[float]
    source: str


class VisionPipeline:
    def __init__(self, camera_enabled: bool = False, camera_index: int = 0) -> None:
        self.camera_enabled = camera_enabled
        self.camera_index = camera_index

    def status(self) -> dict[str, object]:
        return {
            "schema": "bingomate-vision-status/v1",
            "camera_enabled": self.camera_enabled,
            "camera_index": self.camera_index,
            "opencv_available": find_spec("cv2") is not None,
            "pillow_available": find_spec("PIL") is not None,
            "privacy": "camera_disabled_until_user_allows" if not self.camera_enabled else "local_camera_allowed",
            "stores_frames_by_default": False,
        }

    def simulate_scene(self, label: str = "desk") -> dict[str, object]:
        objects = simulated_objects(label)
        detections = [
            VisionDetection("person", 0.72, [0.05, 0.12, 0.24, 0.86], "simulation"),
            VisionDetection("workspace", 0.78, [0.0, 0.58, 1.0, 0.98], "simulation"),
            VisionDetection("edge_device", 0.74, [0.56, 0.38, 0.92, 0.72], "simulation"),
        ]
        return {
            "schema": "bingomate-vision-observation/v1",
            "mode": "local-simulation",
            "scene": label,
            "objects": objects,
            "detections": [asdict(detection) for detection in detections],
            "gestures": ["present"] if "person" in objects else [],
            "privacy": "local_only",
            "generated_at": time.time(),
            "frame": {
                "source": "simulation",
                "width": 640,
                "height": 360,
                "stored": False,
                "included": False,
            },
        }

    def analyze_image_bytes(self, image_bytes: bytes, source: str = "upload") -> dict[str, object]:
        if not image_bytes:
            return self._unavailable_observation("empty_image", source)
        try:
            from PIL import Image, ImageStat
        except ImportError:
            return self._unavailable_observation("pillow_missing", source)

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except Exception:
            return self._unavailable_observation("image_decode_failed", source)

        rgb = image.convert("RGB")
        width, height = rgb.size
        sample = rgb.resize((min(width, 96), min(height, 96)))
        stat = ImageStat.Stat(sample)
        channels = [float(value) for value in stat.mean]
        brightness = round(sum(channels) / 3.0, 2)
        extrema = sample.getextrema()
        channel_ranges = [high - low for low, high in extrema]
        contrast = round(sum(channel_ranges) / 3.0, 2)
        dominant_color = dominant_color_name(channels)
        scene = infer_scene(brightness, contrast, dominant_color, width, height)
        detections = heuristic_detections(sample, width, height, brightness, contrast)
        objects = sorted({detection.label for detection in detections} | {"image_frame"})
        gestures = ["possible_presence"] if any(detection.label == "person_or_object" for detection in detections) else []
        return {
            "schema": "bingomate-vision-observation/v1",
            "mode": "local-image-heuristic",
            "scene": scene,
            "objects": objects,
            "detections": [asdict(detection) for detection in detections],
            "gestures": gestures,
            "privacy": "local_only",
            "generated_at": time.time(),
            "analysis": {
                "brightness": brightness,
                "contrast": contrast,
                "dominant_color": dominant_color,
                "note": "Heuristic local analysis; replace with TensorRT/object models when installed.",
            },
            "frame": {
                "source": source,
                "width": width,
                "height": height,
                "stored": False,
                "included": False,
            },
        }

    def analyze_image_base64(self, image_base64: str, source: str = "upload") -> dict[str, object]:
        try:
            image_bytes = base64.b64decode(image_base64, validate=True)
        except Exception:
            return self._unavailable_observation("invalid_base64_image", source)
        return self.analyze_image_bytes(image_bytes, source)

    def capture_camera(
        self,
        allow_camera: bool,
        camera_index: int | None = None,
        width: int = 640,
        height: int = 480,
        include_frame: bool = False,
    ) -> dict[str, object]:
        selected_index = self.camera_index if camera_index is None else camera_index
        if not self.camera_enabled or not allow_camera:
            observation = self._unavailable_observation("camera_requires_explicit_enable_and_request", "camera")
            observation["camera"] = {
                "enabled": self.camera_enabled,
                "allow_camera": allow_camera,
                "index": selected_index,
            }
            return observation
        try:
            import cv2
        except ImportError:
            observation = self._unavailable_observation("opencv_missing", "camera")
            observation["camera"] = {"enabled": self.camera_enabled, "allow_camera": allow_camera, "index": selected_index}
            return observation

        capture = cv2.VideoCapture(selected_index)
        try:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            ok, frame = capture.read()
            if not ok or frame is None:
                observation = self._unavailable_observation("camera_frame_unavailable", "camera")
                observation["camera"] = {"enabled": self.camera_enabled, "allow_camera": allow_camera, "index": selected_index}
                return observation
            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                observation = self._unavailable_observation("camera_frame_encode_failed", "camera")
                observation["camera"] = {"enabled": self.camera_enabled, "allow_camera": allow_camera, "index": selected_index}
                return observation
            frame_bytes = encoded.tobytes()
        finally:
            capture.release()

        observation = self.analyze_image_bytes(frame_bytes, "camera")
        observation["camera"] = {"enabled": self.camera_enabled, "allow_camera": allow_camera, "index": selected_index}
        if include_frame:
            observation["frame"] = {**dict(observation["frame"]), "included": True}
            observation["frame_base64"] = base64.b64encode(frame_bytes).decode("ascii")
        return observation

    def _unavailable_observation(self, reason: str, source: str) -> dict[str, object]:
        return {
            "schema": "bingomate-vision-observation/v1",
            "mode": "unavailable",
            "scene": "unknown",
            "objects": [],
            "detections": [],
            "gestures": [],
            "privacy": "local_only",
            "generated_at": time.time(),
            "reason": reason,
            "frame": {
                "source": source,
                "width": 0,
                "height": 0,
                "stored": False,
                "included": False,
            },
        }


def simulated_objects(label: str) -> list[str]:
    normalized = label.lower()
    objects = ["person", "desk", "device"]
    if "lab" in normalized or "jetson" in normalized:
        objects.extend(["jetson", "sensor_node", "matrix_display"])
    if "factory" in normalized or "machine" in normalized:
        objects.extend(["machine", "status_light", "tooling"])
    return sorted(set(objects))


def dominant_color_name(channels: list[float]) -> str:
    red, green, blue = channels
    if max(channels) - min(channels) < 22:
        if sum(channels) / 3 < 70:
            return "dark-neutral"
        if sum(channels) / 3 > 190:
            return "bright-neutral"
        return "neutral"
    if red >= green and red >= blue:
        return "red-warm"
    if green >= red and green >= blue:
        return "green-workspace"
    return "blue-cool"


def infer_scene(brightness: float, contrast: float, dominant_color: str, width: int, height: int) -> str:
    if brightness < 45:
        return "dark_scene"
    if brightness > 215 and contrast < 35:
        return "bright_blank_scene"
    if contrast > 150:
        return "high_contrast_workspace"
    if dominant_color == "green-workspace":
        return "electronics_or_lab_scene"
    if width > height:
        return "desk_or_room_scene"
    return "portrait_or_device_scene"


def heuristic_detections(sample: Any, width: int, height: int, brightness: float, contrast: float) -> list[VisionDetection]:
    detections = [VisionDetection("image_frame", 1.0, [0.0, 0.0, 1.0, 1.0], "heuristic")]
    pixels = list(sample.getdata())
    if not pixels:
        return detections
    bright_ratio = sum(1 for red, green, blue in pixels if (red + green + blue) / 3 > 210) / len(pixels)
    dark_ratio = sum(1 for red, green, blue in pixels if (red + green + blue) / 3 < 45) / len(pixels)
    green_ratio = sum(1 for red, green, blue in pixels if green > red * 1.18 and green > blue * 1.12) / len(pixels)
    if bright_ratio > 0.12 and dark_ratio > 0.08:
        detections.append(VisionDetection("display_or_status_light", 0.56, [0.18, 0.18, 0.82, 0.72], "heuristic"))
    if green_ratio > 0.18:
        detections.append(VisionDetection("circuit_or_indicator", 0.52, [0.12, 0.2, 0.88, 0.82], "heuristic"))
    if contrast > 80 and 45 <= brightness <= 210:
        detections.append(VisionDetection("person_or_object", 0.5, [0.25, 0.08, 0.76, 0.92], "heuristic"))
    if high_vertical_variance(sample):
        detections.append(VisionDetection("vertical_edge_structure", 0.49, [0.1, 0.02, 0.9, 0.98], "heuristic"))
    return detections


def high_vertical_variance(sample: Any) -> bool:
    width, height = sample.size
    if width < 8 or height < 8:
        return False
    columns: list[float] = []
    for x in range(width):
        values = []
        for y in range(height):
            red, green, blue = sample.getpixel((x, y))
            values.append((red + green + blue) / 3)
        columns.append(statistics.mean(values))
    if len(columns) < 2:
        return False
    return statistics.pstdev(columns) > 28
