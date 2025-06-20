from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

window_width, window_height = 800, 600
modo = "lapiz"  # "lapiz" o "borrador"
color_lapiz = (0.0, 0.0, 0.0)  # negro
color_fondo = (1.0, 1.0, 1.0)  # blanco
tamano_borrador = 15
puntos = []  # [(x, y, color, size), ...]

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    for x, y, color, size in puntos:
        glColor3f(*color)
        glPointSize(size)
        glBegin(GL_POINTS)
        glVertex2f(x, y)
        glEnd()
    glutSwapBuffers()

def mouse_drag(x, y):
    global modo
    # Convertir coordenadas de ventana a OpenGL
    x_gl = x
    y_gl = window_height - y
    if modo == "lapiz":
        puntos.append((x_gl, y_gl, color_lapiz, 3))
    elif modo == "borrador":
        puntos.append((x_gl, y_gl, color_fondo, tamano_borrador))
    glutPostRedisplay()

def keyboard(key, x, y):
    global modo
    if key == b'l':
        modo = "lapiz"
        print("Modo lápiz")
    elif key == b'b':
        modo = "borrador"
        print("Modo borrador")

def reshape(width, height):
    global window_width, window_height
    window_width, window_height = width, height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"Paint OpenGL con Borrador")
    glClearColor(*color_fondo, 1.0)
    glutDisplayFunc(display)
    glutMotionFunc(mouse_drag)
    glutKeyboardFunc(keyboard)
    glutReshapeFunc(reshape)
    glutMainLoop()

if __name__ == "__main__":
    main()