import sys
import argparse
import pyxel
import random
import time
import math
from typing import List, Optional

class EggPlayer:
    def __init__(self) -> None:
        # Sprite Parameters
        self.x = 0
        self.y = 0
        self.IMG = 0
        self.U = 48
        self.V = 0
        self.WIDTH = 16
        self.HEIGHT = 16
        self.DX = 0.5
        self.COL = 2

        # Status
        self.lives = 3
        self.is_falling = False
        self.started = False
        self.on_platform: Optional['Platform'] = None
        self.last_platform: Optional['Platform'] = None
        self.launched_from: Optional['Platform'] = None
        self.score = 0
        self.landed = False

        # Physics
        self.gravity = 0.15
        self.acceleration = 0.0

        # Respawn timer
        self.respawn_timer = 0.0

        # v7: Powered launch attrs
        self.spacebar_hold_time = 0.0
        self.is_charging = False
        self.powered_launch_ready = False
        self.powered_launch_threshold = 0.5

        # v7: Powered launch speed
        target_height = 70
        self.powered_launch_velocity = -math.sqrt(2 * self.gravity * target_height)

        # Camera reference for death checking
        self.camera: Optional['Camera'] = None

    def update(self, platforms: List['Platform'], scroll_y: int, camera: 'Camera', dt: float) -> None:
        # Store camera reference
        self.camera = camera

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
            self.handle_movement(dt)
            self.update_falling_state()
        else:
            # v6: Freeze during transition
            # v7: Reset charge on transition
            self.reset_powered_launch_state()
            return

    def handle_respawn(self, dt: float) -> None:
        # Subtract elapsed time
        self.respawn_timer -= dt
        if self.respawn_timer <= 0.0 and self.lives > 0:
            if self.last_platform:
                pyxel.playm(4, loop=False)
                self.reset_to_platform()
            else:
                pyxel.playm(4, loop=False)
                self.reset_to_spawn()

    def handle_game_start(self, camera: 'Camera') -> None:
        # v1: Single press launch
        if pyxel.btnp(pyxel.KEY_SPACE) and not camera.transitioning:
            self.started = True
            self.acceleration = -3.5

    def handle_physics(self) -> None:
        self.acceleration += self.gravity
        self.acceleration = min(self.acceleration, 3.5)
        self.y += self.acceleration

    def handle_platform_collision(self, platforms: List['Platform']) -> None:
        # v1: Top-edge landing
        for plat in platforms:
            # v1: No same platform
            if plat == self.launched_from:
                continue
            # v1: No upward landing
            if collision(self, plat) and self.acceleration >= 0:
                self.y = plat.y - self.HEIGHT
                self.acceleration = 0
                if plat != self.last_platform:
                    # v4: Land sound
                    pyxel.playm(2, loop=False)
                    self.score += 1

                self.on_platform = plat
                self.last_platform = plat
                self.launched_from = None
                break

        if self.acceleration > 0:
            self.on_platform = None

    def check_death(self, scroll_y: int) -> None:
        # Skip death checking entirely during camera transitions
        if self.camera and self.camera.transitioning:
            return

        # Normal death checking when not transitioning
        death_line = scroll_y + 128

        if self.y > death_line:
            # v4: Fall sound
            pyxel.playm(3, loop=False)
            self.lives -= 1
            self.launched_from = None
            # v1: 1s replacement delay
            self.respawn_timer = 1.0  # 1s respawn timer
            self.y = death_line + 100

    def handle_movement(self, dt: float) -> None:
        # Move with platform
        if self.on_platform:
            # v6: Follow ellipse x
            if hasattr(self.on_platform, 'elliptical_mode') and self.on_platform.elliptical_mode:
                # Get horizontal movement only
                prev_x = getattr(self.on_platform, '_prev_x', self.on_platform.x)
                delta_x = self.on_platform.x - prev_x
                self.x += delta_x
                # v6: Stick to top surface
                self.y = self.on_platform.y - self.HEIGHT
                self.acceleration = 0
            else:
                self.x += self.on_platform.speed * self.on_platform.direction

        # v7: Powered launch logic
        can_launch = (self.acceleration == 0 and not (self.camera and self.camera.transitioning))
        if can_launch:
            if pyxel.btn(pyxel.KEY_SPACE):
                if not self.is_charging:
                    self.is_charging = True
                    self.spacebar_hold_time = 0.0
                else:
                    self.spacebar_hold_time += dt
                    if (self.spacebar_hold_time >= self.powered_launch_threshold and not self.powered_launch_ready):
                        self.powered_launch_ready = True
            else:
                if self.is_charging:
                    if self.powered_launch_ready:
                        # v7: Powered launch
                        self.acceleration = self.powered_launch_velocity
                        pyxel.playm(5, loop=False)
                    else:
                        # v1/v4: Normal launch
                        self.acceleration = -3.5
                        pyxel.playm(1, loop=False)
                    # Common launch state
                    self.launched_from = self.on_platform
                    self.on_platform = None
                    self.reset_powered_launch_state()
        else:
            # Reset charging if not eligible
            self.reset_powered_launch_state()

        # v1: Air control left
        if pyxel.btn(pyxel.KEY_LEFT) and self.acceleration != 0:
            self.x -= 2
        # v1: Air control right
        if pyxel.btn(pyxel.KEY_RIGHT) and self.acceleration != 0:
            self.x += 2

        # v1: Keep within screen
        self.x = max(0, min(self.x, 128 - self.WIDTH))

    def reset_powered_launch_state(self) -> None:
        # v7: Reset powered state
        self.spacebar_hold_time = 0.0
        self.is_charging = False
        self.powered_launch_ready = False

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

    def reset_to_spawn(self) -> None:
        self.y = 96
        self.x = 56
        self.acceleration = 0
        self.is_falling = False
        self.on_platform = None
        self.started = False

    def draw(self, cam_y: int = 0) -> None:
        if self.respawn_timer <= 0.0:
            pyxel.blt(
                self.x,
                self.y - cam_y,
                self.IMG,
                self.U,
                self.V,
                self.WIDTH,
                self.HEIGHT,
                self.COL
            )
            # v7: Powered visual
            if self.powered_launch_ready:
                pulse_size = int(2 + math.sin(time.perf_counter() * 10) * 1)
                pyxel.circb(
                    self.x + self.WIDTH // 2,
                    self.y - cam_y + self.HEIGHT // 2,
                    self.WIDTH // 2 + pulse_size,
                    10
                )

