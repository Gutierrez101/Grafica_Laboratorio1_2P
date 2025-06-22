import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

# Inicialización
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

# Variables globales
drawing = False
current_tool = "pencil"
eraser_size = 15
line_width = 3
points = []
control_points = []
stored_pixels = []
stored_lines = []
stored_curves = []
stored_circles = []
stored_rectangles = []
current_color = (1.0, 0.0, 0.0)
show_grid = True
grid_size = 20
clipping_rect = None  # (x0, y0, x1, y1)

# Códigos para el algoritmo de Cohen-Sutherland
INSIDE = 0  # 0000
LEFT = 1    # 0001
RIGHT = 2   # 0010
BOTTOM = 4  # 0100
TOP = 8     # 1000

def compute_out_code(x, y, clip_rect):
    code = INSIDE
    if x < clip_rect[0]:
        code |= LEFT
    elif x > clip_rect[2]:
        code |= RIGHT
    if y < clip_rect[1]:
        code |= BOTTOM
    elif y > clip_rect[3]:
        code |= TOP
    return code

def cohen_sutherland_line_clip(x0, y0, x1, y1, clip_rect):
    outcode0 = compute_out_code(x0, y0, clip_rect)
    outcode1 = compute_out_code(x1, y1, clip_rect)
    accept = False

    while True:
        if not (outcode0 | outcode1):
            # Ambos puntos están dentro
            accept = True
            break
        elif outcode0 & outcode1:
            # Ambos puntos están fuera en la misma región
            break
        else:
            # Al menos un punto está fuera, recortar
            x, y = 0, 0
            outcode_out = outcode0 if outcode0 else outcode1

            if outcode_out & TOP:
                x = x0 + (x1 - x0) * (clip_rect[3] - y0) / (y1 - y0)
                y = clip_rect[3]
            elif outcode_out & BOTTOM:
                x = x0 + (x1 - x0) * (clip_rect[1] - y0) / (y1 - y0)
                y = clip_rect[1]
            elif outcode_out & RIGHT:
                y = y0 + (y1 - y0) * (clip_rect[2] - x0) / (x1 - x0)
                x = clip_rect[2]
            elif outcode_out & LEFT:
                y = y0 + (y1 - y0) * (clip_rect[0] - x0) / (x1 - x0)
                x = clip_rect[0]

            if outcode_out == outcode0:
                x0, y0 = x, y
                outcode0 = compute_out_code(x0, y0, clip_rect)
            else:
                x1, y1 = x, y
                outcode1 = compute_out_code(x1, y1, clip_rect)

    if accept:
        return (x0, y0, x1, y1)
    else:
        return None

def set_color(r, g, b):
    global current_color
    current_color = (r/255.0, g/255.0, b/255.0)

def draw_pixel(x, y, store=True, color=None, size=3):
    if color is None:
        color = current_color
    if clipping_rect:
        if not (clipping_rect[0] <= x <= clipping_rect[2] and clipping_rect[1] <= y <= clipping_rect[3]):
            return
    if store:
        stored_pixels.append((x, y, color, size))
    glColor3f(*color)
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()
    glPointSize(1)

def erase_at(x, y):
    global stored_pixels, stored_lines, stored_circles, stored_curves, stored_rectangles
    half = eraser_size // 2
    stored_pixels = [
        (px, py, color, size) for (px, py, color, size) in stored_pixels
        if not (x - half <= px <= x + half and y - half <= py <= y + half)
    ]
    stored_lines = [
        (x0, y0, x1, y1, color, width) for (x0, y0, x1, y1, color, width) in stored_lines
        if not ((x - half <= x0 <= x + half and y - half <= y0 <= y + half) or
                (x - half <= x1 <= x + half and y - half <= y1 <= y + half))
    ]
    stored_circles = [
        (cx, cy, radius, color, width) for (cx, cy, radius, color, width) in stored_circles
        if not (x - half <= cx <= x + half and y - half <= cy <= y + half)
    ]
    stored_curves = [
        (pts, color, width) for (pts, color, width) in stored_curves
        if not any(x - half <= px <= x + half and y - half <= py <= y + half for (px, py) in pts)
    ]
    stored_rectangles = [
        (x0, y0, x1, y1, color, width) for (x0, y0, x1, y1, color, width) in stored_rectangles
        if not ((x - half <= x0 <= x + half and y - half <= y0 <= y + half) or
                (x - half <= x1 <= x + half and y - half <= y1 <= y + half))
    ]

