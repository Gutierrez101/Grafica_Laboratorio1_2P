import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# =========================
# Función del algoritmo de punto medio
# =========================
def midpoint_circle(cx, cy, radius, color, thickness):
    """
    Dibuja un círculo usando el algoritmo de punto medio.
    cx, cy: coordenadas del centro
    radius: radio del círculo
    color: tupla RGB con valores [0.0,1.0]
    thickness: grosor del trazo en píxeles
    """
    x = 0
    y = radius
    d = 1 - radius

    glColor3f(*color)
    glPointSize(thickness)

    glBegin(GL_POINTS)
    while x <= y:
        # Dibujar los 8 puntos simétricos
        pts = [
            ( cx + x, cy + y),
            ( cx + y, cy + x),
            ( cx - x, cy + y),
            ( cx - y, cy + x),
            ( cx + x, cy - y),
            ( cx + y, cy - x),
            ( cx - x, cy - y),
            ( cx - y, cy - x),
        ]
        for px, py in pts:
            glVertex2f(px, py)

        # Actualizar parámetros
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    glEnd()


# =========================
# Inicialización y parámetro estático/teclado
# =========================
def get_user_parameters():
    """
    Solicita por consola los parámetros iniciales:
    centro(x,y) y radio.
    Si el usuario deja vacío, usa valores por defecto.
    """
    try:
        inp = input("Centro x,y (separados por coma) [default 300,300]: ")
        if inp.strip():
            cx, cy = map(int, inp.split(","))
        else:
            cx, cy = 300, 300
    except:
        print("Entrada inválida. Usando centro por defecto (300,300).")
        cx, cy = 300, 300

    try:
        inp = input("Radio [default 100]: ")
        if inp.strip():
            radius = int(inp)
        else:
            radius = 100
    except:
        print("Entrada inválida. Usando radio por defecto 100.")
        radius = 100

    return cx, cy, radius


# =========================
# Función principal
# =========================
def main():
    # Parámetros iniciales
    cx, cy, radius = get_user_parameters()
    color_options = [
        (1.0, 0.0, 0.0),  # Rojo
        (0.0, 1.0, 0.0),  # Verde
        (0.0, 0.0, 1.0),  # Azul
        (1.0, 1.0, 0.0),  # Amarillo
        (1.0, 0.0, 1.0),  # Magenta
    ]
    color_idx = 0
    thickness = 1

    # Inicializar Pygame y OpenGL
    pygame.init()
    width, height = 600, 600
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Círculo: Algoritmo de Punto Medio")

    # Configurar viewport y proyección ortográfica
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Coordenadas de 0 a width/height
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    clock = pygame.time.Clock()
    running = True

    while running:
        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_c:
                    # Cambiar color
                    color_idx = (color_idx + 1) % len(color_options)
                elif event.key == K_PLUS or event.key == K_EQUALS:
                    # Aumentar grosor
                    thickness += 1
                elif event.key == K_MINUS and thickness > 1:
                    # Reducir grosor
                    thickness -= 1

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic izquierdo
                    # Actualizar centro al hacer clic
                    mx, my = event.pos
                    # Convertir coordenada Y (Pygame tiene origen arriba)
                    cy = height - my
                    cx = mx

        # Limpiar pantalla
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # Dibujar círculo con parámetros actuales
        midpoint_circle(cx, cy, radius, color_options[color_idx], thickness)

        # Mostrar cambios
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
