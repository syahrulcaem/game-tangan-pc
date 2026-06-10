"""Global settings for the Rat Swat Game."""

from pathlib import Path

WINDOW_TITLE = "Rat Swat Game"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
FPS = 60

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

GAME_DURATION = 60

BACKGROUND_PATH = Path(r"D:\pengolahangame\bg.jpg")
RAT_IMAGE_PATH = Path(r"D:\pengolahangame\rat.png")
PAW_OPEN_PATH = Path(r"D:\pengolahangame\paw1.png")
PAW_CLOSED_PATH = Path(r"D:\pengolahangame\paw2.png")
HAND_LANDMARKER_MODEL_PATH = Path(r"D:\pengolahangame\assets\hand_landmarker.task")

CURSOR_SIZE = 145
CURSOR_OPEN_SCALE = 1.0
CURSOR_CLOSED_SCALE = 0.92
CURSOR_SMOOTHING = 14.0
CURSOR_SCALE_SPEED = 11.0
TRACKER_POSITION_SMOOTHING = 0.35
HIT_COOLDOWN = 0.15

RAT_SIZE = 140
RAT_SPEED_MIN = 180
RAT_SPEED_MAX = 360
RAT_DIRECTION_CHANGE_MIN = 0.35
RAT_DIRECTION_CHANGE_MAX = 0.9
RAT_IDLE_BOB_SPEED = 6.0
RAT_IDLE_BOB_AMOUNT = 6.0
RAT_HIT_DURATION = 0.2

# Game progression
TOTAL_RATS = 5
RAT_SPAWN_INTERVAL = 1.0

TOP_UI_HEIGHT = 88
PLAY_AREA_MARGIN = 30
PLAY_AREA_TOP = TOP_UI_HEIGHT + 18

PREVIEW_WINDOW_NAME = "Hand Tracking Preview"

WHITE = (255, 255, 255)
BLACK = (16, 16, 20)
TEXT_DARK = (24, 24, 30)
TEXT_LIGHT = (250, 249, 244)
CREAM = (248, 239, 216)
GOLD = (245, 184, 68)
RED = (236, 92, 87)
GREEN = (84, 201, 126)
SKY = (86, 196, 244)
SHADOW = (18, 20, 28)
PANEL = (255, 246, 228)
PANEL_ALT = (252, 232, 194)
BUTTON_PRIMARY = (255, 178, 62)
BUTTON_PRIMARY_HOVER = (255, 197, 98)
BUTTON_SECONDARY = (78, 88, 106)
BUTTON_SECONDARY_HOVER = (99, 112, 133)
OUTLINE = (70, 59, 52)

ASSETS_DIR = Path("assets")
# Camera preview in-game
CAMERA_PREVIEW_SIZE = (240, 180)
CAMERA_PREVIEW_MARGIN = 12
CAMERA_PREVIEW_CORNER = "bottomleft"  # options: topright, topleft, bottomleft

# Levels: higher level -> more rats, faster rats, shorter spawn interval
LEVELS = {
	1: {"total_rats": 5, "speed_multiplier": 1.0, "spawn_interval": 1.0},
	2: {"total_rats": 8, "speed_multiplier": 1.25, "spawn_interval": 0.8},
	3: {"total_rats": 12, "speed_multiplier": 1.6, "spawn_interval": 0.6},
}
