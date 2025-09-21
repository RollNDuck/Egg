import pyxel
import random
import sys

SPACE = 35 #SET PLATFORM DISTANCE

class EggPlayer:
    def __init__(self):
        # Sprite Parameters
        self.x = 56
        self.y = 96
        self.IMG = 0
        self.U = 48
        self.V = 0
        self.WIDTH = 16
        self.HEIGHT = 16
        self.DX = 0.5
        self.COL = 2

        #Status
        self.lives = 3
        self.is_falling = False
        self.started = False
        self.on_platform = None
        self.last_platform = None
        self.launched_from = None
        self.score = 0
        self.landed = False
        # ^^ Variable to keep track of respawn time
        self.respawn_timer = 0

        # Physics
        self.gravity = 0.15
        self.acceleration = 0

    def update(self, platforms, scroll_y, fps):
        if self.respawn_timer > 0:
            self.handle_respawn()
            return

        if not self.started:
            self.handle_game_start()
            return

        self.handle_physics()
        self.handle_platform_collision(platforms)
        self.check_death(scroll_y, fps)
        self.handle_movement()
        self.update_falling_state()

    # ^^ New Separate respawn logic ^^
    def handle_respawn(self):
        self.respawn_timer -= 1
        if self.respawn_timer == 0 and self.lives > 0:
            if self.last_platform:
                self.reset_to_platform()
            else:
                self.reset_to_spawn()

    # Separate game start logic ^^
    def handle_game_start(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.started = True
            self.acceleration = -3.5

    # Separate physics logic ^^
    def handle_physics(self):
        self.acceleration += self.gravity
        self.acceleration = min(self.acceleration, 3.5)
        self.y += self.acceleration

    # Separate platform collision logic ^^
    def handle_platform_collision(self, platforms):
        for plat in platforms:
            if plat == self.launched_from:
                continue
            if collision(self, plat) and self.acceleration >= 0:
                self.y = plat.y - self.HEIGHT
                self.acceleration = 0
                if plat != self.last_platform:
                    self.score += 1

                self.on_platform = plat
                self.last_platform = plat
                self.launched_from = None
                break

        if self.acceleration > 0:
            self.on_platform = None

    # Separate death check logic ^^
    def check_death(self, scroll_y, fps):
        death_line = scroll_y + 128
        if self.y > death_line:
            self.lives -= 1
            self.launched_from = None  # ^^
            self.respawn_timer = fps
            self.y = death_line + 100

    # Separate movement logic ^^
    def handle_movement(self):
        if self.on_platform:
            self.x += self.on_platform.speed * self.on_platform.direction

        if pyxel.btn(pyxel.KEY_SPACE) and self.acceleration == 0:
            self.acceleration = -3.5
            self.launched_from = self.on_platform  # ^^
            self.on_platform = None

        if pyxel.btn(pyxel.KEY_LEFT) and self.acceleration != 0:
            self.x -= 2
        if pyxel.btn(pyxel.KEY_RIGHT) and self.acceleration != 0:
            self.x += 2

    # Separate falling state logic ^^
    def update_falling_state(self):
        if self.on_platform:
            self.is_falling = False
        elif self.acceleration > 0:
            self.is_falling = True
        else:
            self.is_falling = False

    # Separate respawn positioning ^^
    def reset_to_platform(self):
        self.y = self.last_platform.y - self.HEIGHT
        self.x = self.last_platform.x + self.last_platform.WIDTH // 2 - self.WIDTH // 2
        self.acceleration = 0
        self.on_platform = self.last_platform
        self.is_falling = False

    # Separate spawn positioning ^^
    def reset_to_spawn(self):
        self.y = 96
        self.x = 56
        self.acceleration = 0
        self.is_falling = False
        self.on_platform = None
        self.started = False

    def draw(self):
        # ^^ Don't spawn egg if timer isn't done
        if self.respawn_timer == 0:
            pyxel.blt(
                self.x,
                self.y,
                self.IMG,
                self.U,
                self.V,
                self.WIDTH,
                self.HEIGHT,
                self.COL
            )

class Platform:
    def __init__(self, x, y):
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

    def update(self):
        self.x += self.speed * self.direction

        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x + self.WIDTH >= 128:
            self.x = 128 - self.WIDTH
            self.direction = -1

    def draw(self):
        pyxel.blt(
            self.x,
            self.y,
            self.IMG,
            self.U,
            self.V,
            self.WIDTH,
            self.HEIGHT,
            self.COL
        )

class EggRiseApp:
    def __init__(self):
        # ^^ Base timer on attained FPS
        self.fps = 30  # ^^ Default runnable FPS if no FPS input
        if '--fps' in sys.argv:
            fps_index = sys.argv.index('--fps')
            if fps_index + 1 < len(sys.argv):
                self.fps = int(sys.argv[fps_index + 1])

        pyxel.init(128, 128, title="Pyxel Egg Rise Platformer")
        pyxel.load("platformer.pyxres")
        self.player = EggPlayer()
        self.platform = [Platform(random.randint(0, 100), 80 - i * SPACE) for i in range(10)]
        self.scroll_y = 0 # Camera Position
        pyxel.run(self.update, self.draw)

    def update(self):
        self.player.update(self.platform, self.scroll_y, self.fps)
        for plat in self.platform:
            plat.update()

        camera_y_level = self.player.y - 64
        if camera_y_level < self.scroll_y:
            self.scroll_y = camera_y_level

        for plat in list(self.platform):
            if plat.y - self.scroll_y > 128:
                self.platform.remove(plat)
                high_y = min(plats.y for plats in self.platform)
                new_y = high_y - SPACE
                self.platform.append(Platform(random.randint(0, 80), new_y))

    def draw(self):
        pyxel.cls(6)

        pyxel.camera(0, self.scroll_y)

        for plat in self.platform:
            plat.draw()
        self.player.draw()

        pyxel.bltm(0, 0, 0, 0, 0, 128, 128, 2)

        pyxel.camera()
        pyxel.text(0, 0, f"Lives: {self.player.lives}", 1)
        pyxel.text(0, 8, f"Score: {self.player.score}", 1)
        pyxel.text(0, 16, f"Falling {self.player.is_falling}", 1) #Check if falling or not for debugging


def GameOver():
    pass

def collision(player, platform):
    return (
        player.x < platform.x + platform.WIDTH and
        player.x + player.WIDTH > platform.x and
        player.y + player.HEIGHT <= platform.y + 5 and
        player.y + player.HEIGHT >= platform.y
    )

EggRiseApp()
