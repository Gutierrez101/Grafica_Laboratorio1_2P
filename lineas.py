import threading
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np

# Dimensiones de la ventana
ventana_ancho = 800
ventana_alto = 600

# Lista para almacenar las líneas dibujadas como pares de puntos ((x1, y1), (x2, y2))
lineas = []
# Variable para almacenar el primer punto de una línea mientras se espera el segundo clic
punto_inicial = None
# Color actual de las líneas (por defecto rojo)
color_actual = (1.0, 0.0, 0.0)
# Grosor de las líneas
grosor = 2.0

def init():
    """Inicializa el color de fondo y la proyección ortográfica."""
    glClearColor(1.0, 1.0, 1.0, 1.0)  # Fondo blanco
    gluOrtho2D(0, ventana_ancho, 0, ventana_alto)  # Origen (0,0) en esquina inferior izquierda

def display():
    """Función de dibujo principal: limpia la pantalla, dibuja el plano y las líneas."""
    glClear(GL_COLOR_BUFFER_BIT)
    crearPlano()  # Dibuja la cuadrícula/cartesiano
    glColor3f(*color_actual)  # Establece el color de las líneas
    glLineWidth(grosor)       # Establece el grosor de las líneas
    glBegin(GL_LINES)
    for linea in lineas:
        glVertex2d(*linea[0])  # Dibuja el punto inicial de la línea
        glVertex2d(*linea[1])  # Dibuja el punto final de la línea
    glEnd()
    glFlush()  # Fuerza el renderizado

def mouse_click(boton, estado, x, y):
    """Maneja los clics del mouse para dibujar líneas."""
    global punto_inicial
    y = ventana_alto - y  # Invierte el eje Y para que (0,0) sea abajo a la izquierda

    if boton == GLUT_LEFT_BUTTON and estado == GLUT_DOWN:
        if punto_inicial is None:
            # Primer clic: almacena el punto inicial
            punto_inicial = (x, y)
        else:
            # Segundo clic: almacena el punto final y agrega la línea
            punto_final = (x, y)
            lineas.append((punto_inicial, punto_final))
            punto_inicial = None  # Reinicia para la siguiente línea
            glutPostRedisplay()   # Redibuja la ventana

def crearPlano():
    """Dibuja la cuadrícula del plano cartesiano cada 100 unidades."""
    glColor3f(0.5, 0.5, 0.5)  # Color gris para la cuadrícula
    glBegin(GL_LINES)
    # Líneas verticales cada 100 unidades
    for i in np.arange(0, ventana_ancho + 1, 100):
        glVertex2d(i, 0)
        glVertex2d(i, ventana_alto)
    # Líneas horizontales cada 100 unidades
    for j in np.arange(0, ventana_alto + 1, 100):
        glVertex2d(0, j)
        glVertex2d(ventana_ancho, j)
    glEnd()

def teclado(tecla, x, y):
    """
    Maneja las teclas presionadas:
    r: rojo, g: verde, b: azul, +: aumentar grosor, -: disminuir grosor,
    c: limpiar pantalla, t: ingresar línea por teclado.
    """
    global color_actual, grosor
    tecla = tecla.decode('utf-8').lower()  # Convierte la tecla a minúscula

    if tecla == 'r':
        color_actual = (1.0, 0.0, 0.0)  # Cambia a rojo
    elif tecla == 'g':
        color_actual = (0.0, 1.0, 0.0)  # Cambia a verde
    elif tecla == 'b':
        color_actual = (0.0, 0.0, 1.0)  # Cambia a azul
    elif tecla == '+':
        grosor += 1.0                   # Aumenta el grosor de las líneas
    elif tecla == '-':
        grosor = max(1.0, grosor - 1.0) # Disminuye el grosor, mínimo 1.0
    elif tecla == 'c':
        lineas.clear()                  # Limpia todas las líneas
        glutPostRedisplay()             # Redibuja la ventana
    elif tecla == 't':
        # Llama a la función para ingresar coordenadas por teclado en un hilo aparte
        threading.Thread(target=ingresar_coordenadas, daemon=True).start()

def ingresar_coordenadas():
    """
    Permite ingresar dos puntos por consola para dibujar una línea.
    Se ejecuta en un hilo para no bloquear la ventana OpenGL.
    """
    try:
        x1 = float(input("Ingrese x1: "))
        y1 = float(input("Ingrese y1: "))
        x2 = float(input("Ingrese x2: "))
        y2 = float(input("Ingrese y2: "))
        # Agrega la línea con los puntos ingresados
        lineas.append(((x1, y1), (x2, y2)))
        glutPostRedisplay()  # Redibuja la ventana para mostrar la nueva línea
    except ValueError:
        print("\n Coordenadas inválidas. Intenta nuevamente.")

def main():
    """Configura GLUT y lanza el bucle principal."""
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(ventana_ancho, ventana_alto)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Dibujo de Lineas - Mouse y Teclado")
    init()
    glutDisplayFunc(display)      # Función de dibujo
    glutMouseFunc(mouse_click)    # Función para clics del mouse
    glutKeyboardFunc(teclado)     # Función para teclas
    glutMainLoop()                # Inicia el bucle principal de GLUT

if __name__ == '__main__':
    main()
