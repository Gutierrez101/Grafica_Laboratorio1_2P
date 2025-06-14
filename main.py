import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# =========================
# Helper: dibujar texto con OpenGL
# =========================
def draw_text_gl(text, x, y, font, color=(255,255,255,255)):
    """
    Renderiza 'text' con pygame.font a una superficie,
    luego la dibuja en la posición de ventana (x,y) usando glDrawPixels.
    """
    # Render Pygame -> Surface RGBA
    surf = font.render(text, True, color[:3])
    data = pygame.image.tostring(surf, "RGBA", True)
    w, h = surf.get_size()
    # Preparar transparencia
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    # Posicionar en ventana (origen abajo-izquierda)
    glWindowPos2f(x, y)
    # Dibujar píxeles
    glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glDisable(GL_BLEND)


# =========================
# Algoritmo de Punto Medio
# =========================
def midpoint_circle(cx, cy, radius, color, thickness):
    x, y = 0, radius
    d = 1 - radius
    glColor3f(*color)
    glPointSize(thickness)
    glBegin(GL_POINTS)
    while x <= y:
        for dx, dy in [( x, y),( y, x),(-x, y),(-y, x),( x,-y),( y,-x),(-x,-y),(-y,-x)]:
            glVertex2f(cx+dx, cy+dy)
        if d < 0:
            d += 2*x + 3
        else:
            d += 2*(x - y) + 5
            y -= 1
        x += 1
    glEnd()


# =========================
# Algoritmo Paramétrico
# =========================
def parametric_circle(cx, cy, radius, color, thickness):
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
# =========================
def draw_menu(selected, font, width, height):
    # Fondo semitransparente
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(0, height-80)
    glVertex2f(width, height-80)
    glVertex2f(width, height)
    glVertex2f(0, height)
    glEnd()
    glDisable(GL_BLEND)

    # Texto de opciones
    opts = ["1: Punto Medio", "2: Paramétrico"]
    for i, txt in enumerate(opts):
        color = (255,255,0,255) if i==selected else (200,200,200,255)
        x = 20 + i*250
        y = height - 50
        draw_text_gl(txt, x, y, font, color)

    # Instrucción
    draw_text_gl("Pulsa ←/→ o 1/2 para elegir, Enter para confirmar", 20, height-70, font)


# =========================
# Programa principal
# =========================
def main():
    # --- Inicialización ---
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont("Arial", 20)

    width, height = 600, 600
    pygame.display.set_mode((width, height), DOUBLEBUF|OPENGL)
    pygame.display.set_caption("Círculo: Punto Medio vs Paramétrico")

    # Proyección ortográfica 2D
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    clock = pygame.time.Clock()
    running = True

    # Estados
    stage = "menu"          # menu -> select_center -> input_radius -> draw
    selected = 0            # 0 = Punto Medio, 1 = Paramétrico
    cx = cy = None
    radius = None
    rad_str = ""

    # Colores y grosor
    colors = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1)]
    color_idx = 0
    thickness = 1

    while running:
        # --- Eventos ---
        for e in pygame.event.get():
            if e.type == QUIT:
                running = False

            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False

                # Menú: teclas 1/2, ←/→, Enter
                if stage == "menu":
                    if e.key in (K_LEFT, K_1):
                        selected = (selected - 1) % 2
                    elif e.key in (K_RIGHT, K_2):
                        selected = (selected + 1) % 2
                    elif e.key in (K_RETURN, K_KP_ENTER):
                        stage = "select_center"

                # Entrada de radio: dígitos, Backspace, Enter
                elif stage == "input_radius":
                    if K_0 <= e.key <= K_9:
                        rad_str += e.unicode
                    elif e.key == K_BACKSPACE:
                        rad_str = rad_str[:-1]
                    elif e.key in (K_RETURN, K_KP_ENTER):
                        try:
                            radius = int(rad_str)
                        except:
                            radius = 50
                        stage = "draw"

                # Control de color y grosor tras dibujar
                elif stage == "draw":
                    if e.key == K_c:
                        color_idx = (color_idx + 1) % len(colors)
                    elif e.key in (K_PLUS, K_EQUALS, K_KP_PLUS):
                        thickness += 1
                    elif e.key in (K_MINUS, K_KP_MINUS) and thickness>1:
                        thickness -= 1

            # Clic para elegir centro
            elif e.type == MOUSEBUTTONDOWN and stage=="select_center" and e.button==1:
                mx, my = e.pos
                cx, cy = mx, height - my
                stage = "input_radius"

        # --- Render ---
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        if stage == "menu":
            draw_menu(selected, font, width, height)

        elif stage == "select_center":
            draw_text_gl("Haz clic para elegir centro...", 20, height//2, font)

        elif stage == "input_radius":
            draw_text_gl("Introduce radio y Enter: " + rad_str + "_", 20, height//2, font)

        elif stage == "draw":
            # Dibuja el círculo con el método elegido
            method = midpoint_circle if selected==0 else parametric_circle
            method(cx, cy, radius, colors[color_idx], thickness)
            # Instrucciones
            draw_text_gl("C: color | + / -: grosor | Esc: salir", 10, 10, font)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
