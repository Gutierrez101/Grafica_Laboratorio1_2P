import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Configuración inicial
ANCHO = 800
ALTO = 600
color_actual = (1.0, 0.0, 0.0)
grosor = 2.0
lineas = []
punto_inicial = None

def bresenham(x1, y1, x2, y2):
    """Dibuja una línea con el algoritmo de Bresenham."""
    x1 = int(round(x1))
    y1 = int(round(y1))
    x2 = int(round(x2))
    y2 = int(round(y2))

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 >= x1 else -1
    sy = 1 if y2 >= y1 else -1
    err = dx - dy

    while True:
        glVertex2i(x1, y1)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

def crear_plano():
    """Dibuja una cuadrícula cada 100 píxeles."""
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_LINES)
    for i in range(0, ANCHO, 100):
        glVertex2i(i, 0)
        glVertex2i(i, ALTO)
    for j in range(0, ALTO, 100):
        glVertex2i(0, j)
        glVertex2i(ANCHO, j)
    glEnd()

def dibujar():
    """Dibuja todas las líneas y el plano."""
    glClear(GL_COLOR_BUFFER_BIT)
    crear_plano()
    glColor3f(*color_actual)
    glPointSize(grosor)
    glBegin(GL_POINTS)
    for linea in lineas:
        bresenham(linea[0][0], linea[0][1], linea[1][0], linea[1][1])
    glEnd()
    pygame.display.flip()

def main():
    global punto_inicial, color_actual, grosor

    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Líneas con Bresenham - PyOpenGL")
    gluOrtho2D(0, ANCHO, 0, ALTO)

    reloj = pygame.time.Clock()
    corriendo = True

    while corriendo:
        for evento in pygame.event.get():
            if evento.type == QUIT:
                corriendo = False

            elif evento.type == MOUSEBUTTONDOWN and evento.button == 1:
                x, y = evento.pos
                y = ALTO - y  # Invertir eje Y
                if punto_inicial is None:
                    punto_inicial = (x, y)
                else:
                    punto_final = (x, y)
                    lineas.append((punto_inicial, punto_final))
                    punto_inicial = None

            elif evento.type == KEYDOWN:
                if evento.key == K_r:
                    color_actual = (1.0, 0.0, 0.0)
                elif evento.key == K_g:
                    color_actual = (0.0, 1.0, 0.0)
                elif evento.key == K_b:
                    color_actual = (0.0, 0.0, 1.0)
                elif evento.key == K_c:
                    lineas.clear()
                elif evento.key == K_PLUS or evento.key == K_KP_PLUS:
                    grosor += 1.0
                elif evento.key == K_MINUS or evento.key == K_KP_MINUS:
                    grosor = max(1.0, grosor - 1.0)

        dibujar()
        reloj.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()
