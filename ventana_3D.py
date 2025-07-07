# ventana_3D.py
import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

objeto = 1  # 1: cubo, 2: esfera, etc.

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    gluLookAt(0,0,10, 0,0,0, 0,1,0)
    glColor3f(0.8, 0.2, 0.2)
    if objeto == 1:
        glutSolidCube(2)
    elif objeto == 2:
        glutSolidSphere(1, 20, 20)
    # ...otros objetos...
    glutSwapBuffers()

def keyboard(key, x, y):
    global objeto
    if key == b'1':
        objeto = 1
    elif key == b'2':
        objeto = 2
    elif key == b'q' or key == b'\x1b':  # q o ESC para salir
        sys.exit()
    glutPostRedisplay()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(600, 500)
    glutCreateWindow(b"Ventana 3D GLUT")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutMainLoop()

if __name__ == "__main__":
    main()