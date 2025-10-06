# pyright: strict
import sys
import argparse
import pyxel
import random
import time
from typing import List, Optional

class EggPlayer:
    def __init__(self) -> None:
        # Sprite Parameters
        self.x: float = 0
        self.y: float = 0
        self.IMG: int = 0
        self.U: int = 48
        self.V: int = 0
        self.WIDTH: int = 16
        self.HEIGHT: int = 16
        self.DX: float = 0.5
        self.COL: int = 2

        # Status
        self.lives: int = 3
        self.is_falling: bool = False
        self.started: bool = False
        self.on_platform: Optional['Platform'] = None
        self.last_platform: Optional['Platform'] = None
        self.launched_from_platforms: List['Platform'] = []  # Track ALL platforms launched from
        self.score: int = 0
        self.landed: bool = False

        # Physics
        self.gravity: float = 0.15
        self.acceleration: float = 0.0

        # Respawn timer
        self.respawn_timer: float = 0.0

    def update(self, platforms: List['Platform'], scroll_y: int, camera: 'Camera', dt: float) -> None:
        # Time parameter
        if self.respawn_timer > 0:
            self.handle_respawn(dt)
            return

        if not self.started:
            self.handle_game_start(camera)
            return

        # Run controls if not in transition
        if not camera.transitioning:
            self.handle_physics()
            self.handle_platform_collision(platforms)
            self.check_death(scroll_y)
            self.handle_movement()
            self.update_falling_state()

    def handle_respawn(self, dt: float) -> None:
        # Subtract elapsed time
        self.respawn_timer -= dt
        if self.respawn_timer <= 0.0 and self.lives > 0:
            pyxel.playm(4, loop=False)
            self.reset_to_platform()

    def handle_game_start(self, camera: 'Camera') -> None:
        if pyxel.btnp(pyxel.KEY_SPACE) and not camera.transitioning:
            self.started = True
            self.acceleration = -3.5

    def handle_physics(self) -> None:
        self.acceleration += self.gravity
        self.acceleration = min(self.acceleration, 3.5)
        self.y += self.acceleration

    def handle_platform_collision(self, platforms: List['Platform']) -> None:
        for plat in platforms:
            if collision(self, plat) and self.acceleration >= 0:
                # Landing Parameters
                if plat not in self.launched_from_platforms or self.on_platform is plat:
                    self.y = plat.y - self.HEIGHT
                    self.acceleration = 0

                    # Sound and points
                    if plat != self.last_platform and plat not in self.launched_from_platforms:
                        pyxel.playm(2, loop=False)
                        self.score += 1

                    self.on_platform = plat
                    self.last_platform = plat
                    break

        if self.acceleration > 0:
            self.on_platform = None

    def check_death(self, scroll_y: int) -> None:
        death_line: float = scroll_y + 128
        if self.y > death_line:
            pyxel.playm(3, loop=False)
            self.lives -= 1
            self.respawn_timer = 1.0  # 1s respawn timer
            self.y = death_line + 100

    def handle_movement(self) -> None:
        # Move with platform horizontally
        if self.on_platform:
            self.x += self.on_platform.speed * self.on_platform.direction

        if pyxel.btnp(pyxel.KEY_SPACE) and self.acceleration == 0:
            self.acceleration = -3.5
            # Add current platform to launch history
            if self.on_platform and self.on_platform not in self.launched_from_platforms:
                self.launched_from_platforms.append(self.on_platform)
            self.on_platform = None
            pyxel.playm(1, loop=False)

        if pyxel.btn(pyxel.KEY_LEFT) and self.acceleration != 0:
            self.x -= 2
        if pyxel.btn(pyxel.KEY_RIGHT) and self.acceleration != 0:
            self.x += 2

        # Keep egg within screen
        self.x = max(0, min(self.x, 128 - self.WIDTH))

    def update_falling_state(self) -> None:
        if self.on_platform:
            self.is_falling = False
        elif self.acceleration > 0:
            self.is_falling = True
        else:
            self.is_falling = False

    def reset_to_platform(self) -> None:
        if self.last_platform:
            self.y = self.last_platform.y - self.HEIGHT
            self.x = self.last_platform.x + self.last_platform.WIDTH // 2 - self.WIDTH // 2
            self.acceleration = 0
            self.on_platform = self.last_platform
            self.is_falling = False

    def reset_for_new_game(self) -> None:
        self.launched_from_platforms.clear()  # Clear launch history for new games
        self.lives = 3
        self.score = 0
        self.respawn_timer = 0.0
        self.last_platform = None

    def draw(self, cam_y: int = 0) -> None:
        if self.respawn_timer <= 0.0:
            pyxel.blt(
                int(self.x),
                int(self.y - cam_y),
                self.IMG,
                self.U,
                self.V,
                self.WIDTH,
                self.HEIGHT,
                self.COL
            )

