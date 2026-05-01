import pygame
from .ant import Ant
import numpy as np
import matplotlib.pyplot as plt
import math
import random
from .enums import Caste
from .settings import Settings


def main() -> None:
    pygame.init()
    settings = Settings()
    history = {"foods": [],
               "ant_food": []
               }
    screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    pygame.display.set_caption("ACO - 0xS4cha")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)

    pheromones = np.zeros((settings.WIDTH, settings.HEIGHT, 2), dtype=np.float32)
    walls = np.zeros((settings.WIDTH, settings.HEIGHT), dtype=bool)
    nest_pos = {"pos": (settings.WIDTH // 2, settings.HEIGHT // 2)}
    nest_food_stock = 0
    ants = []
    def spawn_ant(x, y):
        r = random.random()
        if r < 0.1: c_type = Caste.SCOUT
        else: c_type = Caste.WORKER
        return Ant(x=x, y=y, caste=c_type, sensor_angle=settings.SENSOR_ANGLE, width=settings.WIDTH, height=settings.HEIGHT, alpha=settings.ALPHA, beta=settings.BETA, gamma=settings.GAMMA,
        decay_per_step=settings.DECAY_PER_STEP, max_pheromone_drop=settings.MAX_PHEROMONE_DROP, min_pheromone_drop=settings.MIN_PHEROMONE_DROP)

    for _ in range(settings.ANT_COUNT):
            ants.append(spawn_ant(nest_pos["pos"][0], nest_pos["pos"][1]))

    foods = []
    for _ in range(settings.FOODS_COUNT):
        foods.append({
            "pos": (random.randint(50, settings.WIDTH-50), random.randint(50, settings.HEIGHT-50)), 
            "amount": random.randint(500, 1000),
            "active": True
            })

    day_time = 0.0
    day_speed = 0.0005
    current_tool = 0
    iterations = 0
    brush_size = 20
    tool_names = ["Foods (Clic)", "Pheromones RED (Clic+Drag)", "Pheromones BLUE (Clic+Drag)", "Wall (Clic+Drag)"]
    running = True
    while running:
        history["foods"].append(nest_food_stock)
        iterations += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: current_tool = 0
                if event.key == pygame.K_2: current_tool = 1
                if event.key == pygame.K_3: current_tool = 2
                if event.key == pygame.K_4: current_tool = 3
                if event.key == pygame.K_c: pheromones[:] = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if current_tool == 0:
                    mx, my = pygame.mouse.get_pos()
                    foods.append({
                        "pos": (mx, my),
                        "amount": 500,
                        "active":   True
                        })
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()

            if current_tool == 1:
                x_min = max(0, mx - brush_size)
                x_max = min(settings.WIDTH, mx + brush_size)
                y_min = max(0, my - brush_size)
                y_max = min(settings.HEIGHT, my + brush_size)
                pheromones[x_min:x_max, y_min:y_max, 0] = 255

            elif current_tool == 2:
                x_min = max(0, mx - brush_size)
                x_max = min(settings.WIDTH, mx + brush_size)
                y_min = max(0, my - brush_size)
                y_max = min(settings.HEIGHT, my + brush_size)
                pheromones[x_min:x_max, y_min:y_max, 1] = 255

            elif current_tool == 3:
                x_min = max(0, mx - brush_size)
                x_max = min(settings.WIDTH, mx + brush_size)
                y_min = max(0, my - brush_size)
                y_max = min(settings.HEIGHT, my + brush_size)
                walls[x_min:x_max, y_min:y_max] = True

        day_time = (day_time + day_speed) % 2.0
        sun_intensity = (math.cos(day_time * math.pi) + 1) / 2
        current_vision_factor = 0.3 + (0.7 * sun_intensity) 
        current_evap = settings.EVAPORATION_NIGHT if sun_intensity < 0.5 else settings.EVAPORATION_DAY
        pheromones *= current_evap
        pheromones[pheromones < 0.01] = 0
        dropped_food_this_frame = 0

        for ant in ants:
            has_delivered = ant.move(pheromones, foods, nest_pos, current_vision_factor, walls)
            if has_delivered:
                dropped_food_this_frame += 1
            ant.deposit_pheromone(pheromones)


        nest_food_stock += dropped_food_this_frame

        screen.fill(settings.COLOR_BG)

        p_visual = np.zeros((settings.WIDTH, settings.HEIGHT, 3), dtype=np.uint8)

        p_visual[:, :, 0] = np.clip(pheromones[:, :, 0] * 5, 0, 255).astype(np.uint8)
        p_visual[:, :, 2] = np.clip(pheromones[:, :, 1] * 5, 0, 255).astype(np.uint8)

        surf = pygame.surfarray.make_surface(p_visual)
        screen.blit(surf, (0, 0))

        pygame.draw.circle(screen, settings.COLOR_NEST, nest_pos["pos"], 10)

        for f in foods:
            if f["active"]:
                rad = max(2, int(f["amount"]/100))
                pygame.draw.circle(screen, settings.COLOR_FOOD, f["pos"], rad)

        for ant in ants:
            color = settings.COLOR_ANT_FOOD if ant.has_food else settings.COLOR_ANT_NO_FOOD
            screen.set_at((int(ant.x), int(ant.y)), color)
        if sun_intensity < 0.8:
            darkness = int(255 * (1.0 - sun_intensity) * 0.8)
            night_surf = pygame.Surface((settings.WIDTH, settings.HEIGHT))
            night_surf.set_alpha(darkness)
            night_surf.fill((0, 0, 20))
            screen.blit(night_surf, (0, 0))
        time_str = "NIGHT" if sun_intensity < 0.5 else "DAY"
        infos = [
            f"Time: {time_str} ({int(sun_intensity*100)}%)",
            f"Stock: {nest_food_stock}",
            f"Tool: {tool_names[current_tool]} (Push 1, 2, 3, 4)",
            f"Push 'C' to delete all pheromones"
        ]
        for i, line in enumerate(infos):
            t = font.render(line, True, (200, 200, 200))
            screen.blit(t, (10, 10 + i*20))

        pygame.display.flip()
        clock.tick(settings.FPS)
        pygame.display.set_caption(f"ACO Simulation - FPS: {int(clock.get_fps())} - Ants: {len(ants)}/{settings.ANT_COUNT} - Iterations: {iterations}")

    pygame.quit()
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(history["foods"], color='#00FF41', linewidth=2, label='Stock de nourriture')
    ax.set_title('Evolution of Ant', color='#00FF41',
                 fontsize=16)
    ax.set_xlabel('Iteration Sequence')
    ax.set_ylabel('Foods')
    ax.grid(True, linestyle='--', alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = "matrix_analysis.png"
    plt.savefig(filename, dpi=100)
    plt.close()


if __name__ == "__main__":
    main()
