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

# Variables del programa
drawing = False
current_tool = "pencil"  # "pencil", "line", "curve"
points = []
current_color = (1.0, 0.0, 0.0)  # Rojo por defecto
control_points = []
stored_lines = []
stored_curves = []
stored_pixels = []

def set_color(r, g, b):
    global current_color
    current_color = (r/255.0, g/255.0, b/255.0)

def draw_pixel(x, y, store=True):
    if store:
        stored_pixels.append((x, y, current_color))
    glColor3f(*current_color)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

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
        # Fórmula de la curva cuadrática de Bézier
        x = (1-t)**2 * points[0][0] + 2*(1-t)*t * points[1][0] + t**2 * points[2][0]
        y = (1-t)**2 * points[0][1] + 2*(1-t)*t * points[1][1] + t**2 * points[2][1]
        glVertex2f(x, y)
    
    glEnd()

def draw_control_points():
    glColor3f(0.0, 0.0, 1.0)  # Azul para puntos de control
    glPointSize(5.0)
    glBegin(GL_POINTS)
    for point in control_points:
        glVertex2f(point[0], point[1])
    glEnd()
    glPointSize(1.0)

def draw_toolbar():
    # Dibuja un área para la barra de herramientas
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(width, 0)
    glVertex2f(width, 40)
    glVertex2f(0, 40)
    glEnd()
    
    # Botón de lápiz
    glColor3f(1.0 if current_tool == "pencil" else 0.6, 0.6, 0.6)
    glRecti(10, 5, 35, 35)
    
    # Botón de línea
    glColor3f(1.0 if current_tool == "line" else 0.6, 0.6, 0.6)
    glRecti(40, 5, 65, 35)
    
    # Botón de curva
    glColor3f(1.0 if current_tool == "curve" else 0.6, 0.6, 0.6)
    glRecti(70, 5, 95, 35)
    
    # Selector de color
    glColor3f(*current_color)
    glRecti(100, 5, 125, 35)

def redraw_all():
    """Redibuja todos los elementos almacenados"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Redibuja todos los píxeles
    for x, y, color in stored_pixels:
        glColor3f(*color)
        glBegin(GL_POINTS)
        glVertex2f(x, y)
        glEnd()
    
    # Redibuja todas las líneas
    for x0, y0, x1, y1, color in stored_lines:
        glColor3f(*color)
        draw_line_bresenham(x0, y0, x1, y1, store=False)
    
    # Redibuja todas las curvas
    for curve_points, color in stored_curves:
        glColor3f(*color)
        draw_bezier_curve(curve_points, store=False)
    
    # Dibuja la barra de herramientas
    draw_toolbar()
    
    # Dibuja puntos de control para la curva
    if current_tool == "curve" and len(control_points) > 0:
        draw_control_points()
    
    pygame.display.flip()

# Bucle principal
running = True
redraw_all()  # Dibuja la pantalla inicial

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if y > 40:  # Fuera de la barra de herramientas
                if current_tool == "pencil":
                    drawing = True
                    draw_pixel(x, y)
                elif current_tool == "line":
                    if len(points) == 0:
                        points = [(x, y)]
                    else:
                        points.append((x, y))
                        draw_line_bresenham(points[0][0], points[0][1], points[1][0], points[1][1])
                        points = []
                        redraw_all()
                elif current_tool == "curve":
                    if len(control_points) < 3:
                        control_points.append((x, y))
                        if len(control_points) == 3:
                            draw_bezier_curve(control_points)
                            control_points = []
                            redraw_all()
            else:
                # Manejo de la barra de herramientas
                if 10 <= x <= 35:
                    current_tool = "pencil"
                    control_points = []
                    points = []
                elif 40 <= x <= 65:
                    current_tool = "line"
                    control_points = []
                    points = []
                elif 70 <= x <= 95:
                    current_tool = "curve"
                    points = []
                elif 100 <= x <= 125:
                    # Cambiar color (simplificado)
                    set_color(
                        (current_color[0] * 255 + 50) % 255,
                        (current_color[1] * 255 + 100) % 255,
                        (current_color[2] * 255 + 150) % 255
                    )
                redraw_all()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
        
        elif event.type == pygame.MOUSEMOTION and drawing:
            x, y = event.pos
            if y > 40 and current_tool == "pencil":
                draw_pixel(x, y)
                redraw_all()
    
    # Control de FPS
    pygame.time.wait(10)

pygame.quit()