class Camera:
    def __init__(self) -> None:
        self.transitioning = False
        self.timer = 0.0
        self.duration = 2.0  # v3: 2s transition
        self.speed = 0.0
        self.offset_y = 0.0

        # Transition tracking
        self._initial_topmost_y = 0.0
        self._distance_to_move = 0.0
        self._old_top_platform: Optional['Platform'] = None
        self._new_p1: Optional['Platform'] = None
        self._new_p2: Optional['Platform'] = None

    def start_transition(self, platforms: List['Platform'], y0: int, y1: int, y2: int) -> None:
        # v3: Init at topmost
        self._initial_topmost_y = min(p.y for p in platforms)
        self._distance_to_move = y0 - self._initial_topmost_y
        self._old_top_platform = min(platforms, key=lambda p: p.y)

        # v3: Spawn P1/P2 above
        p1_init_y = y1 - self._distance_to_move
        p2_init_y = y2 - self._distance_to_move
        # Cast to int for type checker; drawing math tolerates integer y
        self._new_p1 = Platform(random.randint(0, 100), int(p1_init_y))
        self._new_p2 = Platform(random.randint(0, 100), int(p2_init_y))

        # v3: Add new platforms
        platforms.extend([self._new_p1, self._new_p2])

        # v3: Start transition
        self.transitioning = True
        self.timer = self.duration
        self.speed = self._distance_to_move / self.duration

    def update(self, dt: float) -> None:
        if self.transitioning and self.timer > 0:
            # Subtract elapsed time
            self.timer -= dt

            # Transition movement calculator
            time_elapsed = self.duration - self.timer
            self.offset_y = -self.speed * time_elapsed

            if self.timer <= 0:
                self.timer = 0.0

    def finalize_transition(self, platforms: List['Platform'], player: EggPlayer, y0: int, y1: int, y2: int) -> bool:
        if self.transitioning and self.timer <= 0:
            # v3: Set final y
            if self._old_top_platform:
                self._old_top_platform.y = y0
            if self._new_p1:
                self._new_p1.y = y1
            if self._new_p2:
                self._new_p2.y = y2

            # Move player with platform
            if player.on_platform is self._old_top_platform:
                player.y = y0 - player.HEIGHT

            # v3: Keep three platforms
            platforms.clear()
            if self._old_top_platform and self._new_p1 and self._new_p2:
                platforms.extend([self._old_top_platform, self._new_p1, self._new_p2])

            # v3: Reset transition
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
        self.x = x
        self.y = y
        self.IMG = 0
        self.U = 8
        self.V = 8
        self.WIDTH = 24
        self.HEIGHT = 8
        self.DX = 0.5
        self.COL = 2
        # Movement
        self.speed = random.uniform(0.5, 1.5)
        self.direction = random.choice([-1,1])

        # v6: Ellipse props
        self.elliptical_mode = False
        self.ellipse_center_x = x
        self.ellipse_center_y = y
        # Initialize ellipse parameters (seed only; mode off)
        self._set_ellipse_params(
            center_x=x,
            center_y=y,
            a_range=(20, 35),
            b_range=(12, 25),
            min_diff=8.0,
            force_horizontal_major=False,
        )

        # Position tracking for player movement
        self._prev_x = x
        self._prev_y = y

    def update(self, camera: Camera) -> None:
        # v6: Track prev pos
        self._prev_x = self.x
        self._prev_y = self.y

        # v3: Freeze during transition
        if not camera.transitioning:
            if self.elliptical_mode:
                # v6: Update ellipse
                self.ellipse_time += self.ellipse_speed
                new_x = self.ellipse_center_x + self.ellipse_a * math.cos(self.ellipse_time)
                new_y = self.ellipse_center_y + self.ellipse_b * math.sin(self.ellipse_time)

                # Convert from center-based x to left-edge x and clamp
                left_x = new_x - self.WIDTH // 2
                self.x = max(0, min(left_x, 128 - self.WIDTH))
                # Keep vertical movement very limited (visible but playable)
                self.y = max(self.ellipse_center_y - 10, min(new_y, self.ellipse_center_y + 10))
            else:
                # Original horizontal movement
                self.x += self.speed * self.direction

                if self.x <= 0:
                    self.x = 0
                    self.direction = 1
                elif self.x + self.WIDTH >= 128:
                    self.x = 128 - self.WIDTH
                    self.direction = -1

    def enable_elliptical_movement(self, other_platforms: List['Platform']) -> None:
        # v6: Enable ellipse for this middle platform starting this segment
        self._set_ellipse_params(
            center_x=self.x + self.WIDTH // 2,
            center_y=self.y,
            a_range=(25, 35),   # Horizontal axis range
            b_range=(8, 12),    # Small vertical axis for playability
            min_diff=8.0,
            force_horizontal_major=True,
        )

        print(f"Elliptical movement enabled: center=({self.ellipse_center_x:.1f}, {self.ellipse_center_y:.1f}), axes=({self.ellipse_a:.1f}, {self.ellipse_b:.1f})")

        self.elliptical_mode = True

    def _set_ellipse_params(self, center_x, center_y, a_range, b_range, min_diff: float = 8.0, force_horizontal_major: bool = False) -> None:
        # Ellipse center
        self.ellipse_center_x = center_x
        self.ellipse_center_y = center_y

        # Generate axes with inequality guarantee
        a_candidate = random.uniform(a_range[0], a_range[1])
        b_candidate = random.uniform(b_range[0], b_range[1])
        if abs(a_candidate - b_candidate) < min_diff:
            b_candidate = a_candidate + min_diff

        if force_horizontal_major:
            # Ensure horizontal axis is the larger one for playability
            self.ellipse_a = max(a_candidate, b_candidate)
            self.ellipse_b = min(a_candidate, b_candidate)
        else:
            # Random assignment of major/minor axis
            if random.choice([True, False]):
                self.ellipse_a = max(a_candidate, b_candidate)
                self.ellipse_b = min(a_candidate, b_candidate)
            else:
                self.ellipse_a = min(a_candidate, b_candidate)
                self.ellipse_b = max(a_candidate, b_candidate)

        # Clamp horizontal axis to screen
        max_horizontal = min(35, (128 - self.WIDTH) // 2)
        self.ellipse_a = min(self.ellipse_a, max_horizontal)

        # Reset ellipse timing and randomize speed
        self.ellipse_time = 0
        self.ellipse_speed = random.uniform(0.02, 0.04)

    def draw(self, cam_y: int = 0) -> None:
        pyxel.blt(
            self.x,
            self.y - cam_y,
            self.IMG,
            self.U,
            self.V,
            self.WIDTH,
            self.HEIGHT,
            self.COL
        )

class EggRiseApp:
    def __init__(self) -> None:
        pyxel.load("lab06.pyxres")  # v2: Proper graphics
        self.start_game()
        pyxel.run(self.update, self.draw)

    def start_game(self) -> None:
        # Music
        pyxel.playm(0, loop=True)  # v4: BGM loop

        # Camera
        self.camera = Camera()
        self.player = EggPlayer()

        # v3: Three platforms
        self.y0 = 96  # Bottommost platform height
        SPACE = 35 # v1: S spacing
        self.y1 = self.y0 - SPACE  # Middle platform
        self.y2 = self.y1 - SPACE  # Topmost platform
        self.platform = [
            Platform(random.randint(0, 100), self.y0),
            Platform(random.randint(0, 100), self.y1),
            Platform(random.randint(0, 100), self.y2)
        ]

        self.setup_player_spawn()

        # Camera Position
        self.scroll_y = 0
        self.has_transitioned = False

        # v6: Transition counter for elliptical movement (odd transitions enable ellipse)
        self.transition_count = 0

        # Timer
        self.last_time = time.perf_counter()

        # Game over
        self.game_over = False

    def reset_game(self) -> None:
        self.start_game()

    def setup_player_spawn(self) -> None:
        bottom_platform = max(self.platform, key=lambda p: p.y)
        self.player.x = bottom_platform.x + bottom_platform.WIDTH // 2 - self.player.WIDTH // 2
        self.player.y = bottom_platform.y - self.player.HEIGHT
        self.player.on_platform = bottom_platform
        self.player.last_platform = bottom_platform
        self.player.started = True

    def update(self) -> None:
        if pyxel.btnp(pyxel.KEY_R):  # v5: Reset key
            self.reset_game()
            return

        # Delta time for timer (dt)
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now

        # Gameover check
        if self.player.lives <= 0 and self.player.respawn_timer <= 0:
            if not self.game_over:
                self.game_over_state()
            return

        # Update player and platforms
        self.player.update(self.platform, self.scroll_y, self.camera, dt)
        for plat in self.platform:
            plat.update(self.camera)

        # Camera transition
        if self.camera.transitioning:
            self.camera.update(dt)
            if self.camera.finalize_transition(self.platform, self.player, self.y0, self.y1, self.y2):
                self.has_transitioned = True
                self.transition_count += 1
        # v6: Enable ellipse on odd
                if self.transition_count % 2 == 1:
                    middle_platform = sorted(self.platform, key=lambda p: p.y)[1]
                    middle_platform.enable_elliptical_movement(self.platform)
                else:
            # v6: Disable ellipse on even
                    middle_platform = sorted(self.platform, key=lambda p: p.y)[1]
                    middle_platform.elliptical_mode = False
        else:
            self.check_for_transition()

    def check_for_transition(self) -> None:
        # Start transition if egg is at topmost platform
        topmost_platform = min(self.platform, key=lambda p: p.y)
        if (self.player.on_platform is topmost_platform and
            self.player.acceleration == 0):
            self.camera.start_transition(self.platform, self.y0, self.y1, self.y2)

    def draw(self) -> None:
        pyxel.cls(6)

        # Gameover state
        if self.game_over:
            self.draw_game_over()
            return

        cam_offset = int(self.camera.offset_y)

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

        # Debug info (previous + v6 + v7)
        pyxel.text(0, 24, f"Falling: {self.player.is_falling}", 1)
        pyxel.text(0, 32, f"Transition: {self.camera.transitioning}", 1)
        pyxel.text(0, 40, f"Transition Timer: {self.camera.timer:.2f}", 1)
        pyxel.text(0, 48, f"Respawn Timer: {self.player.respawn_timer:.2f}", 1)

        if self.has_transitioned:
            middle_platform = sorted(self.platform, key=lambda p: p.y)[1]
            pyxel.text(0, 56, f"Elliptical: {middle_platform.elliptical_mode}", 1)
            pyxel.text(0, 64, f"Transitions: {self.transition_count}", 1)
            pyxel.text(0, 72, f"Ellipse t: {middle_platform.ellipse_time:.2f}", 1)

        # v7: Powered launch debug
        pyxel.text(0, 80, f"Charging: {self.player.is_charging}", 1)
        pyxel.text(0, 88, f"Hold time: {self.player.spacebar_hold_time:.2f}", 1)
        pyxel.text(0, 96, f"Powered ready: {self.player.powered_launch_ready}", 1)

    def game_over_state(self) -> None:
        self.game_over = True

    def draw_game_over(self) -> None:
        pyxel.stop()
        pyxel.text(45, 60, "GAME OVER", 8)
        pyxel.text(35, 70, f"Final Score: {self.player.score}", 7)
        pyxel.text(25, 80, "Press R to Restart", 7)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (30 or 60)")
    args = parser.parse_args()

    if args.fps not in (30, 60):  # v2: FPS constraint
        print("Error: --fps must be 30 or 60", file=sys.stderr)
        sys.exit(2)

    pyxel.init(128, 128, fps=args.fps, title="Egg Rise")
    EggRiseApp()

if __name__ == "__main__":
    main()