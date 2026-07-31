# Solaris v2.18

import pygame
import math
import configparser

WIDTH = 1280
HEIGHT = 720

G = 0.2

pygame.init()

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.RESIZABLE
)
pygame.display.set_caption("Solaris")

clock = pygame.time.Clock()


class Body:
    def __init__(
            self,
            name,
            x,
            y,
            vx,
            vy,
            mass,
            radius,
            image_appearance,
            image_hitbox,
            show_marker=True,
            static=False
    ):

        self.name = name

        self.x = x
        self.y = y

        self.vx = vx
        self.vy = vy

        self.mass = mass
        self.radius = radius

        self.static = static

        self.show_marker = show_marker

        # Visual image
        self.image = pygame.image.load(
            image_appearance
        ).convert_alpha()

        self.image = pygame.transform.scale(
            self.image,
            (radius * 2, radius * 2)
        )

        # Collision mask
        hitbox_image = pygame.image.load(
            image_hitbox
        ).convert_alpha()

        hitbox_image = pygame.transform.scale(
            hitbox_image,
            (radius * 2, radius * 2)
        )

        self.hitbox = pygame.mask.from_surface(
            hitbox_image
        )

        self.hitbox_width = hitbox_image.get_width()
        self.hitbox_height = hitbox_image.get_height()

    def draw(self, screen, camera_x, camera_y):

        sx = self.x - camera_x + WIDTH // 2
        sy = self.y - camera_y + HEIGHT // 2

        rect = self.image.get_rect(center=(sx, sy))
        screen.blit(self.image, rect)


class Ship:
    def __init__(
        self,
        x,
        y,
        image_appearance,
        image_hitbox,
        mass=10,
        thrust=0.2,
        rotation_speed=3
    ):
        self.x = x
        self.y = y

        self.start_x = x
        self.start_y = y

        self.vx = 0.0
        self.vy = 0.0

        self.start_vx = self.vx
        self.start_vy = self.vy

        self.angle = 0.0

        self.mass = mass
        self.thrust = thrust
        self.rotation_speed = rotation_speed

        self.image_original = pygame.image.load(
            image_appearance
        ).convert_alpha()

        hitbox_image = pygame.image.load(
            image_hitbox
        ).convert_alpha()

        self.hitbox = pygame.mask.from_surface(
            hitbox_image
        )

        self.hitbox_width = hitbox_image.get_width()
        self.hitbox_height = hitbox_image.get_height()

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y

        self.vx = self.start_vx
        self.vy = self.start_vy

        self.angle = 0

    def update(self):

        keys = pygame.key.get_pressed()

        # Resetting
        if keys[pygame.K_r]:
            self.reset()

        # Rotation
        if keys[pygame.K_LEFT]:
            self.angle += self.rotation_speed

        if keys[pygame.K_RIGHT]:
            self.angle -= self.rotation_speed

        rad = math.radians(self.angle)

        # Ship image points UP
        forward_x = -math.sin(rad)
        forward_y = -math.cos(rad)

        # Main engine
        if keys[pygame.K_UP]:
            self.vx += forward_x * self.thrust
            self.vy += forward_y * self.thrust

        # Reverse thrusters
        if keys[pygame.K_DOWN]:
            self.vx -= forward_x * self.thrust
            self.vy -= forward_y * self.thrust

        # Space = brake
        if keys[pygame.K_SPACE]:
            self.vx *= 0.8
            self.vy *= 0.8

        # Print Coords
        if keys[pygame.K_c]:
            print(self.x, self.y)

        self.x += self.vx
        self.y += self.vy

    def draw(self, screen, camera_x, camera_y):

        sx = self.x - camera_x + WIDTH // 2
        sy = self.y - camera_y + HEIGHT // 2

        rotated = pygame.transform.rotate(
            self.image_original,
            self.angle
        )

        rect = rotated.get_rect(center=(sx, sy))
        screen.blit(rotated, rect)


class Dock:
    def __init__(
        self,
        name,
        x,
        y,
        radius,
        message="Docking area"
    ):
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius
        self.message = message


def check_collisions(ship, bodies):

    crash_speed = 5

    for body in bodies:

        # Convert world positions into image offsets
        body_x = int(body.x - body.hitbox_width / 2)
        body_y = int(body.y - body.hitbox_height / 2)

        ship_x = int(ship.x - ship.hitbox_width / 2)
        ship_y = int(ship.y - ship.hitbox_height / 2)

        offset = (
            ship_x - body_x,
            ship_y - body_y
        )

        # Pixel-perfect collision
        if body.hitbox.overlap(ship.hitbox, offset):

            speed = math.sqrt(
                ship.vx ** 2 +
                ship.vy ** 2
            )

            # Sun destroys the ship
            if body.name.lower() == "sun":
                print("You flew into the Sun!")
                return "destroyed"


            # Landing check
            if speed < crash_speed:

                # print("Landed on", body.name)

                ship.vx = 0
                ship.vy = 0

                return "landed"

            else:

                print(
                    "CRASHED into",
                    body.name,
                    "at speed",
                    round(speed, 2)
                )

                return "destroyed"


    return "ok"


def check_docks(ship, docks):

    for dock in docks:

        dx = dock.x - ship.x
        dy = dock.y - ship.y

        distance = math.sqrt(
            dx * dx +
            dy * dy
        )

        if distance <= dock.radius:
            return dock

    return None


