import math
import random
import sys

import pygame
from pygame.locals import (DOUBLEBUF, OPENGL, QUIT, KEYDOWN,
                           K_ESCAPE, K_SPACE, K_LEFT, K_RIGHT, K_r, K_c)
from OpenGL.GL import *
from OpenGL.GLU import *

# Window Configuration

WIDTH, HEIGHT = 1280, 720
WORLD_W, WORLD_H = 16.0, 9.0      # visible world: x in [-8, 8], y in [-4.5, 4.5]
PX = WORLD_W / WIDTH              # size of one screen pixel in world units
INTRO = 2.6                       # seconds of "chapter title card" per chapter

# 3D "monitor" used in chapter 5: x, y, w, h in pixels (origin = bottom-left)
STAGE = (40, 120, 760, 480)         # used for Chapter 5.

# Colors Palette in OpenGL are usually represented in RGB format, where each value ranges from 0.0 to 1.0.
WHITE = (1.0, 1.0, 1.0)
INK = (0.10, 0.08, 0.20)
RED = (1.0, 0.25, 0.25)         # One corner of the triangle in Chapter 3, many highlights
GREEN = (0.20, 0.85, 0.35)      # Another corner of Chapter 3, Status Lamp (ON)
BLUE = (0.25, 0.45, 1.0)        # Third corner of Chapter 3, some UI elements
YELLOW = (1.0, 0.85, 0.20)
ORANGE = (1.0, 0.55, 0.10)
PINK = (1.0, 0.45, 0.55)

SANS_FONTS = "segoeui,arial,helvetica,dejavusans,liberationsans,freesans"       # For plain/normal text
MONO_FONTS = "consolas,couriernew,dejavusansmono,liberationmono,menlo,monospace" #To show the code


# Small math helpers (animation timing / easing)

# Keeps a number within a certain range Ex. k is always between 0 and 1
def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


# Mixture between two values (Linear Interpolation) Ex. a goes from b in the ratio k
def lerp(a, b, k):
    return a + (b - a) * k


# How far has time (t) progressed within the specified interval [a, b] (0 to 1) Ex. To turn on/off a specific part of the animation
def seg(t, a, b):
    return clamp((t - a) / (b - a))


# Slow start → fast in the middle → slow end (smooth transition) Ex. fade-in/out, soft animation
def smoothstep(k):
    k = clamp(k)
    return k * k * (3.0 - 2.0 * k)


# Moves a little further and then stops in place (cartoon style “pop”) Ex. A dot or object suddenly becomes larger
def ease_out_back(k):
    k = clamp(k)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (k - 1.0) ** 3 + c1 * (k - 1.0) ** 2


# Mixture of two colors Ex. Gradually changing colors
def mix(c0, c1, k):
    return (lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k), lerp(c0[2], c1[2], k))


