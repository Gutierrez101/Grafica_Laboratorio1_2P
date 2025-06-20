import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

# Inicialización
pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
pygame.display.set_caption("Paint OpenGL")

# Configuración de OpenGL
glViewport(0, 0, display[0], display[1])
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, display[0], display[1], 0, -1, 1)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

# Variables del programa
dibujo = False
current_tool = "linea"  # "pencil", "line", "curve"
puntos = []
color_defecto = (1.0, 0.0, 0.0)  # Rojo por defecto
control_points = []
lineas_guardadas = []
curvas_guardadas = []
pixiles_guardados = []

# Funciones de dibujo
def set_color(r, g, b):
    global current_color
    current_color = (r/255.0, g/255.0, b/255.0)

#Funcione para dibujar pixels
def dibujar_pixeles(x, y, guardar=True):
    if guardar:
        pixiles_guardados.append((x, y, current_color))
    glColor3f(*current_color)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

#Funcion para algoritmo de bresenham
def algoritmo_bresenham(x0, y0, x1, y1, guardar=True):
    if guardar:
        lineas_guardadas.append((x0, y0, x1, y1, current_color))
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    paso = dy > dx
    
    if paso:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    error = dx // 2
    paso_y = 1 if y0 < y1 else -1
    y = y0
    
    glColor3f(*current_color)
    glBegin(GL_POINTS)
    
    for x in range(int(x0), int(x1) + 1):
        coord = (y, x) if paso else (x, y)
        glVertex2f(coord[0], coord[1])
        error -= dy
        if error < 0:
            y += paso_y
            error += dx
    
    glEnd()

#Funcion de la curva de bezier
def algoritmo_curva_bezier(puntos, segmentos=100, guardar=True):
    if len(puntos) < 3:
        return
    
    if guardar:
        curvas_guardadas.append((puntos.copy(), color_defecto))
    
    glColor3f(*color_defecto)
    glBegin(GL_POINTS)
    
    for i in range(segmentos + 1):
        t = i / segmentos
        # Fórmula de la curva cuadrática de Bézier
        x = (1-t)**2 * points[0][0] + 2*(1-t)*t * points[1][0] + t**2 * points[2][0]
        y = (1-t)**2 * points[0][1] + 2*(1-t)*t * points[1][1] + t**2 * points[2][1]
        glVertex2f(x, y)
    
    glEnd()

#Funcion para dibujar los puntos de control
def dibujar_puntos_control():
    glColor3f(0.0, 0.0, 1.0)  # Azul para puntos de control
    glPointSize(5.0)
    glBegin(GL_POINTS)
    for point in control_points:
        glVertex2f(point[0], point[1])
    glEnd()
    glPointSize(1.0)

def dibujar_toolbar():
    # Dibuja un área para la barra de herramientas
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(display[0], 0)
    glVertex2f(display[0], 40)
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

def redibujar_elementos():
    """Redibuja todos los elementos almacenados"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Redibuja todos los píxeles
    for x, y, color in pixiles_guardados:
        glColor3f(*color)
        glBegin(GL_POINTS)
        glVertex2f(x, y)
        glEnd()
    
    # Redibuja todas las líneas
    for x0, y0, x1, y1, color in lineas_guardadas:
        glColor3f(*color)
        algoritmo_bresenham(x0, y0, x1, y1, store=False)
    
    # Redibuja todas las curvas
    for curve_points, color in curvas_guardadas:
        glColor3f(*color)
        algoritmo_curva_bezier(curve_points, store=False)
    
    # Dibuja la barra de herramientas
    dibujar_toolbar()
    
    # Dibuja puntos de control para la curva
    if current_tool == "curve" and len(control_points) > 0:
        dibujar_puntos_control()
    
    pygame.display.flip()

# Bucle principal
running = True
redibujar_elementos()  # Dibuja la pantalla inicial

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if y > 40:  # Fuera de la barra de herramientas
                if current_tool == "pencil":
                    drawing = True
                    dibujar_pixeles(x, y)
                elif current_tool == "line":
                    if len(points) == 0:
                        points = [(x, y)]
                    else:
                        points.append((x, y))
                        algoritmo_bresenham(points[0][0], points[0][1], points[1][0], points[1][1])
                        points = []
                        redibujar_elementos()
                elif current_tool == "curve":
                    if len(control_points) < 3:
                        control_points.append((x, y))
                        if len(control_points) == 3:
                            algoritmo_curva_bezier(control_points)
                            control_points = []
                            redibujar_elementos()
            else:
                # Manejo de la barra de herramientas
                if 10 <= x <= 35:
                    current_tool = "linea"
                    control_points = []
                    points = []
                elif 40 <= x <= 65:
                    current_tool = "circulo"
                    control_points = []
                    points = []
                elif 70 <= x <= 95:
                    current_tool = "curva"
                    points = []
                elif 100 <= x <= 125:
                    # Cambiar color (simplificado)
                    set_color(
                        (current_color[0] * 255 + 50) % 255,
                        (current_color[1] * 255 + 100) % 255,
                        (current_color[2] * 255 + 150) % 255
                    )
                redibujar_elementos()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
        
        elif event.type == pygame.MOUSEMOTION and drawing:
            x, y = event.pos
            if y > 40 and current_tool == "pencil":
                dibujar_pixeles(x, y)
                redibujar_elementos()
    
    # Control de FPS
    pygame.time.wait(10)

pygame.quit()