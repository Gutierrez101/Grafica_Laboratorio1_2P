import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# =========================
# Helper: dibujar texto con OpenGL
# =========================
def texto(text, x, y, font, color=(0,0,0,0)):
    """
    Renderiza 'text' con pygame.font a una superficie,
    luego la dibuja en la posición de ventana (x,y) usando glDrawPixels.
    """
    superficie = font.render(text, True, color[:3])
    data = pygame.image.tostring(superficie, "RGBA", True)
    w, h = superficie.get_size()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glWindowPos2f(x, y)
    glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glDisable(GL_BLEND)

# =========================
# Dibuja la cuadrícula
# =========================
def cuadricula(width, height, step=20):
    glColor3f(0.8, 0.8, 0.8)
    glLineWidth(1)
    glBegin(GL_LINES)
    # Líneas verticales
    for x in range(0, width, step):
        glVertex2f(x, 0)
        glVertex2f(x, height)
    # Líneas horizontales
    for y in range(0, height, step):
        glVertex2f(0, y)
        glVertex2f(width, y)
    glEnd()

# =========================
# Algoritmo de Punto Medio
# =========================
def punto_medio(cx, cy, radius, color, thickness):
    x, y = 0, radius
    d = 1 - radius
    glColor3f(*color)
    glPointSize(thickness)
    glBegin(GL_POINTS)
    while x <= y:
        for dx, dy in [( x, y),( y, x),(-x, y),(-y, x),( x,-y),( y,-x),(-x,-y),(-y,-x)]:
            glVertex2f(cx+dx, cy+dy)
        if d < 0:
            d += 2*x + 1
        else:
            d += 2*(x - y) + 1
            y -= 1
        x += 1
    glEnd()

# =========================
# Algoritmo Paramétrico
# =========================
def parametrico(cx, cy, radius, color, thickness):
    glColor3f(*color)
    glPointSize(thickness)
    glBegin(GL_POINTS)
    for deg in range(360):
        theta = math.radians(deg)
        glVertex2f(cx + radius*math.cos(theta),
                   cy + radius*math.sin(theta))
    glEnd()

# =========================
# Dibuja el menú con opciones
# blending es una técnica que permite mezclar colores
# para crear efectos de transparencia.
# =========================
def menu(selected, font, width, height):
    glEnable(GL_BLEND)# Habilita el blending para la transparencia de fondo
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)# Configura la función de mezcla
    glColor4f(0, 0, 0, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(0, height-80)
    glVertex2f(width, height-80)
    glVertex2f(width, height)
    glVertex2f(0, height)
    glEnd()
    glDisable(GL_BLEND)# Deshabilita el blending para evitar afectar otros dibujos

    opts = ["1: Punto Medio", "2: Paramétrico"]
    for i, txt in enumerate(opts):
        color = (255,255,0,255) if i==selected else (200,200,200,255)
        x = 20 + i*250
        y = height - 50
        texto(txt, x, y, font, color)

    texto("Pulsa ←/→ o 1/2 para elegir, Enter para confirmar", 20, height-70, font)

# =========================
# Programa principal
# =========================
def main():
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont("Arial", 20)

    width, height = 600, 600
    pygame.display.set_mode((width, height), DOUBLEBUF|OPENGL)
    pygame.display.set_caption("Círculo: Punto Medio vs Paramétrico")

    # Configurar fondo blanco
    glClearColor(1.0, 1.0, 1.0, 1.0)

    glViewport(0, 0, width, height)# Configurar viewport que define la región de la ventana donde se dibuja
    glMatrixMode(GL_PROJECTION)# Configurar la matriz de proyección
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)# Configurar la matriz de modelo-vista
    glLoadIdentity()# Carga la matriz identidad

    clock = pygame.time.Clock()
    running = True
    etapa = "menu"
    selected = 0
    cx = cy = None
    radius = None
    rad_str = ""
    colores = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1)]
    indice_color = 0
    espesor = 1

    while running:
        for e in pygame.event.get():
            if e.type == QUIT:
                running = False
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False
                if etapa == "menu":
                    if e.key in (K_LEFT, K_1):
                        selected = (selected - 1) % 2
                    elif e.key in (K_RIGHT, K_2):
                        selected = (selected + 1) % 2
                    elif e.key in (K_RETURN, K_KP_ENTER):
                        etapa = "select_center"
                elif etapa == "input_radius":
                    if K_0 <= e.key <= K_9:
                        rad_str += e.unicode
                    elif e.key == K_BACKSPACE:
                        rad_str = rad_str[:-1]
                    elif e.key in (K_RETURN, K_KP_ENTER):
                        try:
                            radio = int(rad_str)
                        except:
                            radio = 50
                        etapa = "draw"
                elif etapa == "draw":
                    if e.key == K_c:
                        color_idx = (color_idx + 1) % len(colores)
                    elif e.key in (K_PLUS, K_EQUALS, K_KP_PLUS):
                        espesor += 1
                    elif e.key in (K_MINUS, K_KP_MINUS) and espesor>1:
                        espesor -= 1
            elif e.type == MOUSEBUTTONDOWN and etapa=="select_center" and e.button==1:
                mx, my = e.pos
                cx, cy = mx, height - my
                etapa = "input_radius"

        # Render
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # Dibujar cuadrícula
        cuadricula(width, height)

        if etapa == "menu":
            menu(selected, font, width, height)
        elif etapa == "select_center":
            texto("Haz clic para elegir centro...", 20, height//2, font)
        elif etapa == "input_radius":
            texto("Introduce radio y Enter: " + rad_str + "_", 20, height//2, font)
        elif etapa == "draw":
            method = punto_medio if selected==0 else parametrico
            method(cx, cy, radio, colores[indice_color], espesor)
            texto("C: color | + / -: grosor | Esc: salir", 10, 10, font)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

main()