# Use in Rasterization in Chapter 4 to find out if a point (p) is to the left of any side of a triangle (whether the pixel is inside)
def edge(a, b, p):
    """Edge function: > 0 when p is on the left of the directed edge a->b."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


# OpenGL state + 2D drawing primitives (immediate mode)

def setup_2d():
    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-WORLD_W / 2, WORLD_W / 2, -WORLD_H / 2, WORLD_H / 2, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


# Sets the color and transparency of any subsequent drawing.
def color(c, a=1.0):
    glColor4f(c[0], c[1], c[2], a)


def fill_rect(cx, cy, w, h, c, a=1.0, rot=0.0):
    glPushMatrix()
    glTranslatef(cx, cy, 0.0)
    if rot:
        glRotatef(rot, 0.0, 0.0, 1.0)
    color(c, a)
    glBegin(GL_QUADS)
    glVertex2f(-w / 2, -h / 2)
    glVertex2f(w / 2, -h / 2)
    glVertex2f(w / 2, h / 2)
    glVertex2f(-w / 2, h / 2)
    glEnd()
    glPopMatrix()


def fill_rect_gradient(x0, y0, x1, y1, c_bottom, c_top, a=1.0):
    glBegin(GL_QUADS)
    color(c_bottom, a)
    glVertex2f(x0, y0)
    glVertex2f(x1, y0)
    color(c_top, a)
    glVertex2f(x1, y1)
    glVertex2f(x0, y1)
    glEnd()


# Rounds the four corners of a simple rectangle.
def rounded_rect(cx, cy, w, h, r, c, a=1.0, steps=8):
    r = min(r, w / 2, h / 2)
    hw, hh = w / 2 - r, h / 2 - r
    color(c, a)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for ox, oy, start in ((hw, hh, 0), (-hw, hh, 90), (-hw, -hh, 180), (hw, -hh, 270)):
        for i in range(steps + 1):
            ang = math.radians(start + 90.0 * i / steps)
            glVertex2f(cx + ox + r * math.cos(ang), cy + oy + r * math.sin(ang))
    glVertex2f(cx + hw + r, cy + hh)          # close the fan
    glEnd()


def fill_ellipse(x, y, rx, ry, c, a=1.0, n=36):
    color(c, a)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    for i in range(n + 1):
        ang = 2.0 * math.pi * i / n
        glVertex2f(x + rx * math.cos(ang), y + ry * math.sin(ang))
    glEnd()


def fill_circle(x, y, r, c, a=1.0):
    fill_ellipse(x, y, r, r, c, a)


def ring(x, y, r, c, a=1.0, width=3.0, n=48):
    glLineWidth(width)
    color(c, a)
    glBegin(GL_LINE_LOOP)
    for i in range(n):
        ang = 2.0 * math.pi * i / n
        glVertex2f(x + r * math.cos(ang), y + r * math.sin(ang))
    glEnd()


def line(x0, y0, x1, y1, c, a=1.0, width=3.0):
    glLineWidth(width)
    color(c, a)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x1, y1)
    glEnd()


def outline(points, c, a=1.0, width=3.0, closed=True):
    glLineWidth(width)
    color(c, a)
    glBegin(GL_LINE_LOOP if closed else GL_LINE_STRIP)
    for p in points:
        glVertex2f(p[0], p[1])
    glEnd()


def tri(p0, p1, p2, c, a=1.0):
    color(c, a)
    glBegin(GL_TRIANGLES)
    glVertex2f(p0[0], p0[1])
    glVertex2f(p1[0], p1[1])
    glVertex2f(p2[0], p2[1])
    glEnd()


def tri_gradient(pts, cols, a=1.0):
    glBegin(GL_TRIANGLES)
    for p, c in zip(pts, cols):
        color(c, a)
        glVertex2f(p[0], p[1])
    glEnd()


def arrow(x0, y0, x1, y1, c, a=1.0, width=4.0, head=0.28):
    line(x0, y0, x1, y1, c, a, width)
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    if n < 1e-6:
        return
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    tri((x1, y1),
        (x1 - ux * head + px * head * 0.5, y1 - uy * head + py * head * 0.5),
        (x1 - ux * head - px * head * 0.5, y1 - uy * head - py * head * 0.5), c, a)


def star(x, y, r, rot, c, a=1.0):
    color(c, a)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    for i in range(9):
        ang = math.radians(rot + i * 45.0)
        rr = r if i % 2 == 0 else r * 0.38
        glVertex2f(x + rr * math.cos(ang), y + rr * math.sin(ang))
    glEnd()


def draw_grid(step=1.0, a=0.3):
    glLineWidth(1.0)
    color(WHITE, a)
    glBegin(GL_LINES)
    for i in range(-8, 9):
        glVertex2f(i * step, -4.5)
        glVertex2f(i * step, 4.5)
    for j in range(-4, 5):
        glVertex2f(-8.0, j * step)
        glVertex2f(8.0, j * step)
    glEnd()


def draw_axes(a=1.0):
    xc, yc = (0.85, 0.25, 0.30), (0.15, 0.65, 0.35)
    arrow(-7.8, 0.0, 7.7, 0.0, xc, a * 0.9, 3.0, 0.3)
    arrow(0.0, -3.4, 0.0, 3.4, yc, a * 0.9, 3.0, 0.3)
    draw_text("+x", 7.5, 0.35, 22, xc, a, bold=True)
    draw_text("+y", 0.35, 3.25, 22, yc, a, bold=True)
    fill_circle(0.0, 0.0, 0.08, INK, a)


# Text rendering
class TextCache:
    def __init__(self):
        self.fonts = {}
        self.textures = {}

    def font(self, size, mono=False, bold=False):
        key = (size, mono, bold)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont(MONO_FONTS if mono else SANS_FONTS,
                                                  size, bold=bold)
        return self.fonts[key]

    def width(self, text, size, mono=False, bold=False):
        if not text:
            return 0
        return self.font(size, mono, bold).size(text)[0]

    def clear(self):
        if self.textures:
            glDeleteTextures([e[0] for e in self.textures.values()])
        self.textures = {}

    def get(self, text, size, mono, bold):
        key = (text, size, mono, bold)
        entry = self.textures.get(key)
        if entry is None:
            if len(self.textures) > 500:
                self.clear()
            surf = self.font(size, mono, bold).render(text, True, (255, 255, 255))
            w, h = surf.get_size()
            data = _image_bytes(surf, "RGBA", True)              # True = flip for GL
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, data)
            entry = (tex, w, h)
            self.textures[key] = entry
        return entry


TEXT = TextCache()
_image_bytes = getattr(pygame.image, "tobytes", None) or pygame.image.tostring


def _text_quad(x0, y0, ww, hh, c, a):
    color(c, a)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(x0, y0)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(x0 + ww, y0)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(x0 + ww, y0 + hh)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(x0, y0 + hh)
    glEnd()


def _draw_text_line(text, x, y, size, c, a, align, mono, bold, shadow, scale):
    tex, w, h = TEXT.get(text, size, mono, bold)
    ww, hh = w * PX * scale, h * PX * scale
    if align == "left":
        x0 = x
    elif align == "right":
        x0 = x - ww
    else:
        x0 = x - ww / 2
    y0 = y - hh / 2
    if scale == 1.0:                       # snap to the pixel grid = crisp text
        x0 = round((x0 + WORLD_W / 2) / PX) * PX - WORLD_W / 2
        y0 = round((y0 + WORLD_H / 2) / PX) * PX - WORLD_H / 2
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    if shadow:
        _text_quad(x0 + 2 * PX, y0 - 2 * PX, ww, hh, (0.0, 0.0, 0.0), a * 0.6)
    _text_quad(x0, y0, ww, hh, c, a)
    glDisable(GL_TEXTURE_2D)


def draw_text(text, x, y, size=28, c=WHITE, a=1.0, align="center",
              mono=False, bold=False, shadow=False, scale=1.0):
    if a <= 0.01:
        return
    lines = text.split("\n")
    line_h = size * 1.28 * PX * scale
    top = y + (len(lines) - 1) * line_h / 2.0
    for i, ln in enumerate(lines):
        if ln:
            _draw_text_line(ln, x, top - i * line_h, size, c, a, align,
                            mono, bold, shadow, scale)


def speech_bubble(cx, cy, w, h, tip, text, size=26, a=1.0):
    rounded_rect(cx, cy, w + 0.1, h + 0.1, 0.32, INK, a)
    rounded_rect(cx, cy, w, h, 0.3, WHITE, a)
    bx = cx + clamp((tip[0] - cx) * 0.5, -w / 2 + 0.6, w / 2 - 0.6)
    by = cy - h / 2 + 0.04 if tip[1] < cy else cy + h / 2 - 0.04
    tri((bx - 0.25, by), (bx + 0.25, by), tip, WHITE, a)
    draw_text(text, cx, cy, size, INK, a, bold=True)


# HUD pieces: live-code panel, caption bar, title card, progress bar
def draw_code_panel(lines, header="PyOpenGL", side="right", top=4.4):
    if not lines:
        return
    size = 18
    items = [(ln if isinstance(ln, tuple) else (ln, 1.0)) for ln in lines]
    panel_a = max(a for _, a in items)
    if panel_a <= 0.01:
        return
    wmax = max(TEXT.width(t if t else " ", size, True) for t, _ in items)
    w = wmax * PX + 0.6
    line_h = size * 1.45 * PX
    h = 0.55 + line_h * len(items) + 0.15
    left = 7.85 - w if side == "right" else -7.85
    cx, cy = left + w / 2, top - h / 2
    rounded_rect(cx, cy, w, h, 0.18, (0.05, 0.06, 0.13), 0.90 * panel_a)
    draw_text(header, left + 0.25, top - 0.27, 14, (0.6, 0.7, 1.0), 0.9 * panel_a,
              "left", mono=True)
    for i, (txt, a) in enumerate(items):
        yy = top - 0.55 - line_h * (i + 0.5)
        code, sep, comment = txt.partition("#")
        draw_text(code, left + 0.3, yy, size, (0.92, 0.96, 1.0), a, "left", mono=True)
        if sep:
            off = TEXT.width(code, size, True) * PX
            draw_text("#" + comment, left + 0.3 + off, yy, size,
                      (0.5, 0.85, 0.6), a, "left", mono=True)


def draw_caption(text, a):
    if not text or a <= 0.01:
        return
    rounded_rect(0.0, -4.0, 15.3, 0.95, 0.3, (0.04, 0.04, 0.10), 0.82 * a)
    draw_text(text, 0.0, -4.0, 26, WHITE, a)


def draw_title_card(index, scene, t):
    a = smoothstep(seg(t, 0.0, 0.35)) * (1.0 - smoothstep(seg(t, INTRO - 0.5, INTRO)))
    if a <= 0.01:
        return
    k = lerp(0.85, 1.0, ease_out_back(seg(t, 0.0, 0.6)))
    rounded_rect(0.0, 0.2, 13.5, 3.0, 0.4, (0.05, 0.05, 0.15), 0.9 * a)
    draw_text(scene.label, 0.0, 1.15, 30, YELLOW, a, bold=True, scale=k)
    draw_text(scene.name, 0.0, 0.3, 60, WHITE, a, bold=True, scale=k)
    draw_text(scene.goal, 0.0, -0.65, 26, (0.75, 0.9, 1.0), a, scale=k)


def draw_hud(index, count, scene, show_code):
    label = "Chapter %d of %d: %s" % (index + 1, count, scene.name) \
        if index < count - 1 else "Finale: %s" % scene.name
    hint = "SPACE pause | LEFT/RIGHT chapter | C code | R restart | ESC quit"
    wl = TEXT.width(label, 22, False, True) * PX
    wh = TEXT.width(hint, 15) * PX
    w = max(wl, wh) + 0.4
    rounded_rect(-7.9 + w / 2, 4.08, w, 0.78, 0.2, (0.05, 0.05, 0.12), 0.55)
    draw_text(label, -7.7, 4.25, 22, WHITE, 1.0, "left", bold=True)
    draw_text(hint, -7.7, 3.9, 15, (0.75, 0.8, 0.95), 1.0, "left")


# Vexy Character Draw
BODY = [(-1.1, -0.75), (1.1, -0.75), (0.0, 1.2)]       # Vexy's 3 vertices (CCW)

# Vexy Character Color Setup
BODY_LO = (1.0, 0.55, 0.12)
BODY_HI = (1.0, 0.85, 0.25)
FOOT = (0.55, 0.30, 0.10)

# Different color
# BODY_LO = (0.10, 0.35, 0.90)
# BODY_HI = (0.35, 0.65, 1.00)
# FOOT = (0.10, 0.15, 0.45)

# Vexy Size
def draw_vexy(x=0.0, y=0.0, s=1.0, rot=0.0, mood=1.0, t=0.0, look=(0.0, 0.0),
              body=None, fill=1.0, face=1.0, walk=None, squash=(1.0, 1.0), talk=0.0):

    glPushMatrix()
    glTranslatef(x, y, 0.0)                              # 1. translate
    glRotatef(rot, 0.0, 0.0, 1.0)                        # 2. rotate
    glScalef(s * squash[0], s * squash[1], 1.0)          # 3. scale

    if fill > 0.01:
        for side in (-1, 1):                             # stubby feet
            lift = 0.0
            if walk is not None:
                lift = max(0.0, math.sin(walk + (0.0 if side < 0 else math.pi))) * 0.25
            fill_ellipse(side * 0.55, -0.80 + lift, 0.30, 0.17, FOOT, fill)

    if body is None:
        cols = [BODY_LO, BODY_LO, BODY_HI]
    elif isinstance(body[0], (tuple, list)):
        cols = body
    else:
        cols = [body, body, body]
    tri_gradient(BODY, cols, fill)

    glLineWidth(4.0)                                     # cartoon outline
    color(INK, fill)
    glBegin(GL_LINE_LOOP)
    for p in BODY:
        glVertex2f(p[0], p[1])
    glEnd()
    glPointSize(5.0)                                     # round the corners
    glBegin(GL_POINTS)
    for p in BODY:
        glVertex2f(p[0], p[1])
    glEnd()

    if face > 0.01:
        lx, ly = look
        n = math.hypot(lx, ly)
        if n > 1.0:
            lx, ly = lx / n, ly / n
        blink = 0.12 if (t % 3.4) > 3.25 else 1.0
        for ex in (-0.30, 0.30):
            fill_ellipse(ex, 0.05, 0.20, 0.20 * blink, WHITE, face)
            fill_ellipse(ex + lx * 0.09, 0.05 + ly * 0.09 * blink, 0.09,
                         0.09 * blink, INK, face)
        for cx in (-0.55, 0.55):
            fill_ellipse(cx, -0.20, 0.11, 0.07, PINK, 0.55 * face)
        if talk > 0.05:
            fill_ellipse(0.0, -0.40, 0.14, 0.04 + 0.12 * talk, INK, face)
        else:
            glLineWidth(4.0)
            color(INK, face)
            glBegin(GL_LINE_STRIP)
            for i in range(13):
                mx = -0.30 + 0.60 * i / 12.0
                my = -0.35 - mood * 0.12 * (1.0 - (mx / 0.30) ** 2)
                glVertex2f(mx, my)
            glEnd()
    glPopMatrix()


# Shared scenery
CLOUDS = [(-5.0, 3.3, 1.0, 0.25), (2.0, 3.0, 0.8, 0.18), (6.0, 2.6, 1.2, 0.12)]


def cloud(x, y, s=1.0, a=0.9):
    for dx, dy, r in ((-0.7, -0.05, 0.5), (0.0, 0.15, 0.7), (0.75, -0.05, 0.55), (0.2, -0.2, 0.5)):
        fill_circle(x + dx * s, y + dy * s, r * s, WHITE, a)


def drifting_clouds(t):
    for x0, y0, s, v in CLOUDS:
        cloud(((x0 + t * v + 11.0) % 22.0) - 11.0, y0, s)


def hills():
    fill_ellipse(-4.5, -4.3, 6.5, 1.8, (0.45, 0.78, 0.38))
    fill_ellipse(5.0, -4.4, 7.5, 1.9, (0.38, 0.70, 0.34))


# 3D helpers for chapter 5
_quadric = None


def sphere(radius):
    global _quadric
    if _quadric is None:
        _quadric = gluNewQuadric()
    gluSphere(_quadric, radius, 28, 18)


def begin_3d(perspective, eye, target, ortho_half=4.8):
    x, y, w, h = STAGE
    glViewport(x, y, w, h)
    glClear(GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = w / float(h)
    if perspective:
        gluPerspective(45.0, aspect, 0.1, 100.0)
    else:
        glOrtho(-ortho_half * aspect, ortho_half * aspect, -ortho_half, ortho_half, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(eye[0], eye[1], eye[2], target[0], target[1], target[2], 0.0, 1.0, 0.0)


def end_3d():
    glDisable(GL_LIGHTING)
    glDisable(GL_LIGHT0)
    glDisable(GL_COLOR_MATERIAL)
    glDisable(GL_NORMALIZE)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_POLYGON_OFFSET_FILL)
    setup_2d()


def setup_light(angle_deg):
    glEnable(GL_LIGHT0)
    a = math.radians(angle_deg)
    pos = [3.6 * math.cos(a), 2.4, 3.6 * math.sin(a), 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, pos)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.22, 0.22, 0.30, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.97, 0.85, 1.0])
    return pos


# (normal, color, 4 corners) for each face of a cube with half-size 1
CUBE_FACES = [
    ((1, 0, 0), (0.95, 0.25, 0.25), [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]),
    ((-1, 0, 0), (0.25, 0.80, 0.35), [(-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)]),
    ((0, 1, 0), (0.30, 0.50, 1.00), [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)]),
    ((0, -1, 0), (1.00, 0.85, 0.20), [(-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)]),
    ((0, 0, 1), (0.85, 0.40, 0.95), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
    ((0, 0, -1), (0.20, 0.85, 0.90), [(1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)]),
]


def draw_cube(lighting=False):
    for normal, c, verts in CUBE_FACES:
        glEnable(GL_POLYGON_OFFSET_FILL)       # push fills back a hair so the
        glPolygonOffset(1.0, 1.0)              # outlines never z-fight with them
        if lighting:
            glEnable(GL_LIGHTING)
        glColor3f(c[0], c[1], c[2])
        glBegin(GL_QUADS)
        glNormal3f(normal[0], normal[1], normal[2])   # surface normal for lighting
        for v in verts:
            glVertex3f(v[0], v[1], v[2])
        glEnd()
        glDisable(GL_POLYGON_OFFSET_FILL)
        glDisable(GL_LIGHTING)
        glLineWidth(3.0)
        glColor3f(0.08, 0.08, 0.18)
        glBegin(GL_LINE_LOOP)
        for v in verts:
            glVertex3f(v[0], v[1], v[2])
        glEnd()


def draw_floor_grid():
    glLineWidth(1.0)
    glColor3f(0.55, 0.65, 0.95)
    glBegin(GL_LINES)
    for x in range(-6, 7, 2):
        glVertex3f(x, -0.8, 2.0)
        glVertex3f(x, -0.8, -14.0)
    for z in range(2, -15, -2):
        glVertex3f(-6.0, -0.8, z)
        glVertex3f(6.0, -0.8, z)
    glEnd()

# SCENES Background
class Scene:
    label = ""
    name = ""
    goal = ""
    duration = 10.0
    bg_bottom = (0.80, 0.93, 1.00)
    bg_top = (0.40, 0.70, 0.98)
    captions = []                      # (start, end, text) in scene time

    def code(self, t):
        return []

    def draw(self, t):
        pass

    def caption(self, t):
        for a, b, text in self.captions:
            if a <= t < b:
                return text, min(seg(t, a, a + 0.3), 1.0 - seg(t, b - 0.25, b))
        return "", 0.0

    def talk(self, t):
        text, _ = self.caption(t)
        return (0.35 + 0.35 * math.sin(t * 17.0)) if text else 0.0


class Chapter1(Scene):
    label = "CHAPTER 1"
    name = "Vertices & Primitives"
    goal = "A vertex is a point. Three vertices make a triangle."
    duration = 14.5
    captions = [
        (0.0, 3.5, "Hi! I'm Vexy. Before I was a character, I was just... three points."),
        (3.5, 7.0, "Each point is a VERTEX: a position in space, like (x, y)."),
        (7.0, 10.5, "Connect three vertices and you get a TRIANGLE,\n"
                    "the building block of (almost) all computer graphics."),
        (10.5, 14.5, "Now fill it in... and I'm ALIVE!"),
    ]
    CX, CY, S = 0.0, -0.5, 2.0
    SPARKS = [(-3.2, 1.2), (3.3, 1.5), (-3.6, -1.0), (3.6, -0.8), (1.3, 3.2)]

    def verts(self):
        return [(self.CX + self.S * bx, self.CY + self.S * by) for bx, by in BODY]

    def code(self, t):
        lines = [("glBegin(GL_TRIANGLES)", seg(t, 0.3, 0.8))]
        for i, (x, y) in enumerate(self.verts()):
            lines.append(("  glVertex2f(%+4.1f, %+4.1f)  # v%d" % (x, y, i),
                          seg(t, 1.0 + i, 1.5 + i)))
        lines.append(("glEnd()", seg(t, 3.6, 4.0)))
        return lines

    def draw(self, t):
        drifting_clouds(t)
        hills()
        V = self.verts()

        fill_k = seg(t, 10.5, 11.5)
        face_k = seg(t, 11.5, 12.3)
        alive = t > 11.8
        k = max(0.0, t - 11.8)
        jump = abs(math.sin(k * 3.2)) * 0.45 if alive else 0.0
        sq = math.sin(k * 6.4) * 0.05 if alive else 0.0

        # edges "draw themselves" one after another (GL_LINES)
        edge_a = 1.0 - seg(t, 11.5, 12.0)
        for i in range(3):
            a, b = V[i], V[(i + 1) % 3]
            p = smoothstep(seg(t, 7.0 + i * 0.9, 7.9 + i * 0.9))
            if p > 0 and edge_a > 0:
                line(a[0], a[1], lerp(a[0], b[0], p), lerp(a[1], b[1], p), INK, edge_a, 5.0)

        if fill_k > 0:
            fill_ellipse(self.CX, -2.5, 1.7 - jump, 0.18, INK, 0.22)
            draw_vexy(self.CX, self.CY + jump, self.S, mood=1.0, t=t, fill=fill_k,
                      face=face_k, squash=(1.0 - sq, 1.0 + sq),
                      talk=self.talk(t) * face_k)

        # the vertices themselves: dots that pop in, with labels
        dots_a = 1.0 - seg(t, 11.0, 12.0)
        offsets = [(-0.1, -0.5), (0.1, -0.5), (0.0, 0.55)]
        for i, (x, y) in enumerate(V):
            p = ease_out_back(seg(t, 0.8 + i, 1.5 + i))
            if p > 0 and dots_a > 0:
                pulse = 0.17 + 0.03 * math.sin(t * 5 + i)
                fill_circle(x, y, pulse * p, (0.95, 0.2, 0.3), dots_a)
                ring(x, y, pulse * p, WHITE, dots_a, 3.0)
            la = seg(t, 1.3 + i, 1.9 + i) * dots_a
            draw_text("v%d = (%.1f, %.1f)" % (i, x, y), x + offsets[i][0], y + offsets[i][1],
                      24, INK, la, bold=True)

        if t > 12.0:
            for i, (sx, sy) in enumerate(self.SPARKS):
                tw = 0.5 + 0.5 * math.sin(t * 4 + i * 1.7)
                star(sx, sy + jump * 0.3, 0.12 + 0.14 * tw, t * 40 + i * 20, YELLOW,
                     seg(t, 12.0, 12.6))
            ba = seg(t, 12.3, 12.9)
            speech_bubble(-3.6, 2.9, 3.4, 0.8, (-0.5, 1.9 + jump), "Hi, I'm Vexy!", 26, ba)


class Chapter2(Scene):
    label = "CHAPTER 2"
    name = "Transformations"
    goal = "Translate, rotate and scale: moving vertices with matrices."
    duration = 23.2
    bg_bottom = (0.72, 0.78, 1.00)
    bg_top = (0.50, 0.58, 0.95)
    captions = [
        (0.0, 2.2, "Now that I exist, let's make me MOVE!\n"
                   "Transformations change where every vertex ends up."),
        (2.2, 7.2, "TRANSLATE: slide every vertex by the same offset (dx, dy)."),
        (7.2, 12.0, "ROTATE: swing every vertex around the origin by an angle."),
        (12.0, 16.2, "SCALE: stretch or shrink every vertex's distance from the origin."),
        (16.2, 23.2, "ORDER MATTERS! Same two calls, swapped. OpenGL applies the LAST call first,\n"
                     "so A spins in place while B orbits around the origin."),
    ]
    BASE_S = 1.1
    ORBIT = 1.6
    ORIGIN_A = (-4.0, -0.2)
    ORIGIN_B = (4.0, -0.2)

    def phase(self, t):
        if t < 2.2:
            return "intro"
        if t < 7.2:
            return "translate"
        if t < 12.0:
            return "rotate"
        if t < 16.2:
            return "scale"
        return "order"

    def center_x(self, t):
        if t < 2.2:
            return -5.5
        if t < 6.0:
            # Vexy Speed
            return lerp(-5.5, 5.5, smoothstep(seg(t, 2.2, 6.0)))
        return lerp(5.5, 0.0, smoothstep(seg(t, 6.0, 7.2)))

    def angle(self, t):
        return 360.0 * smoothstep(seg(t, 7.8, 11.6))

    def scale_factor(self, t):
        return 1.0 + 0.7 * math.sin(seg(t, 12.4, 15.8) * 2.0 * math.pi)

    def code(self, t):
        ph = self.phase(t)
        if ph == "intro":
            return ["# every vertex v is multiplied", "# by a 4x4 matrix:  v' = M * v"]
        if ph == "translate":
            return ["glTranslatef(%+5.1f, 0, 0)" % self.center_x(t), "draw_vexy()"]
        if ph == "rotate":
            return ["glRotatef(%5.1f, 0, 0, 1)  # about z" % self.angle(t), "draw_vexy()"]
        if ph == "scale":
            f = self.base_scale_text(t)
            return ["glScalef(%4.2f, %4.2f, 1)" % (f, f), "draw_vexy()"]
        return ["A  glTranslatef(1.6, 0, 0)", "   glRotatef(ang, 0, 0, 1)",
                "B  glRotatef(ang, 0, 0, 1)", "   glTranslatef(1.6, 0, 0)"]

    def base_scale_text(self, t):
        return self.BASE_S * self.scale_factor(t)

    def math_lines(self, t):
        ph = self.phase(t)
        if ph == "translate":
            return ["x' = x + %+.1f" % (self.center_x(t) + 5.5), "y' = y + 0.0"]
        if ph == "rotate":
            return ["x' = x*cos(a) - y*sin(a)", "y' = x*sin(a) + y*cos(a)",
                    "a = %5.1f deg" % self.angle(t)]
        if ph == "scale":
            return ["x' = sx * x", "y' = sy * y", "sx = sy = %.2f" % self.base_scale_text(t)]
        return []

    def draw(self, t):
        ph = self.phase(t)
        draw_grid(1.0, 0.28)
        axes_a = 1.0 - seg(t, 16.0, 16.6)
        if axes_a > 0.01:
            draw_axes(axes_a)
        talk = self.talk(t)
        S = self.BASE_S

        if ph in ("intro", "translate"):
            x = self.center_x(t)
            moving = abs(self.center_x(t + 0.02) - self.center_x(t - 0.02)) > 1e-4
            bounce = abs(math.sin(x * 3.5)) * 0.12 if moving else 0.0
            if t >= 2.4:
                draw_vexy(-5.5, 0.0, S, fill=0.18, face=0.0)            # ghost at the start
                arrow(-5.5, -1.9, x, -1.9, ORANGE, 1.0, 4.0)
                draw_text("dx = %+.1f" % (x + 5.5), (x - 5.5) / 2.0, -2.3, 26, INK, 1.0, bold=True)
            fill_ellipse(x, -1.05, 0.9, 0.14, INK, 0.22)
            draw_vexy(x, bounce, S, mood=1.0, t=t,
                      look=(-1.0 if t > 6.0 else 1.0, 0.0),
                      walk=(x * 3.5 if moving else None), talk=talk)

        elif ph == "rotate":
            ang = self.angle(t)
            r = math.radians(ang)
            c, s_ = math.cos(r), math.sin(r)
            line(0, 0, 2.6, 0, INK, 0.5, 2.0)
            arc = [(2.6 * math.cos(math.radians(a)), 2.6 * math.sin(math.radians(a)))
                   for a in [i * max(ang, 0.1) / 40.0 for i in range(41)]]
            outline(arc, ORANGE, 1.0, 5.0, closed=False)
            line(0, 0, 2.6 * c, 2.6 * s_, ORANGE, 0.9, 3.0)
            draw_vexy(0.0, 0.0, S, rot=ang, mood=0.7, t=t, talk=talk)
            for bx, by in BODY:                                         # the maths, made visible
                vx, vy = S * bx, S * by
                wx, wy = vx * c - vy * s_, vx * s_ + vy * c
                line(0, 0, wx, wy, INK, 0.45, 2.0)
                fill_circle(wx, wy, 0.08, RED, 1.0)
            draw_text("angle = %3.0f deg" % ang, 3.9, 2.0, 28, INK, 1.0, bold=True)

        elif ph == "scale":
            f = self.scale_factor(t)
            outline([(S * bx, S * by) for bx, by in BODY], INK, 0.35, 2.0)   # original size
            draw_vexy(0.0, 0.0, S * f, mood=1.0, t=t, talk=talk)
            for bx, by in BODY:
                wx, wy = S * f * bx, S * f * by
                line(0, 0, wx, wy, INK, 0.45, 2.0)
                fill_circle(wx, wy, 0.08, RED, 1.0)
            draw_text("scale = %.2f" % (S * f), 3.9, 2.0, 28, INK, 1.0, bold=True)

        else:
            self.draw_order_demo(t)

    def draw_order_demo(self, t):
        pop = ease_out_back(seg(t, 16.2, 17.0))

        # vexy rotation speed
        ang = (t - 16.2) * 90.0
        ax, ay = self.ORIGIN_A
        bx, by = self.ORIGIN_B
        R = self.ORBIT
        sc = 0.65 * pop

        for (ox, oy) in (self.ORIGIN_A, self.ORIGIN_B):        # little coordinate crosses
            line(ox - 0.8, oy, ox + 0.8, oy, (0.85, 0.25, 0.30), 0.9, 3.0)
            line(ox, oy - 0.8, ox, oy + 0.8, (0.15, 0.65, 0.35), 0.9, 3.0)
            fill_circle(ox, oy, 0.07, INK, 1.0)
            draw_text("origin", ox - 0.12, oy - 0.3, 18, INK, 1.0, "right", bold=True)
        ring(bx, by, R, INK, 0.35, 2.0)

        # Diamention A: Spin on its own position
        # translate first, then rotate
        glPushMatrix()
        glTranslatef(ax, ay, 0.0)          # panel origin
        glTranslatef(R, 0.0, 0.0)
        glRotatef(ang, 0.0, 0.0, 1.0)
        draw_vexy(0.0, 0.0, sc, mood=1.0, t=t, look=(0.0, 0.0), talk=self.talk(t))
        glPopMatrix()

        # Diamention B: Spin around the origin
        # rotate first, then translate
        glPushMatrix()
        glTranslatef(bx, by, 0.0)          # panel origin
        glRotatef(ang, 0.0, 0.0, 1.0)
        glTranslatef(R, 0.0, 0.0)
        draw_vexy(0.0, 0.0, sc, mood=1.0, t=t, look=(-1.0, 0.0), talk=self.talk(t))
        glPopMatrix()

        a = seg(t, 16.6, 17.4)
        rounded_rect(-4.0, -3.05, 5.7, 0.8, 0.25, INK, 0.85 * a)
        rounded_rect(4.0, -3.05, 5.7, 0.8, 0.25, INK, 0.85 * a)
        draw_text("A: glTranslatef, then glRotatef\nv' = T * R * v  ->  spins in place",
                  -4.0, -3.05, 20, WHITE, a)
        draw_text("B: glRotatef, then glTranslatef\nv' = R * T * v  ->  orbits the origin",
                  4.0, -3.05, 20, WHITE, a)

    def draw_hud_extras(self, t):
        lines = self.math_lines(t)
        if lines:
            draw_code_panel(lines, header="the maths", side="left", top=3.45)


class Chapter3(Scene):
    label = "CHAPTER 3"
    name = "Colors & Interpolation"
    goal = "Colors live on vertices; the GPU blends them across the face."
    duration = 16.0
    captions = [
        (0.0, 3.2, "Vertices can carry more than a position.\n"
                   "Let's give each one a COLOR."),
        (3.2, 7.2, "GL_FLAT: the whole triangle gets ONE color (from its last vertex)."),
        (7.2, 11.2, "GL_SMOOTH: colors are INTERPOLATED (blended) across the triangle."),
        (11.2, 16.0, "Inside, color = w0*red + w1*green + w2*blue.\n"
                     "The weights are called barycentric coordinates."),
    ]
    TRI = [(-1.9, -1.4), (1.9, -1.4), (0.0, 2.0)]
    FLAT_C = (-4.4, -0.1)
    SMOOTH_C = (0.7, -0.1)
    COLS = [RED, GREEN, BLUE]

    def code(self, t):
        shade = "GL_FLAT" if t < 7.2 else "GL_SMOOTH"
        return [("glColor3f(1,0,0)  # v0 red", seg(t, 0.8, 1.3)),
                ("glColor3f(0,1,0)  # v1 green", seg(t, 1.15, 1.65)),
                ("glColor3f(0,0,1)  # v2 blue", seg(t, 1.5, 2.0)),
                ("glShadeModel(%s)" % shade, seg(t, 3.0, 3.5))]

    def pts(self, center):
        return [(center[0] + x, center[1] + y) for x, y in self.TRI]

    def weights(self, t):
        tau = max(0.0, t - 9.5)
        w = [0.33 + 0.28 * math.sin(0.8 * tau),
             0.33 + 0.28 * math.sin(1.1 * tau + 1.7),
             0.33 + 0.28 * math.sin(1.5 * tau + 3.1)]
        w = [max(0.03, v) for v in w]
        s = sum(w)
        return [v / s for v in w]

    def draw(self, t):
        drifting_clouds(t)
        hills()
        panels = ((self.FLAT_C, False, 3.4, "GL_FLAT", "one color per face"),
                  (self.SMOOTH_C, True, 7.4, "GL_SMOOTH", "colors blended"))
        for center, smooth, t0, name, sub in panels:
            P = self.pts(center)
            fa = smoothstep(seg(t, t0, t0 + 1.0))
            if fa > 0:
                glShadeModel(GL_SMOOTH if smooth else GL_FLAT)       # <- the whole lesson
                tri_gradient(P, self.COLS, fa)
                glShadeModel(GL_SMOOTH)
            outline(P, INK, 1.0, 4.0)
            for i, (x, y) in enumerate(P):
                p = ease_out_back(seg(t, 0.4 + 0.35 * i, 1.0 + 0.35 * i))
                if p > 0:
                    fill_circle(x, y, 0.17 * p, self.COLS[i], 1.0)
                    ring(x, y, 0.17 * p, WHITE, 1.0, 3.0)
                    draw_text("v%d" % i, x, y + (0.42 if i == 2 else -0.42), 22, INK, 1.0, bold=True)
            la = seg(t, t0 - 0.3, t0 + 0.3)
            rounded_rect(center[0], 2.55, 2.7, 0.55, 0.25, INK, 0.85 * la)
            draw_text(name, center[0], 2.55, 24, WHITE, la, bold=True)
            draw_text(sub, center[0], -2.0, 22, INK, la, bold=True)

        if t >= 8.5:                                       # mini-Vexy samples the gradient
            w = self.weights(t)
            P = self.pts(self.SMOOTH_C)
            px = sum(w[i] * P[i][0] for i in range(3))
            py = sum(w[i] * P[i][1] for i in range(3))
            col = tuple(sum(w[i] * self.COLS[i][k] for i in range(3)) for k in range(3))
            k = ease_out_back(seg(t, 8.6, 9.4))
            draw_vexy(px, py, 0.42 * k, mood=1.0, t=t, look=(0.0, -0.4), body=col)
            self.draw_bars(t, w, col)

    def draw_bars(self, t, w, col):
        a = smoothstep(seg(t, 11.0, 11.8))
        if a <= 0.01:
            return
        rounded_rect(5.9, 0.2, 3.7, 3.9, 0.3, (0.05, 0.06, 0.14), 0.88 * a)
        draw_text("Weights at Vexy", 5.9, 1.85, 22, WHITE, a, bold=True)
        for i, y in enumerate((1.2, 0.5, -0.2)):
            draw_text("w%d" % i, 4.25, y, 22, WHITE, a, "left", bold=True)
            fill_rect(5.9, y, 2.0, 0.28, (0.2, 0.22, 0.35), a)
            fill_rect(4.9 + w[i], y, 2.0 * w[i], 0.28, self.COLS[i], a)
            draw_text("%.2f" % w[i], 7.0, y, 20, WHITE, a, "left", mono=True)
        draw_text("result", 4.25, -0.95, 22, WHITE, a, "left", bold=True)
        fill_rect(6.2, -0.95, 1.9, 0.5, col, a)
        draw_text("(%.2f, %.2f, %.2f)" % col, 5.9, -1.45, 18, WHITE, a, mono=True)


class Chapter4(Scene):
    label = "CHAPTER 4"
    name = "Rasterization"
    goal = "Turning a triangle into pixels: which pixels does it cover?"
    duration = 17.5
    bg_bottom = (0.07, 0.09, 0.22)
    bg_top = (0.16, 0.20, 0.42)
    captions = [
        (0.0, 4.5, "Your screen is a grid of PIXELS. But my triangle lives BETWEEN them...\n"
                   "so which pixels does it cover?"),
        (4.5, 9.5, "RASTERIZATION: for each pixel, three EDGE tests tell us if its center\n"
                   "is inside the triangle (all three must be >= 0)."),
        (9.5, 14.5, "Pixels inside get a color blended from the three vertices,\n"
                    "just like Chapter 3!"),
        (14.5, 17.5, "Triangles go in, pixels come out. That's rasterization!"),
    ]
    COLS, ROWS, CELL = 26, 14, 0.4
    GX0, GY0 = -7.2, -2.6
    A, B, C = (3.5, 1.5), (21.8, 3.2), (11.5, 12.4)       # Resterization triangle in grid units
    VEXY_POS = (5.6, -1.9)

    def __init__(self):
        area = edge(self.A, self.B, self.C)
        self.cells = []                                     # row-major, bottom row first
        for r in range(self.ROWS):
            for c in range(self.COLS):
                p = (c + 0.5, r + 0.5)                      # pixel CENTER
                e0 = edge(self.A, self.B, p)
                e1 = edge(self.B, self.C, p)
                e2 = edge(self.C, self.A, p)
                inside = e0 >= 0 and e1 >= 0 and e2 >= 0
                col = None
                if inside:
                    wa, wb, wc = e1 / area, e2 / area, e0 / area
                    col = tuple(wa * RED[k] + wb * GREEN[k] + wc * BLUE[k] for k in range(3))
                self.cells.append((c, r, inside, col, e0, e1, e2))

    def to_world(self, p):
        return (self.GX0 + p[0] * self.CELL, self.GY0 + p[1] * self.CELL)

    def scan_index(self, t):
        return int(seg(t, 5.0, 14.5) * len(self.cells))

    def code(self, t):
        a = seg(t, 4.5, 5.2)
        return [("e0 = edge(A, B, p)", a), ("e1 = edge(B, C, p)", a),
                ("e2 = edge(C, A, p)", a), ("inside = min(e0, e1, e2) >= 0", a)]

    def draw(self, t):
        grid_a = smoothstep(seg(t, 0.2, 1.5))
        idx = self.scan_index(t)
        cell, gap = self.CELL, 0.025
        glBegin(GL_QUADS)
        for i, (c, r, inside, col, _, _, _) in enumerate(self.cells):
            if i < idx:
                if inside:
                    color(col, grid_a)
                else:
                    color((0.12, 0.15, 0.30), grid_a)
            else:
                color((0.22, 0.27, 0.50), 0.9 * grid_a)
            x0 = self.GX0 + c * cell + gap
            y0 = self.GY0 + r * cell + gap
            glVertex2f(x0, y0)
            glVertex2f(x0 + cell - 2 * gap, y0)
            glVertex2f(x0 + cell - 2 * gap, y0 + cell - 2 * gap)
            glVertex2f(x0, y0 + cell - 2 * gap)
        glEnd()

        ta = smoothstep(seg(t, 3.0, 4.0))                      # the "true" triangle
        verts = [self.to_world(p) for p in (self.A, self.B, self.C)]
        if ta > 0:
            outline(verts, WHITE, 0.9 * ta, 3.0)
            for v, cc, nm in zip(verts, (RED, GREEN, BLUE), "ABC"):
                fill_circle(v[0], v[1], 0.13, cc, ta)
                ring(v[0], v[1], 0.13, WHITE, ta, 2.0)
                draw_text(nm, v[0], v[1] + (0.38 if nm == "C" else -0.38), 24, WHITE, ta,
                          bold=True, shadow=True)

        scanning = 5.0 <= t < 14.5 and idx < len(self.cells)
        look, mood = (0.0, 0.3), 1.0
        if scanning:
            c, r, inside, col, e0, e1, e2 = self.cells[idx]
            cx = self.GX0 + (c + 0.5) * cell
            cy = self.GY0 + (r + 0.5) * cell
            fill_rect(self.GX0 + self.COLS * cell / 2, cy, self.COLS * cell, cell, WHITE, 0.12)
            outline([(cx - cell / 2, cy - cell / 2), (cx + cell / 2, cy - cell / 2),
                     (cx + cell / 2, cy + cell / 2), (cx - cell / 2, cy + cell / 2)],
                    YELLOW, 1.0, 3.0)
            bob = abs(math.sin(t * 10.0)) * 0.05                # "Pixie" rides the scanline
            fill_rect(-7.5, cy + bob, 0.36, 0.36, YELLOW)
            fill_circle(-7.58, cy + bob + 0.05, 0.04, INK)
            fill_circle(-7.42, cy + bob + 0.05, 0.04, INK)
            look = (cx - self.VEXY_POS[0], cy - self.VEXY_POS[1])
            mood = 0.9 if inside else -0.6
            self.draw_readout(t, c, r, inside, col, e0, e1, e2)
        elif t >= 14.5:
            self.draw_readout(t, None, None, None, None, 0, 0, 0)

        draw_vexy(self.VEXY_POS[0], self.VEXY_POS[1], 0.7, mood=mood, t=t, look=look,
                  talk=self.talk(t) if not scanning else 0.0)

    def draw_readout(self, t, c, r, inside, col, e0, e1, e2):
        a = seg(t, 4.5, 5.2)
        rounded_rect(5.6, 0.6, 4.2, 2.8, 0.3, (0.04, 0.05, 0.12), 0.9 * a)
        if c is None:
            draw_text("Scan complete!", 5.6, 0.6, 26, YELLOW, a, bold=True)
            return
        draw_text("Testing pixel (col %d, row %d)" % (c, r), 5.6, 1.7, 20, WHITE, a, bold=True)
        for i, (name, e) in enumerate((("e0", e0), ("e1", e1), ("e2", e2))):
            good = e >= 0
            draw_text("%s = %+7.1f" % (name, e), 4.3, 1.2 - i * 0.4, 20,
                      GREEN if good else RED, a, "left", mono=True)
        draw_text("inside? YES" if inside else "inside? NO", 5.6, -0.1, 24,
                  GREEN if inside else RED, a, bold=True)
        if inside:
            fill_rect(5.6, -0.55, 1.6, 0.3, col, a)


class Chapter5(Scene):
    label = "CHAPTER 5"
    name = "Depth, Light & Projection"
    goal = "Turning a flat triangle world into a believable 3D one."
    duration = 20.0
    bg_bottom = (0.10, 0.12, 0.28)
    bg_top = (0.20, 0.25, 0.50)
    captions = [
        (0.0, 4.0, "Welcome to 3D! With the DEPTH TEST OFF, whatever is drawn last\n"
                   "covers everything, even things that are behind it."),
        (4.0, 8.5, "DEPTH TEST ON: the depth buffer remembers each pixel's distance,\n"
                   "so the CLOSEST surface wins."),
        (8.5, 13.0, "Add LIGHTING: every face has a NORMAL. The more a face points\n"
                    "toward the light, the brighter it gets."),
        (13.0, 16.5, "PERSPECTIVE projection: far things look smaller, like in real life."),
        (16.5, 20.0, "ORTHOGRAPHIC projection: size never changes with distance.\n"
                     "Great for CAD tools and 2D games."),
    ]

    def code(self, t):
        if t < 4.0:
            return ["glDisable(GL_DEPTH_TEST)", "draw_cube()    # painter's order"]
        if t < 8.5:
            return ["glEnable(GL_DEPTH_TEST)", "draw_cube()    # nearest wins"]
        if t < 13.0:
            return ["glEnable(GL_LIGHTING)", "glLightfv(GL_LIGHT0,GL_POSITION,p)",
                    "glNormal3f(nx, ny, nz)  # per face"]
        if t < 16.5:
            return ["gluPerspective(45, aspect, 0.1, 100)"]
        return ["glOrtho(-w, w, -h, h, 0.1, 100)"]

    def draw_cube_scene(self, t, light):
        glPushMatrix()
        glTranslatef(-0.8, 0.0, 0.0)
        glRotatef(t * 40.0, 1.0, 1.0, 0.3)
        glScalef(1.2, 1.2, 1.2)
        draw_cube(light)
        glPopMatrix()
        # a ball BEHIND the cube: without a depth test it is wrongly painted on top
        glPushMatrix()
        glTranslatef(1.2, 0.1 + 0.2 * math.sin(t * 2.0), -2.2)
        glColor3f(1.0, 0.55, 0.20)
        if light:
            glEnable(GL_LIGHTING)
        sphere(1.1)
        glDisable(GL_LIGHTING)
        glPopMatrix()

    def draw_corridor(self, t, light):
        draw_floor_grid()
        for row_x in (-2.2, 2.2):
            for k in range(4):
                glPushMatrix()
                glTranslatef(row_x, 0.0, -3.0 * k)
                glRotatef(t * 40.0 + k * 30.0, 0.0, 1.0, 0.0)
                glScalef(0.7, 0.7, 0.7)
                draw_cube(light)
                glPopMatrix()

    def draw(self, t):
        depth, light = t >= 4.0, t >= 8.5
        corridor, persp = t >= 13.0, t < 16.5

        rounded_rect(-2.75, 0.0, 9.8, 6.3, 0.3, (0.02, 0.03, 0.08), 1.0)       # monitor
        fill_rect_gradient(-7.5, -3.0, 2.0, 3.0, (0.12, 0.14, 0.30), (0.28, 0.33, 0.55))

        if corridor:
            eye, target = (0.0, 6.0, 6.0), (0.0, 0.0, -3.0)
        else:
            eye, target = (0.0, 1.8, 7.0), (0.0, 0.0, 0.0)
        begin_3d(persp, eye, target)
        if depth:
            glEnable(GL_DEPTH_TEST)
        light_pos = None
        if light:
            glEnable(GL_NORMALIZE)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            light_pos = setup_light(t * 45.0)
        if corridor:
            self.draw_corridor(t, light)
        else:
            self.draw_cube_scene(t, light)
        if light_pos:                                                       # the "sun"
            glDisable(GL_LIGHTING)
            glPushMatrix()
            glTranslatef(light_pos[0], light_pos[1], light_pos[2])
            glColor3f(1.0, 0.95, 0.4)
            sphere(0.18)
            glPopMatrix()
        end_3d()

        # --- 2D side panel: status lamps + Vexy ---------------------------------
        rounded_rect(5.1, 1.0, 5.0, 2.4, 0.3, (0.05, 0.06, 0.14), 0.88)
        self.lamp(3.0, 1.75, depth, "Depth test: " + ("ON" if depth else "OFF"))
        self.lamp(3.0, 1.0, light, "Lighting: " + ("ON" if light else "OFF"))
        self.lamp(3.0, 0.25, True, "Projection: " + ("perspective" if persp else "orthographic"),
                  BLUE if persp else ORANGE)
        mood = -0.8 if t < 4.0 else 1.0
        look = (-0.9, 0.2)
        draw_vexy(5.1, -1.85, 0.8, mood=mood, t=t, look=look, talk=self.talk(t))

    def lamp(self, x, y, on, label, on_color=GREEN):
        c = on_color if on else (0.85, 0.25, 0.25)
        fill_circle(x, y, 0.17, INK, 1.0)
        fill_circle(x, y, 0.12, c, 1.0)
        draw_text(label, x + 0.35, y, 22, WHITE, 1.0, "left")


# class Chapter6(Scene):
#
#     label = "CHAPTER 6"
#
#     name = "Texture Mapping"
#
#     goal = "Applying textures to objects."
#
#     duration = 15.0
#
#     def code(self, t):
#         return []
#
#     def draw(self, t):
#         pass



class Finale(Scene):
    label = "FINALE"
    name = "The Graphics Pipeline"
    goal = "Everything we learned, as one assembly line."
    duration = 16.0
    bg_bottom = (0.20, 0.16, 0.40)
    bg_top = (0.42, 0.30, 0.70)
    captions = [
        (0.0, 2.4, "Let's put it all together: the GRAPHICS PIPELINE!"),
        (2.4, 4.4, "1. Vertices: raw points enter the pipeline."),
        (4.4, 6.2, "2. Transform: move, rotate, scale and project them."),
        (6.2, 8.0, "3. Rasterize: triangles are turned into pixels."),
        (8.0, 9.8, "4. Color: interpolate colors, add light, test depth."),
        (9.8, 11.2, "5. Display: the finished picture reaches your screen!"),
        (11.2, 16.0, "Thanks for watching! Now it's YOUR turn to play with the code."),
    ]
    STOPS = [-6.0, -3.0, 0.0, 3.0, 6.0]
    NAMES = ["1. VERTEX\nDATA", "2. TRANSFORM\nT * R * S", "3. RASTERIZE\nto pixels",
             "4. COLOR\nshade + depth", "5. DISPLAY\nthe screen!"]
    BELT_Y = -1.7
    T0, STAGE_T = 2.6, 1.8

    def __init__(self):
        rnd = random.Random(7)
        palette = [RED, GREEN, BLUE, YELLOW, PINK, ORANGE, WHITE]
        self.confetti = [(rnd.uniform(-7.5, 7.5), rnd.uniform(0.0, 2.0), rnd.uniform(1.5, 3.0),
                          rnd.uniform(0.0, 6.28), rnd.uniform(1.5, 4.0), rnd.choice(palette))
                         for _ in range(90)]
        cell = 0.14                                     # Vexy as chunky pixels
        self.cell = cell
        self.pixels = []
        for gx in range(-10, 10):
            for gy in range(-8, 10):
                p = ((gx + 0.5) * cell, (gy + 0.5) * cell)
                if all(edge(BODY[i], BODY[(i + 1) % 3], p) >= 0 for i in range(3)):
                    self.pixels.append(p)

    def code(self, t):
        return []

    def u(self, t):
        return (t - self.T0) / self.STAGE_T

    def vexy_x(self, t):
        if t < 1.0:
            return -7.6
        if t < self.T0:
            return lerp(-7.6, self.STOPS[0], smoothstep(seg(t, 1.0, self.T0)))
        u = self.u(t)
        if u < 4.0:
            i = int(u)
            f = u - i
            return lerp(self.STOPS[i], self.STOPS[i + 1], smoothstep(seg(f, 0.5, 1.0)))
        return lerp(self.STOPS[4], 0.0, smoothstep(seg(t, 11.2, 12.4)))

    def draw_form(self, form, x, y, s, t):
        if form == 0:                                   # raw vertices
            for bx, by in BODY:
                fill_circle(x + bx * s, y + by * s, 0.11, (0.95, 0.2, 0.3))
                ring(x + bx * s, y + by * s, 0.11, WHITE, 1.0, 2.0)
        elif form == 1:                                 # transformed (wireframe)
            glPushMatrix()
            glTranslatef(x, y, 0.0)
            glRotatef(t * 60.0, 0.0, 0.0, 1.0)
            k = s * (1.0 + 0.15 * math.sin(t * 3.0))
            glScalef(k, k, 1.0)
            outline(BODY, WHITE, 1.0, 3.0)
            glPopMatrix()
        elif form == 2:                                 # rasterized (pixels)
            half = self.cell * s * 0.46
            color((0.85, 0.9, 1.0), 1.0)
            glBegin(GL_QUADS)
            for px, py in self.pixels:
                cx, cy = x + px * s, y + py * s
                glVertex2f(cx - half, cy - half)
                glVertex2f(cx + half, cy - half)
                glVertex2f(cx + half, cy + half)
                glVertex2f(cx - half, cy + half)
            glEnd()
        elif form == 3:                                 # colored
            tri_gradient([(x + bx * s, y + by * s) for bx, by in BODY], [RED, GREEN, BLUE])
        else:                                           # final image
            draw_vexy(x, y, s, mood=1.0, t=t, talk=self.talk(t))

    def draw(self, t):
        u = self.u(t)
        vx = self.vexy_x(t)
        fin = seg(t, 11.2, 12.4)
        st_a = 1.0 - smoothstep(seg(t, 11.0, 12.0))

        fill_rect(0.0, -3.3, 16.0, 2.6, (0.13, 0.10, 0.26))               # floor
        fill_rect(0.0, self.BELT_Y - 0.15, 16.0, 0.3, (0.28, 0.28, 0.36)) # conveyor belt
        for i in range(30):
            bx = -8.0 + ((i * 0.55 + t * 0.9) % 16.0)
            fill_rect(bx, self.BELT_Y - 0.15, 0.08, 0.3, (0.18, 0.18, 0.25))

        if st_a > 0.01:
            for i, sx in enumerate(self.STOPS):
                glow = clamp(1.4 - abs(vx - sx)) if t >= 1.0 else 0.0
                rounded_rect(sx, 0.5, 2.62, 3.5, 0.28, WHITE, (0.15 + 0.6 * glow) * st_a)
                rounded_rect(sx, 0.5, 2.5, 3.38, 0.25, mix((0.18, 0.15, 0.34), (0.45, 0.35, 0.80), glow),
                             0.95 * st_a)
                draw_text(self.NAMES[i], sx, 1.7, 18, WHITE, st_a, bold=True)
                fill_circle(sx, 0.75, 0.15, mix((0.4, 0.4, 0.5), GREEN, glow), st_a)

        k = math.floor(u + 0.05)
        form = 4 if t >= 11.2 else int(clamp(k, 0, 4))
        y = lerp(self.BELT_Y + 0.55, -0.6, fin)
        s = lerp(0.75, 1.5, fin)
        if 1 <= k <= 4 and t < 11.2:                                      # poof on every stage
            p = (u + 0.05) - k
            if p < 0.4:
                star(vx, y + 0.3, 0.6 + p * 2.0, p * 200, YELLOW, 1.0 - p / 0.4)
        if t >= 0.5:
            self.draw_form(form, vx, y, s, t)

        if t >= 11.4:                                                     # confetti!
            for x0, delay, speed, phase, freq, col in self.confetti:
                dt = t - 11.4 - delay
                if dt <= 0:
                    continue
                cy = 4.8 - ((dt * speed) % 10.0)
                cx = x0 + math.sin(dt * freq + phase) * 0.4
                fill_rect(cx, cy, 0.16, 0.10, col, 1.0, (dt * 200.0 + phase * 50.0) % 360.0)

        if fin > 0:
            draw_text("THE END", 0.0, 3.15, 64, YELLOW, fin, bold=True, shadow=True,
                      scale=lerp(0.7, 1.0, ease_out_back(fin)))
            draw_text("You learned: vertices, transformations, interpolation,\n"
                      "rasterization, depth, lighting and projection.", 0.0, 2.15, 26, WHITE,
                      fin, shadow=True)
            speech_bubble(4.9, 0.5, 4.6, 1.7, (1.5, 0.0),
                          "Your turn! Edit my\nvertices, colors and\ntransformations in the code.",
                          22, seg(t, 12.4, 13.0))

# The player: runs the chapters in order, draws the HUD, handles input
class Player:
    def __init__(self):
        self.scenes = [Chapter1(), Chapter2(), Chapter3(), Chapter4(), Chapter5(), Finale()]
        # self.scenes = [Chapter1(), Chapter2(), Chapter3(), Chapter4(), Chapter5(),chapter6(), Finale()]
        self.idx = 0
        self.t = 0.0
        self.paused = False
        self.show_code = True

    def goto(self, i):
        self.idx = i % len(self.scenes)
        self.t = 0.0

    def total(self, i=None):
        i = self.idx if i is None else i
        return INTRO + self.scenes[i].duration

    def update(self, dt):
        if self.paused:
            return
        self.t += dt
        if self.t >= self.total():
            self.goto(self.idx + 1)

    def overall_progress(self):
        done = sum(self.total(i) for i in range(self.idx))
        whole = sum(self.total(i) for i in range(len(self.scenes)))
        return (done + self.t) / whole

    def draw(self):
        sc = self.scenes[self.idx]
        t, st = self.t, self.t - INTRO               # st = time since the title card ended
        setup_2d()
        fill_rect_gradient(-8.0, -4.5, 8.0, 4.5, sc.bg_bottom, sc.bg_top)
        sc.draw(st)
        setup_2d()                                   # chapter 5 changed GL state

        draw_hud(self.idx, len(self.scenes), sc, self.show_code)
        if self.show_code:
            draw_code_panel(sc.code(st))
            if hasattr(sc, "draw_hud_extras"):
                sc.draw_hud_extras(st)
        text, a = sc.caption(st)
        draw_caption(text, a)
        draw_title_card(self.idx, sc, t)

        fill_rect(0.0, -4.47, 16.0, 0.06, WHITE, 0.15)               # progress bar
        pw = 16.0 * self.overall_progress()
        fill_rect(-8.0 + pw / 2, -4.47, pw, 0.06, YELLOW, 0.9)

        if self.paused:
            rounded_rect(0.0, 3.95, 2.2, 0.6, 0.2, (0.05, 0.05, 0.12), 0.8)
            draw_text("|| PAUSED", 0.0, 3.95, 24, WHITE, 1.0, bold=True)

        fade = max(1.0 - seg(t, 0.0, 0.5), seg(t, self.total() - 0.5, self.total()))
        if fade > 0.01:
            fill_rect(0.0, 0.0, 16.5, 9.5, (0.0, 0.0, 0.0), fade)

# main
def init_window():
    pygame.init()
    pygame.display.set_caption("Vexy the Vertex - a Graphics Pipeline cartoon")
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    try:                                     # try smooth (anti-aliased) edges first
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    except pygame.error:
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
        pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    try:
        glEnable(GL_MULTISAMPLE)
    except Exception:
        pass
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_POINT_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)


def main():
    init_window()
    player = Player()
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.1)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    player.paused = not player.paused
                elif event.key == K_RIGHT:
                    player.goto(player.idx + 1)
                elif event.key == K_LEFT:
                    player.goto(player.idx if player.t > 3.0 else player.idx - 1)
                elif event.key == K_r:
                    player.goto(0)
                elif event.key == K_c:
                    player.show_code = not player.show_code
        player.update(dt)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        player.draw()
        pygame.display.flip()
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
