"""Real-time hand tracking using OpenCV and MediaPipe Hand Landmarker."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

import settings
from utils import clamp, lerp


class HandTracker:
    """Capture webcam frames on a background thread and expose hand state safely."""

    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_width, self.screen_height = screen_size
        self.cursor_position = (self.screen_width / 2, self.screen_height / 2)
        self.smoothed_position = self.cursor_position
        self.is_closed = False
        self.hand_visible = False
        self.webcam_ok = False
        self.preview_enabled = True
        self.preview_fps = 0.0
        self.error_message = ""
        self._latest_frame = None

        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._cap: cv2.VideoCapture | None = None

        self._landmarker: vision.HandLandmarker | None = None
        self._connections = list(vision.HandLandmarksConnections.HAND_CONNECTIONS)
        self._model_path = Path(settings.HAND_LANDMARKER_MODEL_PATH)

        try:
            self._landmarker = self._create_landmarker()
        except Exception as error:  # pragma: no cover - defensive fallback
            self.error_message = f"Hand tracker init failed: {error}"

    def _create_landmarker(self) -> vision.HandLandmarker:
        """Create the MediaPipe Tasks hand landmarker from a local `.task` model."""
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self._model_path}. "
                "Download the official hand_landmarker.task model into the assets folder."
            )

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(self._model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.55,
        )
        return vision.HandLandmarker.create_from_options(options)

    def start(self) -> None:
        if self._running:
            return

        if self._landmarker is None:
            self.webcam_ok = False
            return

        self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap.release()
            self._cap = cv2.VideoCapture(0)

        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)
            self._running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
        else:
            self.webcam_ok = False

    def stop(self) -> None:
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        if self._cap:
            self._cap.release()
            self._cap = None

        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None

        # we no longer open a persistent OpenCV window for preview in-game
        # so there's nothing to destroy here

    def get_state(self) -> dict[str, object]:
        with self._lock:
            return {
                "cursor_pos": self.cursor_position,
                "is_closed": self.is_closed,
                "hand_visible": self.hand_visible,
                "webcam_ok": self.webcam_ok,
                "preview_fps": self.preview_fps,
                "error_message": self.error_message,
            }

    def _capture_loop(self) -> None:
        previous_time = time.perf_counter()

        while self._running and self._cap and self._landmarker:
            success, frame = self._cap.read()
            current_time = time.perf_counter()
            delta = max(current_time - previous_time, 1e-6)
            previous_time = current_time
            self.preview_fps = 1.0 / delta

            if not success:
                self._update_state(webcam_ok=False, hand_visible=False)
                time.sleep(0.01)
                continue

            self.webcam_ok = True
            mirrored_frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(mirrored_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int(current_time * 1000)
            results = self._landmarker.detect_for_video(mp_image, timestamp_ms)
            annotated_frame = mirrored_frame.copy()

            detected_position = self.smoothed_position
            is_closed = False
            hand_visible = False

            if results.hand_landmarks:
                hand_visible = True
                hand_landmarks = results.hand_landmarks[0]
                self._draw_landmarks(annotated_frame, hand_landmarks)

                middle_base = hand_landmarks[9]
                middle_tip = hand_landmarks[12]
                cursor_tip = hand_landmarks[8]

                is_closed = middle_tip.y > middle_base.y

                raw_x = clamp(cursor_tip.x * self.screen_width, 0, self.screen_width)
                raw_y = clamp(cursor_tip.y * self.screen_height, 0, self.screen_height)
                detected_position = (
                    lerp(self.smoothed_position[0], raw_x, settings.TRACKER_POSITION_SMOOTHING),
                    lerp(self.smoothed_position[1], raw_y, settings.TRACKER_POSITION_SMOOTHING),
                )

                cv2.putText(
                    annotated_frame,
                    f"Gesture: {'Closed' if is_closed else 'Open'}",
                    (14, 34),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.85,
                    (70, 255, 120) if not is_closed else (70, 140, 255),
                    2,
                    cv2.LINE_AA,
                )
            else:
                cv2.putText(
                    annotated_frame,
                    "Show one hand to control the paw",
                    (14, 34),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 245, 120),
                    2,
                    cv2.LINE_AA,
                )

            self.smoothed_position = detected_position
            self._update_state(
                cursor_pos=detected_position,
                is_closed=is_closed,
                hand_visible=hand_visible,
                webcam_ok=True,
            )

            cv2.putText(
                annotated_frame,
                f"Preview FPS: {self.preview_fps:5.1f}",
                (14, annotated_frame.shape[0] - 16),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # Always keep a copy of the latest annotated frame for in-game preview.
            # Do not open a large OpenCV window when embedding preview inside the game.
            with self._lock:
                self._latest_frame = annotated_frame.copy()

        self.webcam_ok = False

    def _draw_landmarks(self, frame, hand_landmarks) -> None:
        """Draw a clean landmark overlay without depending on the legacy solutions API."""
        frame_height, frame_width = frame.shape[:2]
        points: list[tuple[int, int]] = []

        for landmark in hand_landmarks:
            point = (
                int(clamp(landmark.x, 0.0, 1.0) * frame_width),
                int(clamp(landmark.y, 0.0, 1.0) * frame_height),
            )
            points.append(point)

        for connection in self._connections:
            start_point = points[connection.start]
            end_point = points[connection.end]
            cv2.line(frame, start_point, end_point, (255, 210, 90), 2, cv2.LINE_AA)

        for index, point in enumerate(points):
            color = (86, 196, 244) if index in {8, 12} else (76, 223, 131)
            cv2.circle(frame, point, 5, color, -1, cv2.LINE_AA)
            cv2.circle(frame, point, 8, (30, 30, 40), 1, cv2.LINE_AA)

    def _update_state(
        self,
        *,
        cursor_pos: tuple[float, float] | None = None,
        is_closed: bool | None = None,
        hand_visible: bool | None = None,
        webcam_ok: bool | None = None,
    ) -> None:
        with self._lock:
            if cursor_pos is not None:
                self.cursor_position = cursor_pos
            if is_closed is not None:
                self.is_closed = is_closed
            if hand_visible is not None:
                self.hand_visible = hand_visible
            if webcam_ok is not None:
                self.webcam_ok = webcam_ok

    def get_latest_preview(self):
        """Return a copy of the latest annotated preview frame (BGR) or None."""
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()
