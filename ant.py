from pydantic import BaseModel, Field
from enums import Caste
import math
import random
import numpy as np

CASTE_STATS = {
    Caste.WORKER:  {"speed": 2.0, "carry": True,  "vis": 1.0},
    Caste.SCOUT:   {"speed": 3.5, "carry": False, "vis": 1.5}
}


class Ant(BaseModel):
    x: int = Field(...)
    y: int = Field(...)
    caste: Caste = Field(...)
    sensor_angle: float = Field(...)
    width: int =  Field(...)
    height: int = Field(...)
    alpha: float = Field(...)
    beta: float = Field(...)
    gamma: float = Field(...)
    decay_per_step: float = Field(...)
    max_pheromone_drop: int = Field(...)
    min_pheromone_drop: int = Field(...)
    speed: float = 0
    carry: float = False
    vision_mult: float = 0
    angle: float = Field(default_factory=lambda: random.uniform(0, 2 * math.pi))
    has_food: bool = False
    steps_from_nest: int = 0
    steps_from_food: int = 0
    
    def model_post_init(self, __context: Any) -> None:
        stats = CASTE_STATS[self.caste]
        self.speed = stats["speed"]
        self.carry = stats["carry"]
        self.vision_mult = stats["vis"]

    def move(self, grid_pheromones, foods, nest_pos, time_factor, walls):
        target = None
        heuristic_influence = 0
        VISION_RADIUS = 60 * self.vision_mult * time_factor
        SENSOR_DIST = 30 * self.vision_mult
        SENSOR_ANGLE = self.sensor_angle
        WIDTH =  self.width
        HEIGHT =  self.height
        ALPHA = self.alpha
        BETA = self.beta
        GAMMA = self.gamma
        if not self.has_food:
            closest_food = None
            if self.caste == Caste.WORKER:
                min_dist = VISION_RADIUS
                for f in foods:
                    dist = math.hypot(f["pos"][0] - self.x, f["pos"][1] - self.y)
                    if dist < min_dist and f["active"]:
                        angle_to = math.atan2(f["pos"][1] - self.y, f["pos"][0] - self.x)
                        angle_diff = (angle_to - self.angle + math.pi) % (2 * math.pi) - math.pi
                        if abs(angle_diff) < SENSOR_ANGLE:
                            min_dist = dist
                            closest_food = f
                
                if closest_food:
                    target = closest_food["pos"]
                    if min_dist < 5:
                        self.has_food = True
                        closest_food["amount"] -= 1
                        if closest_food["amount"] <= 0:
                            closest_food["active"] = False
                        self.angle += math.pi
                        self.steps_from_food = 0
                        return False

        else:
            dist = math.hypot(nest_pos["pos"][0] - self.x, nest_pos["pos"][1] - self.y)
            if dist < VISION_RADIUS:
                angle_to = math.atan2(nest_pos["pos"][1] - self.y, nest_pos["pos"][0] - self.x)
                angle_diff = (angle_to - self.angle + math.pi) % (2 * math.pi) - math.pi
                if abs(angle_diff) < SENSOR_ANGLE:
                    target = nest_pos["pos"]
                    if dist < 5:
                        self.has_food = False
                        self.angle += math.pi
                        self.steps_from_nest = 0
                        return True

        directions = [-0.5, 0, 0.5]
        probs = []
        
        pheromone_layer = 0 if not self.has_food else 1 
        
        for d in directions:
            check_angle = self.angle + d
            cx = int(self.x + math.cos(check_angle) * SENSOR_DIST)
            cy = int(self.y + math.sin(check_angle) * SENSOR_DIST)
            
            tau = 0
            if 0 <= cx < WIDTH and 0 <= cy < HEIGHT:
                tau = np.mean(grid_pheromones[max(0, cx-1):min(WIDTH, cx+2), 
                                               max(0, cy-1):min(HEIGHT, cy+2), 
                                               pheromone_layer])
            
            eta = 1.0
            if target:
                angle_to_target = math.atan2(target[1] - self.y, target[0] - self.x)
                angle_diff = abs((angle_to_target - check_angle + math.pi) % (2 * math.pi) - math.pi)
                eta = 10.0 if angle_diff < 0.2 else 1.0

            score = (tau ** ALPHA) * (eta ** BETA) + GAMMA
            probs.append(score)

        total_score = sum(probs)
        
        if total_score > 0:
            chosen_dir_index = random.choices([0, 1, 2], weights=probs, k=1)[0]
            
            steering = directions[chosen_dir_index]
            self.angle += steering * 0.2 + random.uniform(-0.05, 0.05)

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        if self.x < 0 or self.x > WIDTH:
            self.angle = math.pi - self.angle
            self.x = max(0, min(WIDTH, self.x))
        if self.y < 0 or self.y > HEIGHT:
            self.angle = -self.angle
            self.y = max(0, min(HEIGHT, self.y))
            
        self.steps_from_nest += 1
        self.steps_from_food += 1

    def deposit_pheromone(self, grid_pheromones):
        WIDTH =  self.width
        HEIGHT =  self.height
        DECAY_PER_STEP = self.decay_per_step
        MAX_PHEROMONE_DROP = self.max_pheromone_drop
        MIN_PHEROMONE_DROP = self.min_pheromone_drop
        xi, yi = int(self.x), int(self.y)
        if 0 <= xi < WIDTH and 0 <= yi < HEIGHT:
            
            amount = MIN_PHEROMONE_DROP
            
            if self.has_food:
                strength = max(0, MAX_PHEROMONE_DROP - (self.steps_from_nest * DECAY_PER_STEP))
                amount = max(MIN_PHEROMONE_DROP, strength)
                grid_pheromones[xi, yi, 0] = min(255, grid_pheromones[xi, yi, 0] + amount)
            else:
                strength = max(0, MAX_PHEROMONE_DROP - (self.steps_from_food * DECAY_PER_STEP))
                amount = max(MIN_PHEROMONE_DROP, strength)
                grid_pheromones[xi, yi, 1] = min(255, grid_pheromones[xi, yi, 1] + amount)