def draw_line_bresenham(x0, y0, x1, y1, store=True):
    if clipping_rect:
        result = cohen_sutherland_line_clip(x0, y0, x1, y1, clipping_rect)
        if not result:
            return
        x0, y0, x1, y1 = result

    if store:
        stored_lines.append((x0, y0, x1, y1, current_color, line_width))
    
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
    glLineWidth(line_width)
    glBegin(GL_POINTS)
    for x in range(int(x0), int(x1) + 1):
        coord = (y, x) if steep else (x, y)
        glVertex2f(coord[0], coord[1])
        error -= dy
        if error < 0:
            y += y_step
            error += dx
    glEnd()
    glLineWidth(1)

def draw_bezier_curve(pts, segments=100, store=True):
    if store:
        stored_curves.append((pts.copy(), current_color, line_width))
    
    glColor3f(*current_color)
    glLineWidth(line_width)
    glBegin(GL_LINE_STRIP)
    for i in range(segments + 1):
        t = i / segments
        x = (1 - t) ** 2 * pts[0][0] + 2 * (1 - t) * t * pts[1][0] + t ** 2 * pts[2][0]
        y = (1 - t) ** 2 * pts[0][1] + 2 * (1 - t) * t * pts[1][1] + t ** 2 * pts[2][1]
        if clipping_rect:
            if clipping_rect[0] <= x <= clipping_rect[2] and clipping_rect[1] <= y <= clipping_rect[3]:
                glVertex2f(x, y)
        else:
            glVertex2f(x, y)
    glEnd()
    glLineWidth(1)

def draw_circle(cx, cy, radius, segments=100, store=True):
    if store:
        stored_circles.append((cx, cy, radius, current_color, line_width))
    
    glColor3f(*current_color)
    glLineWidth(line_width)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        x = cx + radius * math.cos(theta)
        y = cy + radius * math.sin(theta)
        if clipping_rect:
            if clipping_rect[0] <= x <= clipping_rect[2] and clipping_rect[1] <= y <= clipping_rect[3]:
                glVertex2f(x, y)
        else:
            glVertex2f(x, y)
    glEnd()
    glLineWidth(1)

def draw_rectangle(x0, y0, x1, y1, store=True):
    if store:
        stored_rectangles.append((x0, y0, x1, y1, current_color, line_width))
    
    glColor3f(*current_color)
    glLineWidth(line_width)
    glBegin(GL_LINE_LOOP)
    # Aplicar recorte a cada línea del rectángulo
    points = [
        (x0, y0), (x1, y0), (x1, y1), (x0, y1)
    ]
    for i in range(4):
        xa, ya = points[i]
        xb, yb = points[(i + 1) % 4]
        if clipping_rect:
            result = cohen_sutherland_line_clip(xa, ya, xb, yb, clipping_rect)
            if result:
                xa, ya, xb, yb = result
                glVertex2f(xa, ya)
                glVertex2f(xb, yb)
        else:
            glVertex2f(xa, ya)
            glVertex2f(xb, yb)
    glEnd()
    glLineWidth(1)

def draw_grid():
    if not show_grid:
        return
        
    glColor3f(0.9, 0.9, 0.9)
    glLineWidth(1)
    glBegin(GL_LINES)
    
    # Líneas verticales
    for x in range(0, width, grid_size):
        glVertex2f(x, 40)
        glVertex2f(x, height)
    
    # Líneas horizontales
    for y in range(40, height, grid_size):
        glVertex2f(0, y)
        glVertex2f(width, y)
    
    glEnd()

