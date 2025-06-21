import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

# Inicialización
globals = {}
pygame.init()
width, height = 800, 600
pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Paint OpenGL")

# Configuración de OpenGL
glViewport(0, 0, width, height)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, width, height, 0, -1, 1)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

# Variables del programa
drawing = False
current_tool = "pencil"  # "pencil", "line", "circle", "curve", "eraser"
eraser_size = 15  # Tamaño del borrador
points = []
control_points = []
stored_pixels = []
stored_lines = []
stored_curves = []
stored_circles = []
current_color = (1.0, 0.0, 0.0)  # Rojo por defecto

# Funciones auxiliares
def set_color(r, g, b):
    global current_color
    current_color = (r/255.0, g/255.0, b/255.0)

# Dibujo de píxeles, líneas y curvas

def draw_pixel(x, y, store=True, color=None, size=1):
    if color is None:
        color = current_color
    if store:
        stored_pixels.append((x, y, color, size))
    glColor3f(*color)
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()
    glPointSize(1)

def erase_at(x, y):
    global stored_pixels, stored_lines, stored_circles, stored_curves
    half = eraser_size // 2

    # Borra puntos
    stored_pixels = [
        (px, py, color, size)
        for (px, py, color, size) in stored_pixels
        if not (x - half <= px <= x + half and y - half <= py <= y + half)
    ]

    # Borra líneas si algún extremo está en el área del borrador
    stored_lines = [
        (x0, y0, x1, y1, color)
        for (x0, y0, x1, y1, color) in stored_lines
        if not (
            (x - half <= x0 <= x + half and y - half <= y0 <= y + half) or
            (x - half <= x1 <= x + half and y - half <= y1 <= y + half)
        )
    ]

    # Borra círculos si el centro está en el área del borrador
    stored_circles = [
        (cx, cy, radius, color)
        for (cx, cy, radius, color) in stored_circles
        if not (x - half <= cx <= x + half and y - half <= cy <= y + half)
    ]

    # Borra curvas si algún punto de control está en el área del borrador
    stored_curves = [
        (pts, color)
        for (pts, color) in stored_curves
        if not any(x - half <= px <= x + half and y - half <= py <= y + half for (px, py) in pts)
    ]

def draw_line_bresenham(x0, y0, x1, y1, store=True):
    if store:
        stored_lines.append((x0, y0, x1, y1, current_color))
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    steep = dy > dx
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    error = dx // 2
    y_step = 1 if y0 < y1 else -1
    y = y0
    glColor3f(*current_color)
    glBegin(GL_POINTS)
    for x in range(int(x0), int(x1) + 1):
        coord = (y, x) if steep else (x, y)
        glVertex2f(coord[0], coord[1])
        error -= dy
        if error < 0:
            y += y_step
            error += dx
    glEnd()


def draw_bezier_curve(points, segments=100, store=True):
    if len(points) < 3:
        return
    if store:
        stored_curves.append((points.copy(), current_color))
    glColor3f(*current_color)
    glBegin(GL_LINE_STRIP)
    for i in range(segments + 1):
        t = i / segments
        x = (1-t)**2 * points[0][0] + 2*(1-t)*t * points[1][0] + t**2 * points[2][0]
        y = (1-t)**2 * points[0][1] + 2*(1-t)*t * points[1][1] + t**2 * points[2][1]
        glVertex2f(x, y)
    glEnd()

# Dibujo de círculos y cuadrícula

def draw_circle(cx, cy, radius=50, segments=100, store=True):
    if store:
        stored_circles.append((cx, cy, radius, current_color))
    glColor3f(*current_color)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        x = cx + radius * math.cos(theta)
        y = cy + radius * math.sin(theta)
        glVertex2f(x, y)
    glEnd()


def draw_grid(spacing=20):
    glColor3f(0.9, 0.9, 0.9)
    glBegin(GL_LINES)
    for x in range(0, width, spacing):
        glVertex2f(x, 40)
        glVertex2f(x, height)
    for y in range(40, height, spacing):
        glVertex2f(0, y)
        glVertex2f(width, y)
    glEnd()