class Camera:
    def __init__(self) -> None:
        self.transitioning: bool = False
        self.timer: float = 0.0
        self.duration: float = 2.0  # 2s topmost platform transition
        self.speed: float = 0.0
        self.offset_y: float = 0.0

        # Transition tracking
        self._initial_topmost_y: float = 0.0
        self._distance_to_move: float = 0.0
        self._old_top_platform: Optional['Platform'] = None
        self._new_p1: Optional['Platform'] = None
        self._new_p2: Optional['Platform'] = None

    def start_transition(self, platforms: List['Platform'], y0: int, y1: int, y2: int) -> None:
        # Initialize at topmost platform
        self._initial_topmost_y = min(p.y for p in platforms)
        self._distance_to_move = y0 - self._initial_topmost_y
        self._old_top_platform = min(platforms, key=lambda p: p.y)

        # Create 2 new platforms that will appear from above
        p1_init_y: float = y1 - self._distance_to_move
        p2_init_y: float = y2 - self._distance_to_move
        self._new_p1 = Platform(random.randint(0, 100), int(p1_init_y))
        self._new_p2 = Platform(random.randint(0, 100), int(p2_init_y))

        # Add new platforms to the list
        platforms.extend([self._new_p1, self._new_p2])

        # Start transition
        self.transitioning = True
        self.timer = self.duration
        self.speed = self._distance_to_move / self.duration

    def update(self, dt: float) -> None:
        if self.transitioning and self.timer > 0:
            # Subtract elapsed time
            self.timer -= dt

            # Transition movement calculator
            time_elapsed: float = self.duration - self.timer
            self.offset_y = -self.speed * time_elapsed

            if self.timer <= 0:
                self.timer = 0.0

    def finalize_transition(self, platforms: List['Platform'], player: EggPlayer, y0: int, y1: int, y2: int) -> bool:
        if self.transitioning and self.timer <= 0:
            # Set final y positions
            if self._old_top_platform:
                self._old_top_platform.y = y0
            if self._new_p1:
                self._new_p1.y = y1
            if self._new_p2:
                self._new_p2.y = y2

            # Move player with platform
            if player.on_platform is self._old_top_platform:
                player.y = y0 - player.HEIGHT

            # Keep only the three platforms
            platforms.clear()
            if self._old_top_platform and self._new_p1 and self._new_p2:
                platforms.extend([self._old_top_platform, self._new_p1, self._new_p2])

            # Reset transition state
            self.transitioning = False
            self.timer = 0.0
            self.speed = 0.0
            self.offset_y = 0.0

            # Clear references
            self._old_top_platform = None
            self._new_p1 = None
            self._new_p2 = None
            self._initial_topmost_y = 0.0
            self._distance_to_move = 0.0

            return True
        return False

def collision(player: 'EggPlayer', platform: 'Platform') -> bool:
    return (
        player.x < platform.x + platform.WIDTH and
        player.x + player.WIDTH > platform.x and
        player.y + player.HEIGHT <= platform.y + 5 and
        player.y + player.HEIGHT >= platform.y
    )

class Platform:
    def __init__(self, x: int, y: int) -> None:
        # Sprite Paramaters
        self.x: float = x
        self.y: float = y
        self.IMG: int = 0
        self.U: int = 8
        self.V: int = 8
        self.WIDTH: int = 24
        self.HEIGHT: int = 8
        self.DX: float = 0.5
        self.COL: int = 2
        # Movement
        self.speed: float = random.uniform(0.5, 1.5)
        self.direction: int = random.choice([-1,1])

    def update(self, camera: Camera) -> None:
        # Don't move horizontally if transitioning
        if not camera.transitioning:
            self.x += self.speed * self.direction

            if self.x <= 0:
                self.x = 0
                self.direction = 1
            elif self.x + self.WIDTH >= 128:
                self.x = 128 - self.WIDTH
                self.direction = -1

    def draw(self, cam_y: int = 0) -> None:
        pyxel.blt(
            int(self.x),
            int(self.y - cam_y),
            self.IMG,
            self.U,
            self.V,
            self.WIDTH,
            self.HEIGHT,
            self.COL
        )

