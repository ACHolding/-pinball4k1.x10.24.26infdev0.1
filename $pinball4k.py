
from panda3d.core import loadPrcFileData

loadPrcFileData("", """
audio-library-name null
load-display pandagl
framebuffer-srgb false
win-size 1920 1080
""")

from ursina import *
from panda3d.core import Shader
import math
import random

app = Ursina(
    size=(1920, 1080),
    borderless=False,
    development_mode=False
)

window.title = "CatSDK Green Pinball 3D"
window.color = color.rgb(0, 65, 20)
window.exit_button.visible = False
window.fps_counter.enabled = True

# GLSL 1.20 compatibility shader.
# Uses a uniform color instead of Ursina's
# automatically generated GLSL shaders.
vertex_shader = """
#version 120
void main() {
    gl_Position = gl_ModelViewProjectionMatrix
                  * gl_Vertex;
}
"""

fragment_shader = """
#version 120
uniform vec4 object_color;
void main() {
    gl_FragColor = object_color;
}
"""

green_shader = Shader.make(
    Shader.SL_GLSL,
    vertex=vertex_shader,
    fragment=fragment_shader
)

# Camera
camera.position = (0, 18, -19)
camera.look_at((0, 0, 0))
camera.fov = 58

GREEN = (0.05, 0.8, 0.15, 1)
DARK_GREEN = (0.02, 0.22, 0.07, 1)
LIME = (0.5, 1.0, 0.1, 1)
YELLOW = (1.0, 0.8, 0.1, 1)
WHITE = (0.9, 0.95, 1.0, 1)

def model(kind, pos, scale, tint):
    e = Entity(
        model=kind,
        position=pos,
        scale=scale,
        color=color.white,
        double_sided=True
    )

    e.setShader(green_shader, 100)
    e.setShaderInput("object_color", *tint)
    return e

def box(pos, scale, tint):
    return model("cube", pos, scale, tint)

def sphere(pos, size, tint):
    return model("sphere", pos, size, tint)

# Table
box((0, -.4, 0), (10, .6, 17), DARK_GREEN)
box((0, -.05, 0), (9.4, .12, 16), GREEN)

# Rails
box((-4.8, .4, 0), (.35, .9, 16), LIME)
box((4.8, .4, 0), (.35, .9, 16), LIME)
box((0, .4, 8), (9.6, .9, .35), LIME)

# Bumpers
bumpers = [
    (-2.3, 4, .75),
    (2.3, 4, .75),
    (0, 2.1, .85),
    (-2.5, -.4, .65),
    (2.5, -.4, .65)
]

for x, z, radius in bumpers:
    sphere(
        (x, .35, z),
        radius * 1.8,
        YELLOW
    )

# Flippers
LEFT = Vec2(-1.2, -5.6)
RIGHT = Vec2(1.2, -5.6)
FLIPPER_LENGTH = 2.25

left_flipper = box(
    (-1.2, .35, -5.6),
    (FLIPPER_LENGTH, .4, .55),
    LIME
)

right_flipper = box(
    (1.2, .35, -5.6),
    (FLIPPER_LENGTH, .4, .55),
    LIME
)

# Ball
BALL_RADIUS = .23

ball = sphere(
    (3.8, .45, -6.5),
    BALL_RADIUS * 2,
    WHITE
)

ball_pos = Vec2(3.8, -6.5)
ball_vel = Vec2(0, 0)

score = 0
balls_left = 3
playing = False
game_over = False

score_text = Text(
    text="SCORE: 0",
    position=(-.8, .43),
    scale=1.5,
    color=color.white
)

balls_text = Text(
    text="BALLS: 3",
    position=(.5, .43),
    scale=1.5,
    color=color.white
)

message = Text(
    text="SPACE TO LAUNCH",
    origin=(0, 0),
    position=(0, -.43),
    scale=1.5,
    color=color.white
)

def reset_ball():
    global playing, ball_pos, ball_vel
    playing = False
    ball_pos = Vec2(3.8, -6.5)
    ball_vel = Vec2(0, 0)
    if not game_over:
        message.text = "SPACE TO LAUNCH"

def input(key):
    global playing, ball_vel
    global score, balls_left, game_over

    if key == "r":
        score = 0
        balls_left = 3
        game_over = False
        score_text.text = "SCORE: 0"
        balls_text.text = "BALLS: 3"
        reset_ball()

    if key == "space" and not playing and not game_over:
        playing = True
        ball_vel = Vec2(
            random.uniform(-2, -1),
            14
        )
        message.text = ""

def update():
    global ball_pos, ball_vel
    global score, balls_left, game_over

    dt = min(time.dt, 1 / 30)

    left_active = bool(
        held_keys["a"] or held_keys["left arrow"]
    )
    right_active = bool(
        held_keys["d"] or held_keys["right arrow"]
    )

    left_angle = 62 if left_active else 18
    right_angle = 118 if right_active else 162

    for entity, pivot, angle in (
        (left_flipper, LEFT, left_angle),
        (right_flipper, RIGHT, right_angle)
    ):
        a = math.radians(angle)
        entity.rotation_y = -angle
        entity.x = pivot.x + math.cos(a) * FLIPPER_LENGTH / 2
        entity.z = pivot.y + math.sin(a) * FLIPPER_LENGTH / 2

    if not playing:
        ball.position = (ball_pos.x, .45, ball_pos.y)
        return

    for _ in range(4):
        step = dt / 4
        ball_vel.y -= 8.5 * step
        ball_pos += ball_vel * step

        if abs(ball_pos.x) > 4.35:
            ball_pos.x = max(
                -4.35, min(4.35, ball_pos.x)
            )
            ball_vel.x *= -.9

        if ball_pos.y > 7.55:
            ball_pos.y = 7.55
            ball_vel.y = -abs(ball_vel.y) * .9

        for bx, bz, radius in bumpers:
            delta = ball_pos - Vec2(bx, bz)
            distance = delta.length()
            minimum = radius + BALL_RADIUS

            if distance < minimum:
                normal = (
                    delta / distance
                    if distance > .0001
                    else Vec2(0, 1)
                )

                ball_pos = Vec2(bx, bz) + normal * minimum
                impact = ball_vel.dot(normal)

                if impact < 0:
                    ball_vel -= normal * (2 * impact)
                    ball_vel += normal * 3
                    score += 100
                    score_text.text = f"SCORE: {score}"

        # Flipper collisions
        for pivot, angle, active, left in (
            (LEFT, left_angle, left_active, True),
            (RIGHT, right_angle, right_active, False)
        ):
            a = math.radians(angle)
            direction = Vec2(
                math.cos(a), math.sin(a)
            )

            projection = max(
                0,
                min(
                    FLIPPER_LENGTH,
                    (ball_pos - pivot).dot(direction)
                )
            )

            closest = pivot + direction * projection
            delta = ball_pos - closest
            distance = delta.length()

            if distance < BALL_RADIUS + .3:
                normal = (
                    delta / distance
                    if distance > .0001
                    else Vec2(0, 1)
                )

                ball_pos = closest + normal * (
                    BALL_RADIUS + .3
                )

                if active:
                    ball_vel.y = 12
                    ball_vel.x += 2 if left else -2
                elif ball_vel.y < 0:
                    ball_vel.y = 5

        if ball_pos.y < -8:
            balls_left -= 1
            balls_text.text = f"BALLS: {balls_left}"

            if balls_left <= 0:
                game_over = True
                message.text = "GAME OVER - PRESS R"

            reset_ball()
            break

    ball.position = (ball_pos.x, .45, ball_pos.y)

app.run()