# Barra de herramientas
def draw_toolbar():
    # Fondo blanco
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(width, 0)
    glVertex2f(width, 40)
    glVertex2f(0, 40)
    glEnd()

    # Íconos: lápiz, línea, círculo, curva, borrador
    icons = [("pencil", 10), ("line", 50), ("circle", 90), ("curve", 130), ("eraser", 170)]
    for tool, x in icons:
        glColor3f(1.0 if current_tool == tool else 0.6, 0.6, 0.6)
        glRecti(x, 5, x + 30, 35)
        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        if tool == "pencil":
            glVertex2f(x + 5, 30)
            glVertex2f(x + 25, 10)
        elif tool == "line":
            glVertex2f(x + 5, 30)
            glVertex2f(x + 25, 10)
        elif tool == "circle":
            for i in range(20):
                theta = 2 * math.pi * i / 20
                glVertex2f(x + 15 + 10 * math.cos(theta), 20 + 10 * math.sin(theta))
        elif tool == "curve":
            for t in np.linspace(0, 1, 20):
                x0, y0 = x + 5, 30
                x1, y1 = x + 15, 10
                x2, y2 = x + 25, 30
                xt = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t ** 2 * x2
                yt = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t ** 2 * y2
                glVertex2f(xt, yt)
        elif tool == "eraser":
            # Dibuja un cuadrado blanco con borde negro
            glEnd()
            glColor3f(1, 1, 1)
            glRecti(x + 7, 13, x + 23, 29)
            glColor3f(0, 0, 0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x + 7, 13)
            glVertex2f(x + 23, 13)
            glVertex2f(x + 23, 29)
            glVertex2f(x + 7, 29)
        glEnd()

    # Selección de colores: Rojo, Verde, Azul
    color_boxes = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    for i, color in enumerate(color_boxes):
        x = 210 + i * 40
        glColor3f(*color)
        glRecti(x, 5, x + 30, 35)

# Redibuja todo

def redraw_all():
    glClearColor(1, 1, 1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw_grid()

    # Píxeles
    for x, y, color, size in stored_pixels:
        glColor3f(*color)
        glPointSize(size)
        glBegin(GL_POINTS)
        glVertex2f(x, y)
        glEnd()
    glPointSize(1)

    # Líneas
    for x0, y0, x1, y1, color in stored_lines:
        glColor3f(*color)
        draw_line_bresenham(x0, y0, x1, y1, store=False)

    # Curvas Bézier
    for pts, color in stored_curves:
        glColor3f(*color)
        draw_bezier_curve(pts, store=False)

    # Círculos
    for cx, cy, radius, color in stored_circles:
        glColor3f(*color)
        glBegin(GL_LINE_LOOP)
        for i in range(100):
            theta = 2.0 * math.pi * i / 100
            x = cx + radius * math.cos(theta)
            y = cy + radius * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

    draw_toolbar()
    # Puntos de control curva
    if current_tool == "curve" and control_points:
        glColor3f(0, 0, 1)
        glPointSize(5)
        glBegin(GL_POINTS)
        for px, py in control_points:
            glVertex2f(px, py)
        glEnd()
        glPointSize(1)

    pygame.display.flip()

# Bucle principal
running = True
redraw_all()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if y > 40:
                if current_tool == "pencil":
                    drawing = True
                    draw_pixel(x, y, size=3)
                    redraw_all()
                elif current_tool == "eraser":
                    drawing = True
                    erase_at(x, y)
                    redraw_all()
                elif current_tool == "line":
                    if not points:
                        points = [(x, y)]
                    else:
                        x0, y0 = points[0]
                        draw_line_bresenham(x0, y0, x, y)
                        points.clear()
                        redraw_all()
                elif current_tool == "circle":
                    if not points:
                        points = [(x, y)]
                    else:
                        x0, y0 = points[0]
                        radius = int(math.hypot(x - x0, y - y0))
                        draw_circle(x0, y0, radius)
                        points.clear()
                        redraw_all()
                elif current_tool == "curve":
                    if len(control_points) < 3:
                        control_points.append((x, y))
                        if len(control_points) == 3:
                            draw_bezier_curve(control_points)
                            control_points.clear()
                            redraw_all()
            else:
                # Interacción con toolbar
                if 10 <= x <= 40:
                    current_tool = "pencil"; points.clear(); control_points.clear()
                elif 50 <= x <= 80:
                    current_tool = "line"; points.clear(); control_points.clear()
                elif 90 <= x <= 120:
                    current_tool = "circle"; points.clear(); control_points.clear()
                elif 130 <= x <= 160:
                    current_tool = "curve"; points.clear(); control_points.clear()
                elif 170 <= x <= 200:
                    current_tool = "eraser"; points.clear(); control_points.clear()
                elif 210 <= x <= 240:
                    set_color(255, 0, 0)
                elif 250 <= x <= 280:
                    set_color(0, 255, 0)
                elif 290 <= x <= 320:
                    set_color(0, 0, 255)
                redraw_all()
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
        elif event.type == pygame.MOUSEMOTION and drawing:
            x, y = event.pos
            if y > 40:
                if current_tool == "pencil":
                    draw_pixel(x, y, size=3)
                    redraw_all()
                elif current_tool == "eraser":
                    erase_at(x, y)
                    redraw_all()
    pygame.time.wait(10)
pygame.quit()