class EggRiseApp:
    def __init__(self) -> None:
        pyxel.load("lab06.pyxres")

        self.start_game()

        pyxel.run(self.update, self.draw)

    def start_game(self) -> None:
        # Music
        pyxel.playm(0, loop=True)

        # Camera
        self.camera: Camera = Camera()
        self.player: EggPlayer = EggPlayer()

        # 3 platforms
        self.y0: int = 96  # Bottommost platform height
        SPACE: int = 35
        self.y1: int = self.y0 - SPACE  # Middle platform
        self.y2: int = self.y1 - SPACE  # Topmost platform
        self.platform: List[Platform] = [
            Platform(random.randint(0, 100), self.y0),
            Platform(random.randint(0, 100), self.y1),
            Platform(random.randint(0, 100), self.y2)
        ]

        self.setup_player_spawn()

        # Camera Position
        self.scroll_y: int = 0
        self.has_transitioned: bool = False

        # Timer
        self.last_time: float = time.perf_counter()

        # Game over
        self.game_over: bool = False

    def reset_game(self) -> None:
        # Reset player state for new game
        self.player.reset_for_new_game()
        self.start_game()

    def setup_player_spawn(self) -> None:
        bottom_platform: Platform = max(self.platform, key=lambda p: p.y)
        self.player.x = bottom_platform.x + bottom_platform.WIDTH // 2 - self.player.WIDTH // 2
        self.player.y = bottom_platform.y - self.player.HEIGHT
        self.player.on_platform = bottom_platform
        self.player.last_platform = bottom_platform
        self.player.started = True # In-play

    def update(self) -> None:
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_game()
            return

        # Delta time for timer (dt)
        now: float = time.perf_counter()
        dt: float = now - self.last_time
        self.last_time = now

        # Gameover check
        if self.player.lives <= 0 and self.player.respawn_timer <= 0:
            if not self.game_over:
                self.game_over_state()
            return

        # Respawn time and transition
        self.player.update(self.platform, self.scroll_y, self.camera, dt)
        for plat in self.platform:
            plat.update(self.camera)

        # Camera transition
        if self.camera.transitioning:
            self.camera.update(dt)
            if self.camera.finalize_transition(self.platform, self.player, self.y0, self.y1, self.y2):
                self.has_transitioned = True
        else:
            self.check_for_transition()

    def check_for_transition(self) -> None:
        # Start transition if egg is at topmost platform
        topmost_platform: Platform = min(self.platform, key=lambda p: p.y)
        if (self.player.on_platform is topmost_platform and self.player.acceleration == 0):
            self.camera.start_transition(self.platform, self.y0, self.y1, self.y2)

    def draw(self) -> None:
        pyxel.cls(6)

        # Gameover stated
        if self.game_over:
            self.draw_game_over()
            return

        cam_offset: int = int(self.camera.offset_y)

        for plat in self.platform:
            plat.draw(cam_offset)
        self.player.draw(cam_offset)

        # Only draw ground tilemap before first transition
        if not self.has_transitioned:
            pyxel.bltm(0, -cam_offset, 0, 0, 0, 128, 128, 2)

        # UI elements
        pyxel.text(0, 1, f"Press R to Restart", 8)
        pyxel.text(0, 8, f"Lives: {self.player.lives}", 1)
        pyxel.text(0, 16, f"Score: {self.player.score}", 1)

        # UI for testing - uncomment to debug
        # pyxel.text(0, 24, f"Falling {self.player.is_falling}", 1)
        # pyxel.text(0, 32, f"Transition: {self.camera.transitioning}", 1)
        # pyxel.text(0, 40, f"Transition Timer: {self.camera.timer:.2f}", 1)
        # pyxel.text(0, 48, f"Respawn Timer: {self.player.respawn_timer:.2f}", 1)
        # pyxel.text(0, 56, f"Launched from: {len(self.player.launched_from_platforms)}", 1)

    # Game over func
    def game_over_state(self) -> None:
        self.game_over = True

    # Game over draw
    def draw_game_over(self) -> None:
        pyxel.stop()
        pyxel.text(45, 60, "GAME OVER", 8)
        pyxel.text(35, 70, f"Final Score: {self.player.score}", 7)
        pyxel.text(25, 80, "Press R to Restart", 7)

def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (30 or 60)")
    args: argparse.Namespace = parser.parse_args()

    if args.fps not in (30, 60):
        print("Error: --fps must be 30 or 60", file=sys.stderr)
        sys.exit(2)

    pyxel.init(128, 128, fps=args.fps, title="Egg Rise")
    EggRiseApp()

if __name__ == "__main__":
    main()
