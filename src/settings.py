from pydantic import BaseModel
import math


class Settings(BaseModel):
    WIDTH: int = 1920
    HEIGHT: int = 1080
    ANT_COUNT: int = 5000
    ENERGY_SPAWN: float = 0.5  # (0-1)
    HEALTH_SPAWN: float = 1.0  # (0-1)
    FOODS_COUNT: int = 20
    FPS: int = 60

    ALPHA: float = 1.5
    BETA: float = 2.0
    GAMMA: float = 0.01
    EVAPORATION_DAY: float = 0.99
    EVAPORATION_NIGHT: float = 0.995

    SENSOR_ANGLE: float = math.pi / 4
    EVAPORATION_RATE: float = 0.99
    DIFFUSION_RATE: float = 0.05

    MAX_PHEROMONE_DROP: int = 1005
    MIN_PHEROMONE_DROP: int = 10
    DECAY_PER_STEP: float = 0.1

    COLOR_BG: tuple[int, int, int] = (0, 0, 0)
    COLOR_NEST: tuple[int, int, int] = (255, 255, 255)
    COLOR_FOOD: tuple[int, int, int] = (0, 255, 0)
    COLOR_ANT_NO_FOOD: tuple[int, int, int] = (100, 100, 255)
    COLOR_ANT_FOOD: tuple[int, int, int] = (255, 100, 100)

    COLOR_TRAIL_HOME: tuple[int, int, int] = (0, 0, 255)
    COLOR_TRAIL_FOOD: tuple[int, int, int] = (255, 0, 0)
