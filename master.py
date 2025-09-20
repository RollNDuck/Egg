import pyxel
import random

class EggPlayer:
    def __init__(self):
        # Sprite Parameters
        self.x = 56
        self.y = 0
        self.IMG = 0
        self.U = 48
        self.V = 0
        self.WIDTH = 16
        self.HEIGHT = 16
        self.DX = 0.5
        self.COL = 2

        # Game Parameters
        self.lives = 3
        self.started = False

        # ^^ Physics Parameters
        self.gravity = 0.15
        self.acceleration = 0
        # ^^Egg placement + platform determinant
        self.on_platform = None

    def update(self, platforms):
        # ^^Platform logic
        if self.on_platform is None:
            self._update_airborne(platforms)
        else:
            self._update_on_platform()

        if self.y >= 112:
            self.y = 112
            self.lives -= 1
            self.acceleration = 0
            # ^^ Removed comments on locked position (adjusted via platform logic)
            if platforms:
                self.on_platform = platforms[0]
                self.x = self.on_platform.x + self.on_platform.WIDTH/2 - self.WIDTH/2
                self.y = self.on_platform.y - self.HEIGHT

        if pyxel.btn(pyxel.KEY_SPACE) and self.acceleration == 0:
            self.acceleration = -3.5
            self.on_platform = None

    def _update_airborne(self, platforms):
        # ^^Only include gravity if not on platform
        self.acceleration += self.gravity
        self.y += self.acceleration

        # ^^If gravity present (egg not on platform), check if lands on platform
        if self.acceleration > 0:
            for platform in platforms:
                egg_bottom = self.y + self.HEIGHT
                egg_center_x = self.x + self.WIDTH/2
                on_platform_vertically = platform.y <= egg_bottom <= platform.y + 5
                on_platform_horizontally = platform.x <= egg_center_x <= platform.x + platform.WIDTH

                if on_platform_vertically and on_platform_horizontally:
                    # ^^ Platform landing
                    self.y = platform.y - self.HEIGHT
                    self.acceleration = 0
                    self.on_platform = platform
                    break

    def _update_on_platform(self):
        self.x = self.on_platform.x + self.on_platform.WIDTH/2 - self.WIDTH/2
        self.y = self.on_platform.y - self.HEIGHT


class Platform:
    def __init__(self, x ,y):
        # ^^Platform Sprite Parameters
        self.x = x
        self.y = y
        self.IMG = 0
        self.U = 0  # ^^Temporary basic ahh boxes
        self.V = 16  # ^^^^
        self.WIDTH = 32
        self.HEIGHT = 8
        # ^^Random Reqs for platform
        self.speed = random.uniform(0.5, 1.5)
        self.direction = random.choice([-1, 1])

    def update(self):
        # ^^ Move platform horizontally
        self.x += self.speed * self.direction

        # ^^Reverse direction when hitting screen bounds
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x + self.WIDTH >= 128:
            self.x = 128 - self.WIDTH
            self.direction = -1

    def draw(self):
        # ^^Temporary basic ahh boxes
        pyxel.rect(self.x, self.y, self.WIDTH, self.HEIGHT, 1)
        pyxel.rectb(self.x, self.y, self.WIDTH, self.HEIGHT, 0)

class EggRiseApp:
    def __init__(self):
        pyxel.init(128, 128, title="Pyxel Egg Rise Platformer")
        pyxel.load("platformer.pyxres")
        self.player = EggPlayer()
        self.platforms = []

        # ^^Create initial platforms (with set distance)
        distance = 25
        bottom_platform_y = 100
        middle_platform_y = bottom_platform_y - distance - 8
        top_platform_y = bottom_platform_y - 2 * (distance + 8)
        platform_y_positions = [bottom_platform_y, middle_platform_y, top_platform_y]  # ^^Bottom to top

        for i, y_pos in enumerate(platform_y_positions):
            x_pos = random.randint(0, 96)  # ^^Random platform position
            platform = Platform(x_pos, y_pos)
            self.platforms.append(platform)

        # ^^Start player on lowest platform
        if self.platforms:
            self.player.on_platform = self.platforms[0]
            self.player.x = self.platforms[0].x + self.platforms[0].WIDTH/2 - self.player.WIDTH/2
            self.player.y = self.platforms[0].y - self.player.HEIGHT

        pyxel.run(self.update, self.draw)

    def update(self):
        # ^^ Include platforms
        for platform in self.platforms:
            platform.update()

        self.player.update(self.platforms)

    def draw(self):
        pyxel.cls(6)
        pyxel.text(0, 0, f"Lives: {self.player.lives}", 1)

        # ^^ Include platforms
        for platform in self.platforms:
            platform.draw()

        pyxel.blt(
            self.player.x,
            self.player.y,
            self.player.IMG,
            self.player.U,
            self.player.V,
            self.player.WIDTH,
            self.player.HEIGHT,
            self.player.COL
        )

def GameOver():
    pass

EggRiseApp()