def draw_icon(tool, x):
    if tool == "pencil":
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 8, 30); glVertex2f(x + 22, 15)
        glEnd()
    elif tool == "line":
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 5, 30); glVertex2f(x + 25, 10)
        glEnd()
    elif tool == "circle":
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        for i in range(20):
            theta = 2 * math.pi * i / 20
            glVertex2f(x + 15 + 10 * math.cos(theta), 20 + 10 * math.sin(theta))
        glEnd()
    elif tool == "curve":
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_STRIP)
        for t in np.linspace(0, 1, 20):
            x0, y0 = x + 5, 30
            x1, y1 = x + 15, 10
            x2, y2 = x + 25, 30
            xt = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t ** 2 * x2
            yt = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t ** 2 * y2
            glVertex2f(xt, yt)
        glEnd()
    elif tool == "eraser":
        glColor3f(1, 1, 1)
        glRecti(x + 7, 13, x + 23, 29)
        glColor3f(0, 0, 0)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 7, 13); glVertex2f(x + 23, 13)
        glVertex2f(x + 23, 29); glVertex2f(x + 7, 29)
        glEnd()
    elif tool == "rectangle":
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 8, 12, x + 22, 28)
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 8, 12); glVertex2f(x + 22, 12)
        glVertex2f(x + 22, 28); glVertex2f(x + 8, 28)
        glEnd()
    elif tool == "crop":
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 5, 10, x + 25, 30)
        glColor3f(1, 1, 1)
        glRecti(x + 10, 15, x + 20, 25)
        glColor3f(0, 0, 0)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 5, 10); glVertex2f(x + 25, 10)
        glVertex2f(x + 25, 30); glVertex2f(x + 5, 30)
        glEnd()
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 7, 12); glVertex2f(x + 13, 18)
        glVertex2f(x + 23, 12); glVertex2f(x + 17, 18)
        glVertex2f(x + 13, 18); glVertex2f(x + 15, 20)
        glVertex2f(x + 17, 18); glVertex2f(x + 15, 20)
        glEnd()

def draw_toolbar():
    glColor3f(0.9, 0.9, 0.9)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(width, 0)
    glVertex2f(width, 40)
    glVertex2f(0, 40)
    glEnd()
    
    glColor3f(0.6, 0.6, 0.6)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(0, 40)
    glVertex2f(width, 40)
    glEnd()
    
    tools = ["pencil", "line", "circle", "curve", "eraser", "rectangle", "crop"]
    for i, tool in enumerate(tools):
        x = 10 + i * 40
        if tool == current_tool:
            glColor3f(0.7, 0.7, 0.9)
            glRecti(x - 2, 3, x + 32, 37)
        
        glColor3f(0.8, 0.8, 0.8)
        glRecti(x, 5, x + 30, 35)
        draw_icon(tool, x)
    
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
    for i, (r, g, b) in enumerate(colors):
        cx = 290 + i * 35
        glColor3f(r / 255.0, g / 255.0, b / 255.0)
        glRecti(cx, 5, cx + 30, 35)
        glColor3f(0.3, 0.3, 0.3)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx, 5); glVertex2f(cx + 30, 5)
        glVertex2f(cx + 30, 35); glVertex2f(cx, 35)
        glEnd()
    
    glColor3f(0.2, 0.2, 0.2)
    glRasterPos2f(470, 25)
    text = f"Grosor: {line_width} (T/G para cambiar)"
    for char in text:
        pygame.font.init()
        font = pygame.font.SysFont('Arial', 12)
        text_surface = font.render(char, True, (50, 50, 50))
        texture_data = pygame.image.tostring(text_surface, "RGBA", True)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                    GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glRasterPos2f(glGetDoublev(GL_CURRENT_RASTER_POSITION)[0] + text_surface.get_width(), 25)

