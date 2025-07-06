#Ventana de visualización 3D con OpenGL
#Importar las librerías necesarias
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
import sys

salir_ventana = False  # bandera para indicar si se debe salir sin cerrar el programa
ventana_activa=True
# ============================
# Variables globales de estado
# ============================
WIDTH, HEIGHT = 800, 600

# Proyección y cámara
modo_perspectiva: bool = True
zoom: float = 1.0
angulo_x, angulo_y = 30.0, -30.0

# Rotación automática
auto_rotar: bool = False
velocidad_auto: float = 0.2

# Luz y sombras
pos_luz = [2.0, 5.0, 2.0, 1.0]
habilitar_luz: bool = True
habilitar_sombra: bool = True

# Modo de dibujo
modo_dibujo = "cubo"
modo_visualizacion = "wireframe"

# ============================
# Inicialización OpenGL
# ============================
def init():
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, pos_luz)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)

# ============================
# Proyección
# ============================
def configurar_proyeccion():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = WIDTH / HEIGHT
    if modo_perspectiva:
        gluPerspective(45 * zoom, aspect, 0.1, 100.0)
    else:
        glOrtho(-5 * zoom, 5 * zoom, -5 * zoom, 5 * zoom, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

# ============================
# Sombra
# ============================
def matriz_sombra(luz, plano=(0.0, 1.0, 0.0, 0.0)):
    A, B, C, D = plano
    Lx, Ly, Lz, Lw = luz
    dot = A*Lx + B*Ly + C*Lz + D*Lw
    mat = [dot - Lx*A, -Lx*B, -Lx*C, -Lx*D,
           -Ly*A, dot - Ly*B, -Ly*C, -Ly*D,
           -Lz*A, -Lz*B, dot - Lz*C, -Lz*D,
           -Lw*A, -Lw*B, -Lw*C, dot - Lw*D]
    return mat

# ============================
# Dibujos
# ============================
def dibujar_ejes():
    glLineWidth(3)
    glBegin(GL_LINES)
    glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(2, 0, 0)
    glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 2, 0)
    glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 2)
    glEnd()
    glLineWidth(1)

def dibujar_cuadricula():
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_LINES)
    for i in range(-10, 11):
        glVertex3f(i, 0, -10); glVertex3f(i, 0, 10)
        glVertex3f(-10, 0, i); glVertex3f(10, 0, i)
    glEnd()

def dibujar_objeto():
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if modo_visualizacion == "wireframe" else GL_FILL)
    glColor3f(0.8, 0.2, 0.2)
    draw = {
        "cubo": glutSolidCube if modo_visualizacion == "solido" else glutWireCube,
        "esfera": glutSolidSphere if modo_visualizacion == "solido" else glutWireSphere,
        "cono": glutSolidCone if modo_visualizacion == "solido" else glutWireCone,
        "tetera": glutSolidTeapot if modo_visualizacion == "solido" else glutWireTeapot,
        "toro": glutSolidTorus if modo_visualizacion == "solido" else glutWireTorus,
    }[modo_dibujo]
    if modo_dibujo == "esfera":
        draw(1.0, 20, 20)
    elif modo_dibujo == "cono":
        draw(1.0, 2.0, 20, 20)
    elif modo_dibujo == "toro":
        draw(0.3, 1.0, 20, 20)
    else:
        draw(1.5 if modo_dibujo == "cubo" else 1.0)

def dibujar_sombra():
    if not habilitar_sombra:
        return
    glDisable(GL_LIGHTING)
    glColor4f(0.0, 0.0, 0.0, 0.4)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    mat = matriz_sombra(pos_luz)
    glPushMatrix()
    glMultMatrixf(mat)
    dibujar_objeto()
    glPopMatrix()
    glDisable(GL_BLEND)
    if habilitar_luz:
        glEnable(GL_LIGHTING)

def barra_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()
    glColor3f(0.25, 0.25, 0.25)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(WIDTH, 0); glVertex2f(WIDTH, 40); glVertex2f(0, 40)
    glEnd()
    glColor3f(1, 1, 1)
    texto = (
        f"Modo: {modo_dibujo} | Viz.: {modo_visualizacion} | Proy.: {'Perspectiva' if modo_perspectiva else 'Ortográfica'} "
        f"| Luz: {'ON' if habilitar_luz else 'OFF'} | Sombra: {'ON' if habilitar_sombra else 'OFF'} | Rot. auto: {'ON' if auto_rotar else 'OFF'}"
    )
    glRasterPos2f(10, 24)
    for ch in texto:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ============================
# Display & callbacks
# ============================
def display():
    if not ventana_activa:
        return
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
    glRotatef(angulo_x, 1, 0, 0)
    glRotatef(angulo_y, 0, 1, 0)
    if habilitar_luz:
        glEnable(GL_LIGHTING)
        glLightfv(GL_LIGHT0, GL_POSITION, pos_luz)
    else:
        glDisable(GL_LIGHTING)
    dibujar_cuadricula()
    dibujar_ejes()
    dibujar_sombra()
    dibujar_objeto()
    barra_hud()
    glutSwapBuffers()

def idle():
    global angulo_y
    if ventana_activa and auto_rotar:
        angulo_y+=velocidad_auto
        glutPostRedisplay()

def reshape(w, h):
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = max(1, w), max(1, h)
    glViewport(0, 0, WIDTH, HEIGHT)
    configurar_proyeccion()

def teclado(key, x, y):
    global modo_perspectiva, modo_visualizacion, modo_dibujo
    global habilitar_luz, zoom, auto_rotar, habilitar_sombra, salir_ventana
    k = key.decode("utf-8").lower()
    if k == "p":
        modo_perspectiva = not modo_perspectiva
        configurar_proyeccion()
    elif k == "w": modo_visualizacion = "wireframe"
    elif k == "s": modo_visualizacion = "solido"
    elif k in "12345":
        modo_dibujo = {"1": "cubo", "2": "esfera", "3": "cono", "4": "tetera", "5": "toro"}[k]
    elif k == "l": habilitar_luz = not habilitar_luz
    elif k == "k": habilitar_sombra = not habilitar_sombra
    elif k == "+":
        zoom = max(0.1, zoom * 0.9)
        configurar_proyeccion()
    elif k == "-":
        zoom *= 1.1
        configurar_proyeccion()
    elif k == "r": auto_rotar = not auto_rotar
    elif k == "b" or k == "\x1b":
        salir_ventana = True
        ventana_activa = False
        glutDestroyWindow(glutGetWindow())
        return
    glutPostRedisplay()

def mouse(btn, estado, x, y):
    global pos_luz
    if btn == GLUT_LEFT_BUTTON and estado == GLUT_DOWN:
        glutMotionFunc(arrastrar)
    elif btn == GLUT_RIGHT_BUTTON and estado == GLUT_DOWN:
        pos_luz = [x / WIDTH * 10 - 5, (HEIGHT - y) / HEIGHT * 10, 5, 1.0]
        glutPostRedisplay()

def arrastrar(x, y):
    global angulo_x, angulo_y
    angulo_y += (x - WIDTH / 2) * 0.005
    angulo_x -= (y - HEIGHT / 2) * 0.005
    glutPostRedisplay()

# ============================
# Main
# ============================
def abrir_ventana_3d():
    global salir_ventana, ventana_activa
    salir_ventana = False
    ventana_activa = True
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"Editor 3D - Paint OpenGL")
    init()
    configurar_proyeccion()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    while not salir_ventana:
        glutMainLoopEvent()
        idle()

if __name__ == "__main__":
    abrir_ventana_3d()
