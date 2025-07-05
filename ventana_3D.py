from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
import pygame
import sys
import math

# Variables de control
ancho, alto = 800, 600
modo_perspectiva = True  # True = perspectiva cónica, False = ortográfica
modo_dibujo = "cubo"     # Modos: "cubo", "esfera", "cono", "tetera", "toro"
modo_visualizacion = "wireframe"  # "wireframe" o "solido"
angulo_x, angulo_y = 30, -30
zoom = 1.0
posicion_luz = [2.0, 5.0, 2.0, 1.0]  # Posición de la luz (x, y, z, w)
habilitar_luz = True

def init():
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    # Configuración básica de iluminación
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, posicion_luz)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

def reshape(w, h):
    global ancho, alto
    ancho, alto = w, h
    glViewport(0, 0, w, h)
    configurar_proyeccion()

def configurar_proyeccion():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = ancho / alto

    if modo_perspectiva:
        # Perspectiva cónica
        gluPerspective(45 * zoom, aspect_ratio, 0.1, 100.0)
    else:
        # Perspectiva ortográfica
        glOrtho(-5 * zoom, 5 * zoom, -5 * zoom, 5 * zoom, 0.1, 100.0)

    glMatrixMode(GL_MODELVIEW)

def dibujar_ejes():
    glLineWidth(3)
    glBegin(GL_LINES)
    # Eje X (rojo)
    glColor3f(1, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(2, 0, 0)
    # Eje Y (verde)
    glColor3f(0, 1, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 2, 0)
    # Eje Z (azul)
    glColor3f(0, 0, 1)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 2)
    glEnd()
    glLineWidth(1)

def dibujar_cuadricula():
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_LINES)
    for i in range(-10, 11):
        glVertex3f(i, 0, -10)
        glVertex3f(i, 0, 10)
        glVertex3f(-10, 0, i)
        glVertex3f(10, 0, i)
    glEnd()

def dibujar_objeto():
    glColor3f(0.8, 0.2, 0.2)
    
    if modo_visualizacion == "wireframe":
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    if modo_dibujo == "cubo":
        if modo_visualizacion == "wireframe":
            glutWireCube(1.5)
        else:
            glutSolidCube(1.5)
    elif modo_dibujo == "esfera":
        if modo_visualizacion == "wireframe":
            glutWireSphere(1.0, 20, 20)
        else:
            glutSolidSphere(1.0, 20, 20)
    elif modo_dibujo == "cono":
        if modo_visualizacion == "wireframe":
            glutWireCone(1.0, 2.0, 20, 20)
        else:
            glutSolidCone(1.0, 2.0, 20, 20)
    elif modo_dibujo == "tetera":
        if modo_visualizacion == "wireframe":
            glutWireTeapot(1.0)
        else:
            glutSolidTeapot(1.0)
    elif modo_dibujo == "toro":
        if modo_visualizacion == "wireframe":
            glutWireTorus(0.3, 1.0, 20, 20)
        else:
            glutSolidTorus(0.3, 1.0, 20, 20)

def dibujar_barra_herramientas():
    # Configurar vista ortográfica 2D para la barra de herramientas
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, ancho, alto, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Fondo de la barra de herramientas
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(ancho, 0)
    glVertex2f(ancho, 40)
    glVertex2f(0, 40)
    glEnd()
    
    # Texto de instrucciones
    glColor3f(1, 1, 1)
    texto = f"Modo: {modo_dibujo} | Visualización: {modo_visualizacion} | Perspectiva: {'Cónica' if modo_perspectiva else 'Ortográfica'} | Luz: {'ON' if habilitar_luz else 'OFF'}"
    glRasterPos2f(10, 20)
    for char in texto:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    # Restaurar matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Configurar cámara
    gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
    
    # Aplicar rotaciones
    glRotatef(angulo_x, 1, 0, 0)
    glRotatef(angulo_y, 0, 1, 0)
    
    # Configurar iluminación
    if habilitar_luz:
        glEnable(GL_LIGHTING)
        glLightfv(GL_LIGHT0, GL_POSITION, posicion_luz)
    else:
        glDisable(GL_LIGHTING)
    
    # Dibujar elementos
    dibujar_cuadricula()
    dibujar_ejes()
    dibujar_objeto()
    
    # Dibujar barra de herramientas
    dibujar_barra_herramientas()
    
    glutSwapBuffers()

def teclado(tecla, x, y):
    global modo_perspectiva, modo_dibujo, modo_visualizacion, habilitar_luz, zoom
    
    tecla = tecla.decode('utf-8').lower()
    
    if tecla == 'p':
        modo_perspectiva = not modo_perspectiva
        configurar_proyeccion()
    elif tecla == 'w':
        modo_visualizacion = "wireframe"
    elif tecla == 's':
        modo_visualizacion = "solido"
    elif tecla == '1':
        modo_dibujo = "cubo"
    elif tecla == '2':
        modo_dibujo = "esfera"
    elif tecla == '3':
        modo_dibujo = "cono"
    elif tecla == '4':
        modo_dibujo = "tetera"
    elif tecla == '5':
        modo_dibujo = "toro"
    elif tecla == 'l':
        habilitar_luz = not habilitar_luz
    elif tecla == '+':
        zoom *= 0.9
        configurar_proyeccion()
    elif tecla == '-':
        zoom *= 1.1
        configurar_proyeccion()
    elif tecla == '\x1b':  # ESC
        glutLeaveMainLoop()
        return
    
    glutPostRedisplay()

def mouse(boton, estado, x, y):
    global angulo_x, angulo_y, posicion_luz
    
    if boton == GLUT_LEFT_BUTTON and estado == GLUT_DOWN:
        # Rotar vista
        glutMotionFunc(arrastrar_mouse)
    elif boton == GLUT_RIGHT_BUTTON and estado == GLUT_DOWN:
        # Mover luz
        posicion_luz = [x/ancho*10-5, (alto-y)/alto*10, 5, 1.0]
        glutPostRedisplay()

def arrastrar_mouse(x, y):
    global angulo_x, angulo_y
    
    angulo_y += (x - ancho/2) * 0.5
    angulo_x -= (y - alto/2) * 0.5
    glutPostRedisplay()

def abrir_ventana_3d():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(ancho, alto)
    glutCreateWindow(b"Editor 3D - Paint OpenGL")
    
    init()
    configurar_proyeccion()
    
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutMouseFunc(mouse)
    
    glutMainLoop()

if __name__ == "__main__":
    abrir_ventana_3d()