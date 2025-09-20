import pyxel
import random

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
        self.score = 0
        self.landed = False

        # Physics
        self.gravity = 0.15
        self.acceleration = 0

    def update(self, platforms, scroll_y):
        if not self.started:
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.started = True
                self.acceleration = -3.5
            return

        self.acceleration += self.gravity
        self.acceleration = min(self.acceleration, 3.5)
        self.y += self.acceleration

        for plat in platforms:
            if collision(self, plat) and self.acceleration >= 0:
                self.y = plat.y - self.HEIGHT
                self.acceleration = 0
                if plat != self.last_platform:
                    self.score += 1
                
                self.on_platform = plat
                self.last_platform = plat
                break

        if self.acceleration > 0:
            self.on_platform = None

        death_line = scroll_y + 128
        if self.y > death_line:
            self.lives -= 1
            if self.lives > 0 and self.last_platform: # Death at platforms
                self.y = self.last_platform.y - self.HEIGHT
                self.x = self.last_platform.x + self.last_platform.WIDTH // 2 - self.WIDTH // 2
                self.acceleration = 0
                self.on_platform = self.last_platform
                self.is_falling = False
            elif self.lives > 0 and self.last_platform is None: # Death at spawn
                self.y = 96
                self.x = 56
                self.acceleration = 0
                self.is_falling = False
                self.on_platform = None
                self.started = False
            else: # No more lives
                self.y = death_line - 1
                self.acceleration = 0
                self.started = False

        if self.on_platform: # If on platform playher speed match the platform speed
            self.x += self.on_platform.speed * self.on_platform.direction

        if pyxel.btn(pyxel.KEY_SPACE) and self.acceleration == 0:
            self.acceleration = -3.5
            self.on_platform = None

        if pyxel.btn(pyxel.KEY_LEFT) and self.acceleration != 0:
            self.x -= 2
        if pyxel.btn(pyxel.KEY_RIGHT) and self.acceleration != 0:
            self.x += 2

        if self.on_platform:
            self.is_falling = False
        elif self.acceleration > 0:
            self.is_falling = True
        else:
            self.is_falling = False

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
        pyxel.init(128, 128, title="Pyxel Egg Rise Platformer")
        pyxel.load("platformer.pyxres")
        self.player = EggPlayer()
        self.platform = [Platform(random.randint(0, 100), 80 - i * SPACE) for i in range(10)]
        self.scroll_y = 0 # Camera Position
        pyxel.run(self.update, self.draw)

    def update(self):
        self.player.update(self.platform, self.scroll_y)
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