def redraw_all():
    glClearColor(1, 1, 1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    draw_grid()
    
    # Dibujar elementos almacenados
    for x, y, color, size in stored_pixels:
        draw_pixel(x, y, store=False, color=color, size=size)
    for x0, y0, x1, y1, color, width in stored_lines:
        glColor3f(*color)
        glLineWidth(width)
        draw_line_bresenham(x0, y0, x1, y1, store=False)
    for pts, color, width in stored_curves:
        glColor3f(*color)
        glLineWidth(width)
        draw_bezier_curve(pts, store=False)
    for cx, cy, radius, color, width in stored_circles:
        glColor3f(*color)
        glLineWidth(width)
        draw_circle(cx, cy, radius, store=False)
    for x0, y0, x1, y1, color, width in stored_rectangles:
        glColor3f(*color)
        glLineWidth(width)
        draw_rectangle(x0, y0, x1, y1, store=False)
    
    # Dibujar área de recorte si existe
    if clipping_rect:
        x0, y0, x1, y1 = clipping_rect
        glColor3f(0.5, 0.5, 0.8)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x0, y0)
        glVertex2f(x1, y0)
        glVertex2f(x1, y1)
        glVertex2f(x0, y1)
        glEnd()
        
        glColor4f(0.7, 0.7, 0.9, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(width, 0)
        glVertex2f(width, height); glVertex2f(0, height)
        glEnd()
        glBegin(GL_LINES)
        glVertex2f(x0, y0); glVertex2f(x1, y1)
        glVertex2f(x1, y0); glVertex2f(x0, y1)
        glEnd()
    
    draw_toolbar()
    pygame.display.flip()

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
                    draw_pixel(x, y)
                elif current_tool == "eraser":
                    drawing = True
                    erase_at(x, y)
                elif current_tool == "line":
                    points.append((x, y))
                    if len(points) == 2:
                        draw_line_bresenham(*points[0], *points[1])
                        points.clear()
                elif current_tool == "circle":
                    points.append((x, y))
                    if len(points) == 2:
                        x0, y0 = points[0]
                        radius = int(math.hypot(x - x0, y - y0))
                        draw_circle(x0, y0, radius)
                        points.clear()
                elif current_tool == "rectangle":
                    points.append((x, y))
                    if len(points) == 2:
                        draw_rectangle(*points[0], *points[1])
                        points.clear()
                elif current_tool == "curve":
                    control_points.append((x, y))
                    if len(control_points) == 3:
                        draw_bezier_curve(control_points)
                        control_points.clear()
                elif current_tool == "crop":
                    points.append((x, y))
                    if len(points) == 2:
                        x0, y0 = min(points[0][0], points[1][0]), min(points[0][1], points[1][1])
                        x1, y1 = max(points[0][0], points[1][0]), max(points[0][1], points[1][1])
                        clipping_rect = (x0, y0, x1, y1)
                        points.clear()
                redraw_all()
            else:
                tools = ["pencil", "line", "circle", "curve", "eraser", "rectangle", "crop"]
                for i, tool in enumerate(tools):
                    if 10 + i * 40 <= x <= 40 + i * 40:
                        current_tool = tool
                        if tool != "crop":
                            clipping_rect = None
                
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
                for i, (r, g, b) in enumerate(colors):
                    if 290 + i * 35 <= x <= 320 + i * 35:
                        set_color(r, g, b)
                
                points.clear(); control_points.clear()
                redraw_all()
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
        elif event.type == pygame.MOUSEMOTION and drawing:
            x, y = event.pos
            if y > 40:
                if current_tool == "pencil":
                    draw_pixel(x, y)
                elif current_tool == "eraser":
                    erase_at(x, y)
                redraw_all()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                show_grid = not show_grid
                redraw_all()
            elif event.key == pygame.K_t:
                line_width = min(10, line_width + 1)
                redraw_all()
            elif event.key == pygame.K_g and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                line_width = max(1, line_width - 1)
                redraw_all()
            elif event.key == pygame.K_ESCAPE:
                clipping_rect = None
                redraw_all()
    
    pygame.time.wait(10)
pygame.quit()