def draw_offscreen_marker(screen, body, camera_x, camera_y):
    # Position relative to camera
    dx = body.x - camera_x
    dy = body.y - camera_y
    distance = math.sqrt(dx * dx + dy * dy)

    # Convert to screen coordinates
    sx = dx + WIDTH // 2
    sy = dy + HEIGHT // 2

    # Already visible?
    if 0 < sx < WIDTH and 0 < sy < HEIGHT:
        return

    # Direction angle
    angle = math.atan2(dy, dx)

    # Put marker on screen border
    margin = 50

    center_x = WIDTH // 2
    center_y = HEIGHT // 2

    # Find intersection with border
    scale_x = (WIDTH / 2 - margin) / abs(math.cos(angle))
    scale_y = (HEIGHT / 2 - margin) / abs(math.sin(angle))

    scale = min(scale_x, scale_y)

    marker_x = center_x + math.cos(angle) * scale
    marker_y = center_y + math.sin(angle) * scale

    # Draw arrow
    size = 12

    points = [
        (
            marker_x + math.cos(angle) * size,
            marker_y + math.sin(angle) * size
        ),
        (
            marker_x + math.cos(angle + 2.5) * size,
            marker_y + math.sin(angle + 2.5) * size
        ),
        (
            marker_x + math.cos(angle - 2.5) * size,
            marker_y + math.sin(angle - 2.5) * size
        )
    ]

    pygame.draw.polygon(
        screen,
        (255, 255, 255),
        points
    )

    # Name label
    font = pygame.font.SysFont(None, 28)

    text = font.render(
        f"{body.name} {int(distance)}u",
        True,
        (255, 255, 255)
    )

    # Put text away from the arrow
    label_x = marker_x
    label_y = marker_y

    if marker_x < WIDTH / 2:
        # Left side -> text goes right
        label_x += 20
    else:
        # Right side -> text goes left
        label_x -= text.get_width() + 20

    if marker_y < HEIGHT / 2:
        # Top -> text goes down
        label_y += 20
    else:
        # Bottom -> text goes up
        label_y -= text.get_height() + 20

    # Clamp inside screen
    label_x = max(
        5,
        min(label_x, WIDTH - text.get_width() - 5)
    )

    label_y = max(
        5,
        min(label_y, HEIGHT - text.get_height() - 5)
    )

    screen.blit(
        text,
        (label_x, label_y)
    )

def load_ship(filename):

    cfg = configparser.ConfigParser()
    cfg.read(filename)

    s = cfg["ship"]

    return Ship(
        x=float(s["x"]),
        y=float(s["y"]),
        image_appearance=s["image_appearance"],
        image_hitbox=s["image_hitbox"],
        mass=float(s["mass"]),
        thrust=float(s["thrust"]),
        rotation_speed=float(s["rotation_speed"])
    )


def load_docks(filename):

    cfg = configparser.ConfigParser()
    cfg.read(filename)

    docks = []

    for section in cfg.sections():

        if section.startswith("dock"):

            docks.append(
                Dock(
                    name=cfg[section]["name"],
                    x=float(cfg[section]["x"]),
                    y=float(cfg[section]["y"]),
                    radius=float(cfg[section]["radius"]),
                    message=cfg[section].get(
                        "message",
                        "Docking area"
                    )
                )
            )

    return docks


def apply_gravity(ship, bodies):

    for body in bodies:

        dx = body.x - ship.x
        dy = body.y - ship.y

        dist_sq = dx * dx + dy * dy

        min_dist = body.radius

        if dist_sq < min_dist * min_dist:
            dist_sq = min_dist * min_dist

        if dist_sq < 25:
            continue

        dist = math.sqrt(dist_sq)

        force = G * body.mass / dist_sq

        ship.vx += force * dx / dist
        ship.vy += force * dy / dist


def load_world(filename):

    cfg = configparser.ConfigParser()
    cfg.read(filename)

    bodies = []

    for section in cfg.sections():

        if section.startswith("body"):
            body = Body(
                name=cfg[section]["name"],
                x=float(cfg[section]["x"]),
                y=float(cfg[section]["y"]),
                vx=float(cfg[section]["vx"]),
                vy=float(cfg[section]["vy"]),
                mass=float(cfg[section]["mass"]),
                radius=int(cfg[section]["radius"]),
                image_appearance=cfg[section]["image_appearance"],
                image_hitbox=cfg[section]["image_hitbox"],
                show_marker=cfg[section].getboolean(
                    "show_marker",
                    fallback=True
                ),
                static=cfg[section].getboolean("static")
            )

            bodies.append(body)

    return bodies

system = "Terra.cfg"

bodies = load_world(system)
ship = load_ship(system)
docks = load_docks(system)

running = True
current_dock = None

while running:

    dt = clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE:
            WIDTH = event.w
            HEIGHT = event.h

            screen = pygame.display.set_mode(
                (WIDTH, HEIGHT),
                pygame.RESIZABLE
            )

        if event.type == pygame.K_c:
            print(str(ship.x)+", "+str(ship.y))

    result = check_collisions(ship, bodies)

    if result != "landed":
        apply_gravity(ship, bodies)

    ship.update()

    if result == "destroyed":
        ship.reset()

    camera_x = ship.x
    camera_y = ship.y

    screen.fill((0, 0, 10))

    for body in bodies:
        body.draw(screen, camera_x, camera_y)

        if body.show_marker:
            draw_offscreen_marker(
                screen,
                body,
                camera_x,
                camera_y
            )

    dock = check_docks(ship, docks)

    if dock:

        if current_dock != dock.name:
            print()
            print("DOCKING CONTROL")
            print(dock.message)
            print()

            current_dock = dock.name

    else:
        current_dock = None

    ship.draw(screen, camera_x, camera_y)

    pygame.display.flip()

pygame.quit()