# Ventana de visualización 3D con OpenGL - Versión Mejorada
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
from OpenGL.GLUT import GLUT_KEY_UP, GLUT_KEY_DOWN, GLUT_KEY_LEFT, GLUT_KEY_RIGHT
from juego import dibujar_escena_juego

import sys
import math
import numpy as np
from PIL import Image  # Para manejo de texturas
import tkinter as tk
from tkinter import colorchooser, filedialog
import random

# Estados de la aplicación
class AppState:
    def __init__(self):
        self.modo_juego = False

        self.back_face_culling = True  # Eliminación de caras traseras
        self.z_buffer_activo = True    # Z-buffer para superficies ocultas
        self.mostrar_normales = False  # Mostrar vectores normales
        self.algoritmo_ocultas = "z_buffer"  # Algoritmo actual
        self.submenu_ocultas_visible = False

        self.salir_ventana = False
        self.ventana_activa = True
        self.WIDTH, self.HEIGHT = 1200, 800

        self.punto_seleccionado = None
        self.modal_placing = False
        self.selection_mode = False
        self.modo_edicion = None

        self.modo_perspectiva = True
        self.zoom = 1.0
        self.angulo_x, self.angulo_y = 45.0, -45.0
        self.auto_rotar = False
        self.velocidad_auto = 0.2

        self.habilitar_luz = True
        self.habilitar_sombra = True
        self.modo_visualizacion = "solido"
        
        # Terreno
        self.tamanio_terreno = 20
        self.divisiones_terreno = 50
        self.color_terreno = (0.2, 0.25, 0.3)
        self.color_lineas = (0.4, 0.4, 0.4)
        self.textura_terreno = None
        self.textura_habilitada = False
        self.textura_path = None
        
        # Objetos 3D
        self.objetos = []
        self.camaras = []
        self.luces = []
        self.figuras = []  # Reemplaza cubos, esferas y torus
        
        # Texturas para objetos
        self.textura_figuras = None
        self.textura_objetos_habilitada = False
        
        # Selección CORREGIDA
        self.objeto_seleccionado = None
        self.tipo_seleccion = None
        self.mouse_anterior = (0, 0)
        self.dragging = False
        self.rotando = False
        self.escalando = False
        
        # Nuevos controles para escalado
        self.cara_seleccionada = None  # Para escalado por caras
        self.punto_inicial_escalado = None
        
        # Transformaciones
        self.centro_transformacion = None
        self.angulo_rotacion = 0
        self.factor_escala = 1.0

        # Menú contextual
        self.show_help = False
        self.panel_luz_visible = False
        self.menu_contextual_visible = False
        self.menu_pos = (0, 0)
        self.opciones_menu = []
        self.submenu_textura_visible = False
        self.submenu_figuras_visible = False  # Nuevo submenú para figuras

        # Propiedades temporales
        self.color_luz_temp = [1.0, 1.0, 1.0, 1.0]
        self.tipo_luz_temp = 'puntual'
        self.angulo_spot_temp = 45.0
        self.exponente_spot_temp = 2.0

        # Cámara actual
        self.camara_actual = None
        self.luz_actual = 0

app = AppState()

def cargar_textura(ruta_imagen):
    """Cargar una textura desde un archivo de imagen"""
    try:
        imagen = Image.open(ruta_imagen)
        imagen = imagen.transpose(Image.FLIP_TOP_BOTTOM)
        datos = imagen.convert("RGBA").tobytes()
        
        textura_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textura_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, imagen.width, imagen.height, 
                        0, GL_RGBA, GL_UNSIGNED_BYTE, datos)
        
        return textura_id
    except Exception as e:
        print(f"Error cargando textura: {e}")
        return None

def init():
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    glDepthFunc(GL_LESS)  # Función de comparación Z-buffer
    glEnable(GL_CULL_FACE)  # Habilitar eliminación de caras
    glCullFace(GL_BACK)     # Eliminar caras traseras
    glFrontFace(GL_CCW)     # Orientación antihoraria para caras frontales
    
    glEnable(GL_LIGHTING)
    configurar_luz_global()
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_TEXTURE_2D)

def configurar_proyeccion():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = app.WIDTH / app.HEIGHT
    if app.modo_perspectiva:
        gluPerspective(45 * app.zoom, aspect, 0.1, 100.0)
    else:
        glOrtho(-5 * app.zoom, 5 * app.zoom, -5 * app.zoom, 5 * app.zoom, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

def configurar_luz_global():
    """Configurar luz global por defecto"""
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

def configurar_luz(index):
    if index < 0 or index >= len(app.luces):
        return
    
    luz = app.luces[index]
    luz_id = GL_LIGHT1 + index
    
    if luz['activa']:
        glEnable(luz_id)
    else:
        glDisable(luz_id)
    
    if luz['tipo_luz'] == 'directional':
        pos = [luz['pos'][0], luz['pos'][1], luz['pos'][2], 0.0]
    else:
        pos = [luz['pos'][0], luz['pos'][1], luz['pos'][2], 1.0]
    
    glLightfv(luz_id, GL_POSITION, pos)
    glLightfv(luz_id, GL_DIFFUSE, luz['color'])
    glLightfv(luz_id, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    
    if luz['tipo_luz'] == 'spot':
        glLightf(luz_id, GL_SPOT_CUTOFF, luz['angulo_spot'])
        glLightf(luz_id, GL_SPOT_EXPONENT, luz['exponente_spot'])
        glLightfv(luz_id, GL_SPOT_DIRECTION, luz['direccion'])

def dibujar_ejes():
    glLineWidth(3)
    glBegin(GL_LINES)
    glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(2, 0, 0)
    glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 2, 0)
    glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 2)
    glEnd()
    glLineWidth(1)

def dibujar_terreno():
    # Terreno principal
    if app.textura_terreno and app.textura_habilitada:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, app.textura_terreno)
        glColor3f(1, 1, 1)  # Color blanco para que la textura se vea correctamente
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3f(*app.color_terreno)
    
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    tamaño = app.tamanio_terreno
    mitad = tamaño / 2
    
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-mitad, 0, -mitad)
    glTexCoord2f(1, 0); glVertex3f(mitad, 0, -mitad)
    glTexCoord2f(1, 1); glVertex3f(mitad, 0, mitad)
    glTexCoord2f(0, 1); glVertex3f(-mitad, 0, mitad)
    glEnd()
    
    # Cuadrícula sobre el terreno
    glDisable(GL_TEXTURE_2D)
    glColor3f(*app.color_lineas)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    
    divisiones = app.divisiones_terreno
    paso = tamaño / divisiones

    glLineWidth(1.5)
    glBegin(GL_LINES)
    for i in range(0, divisiones + 1, 5):
        x = i * paso - mitad
        glVertex3f(x, 0.01, -mitad)
        glVertex3f(x, 0.01, mitad)
        glVertex3f(-mitad, 0.01, x)
        glVertex3f(mitad, 0.01, x)
    glEnd()
    
    glLineWidth(0.5)
    glBegin(GL_LINES)
    for i in range(divisiones + 1):
        if i % 5 != 0:
            x = i * paso - mitad
            glVertex3f(x, 0.01, -mitad)
            glVertex3f(x, 0.01, mitad)
            glVertex3f(-mitad, 0.01, x)
            glVertex3f(mitad, 0.01, x)
    glEnd()
    
    glLineWidth(1)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glDisable(GL_TEXTURE_2D)

def dibujar_manipuladores_escalado(pos, escala):
    """Dibujar manipuladores para escalado en modo E"""
    if not app.escalando:
        return
        
    glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(*pos)
    
    # Manipuladores en las caras del cubo
    manipuladores = [
        ([escala[0]/2, 0, 0], [1, 0, 0], 'x+'),      # Cara derecha
        ([-escala[0]/2, 0, 0], [1, 0, 0], 'x-'),     # Cara izquierda
        ([0, escala[1]/2, 0], [0, 1, 0], 'y+'),      # Cara superior
        ([0, -escala[1]/2, 0], [0, 1, 0], 'y-'),     # Cara inferior
        ([0, 0, escala[2]/2], [0, 0, 1], 'z+'),      # Cara frontal
        ([0, 0, -escala[2]/2], [0, 0, 1], 'z-')      # Cara trasera
    ]
    
    for pos_manip, color, cara in manipuladores:
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(*pos_manip)
        glutSolidSphere(0.1, 8, 8)
        glPopMatrix()
    
    glPopMatrix()
    glEnable(GL_LIGHTING)

def dibujar_carro(pos, escala=(1,1,1), rotacion=(0,0,0), color=(0.8, 0.2, 0.2), seleccionado=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    if seleccionado:
        glDisable(GL_LIGHTING)
        glColor3f(1, 1, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        
        # Dibujar ejes de transformación
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    # Aplicar color/textura según configuración
    if app.textura_figuras and app.textura_objetos_habilitada:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, app.textura_figuras)
        glColor3f(1, 1, 1)  # Color blanco para textura
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3f(*color)  # Usar color pasado como parámetro
    
   # --- Cuerpo principal del carro ---
    # Chasis inferior
    glPushMatrix()
    glTranslatef(0, 0.3, 0)
    glScalef(1.8, 0.4, 3.5)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Capó delantero
    glPushMatrix()
    glTranslatef(0, 0.5, 1.0)
    glScalef(1.6, 0.3, 1.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Parte trasera
    glPushMatrix()
    glTranslatef(0, 0.5, -1.0)
    glScalef(1.6, 0.4, 1.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Techo curvado
    glPushMatrix()
    glTranslatef(0, 0.9, 0)
    glScalef(1.2, 0.3, 2.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Parabrisas (vidrio)
    glColor4f(0.3, 0.4, 0.5, 0.5)  # Color azulado transparente
    glBegin(GL_QUADS)
    glVertex3f(-0.6, 0.7, 0.5); glVertex3f(0.6, 0.7, 0.5)
    glVertex3f(0.6, 0.9, 0.2); glVertex3f(-0.6, 0.9, 0.2)
    glEnd()
    
    # Ventanas laterales
    glBegin(GL_QUADS)
    glVertex3f(0.6, 0.7, -0.5); glVertex3f(0.6, 0.7, 0.5)
    glVertex3f(0.6, 0.9, 0.2); glVertex3f(0.6, 0.9, -0.2)
    glEnd()
    
    glBegin(GL_QUADS)
    glVertex3f(-0.6, 0.7, -0.5); glVertex3f(-0.6, 0.7, 0.5)
    glVertex3f(-0.6, 0.9, 0.2); glVertex3f(-0.6, 0.9, -0.2)
    glEnd()
    
    # Faros delanteros
    glColor3f(0.9, 0.9, 0.7)  # Color amarillo claro
    glPushMatrix()
    glTranslatef(0.7, 0.5, 1.3)
    glutSolidSphere(0.15, 16, 16)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-0.7, 0.5, 1.3)
    glutSolidSphere(0.15, 16, 16)
    glPopMatrix()
    
    # Luces traseras
    glColor3f(0.8, 0.1, 0.1)  # Rojo
    glPushMatrix()
    glTranslatef(0.5, 0.5, -1.5)
    glutSolidSphere(0.15, 16, 16)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-0.5, 0.5, -1.5)
    glutSolidSphere(0.15, 16, 16)
    glPopMatrix()
    
    # Ruedas (mejoradas)
    glColor3f(0.1, 0.1, 0.1)  # Negro
    for x in [-0.8, 0.8]:
        for z in [-1.2, 1.2]:
            glPushMatrix()
            glTranslatef(x, 0.1, z)
            glutSolidTorus(0.1, 0.25, 16, 16)  # Neumático
            glColor3f(0.5, 0.5, 0.5)  # Gris para la llanta
            glutSolidTorus(0.05, 0.15, 16, 16)
            glPopMatrix()
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()
    
    # Dibujar manipuladores de escalado si está seleccionado y en modo escalado
    if seleccionado and app.escalando and app.tipo_seleccion == 'figura':
        dibujar_manipuladores_escalado(pos, escala)

def dibujar_arbol(pos, escala=(1,1,1), rotacion=(0,0,0), color=(0.4, 0.2, 0.1), seleccionado=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    if seleccionado:
        glDisable(GL_LIGHTING)
        glColor3f(1, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        
        # Dibujar ejes de transformación
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    # Aplicar color/textura según configuración
    if app.textura_figuras and app.textura_objetos_habilitada:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, app.textura_figuras)
        glColor3f(1, 1, 1)  # Color blanco para textura
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3f(*color)  # Usar color pasado como parámetro
    
    # Tronco del árbol
    glColor3f(0.4, 0.2, 0.1)  # Marrón para el tronco
    glPushMatrix()
    glTranslatef(0, 1.0, 0)
    glScalef(0.3, 2.0, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Copa del árbol (usando fractales simples)
    glColor3f(0.1, 0.5, 0.1)  # Verde para las hojas
    for i in range(3):  # 3 niveles de ramas
        y_pos = 2.0 + i * 0.7
        size = 1.2 - i * 0.3
        glPushMatrix()
        glTranslatef(0, y_pos, 0)
        glutSolidSphere(size, 10, 10)
        glPopMatrix()
    
    glDisable(GL_TEXTURE_2D)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glPopMatrix()
    
    if seleccionado and app.escalando and app.tipo_seleccion == 'figura':
        dibujar_manipuladores_escalado(pos, escala)

def dibujar_arbusto(pos, escala=(1,1,1), rotacion=(0,0,0), color=(0.1, 0.5, 0.1), seleccionado=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    if seleccionado:
        glDisable(GL_LIGHTING)
        glColor3f(1, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        
        # Dibujar ejes de transformación
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    # Aplicar color/textura según configuración
    if app.textura_figuras and app.textura_objetos_habilitada:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, app.textura_figuras)
        glColor3f(1, 1, 1)  # Color blanco para textura
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3f(*color)  # Usar color pasado como parámetro
    
    # Base del arbusto
    glPushMatrix()
    glutSolidSphere(0.5, 10, 10)
    glPopMatrix()
    
    # Fractal simple para helecho
    def dibujar_helecho(x, y, z, size, angle, depth):
        if depth <= 0:
            return
            
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(angle, 0, 0, 1)
        
        # Tallo
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, size, 0)
        glEnd()
        
        # Hojas
        glBegin(GL_TRIANGLES)
        glVertex3f(0, size*0.3, 0)
        glVertex3f(-size*0.2, size*0.5, 0)
        glVertex3f(size*0.2, size*0.5, 0)
        glEnd()
        
        # Ramas recursivas
        dibujar_helecho(0, size*0.7, 0, size*0.7, angle+20, depth-1)
        dibujar_helecho(0, size*0.7, 0, size*0.7, angle-20, depth-1)
        
        glPopMatrix()
    
    glDisable(GL_LIGHTING)
    glColor3f(0.1, 0.5, 0.1)
    dibujar_helecho(0, 0.5, 0, 0.5, 0, 3)
    glEnable(GL_LIGHTING)
    
    glDisable(GL_TEXTURE_2D)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glPopMatrix()
    
    if seleccionado and app.escalando and app.tipo_seleccion == 'figura':
        dibujar_manipuladores_escalado(pos, escala)

def dibujar_casa(pos, escala=(1,1,1), rotacion=(0,0,0), color=(0.8, 0.6, 0.4), seleccionado=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    if seleccionado:
        glDisable(GL_LIGHTING)
        glColor3f(1, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        
        # Dibujar ejes de transformación
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    # Aplicar color/textura según configuración
    if app.textura_figuras and app.textura_objetos_habilitada:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, app.textura_figuras)
        glColor3f(1, 1, 1)  # Color blanco para textura
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3f(*color)  # Usar color pasado como parámetro
    
    # --- Estructura principal ---
    # Base de la casa (paredes)
    glPushMatrix()
    glScalef(1.8, 1.0, 1.8)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Techo a dos aguas (más detallado)
    glColor3f(0.5, 0.2, 0.1)  # Color rojizo para tejas
    glBegin(GL_TRIANGLES)
    # Cara frontal
    glVertex3f(-0.9, 1.0, 0.9)
    glVertex3f(0.9, 1.0, 0.9)
    glVertex3f(0.0, 2.0, 0.0)
    # Cara derecha
    glVertex3f(0.9, 1.0, 0.9)
    glVertex3f(0.9, 1.0, -0.9)
    glVertex3f(0.0, 2.0, 0.0)
    # Cara trasera
    glVertex3f(0.9, 1.0, -0.9)
    glVertex3f(-0.9, 1.0, -0.9)
    glVertex3f(0.0, 2.0, 0.0)
    # Cara izquierda
    glVertex3f(-0.9, 1.0, -0.9)
    glVertex3f(-0.9, 1.0, 0.9)
    glVertex3f(0.0, 2.0, 0.0)
    glEnd()
    
    # Chimenea
    glColor3f(0.6, 0.6, 0.6)
    glPushMatrix()
    glTranslatef(0.5, 1.5, -0.5)
    glScalef(0.2, 0.8, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # --- Detalles de la casa ---
    # Puerta principal
    glColor3f(0.4, 0.3, 0.2)
    glPushMatrix()
    glTranslatef(0.0, -0.5, 0.9)
    glScalef(0.4, 0.8, 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Ventanas
    glColor4f(0.3, 0.5, 0.8, 0.7)  # Color de vidrio
    for x in [-0.6, 0.6]:
        for z in [-0.5, 0.5]:
            glPushMatrix()
            glTranslatef(x, 0.3, z)
            glScalef(0.3, 0.4, 0.1)
            glutSolidCube(1.0)
            glPopMatrix()
    
    # Marco de ventanas
    glColor3f(0.3, 0.2, 0.1)
    for x in [-0.6, 0.6]:
        for z in [-0.5, 0.5]:
            glPushMatrix()
            glTranslatef(x, 0.3, z)
            glScalef(0.35, 0.45, 0.11)
            glutWireCube(1.0)
            glPopMatrix()
    
    # Escalones
    glColor3f(0.5, 0.4, 0.3)
    for i in range(3):
        glPushMatrix()
        glTranslatef(0, -0.6 - i*0.1, 0.9 + i*0.1)
        glScalef(0.5 - i*0.1, 0.1, 0.3 - i*0.1)
        glutSolidCube(1.0)
        glPopMatrix()
    
    glDisable(GL_TEXTURE_2D)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glPopMatrix()
    
    if seleccionado and app.escalando and app.tipo_seleccion == 'figura':
        dibujar_manipuladores_escalado(pos, escala)

def dibujar_montana(pos, escala=(1,1,1), rotacion=(0,0,0), color=(0.5, 0.4, 0.3), seleccionado=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    if seleccionado:
        glDisable(GL_LIGHTING)
        glColor3f(1, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        
        # Dibujar ejes de transformación
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    # Aplicar color/textura según configuración
    if app.textura_figuras and app.textura_objetos_habilitada:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, app.textura_figuras)
        glColor3f(1, 1, 1)  # Color blanco para textura
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3f(*color)  # Usar color pasado como parámetro
    
   # Base de la montaña (más detallada)
    glPushMatrix()
    glScalef(1.5, 1.5, 1.5)  # Más ancha
    
    # Usar una pirámide con lados escalonados para más realismo
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 2, 0)  # Pico
    for i in range(13):  # 12 lados + 1 para cerrar
        ang = i * 2 * math.pi / 12
        x = math.cos(ang)
        z = math.sin(ang)
        
        # Crear escalones en la montaña
        if i % 3 == 0:
            glVertex3f(x, 0.5, z)
            glVertex3f(x*0.8, 0.8, z*0.8)
        elif i % 3 == 1:
            glVertex3f(x*0.8, 0.8, z*0.8)
            glVertex3f(x*0.5, 1.2, z*0.5)
        else:
            glVertex3f(x*0.5, 1.2, z*0.5)
            glVertex3f(x*0.2, 1.7, z*0.2)
    glEnd()
    
    # Detalles de rocas en la base
    glColor3f(0.4, 0.35, 0.3)  # Color más oscuro para rocas
    for i in range(8):
        ang = i * 2 * math.pi / 8
        x = math.cos(ang) * 1.2
        z = math.sin(ang) * 1.2
        glPushMatrix()
        glTranslatef(x, 0.1, z)
        glutSolidSphere(0.2 + random.random()*0.1, 8, 8)
        glPopMatrix()
    
    # Nieve en la cima
    glColor3f(0.9, 0.9, 0.95)
    glPushMatrix()
    glTranslatef(0, 1.5, 0)
    glutSolidSphere(0.5, 8, 8)
    glPopMatrix()
    
    glPopMatrix()
    
    glDisable(GL_TEXTURE_2D)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glPopMatrix()
    
    if seleccionado and app.escalando and app.tipo_seleccion == 'figura':
        dibujar_manipuladores_escalado(pos, escala)

def dibujar_camara(pos, look_at, up, escala=(1,1,1), rotacion=(0,0,0), seleccionada=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    # Calcular orientación hacia el punto look_at
    dx, dy, dz = look_at[0]-pos[0], look_at[1]-pos[1], look_at[2]-pos[2]
    distancia = math.sqrt(dx*dx + dy*dy + dz*dz)
    if distancia > 0.001:  # Evitar división por cero
        angulo = math.degrees(math.atan2(dx, dz))
        glRotatef(angulo, 0, 1, 0)
    
    glDisable(GL_LIGHTING)
    
    if seleccionada:
        glColor3f(1.0, 0.0, 0.0)  # Rojo para seleccionada
        glLineWidth(4)
        
        # Dibujar ejes de transformación cuando está seleccionada
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
    else:
        glColor3f(0.2, 0.2, 0.8)  # Azul para cámara normal
        glLineWidth(2)
    
    # 1. Dibujar cuerpo principal de la cámara (cubo)
    glBegin(GL_QUADS)
    # Cara frontal
    glVertex3f(-0.3, -0.3, 0.1)
    glVertex3f(0.3, -0.3, 0.1)
    glVertex3f(0.3, 0.3, 0.1)
    glVertex3f(-0.3, 0.3, 0.1)
    # Cara trasera
    glVertex3f(-0.3, -0.3, -0.1)
    glVertex3f(-0.3, 0.3, -0.1)
    glVertex3f(0.3, 0.3, -0.1)
    glVertex3f(0.3, -0.3, -0.1)
    # Cara superior
    glVertex3f(-0.3, 0.3, -0.1)
    glVertex3f(-0.3, 0.3, 0.1)
    glVertex3f(0.3, 0.3, 0.1)
    glVertex3f(0.3, 0.3, -0.1)
    # Cara inferior
    glVertex3f(-0.3, -0.3, -0.1)
    glVertex3f(0.3, -0.3, -0.1)
    glVertex3f(0.3, -0.3, 0.1)
    glVertex3f(-0.3, -0.3, 0.1)
    # Cara izquierda
    glVertex3f(-0.3, -0.3, -0.1)
    glVertex3f(-0.3, -0.3, 0.1)
    glVertex3f(-0.3, 0.3, 0.1)
    glVertex3f(-0.3, 0.3, -0.1)
    # Cara derecha
    glVertex3f(0.3, -0.3, -0.1)
    glVertex3f(0.3, 0.3, -0.1)
    glVertex3f(0.3, 0.3, 0.1)
    glVertex3f(0.3, -0.3, 0.1)
    glEnd()
    
    # 2. Dibujar lente (cilindro frontal)
    glColor3f(0.1, 0.1, 0.1)  # Negro para el lente
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0.15)  # Centro del lente
    for i in range(17):  # 16 segmentos + 1 para cerrar
        ang = i * 2 * math.pi / 16
        x = 0.2 * math.cos(ang)
        y = 0.2 * math.sin(ang)
        glVertex3f(x, y, 0.15)
    glEnd()
    
    # 3. Dibujar aro del lente
    glColor3f(0.8, 0.8, 0.2) if not seleccionada else glColor3f(1, 0, 0)
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(17):  # 16 segmentos + 1 para cerrar
        ang = i * 2 * math.pi / 16
        x_ext = 0.25 * math.cos(ang)
        y_ext = 0.25 * math.sin(ang)
        x_int = 0.2 * math.cos(ang)
        y_int = 0.2 * math.sin(ang)
        glVertex3f(x_ext, y_ext, 0.12)
        glVertex3f(x_int, y_int, 0.12)
    glEnd()
    
    # 4. Dibujar línea de dirección (hacia dónde apunta)
    glColor3f(1, 0, 0) if seleccionada else glColor3f(0, 1, 0)
    glLineWidth(3)
    glBegin(GL_LINES)
    glVertex3f(0, 0, 0.15)
    glVertex3f(0, 0, -1.0)  # Línea más larga para mejor visualización
    glEnd()
    
    # 5. Flecha en la punta de la línea de dirección
    glBegin(GL_TRIANGLES)
    glVertex3f(0, 0, -1.0)
    glVertex3f(-0.1, 0.1, -0.8)
    glVertex3f(0.1, 0.1, -0.8)
    
    glVertex3f(0, 0, -1.0)
    glVertex3f(-0.1, -0.1, -0.8)
    glVertex3f(0.1, -0.1, -0.8)
    glEnd()
    
    # 6. Etiqueta "CAM" si no está seleccionada
    if not seleccionada:
        glColor3f(1, 1, 1)
        glRasterPos3f(-0.15, 0.4, 0)
        texto = "CAM"
        for char in texto:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    glLineWidth(1)
    glEnable(GL_LIGHTING)
    glPopMatrix()

def dibujar_luz(pos, color, tipo, escala=(1,1,1), rotacion=(0,0,0), seleccionada=False):
    glPushMatrix()
    glTranslatef(*pos[:3])
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    glDisable(GL_LIGHTING)
    
    if seleccionada:
        glColor3f(1, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        glutWireSphere(0.25, 16, 16)
        
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
    else:
        glColor3f(*color[:3])
    
    # Esfera
    glutSolidSphere(0.25, 16, 16)
    
    # Líneas radiales
    glColor3f(1, 1, 0.5)
    glBegin(GL_LINES)
    for i in range(12):
        ang = i * 30 * math.pi / 180
        glVertex3f(0, 0, 0)
        glVertex3f(0.6 * math.cos(ang), 0.6 * math.sin(ang), 0)
    glEnd()
    
    glEnable(GL_LIGHTING)
    glPopMatrix()

def dibujar_barra_herramientas():
    # Guardar estado actual
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, app.WIDTH, app.HEIGHT, 0)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    # Fondo barra
    glColor3f(0.13, 0.13, 0.16)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(app.WIDTH, 0)
    glVertex2f(app.WIDTH, 40)
    glVertex2f(0, 40)
    glEnd()

    # Botones principales
    botones = [
        ("Seleccionar", 10, app.selection_mode),
        ("Camara", 120, app.modo_edicion == 'colocar_camara'),
        ("Luz", 230, app.modo_edicion == 'colocar_luz'),
        ("Figuras", 340, app.modo_edicion == 'colocar_figura'),  # Botón único para figuras
        ("Textura", 450, False),
        ("Eliminar", 560, False),
        ("Vista Cam", 670, app.camara_actual is not None),
        ("Vista Libre", 780, app.camara_actual is None),
        ("Ocultas", 890, False),
        ("Juego", 1000, app.modo_juego)
    ]
    
    for nombre, x, activo in botones:
        if activo:
            glColor3f(0.4, 0.6, 0.4)
        else:
            glColor3f(0.22, 0.22, 0.32)
        
        glBegin(GL_QUADS)
        glVertex2f(x, 8)
        glVertex2f(x+100, 8)
        glVertex2f(x+100, 32)
        glVertex2f(x, 32)
        glEnd()
        
        glColor3f(1, 1, 1)
        glRasterPos2f(x+12, 25)
        for c in nombre:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

    # Submenú de caras ocultas
    if app.submenu_ocultas_visible:
        glColor3f(0.2, 0.3, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(890, 40)
        glVertex2f(890+180, 40)
        glVertex2f(890+180, 160)
        glVertex2f(890, 160)
        glEnd()
        
        opciones_ocultas = [
            (f"Z-Buffer: {'ON' if app.z_buffer_activo else 'OFF'}", 900, 55),
            (f"Back-Face: {'ON' if app.back_face_culling else 'OFF'}", 900, 75),
            (f"Normales: {'ON' if app.mostrar_normales else 'OFF'}", 900, 95),
            ("Wireframe", 900, 115),
            ("Solido", 900, 135),
            ("Puntos", 900, 155)
        ]
        
        for texto, x, y in opciones_ocultas:
            glColor3f(1, 1, 1)
            glRasterPos2f(x, y)
            for c in texto:
                glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

    # Submenú de textura
    if app.submenu_textura_visible:
        glColor3f(0.25, 0.25, 0.35)
        glBegin(GL_QUADS)
        glVertex2f(450, 40)
        glVertex2f(650, 40)
        glVertex2f(650, 100)
        glVertex2f(450, 100)
        glEnd()
        
        glColor3f(0.4, 0.4, 0.5)
        glBegin(GL_LINES)
        glVertex2f(455, 70)
        glVertex2f(645, 70)
        glEnd()
        
        glColor3f(0.35, 0.35, 0.45)
        glBegin(GL_QUADS)
        glVertex2f(455, 45)
        glVertex2f(645, 45)
        glVertex2f(645, 65)
        glVertex2f(455, 65)
        glEnd()
        
        glBegin(GL_QUADS)
        glVertex2f(455, 75)
        glVertex2f(645, 75)
        glVertex2f(645, 95)
        glVertex2f(455, 95)
        glEnd()
        
        opciones = [
            ("Aplicar Color", 460, 58),
            ("Aplicar Textura", 460, 88)
        ]
        
        for texto, x, y in opciones:
            glColor3f(1, 1, 1)
            glRasterPos2f(x, y)
            for c in texto:
                glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

    # Submenú de figuras
    if app.submenu_figuras_visible:
        glColor3f(0.25, 0.35, 0.45)
        glBegin(GL_QUADS)
        glVertex2f(340, 40)
        glVertex2f(540, 40)
        glVertex2f(540, 200)
        glVertex2f(340, 200)
        glEnd()
        
        opciones_figuras = [
            ("Carro", 350, 60),
            ("Arbol", 350, 90),
            ("Arbusto", 350, 120),
            ("Casa", 350, 150),
            ("Montaña", 350, 180)
        ]
        
        for texto, x, y in opciones_figuras:
            glColor3f(1, 1, 1)
            glRasterPos2f(x, y)
            for c in texto:
                glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

    # Restaurar estado
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()  # MODELVIEW
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()  # PROJECTION
    glMatrixMode(GL_MODELVIEW)

def obtener_posicion_3d(x, y):
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    if app.camara_actual is not None and app.camaras:
        cam = app.camaras[app.camara_actual]
        gluLookAt(cam['pos'][0], cam['pos'][1], cam['pos'][2],
                    cam['look_at'][0], cam['look_at'][1], cam['look_at'][2],
                    cam['up'][0], cam['up'][1], cam['up'][2])
    else:
        gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(app.angulo_x, 1, 0, 0)
        glRotatef(app.angulo_y, 0, 1, 0)
    
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    
    glPopMatrix()
    
    winY = float(viewport[3] - y)
    
    try:
        pos1 = gluUnProject(x, winY, 0.0, modelview, projection, viewport)
        pos2 = gluUnProject(x, winY, 1.0, modelview, projection, viewport)
        
        if pos1 and pos2:
            dir_ray = np.subtract(pos2, pos1)
            if abs(dir_ray[1]) > 1e-6:
                t = -pos1[1] / dir_ray[1]
                if t >= 0:
                    pos = np.add(pos1, np.multiply(dir_ray, t))
                    
                    mitad = app.tamanio_terreno / 2
                    pos[0] = max(-mitad, min(mitad, pos[0]))
                    pos[1] = 0
                    pos[2] = max(-mitad, min(mitad, pos[2]))
                    return [pos[0], pos[1], pos[2]]
    except Exception as e:
        print(f"Error en obtener_posicion_3d: {e}")
    
    return None

def seleccionar_objeto(x, y):
    glSelectBuffer(512)
    glRenderMode(GL_SELECT)
    glInitNames()
    
    viewport = glGetIntegerv(GL_VIEWPORT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluPickMatrix(x, viewport[3]-y, 5, 5, viewport)
    
    aspect = app.WIDTH / app.HEIGHT
    if app.modo_perspectiva:
        gluPerspective(45 * app.zoom, aspect, 0.1, 100.0)
    else:
        glOrtho(-5 * app.zoom, 5 * app.zoom, -5 * app.zoom, 5 * app.zoom, 0.1, 100.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if app.camara_actual is not None and app.camaras:
        cam = app.camaras[app.camara_actual]
        gluLookAt(cam['pos'][0], cam['pos'][1], cam['pos'][2],
                    cam['look_at'][0], cam['look_at'][1], cam['look_at'][2],
                    cam['up'][0], cam['up'][1], cam['up'][2])
    else:
        gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(app.angulo_x, 1, 0, 0)
        glRotatef(app.angulo_y, 0, 1, 0)
    
    # CAMARAS - tipo 1
    for i, cam in enumerate(app.camaras):
        glPushName(1)
        glPushName(i)
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], cam['escala'], cam['rotacion'], False)
        glPopName()
        glPopName()
    
    # LUCES - tipo 2
    for i, luz in enumerate(app.luces):
        glPushName(2)
        glPushName(i)
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'], luz['escala'], luz['rotacion'], False)
        glPopName()
        glPopName()
    
    # FIGURAS - tipo 3
    for i, figura in enumerate(app.figuras):
        glPushName(3)
        glPushName(i)
        if figura['tipo'] == 'carro':
            dibujar_carro(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], False)
        elif figura['tipo'] == 'arbol':
            dibujar_arbol(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], False)
        elif figura['tipo'] == 'arbusto':
            dibujar_arbusto(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], False)
        elif figura['tipo'] == 'casa':
            dibujar_casa(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], False)
        elif figura['tipo'] == 'montana':
            dibujar_montana(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], False)
        glPopName()
        glPopName()
        
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glFlush()
    
    hits = glRenderMode(GL_RENDER)
    
    if hits:
        hit = hits[0]
        if len(hit.names) >= 2:
            tipo = hit.names[0]
            idx = hit.names[1]
            
            if tipo == 1: return 'camara', idx
            elif tipo == 2: return 'luz', idx
            elif tipo == 3: return 'figura', idx
    
    return None, None

def eliminar_objeto_seleccionado():
    if app.tipo_seleccion == 'camara' and app.objeto_seleccionado is not None:
        if 0 <= app.objeto_seleccionado < len(app.camaras):
            app.camaras.pop(app.objeto_seleccionado)
            if app.camara_actual == app.objeto_seleccionado:
                app.camara_actual = None
            elif app.camara_actual is not None and app.camara_actual > app.objeto_seleccionado:
                app.camara_actual -= 1
    
    elif app.tipo_seleccion == 'luz' and app.objeto_seleccionado is not None:
        if 0 <= app.objeto_seleccionado < len(app.luces):
            luz_id = GL_LIGHT1 + app.objeto_seleccionado
            glDisable(luz_id)
            app.luces.pop(app.objeto_seleccionado)
    
    elif app.tipo_seleccion == 'figura' and app.objeto_seleccionado is not None:
        if 0 <= app.objeto_seleccionado < len(app.figuras):
            app.figuras.pop(app.objeto_seleccionado)
    
    app.objeto_seleccionado = None
    app.tipo_seleccion = None

def agregar_camara(posicion):
    nueva_camara = {
        'pos': [posicion[0], 1.5, posicion[2]],
        'look_at': [posicion[0], 1.5, posicion[2]-2],
        'up': [0.0, 1.0, 0.0],
        'escala': [1.0, 1.0, 1.0],
        'rotacion': [0.0, 0.0, 0.0]
    }
    app.camaras.append(nueva_camara)
    app.objeto_seleccionado = len(app.camaras) - 1
    app.tipo_seleccion = 'camara'
    print(f"Cámara agregada en: {posicion}")

def agregar_luz(posicion):
    nueva_luz = {
        'pos': [posicion[0], 2.0, posicion[2], 1.0],
        'color': [1.0, 1.0, 1.0, 1.0],
        'activa': True,
        'tipo_luz': 'puntual',
        'angulo_spot': 45.0,
        'exponente_spot': 2.0,
        'direccion': [0.0, -1.0, 0.0],
        'escala': [1.0, 1.0, 1.0],
        'rotacion': [0.0, 0.0, 0.0]
    }
    app.luces.append(nueva_luz)
    app.objeto_seleccionado = len(app.luces) - 1
    app.tipo_seleccion = 'luz'
    configurar_luz(app.objeto_seleccionado)
    print(f"Luz agregada en: {posicion}")

def agregar_figura(posicion, tipo_figura):
    nueva_figura = {
        'pos': [posicion[0], 0.5, posicion[2]],
        'escala': [1.0, 1.0, 1.0],
        'rotacion': [0.0, 0.0, 0.0],
        'color': [0.8, 0.2, 0.2],  # Color inicial
        'tipo': tipo_figura
    }
    app.figuras.append(nueva_figura)
    app.objeto_seleccionado = len(app.figuras) - 1
    app.tipo_seleccion = 'figura'
    print(f"Figura {tipo_figura} agregada en: {posicion}")

def detectar_cara_figura(x, y):
    """Detectar qué cara de la figura se está seleccionando para escalado"""
    if app.tipo_seleccion != 'figura' or app.objeto_seleccionado is None:
        return None
    
    figura = app.figuras[app.objeto_seleccionado]
    pos_3d = obtener_posicion_3d(x, y)
    if pos_3d is None:
        return None
    
    # Determinar cara más cercana basada en la posición
    centro = figura['pos']
    dx = pos_3d[0] - centro[0]
    dy = pos_3d[1] - centro[1] 
    dz = pos_3d[2] - centro[2]
    
    # Encontrar el eje con mayor diferencia
    abs_dx, abs_dy, abs_dz = abs(dx), abs(dy), abs(dz)
    
    if abs_dx > abs_dy and abs_dx > abs_dz:
        return 'x+' if dx > 0 else 'x-'
    elif abs_dy > abs_dx and abs_dy > abs_dz:
        return 'y+' if dy > 0 else 'y-'
    else:
        return 'z+' if dz > 0 else 'z-'

def escalar_objeto(cara, delta):
    """Escalar un objeto en la dirección especificada"""
    if app.objeto_seleccionado is None:
        return
    
    factor = 1 + delta * 0.01  # Factor de escalado basado en delta del mouse
    
    if app.tipo_seleccion == 'figura':
        figura = app.figuras[app.objeto_seleccionado]
        if cara == 'x+' or cara == 'x-':
            figura['escala'][0] *= factor
        elif cara == 'y+' or cara == 'y-':
            figura['escala'][1] *= factor
        elif cara == 'z+' or cara == 'z-':
            figura['escala'][2] *= factor

def mostrar_coordenadas():
    if app.objeto_seleccionado is not None:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, app.WIDTH, app.HEIGHT, 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        
        glColor3f(1, 1, 1)
        glRasterPos2f(10, 60)
        
        if app.tipo_seleccion == 'camara':
            pos = app.camaras[app.objeto_seleccionado]['pos']
            texto = f"Camara seleccionada: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        elif app.tipo_seleccion == 'luz':
            pos = app.luces[app.objeto_seleccionado]['pos']
            texto = f"Luz seleccionada: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        elif app.tipo_seleccion == 'figura':
            pos = app.figuras[app.objeto_seleccionado]['pos']
            tipo = app.figuras[app.objeto_seleccionado]['tipo']
            texto = f"Figura seleccionada ({tipo}): X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        
        for char in texto:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        
        # Mostrar modo actual
        glRasterPos2f(10, 80)
        modo_texto = ""
        if app.dragging:
            modo_texto = "MODO: Mover (G) - Mouse o flechas"
        elif app.rotando:
            modo_texto = "MODO: Rotar (R) - Flechas del teclado"
        elif app.escalando:
            modo_texto = "MODO: Escalar (E) - Flechas o mouse en manipuladores"
        
        for char in modo_texto:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        
        glEnable(GL_LIGHTING)
        glPopMatrix()  # Restaurar MODELVIEW
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()  # Restaurar PROJECTION
        glMatrixMode(GL_MODELVIEW)  # Volver a MODELVIEW

def mover_objeto_con_teclado(dx, dy, dz):
    """Función para mover objetos con las flechas del teclado"""
    if app.objeto_seleccionado is None:
        return
    
    if app.tipo_seleccion == 'camara':
        cam = app.camaras[app.objeto_seleccionado]
        cam['pos'][0] += dx
        cam['pos'][1] += dy
        cam['pos'][2] += dz
        # Mantener dirección de la cámara
        cam['look_at'][0] += dx
        cam['look_at'][1] += dy
        cam['look_at'][2] += dz
        
    elif app.tipo_seleccion == 'luz':
        luz = app.luces[app.objeto_seleccionado]
        luz['pos'][0] += dx
        luz['pos'][1] += dy
        luz['pos'][2] += dz
        configurar_luz(app.objeto_seleccionado)
        
    elif app.tipo_seleccion == 'figura':
        figura = app.figuras[app.objeto_seleccionado]
        figura['pos'][0] += dx
        figura['pos'][1] += dy
        figura['pos'][2] += dz

def rotar_objeto_con_teclado(rx, ry, rz):
    """Función para rotar objetos con las flechas del teclado"""
    if app.objeto_seleccionado is None:
        return
    
    if app.tipo_seleccion == 'camara':
        cam = app.camaras[app.objeto_seleccionado]
        cam['rotacion'][0] += rx
        cam['rotacion'][1] += ry
        cam['rotacion'][2] += rz
        
    elif app.tipo_seleccion == 'luz':
        luz = app.luces[app.objeto_seleccionado]
        luz['rotacion'][0] += rx
        luz['rotacion'][1] += ry
        luz['rotacion'][2] += rz
        
    elif app.tipo_seleccion == 'figura':
        figura = app.figuras[app.objeto_seleccionado]
        figura['rotacion'][0] += rx
        figura['rotacion'][1] += ry
        figura['rotacion'][2] += rz

def escalar_objeto_con_teclado(factor):
    """Función para escalar objetos con las flechas del teclado"""
    if app.objeto_seleccionado is None:
        return
    
    if app.tipo_seleccion == 'camara':
        cam = app.camaras[app.objeto_seleccionado]
        for i in range(3):
            cam['escala'][i] *= factor
            
    elif app.tipo_seleccion == 'luz':
        luz = app.luces[app.objeto_seleccionado]
        for i in range(3):
            luz['escala'][i] *= factor
            
    elif app.tipo_seleccion == 'figura':
        figura = app.figuras[app.objeto_seleccionado]
        for i in range(3):
            figura['escala'][i] *= factor

def aplicar_color_objeto():
    """Aplicar un color al objeto seleccionado"""
    if app.objeto_seleccionado is None:
        print("No hay objeto seleccionado")
        return
    
    # Crear una ventana temporal de Tkinter para el color picker
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    
    # Abrir el selector de color
    color = colorchooser.askcolor(title="Seleccionar color")
    root.destroy()  # Destruir la ventana temporal
    
    if color[0] is None:  # El usuario canceló
        print("Selección de color cancelada")
        return
    
    # Convertir el color de 0-255 a 0.0-1.0
    r, g, b = color[0]
    color_normalizado = [r/255.0, g/255.0, b/255.0]
    
    # Aplicar el color según el tipo de objeto
    if app.tipo_seleccion == 'figura' and 0 <= app.objeto_seleccionado < len(app.figuras):
        app.figuras[app.objeto_seleccionado]['color'] = color_normalizado
        print(f"Color aplicado a la figura: {color_normalizado}")
    elif app.tipo_seleccion == 'luz' and 0 <= app.objeto_seleccionado < len(app.luces):
        app.luces[app.objeto_seleccionado]['color'] = color_normalizado + [1.0]  # Agregar alpha
        configurar_luz(app.objeto_seleccionado)
        print(f"Color aplicado a la luz: {color_normalizado}")
    else:
        app.color_terreno=color_normalizado
        print(f"No se puede aplicar color a objeto de tipo: {app.tipo_seleccion}")
    
    # Forzar actualización de la pantalla
    glutPostRedisplay()

def aplicar_textura_objeto():
    """Aplicar una textura al objeto seleccionado"""
    if app.objeto_seleccionado is None:
        return
    
    # Abrir diálogo para seleccionar archivo
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Seleccionar textura", 
                                        filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if not file_path:
        return
    
    # Cargar la textura
    textura_id = cargar_textura(file_path)
    if textura_id is None:
        return
    
    # Asignar la textura al objeto correspondiente
    if app.objeto_seleccionado is not None:
        if app.textura_figuras:
            glDeleteTextures([app.textura_figuras])
        app.textura_figuras = textura_id
        print(f"Textura aplicada: {file_path}")
    else:
        if app.textura_terreno:
            glDeleteTextures([app.textura_terreno])
        app.textura_terreno=textura_id
        app.textura_path=file_path
        print("Textura del terreno cambiada")
    
    glutPostRedisplay()

def aplicar_eliminacion_ocultas():
    """Aplicar configuraciones de eliminación de caras y líneas ocultas"""
    
    # Z-Buffer (eliminación de superficies ocultas)
    if app.z_buffer_activo:
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)
        glClear(GL_DEPTH_BUFFER_BIT)
    else:
        glDisable(GL_DEPTH_TEST)
    
    # Back-face culling (eliminación de caras traseras)
    if app.back_face_culling:
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
    else:
        glDisable(GL_CULL_FACE)

def dibujar_normales_objeto():
    """Dibujar normales de los objetos para visualización"""
    if not app.mostrar_normales or app.objeto_seleccionado is None:
        return
    
    glDisable(GL_LIGHTING)
    glColor3f(1, 1, 0)  # Amarillo para normales
    glLineWidth(3)
    
    # Dibujar normales según el tipo de objeto seleccionado
    if app.tipo_seleccion == 'figura':
        figura = app.figuras[app.objeto_seleccionado]
        pos = figura['pos']
        escala = figura['escala']
        
        glBegin(GL_LINES)
        # Normales en los ejes principales
        glVertex3f(pos[0], pos[1], pos[2])
        glVertex3f(pos[0] + escala[0], pos[1], pos[2])
        
        glVertex3f(pos[0], pos[1], pos[2])
        glVertex3f(pos[0], pos[1] + escala[1], pos[2])
        
        glVertex3f(pos[0], pos[1], pos[2])
        glVertex3f(pos[0], pos[1], pos[2] + escala[2])
        glEnd()
    
    glLineWidth(1)
    glEnable(GL_LIGHTING)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    if app.modo_juego:
        dibujar_escena_juego()
        glutSwapBuffers()
        return
    
    aplicar_eliminacion_ocultas()  # Aplicar configuraciones de eliminación
    
    if app.camara_actual is not None and app.camaras:
        cam = app.camaras[app.camara_actual]
        gluLookAt(cam['pos'][0], cam['pos'][1], cam['pos'][2],
                    cam['look_at'][0], cam['look_at'][1], cam['look_at'][2],
                    cam['up'][0], cam['up'][1], cam['up'][2])
    else:
        gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(app.angulo_x, 1, 0, 0)
        glRotatef(app.angulo_y, 0, 1, 0)
    
    dibujar_terreno()
    
    for i, cam in enumerate(app.camaras):
        seleccionada = (app.objeto_seleccionado == i and app.tipo_seleccion == 'camara')
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], 
                        cam['escala'], cam['rotacion'], seleccionada)
    
    for i, luz in enumerate(app.luces):
        seleccionada = (app.objeto_seleccionado == i and app.tipo_seleccion == 'luz')
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'],
                    luz['escala'], luz['rotacion'], seleccionada)
    
    for i, figura in enumerate(app.figuras):
        seleccionada = (app.objeto_seleccionado == i and app.tipo_seleccion == 'figura')
        if figura['tipo'] == 'carro':
            dibujar_carro(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], seleccionada)
        elif figura['tipo'] == 'arbol':
            dibujar_arbol(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], seleccionada)
        elif figura['tipo'] == 'arbusto':
            dibujar_arbusto(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], seleccionada)
        elif figura['tipo'] == 'casa':
            dibujar_casa(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], seleccionada)
        elif figura['tipo'] == 'montana':
            dibujar_montana(figura['pos'], figura['escala'], figura['rotacion'], figura['color'], seleccionada)
    
    dibujar_normales_objeto()  # Dibujar normales si están habilitadas
    
    dibujar_barra_herramientas()
    mostrar_coordenadas()
    
    glutSwapBuffers()

def idle():
    if app.ventana_activa and app.auto_rotar:
        app.angulo_y += app.velocidad_auto
        glutPostRedisplay()

def reshape(w, h):
    app.WIDTH, app.HEIGHT = max(1, w), max(1, h)
    glViewport(0, 0, app.WIDTH, app.HEIGHT)
    configurar_proyeccion()

def teclado(key, x, y):
    k = key.decode("utf-8").lower()
    
    if k == "\x1b":  # ESC para salir
        app.salir_ventana = True
        glutDestroyWindow(glutGetWindow())
        return
    
    # Resetear modos
    if k == ' ':  # Espacio para cancelar modo actual
        app.modal_placing = False
        app.selection_mode = False
        app.modo_edicion = None
        app.dragging = False
        app.rotando = False
        app.escalando = False
        app.cara_seleccionada = None
        app.submenu_textura_visible = False
        app.submenu_figuras_visible = False
        print("Modos reseteados")
    
    # Modos de edición
    if k == 'c':  # Colocar cámara
        app.modo_edicion = 'colocar_camara'
        app.modal_placing = True
        app.selection_mode = False
        app.submenu_textura_visible = False
        app.submenu_figuras_visible = False
        print("Modo: Colocar cámara - Click en el terreno")
    
    elif k == 'l':  # Colocar luz
        app.modo_edicion = 'colocar_luz'
        app.modal_placing = True
        app.selection_mode = False
        app.submenu_textura_visible = False
        app.submenu_figuras_visible = False
        print("Modo: Colocar luz - Click en el terreno")
    
    elif k == 'f':  # Colocar figura
        app.modo_edicion = 'colocar_figura'
        app.submenu_figuras_visible = True
        app.modal_placing = False
        app.selection_mode = False
        app.submenu_textura_visible = False
        print("Modo: Seleccionar figura a colocar")
    
    elif k == 's':  # Modo selección
        app.selection_mode = True
        app.modal_placing = False
        app.modo_edicion = None
        app.submenu_textura_visible = False
        app.submenu_figuras_visible = False
        print("Modo: Selección - Click derecho en objetos")
    
    # Transformación de objetos seleccionados
    if app.objeto_seleccionado is not None:
        if k == 'g':  # Mover
            app.dragging = True
            app.rotando = False
            app.escalando = False
            app.cara_seleccionada = None
            app.submenu_textura_visible = False
            app.submenu_figuras_visible = False
            print("Modo: Mover objeto (mouse o flechas)")
        elif k == 'r':  # Rotar
            app.rotando = True
            app.dragging = False
            app.escalando = False
            app.cara_seleccionada = None
            app.submenu_textura_visible = False
            app.submenu_figuras_visible = False
            print("Modo: Rotar objeto (flechas del teclado)")
        elif k == 'e':  # Escalar
            app.escalando = True
            app.dragging = False
            app.rotando = False
            app.submenu_textura_visible = False
            app.submenu_figuras_visible = False
            print("Modo: Escalar objeto (flechas o mouse)")
        elif k == 'x':  # Eliminar
            eliminar_objeto_seleccionado()
            app.submenu_textura_visible = False
            app.submenu_figuras_visible = False
            print("Objeto eliminado")
    
    # Visualización
    if k == 'v':  # Cambiar vista de cámara a libre
        if app.camara_actual is not None:
            app.camara_actual = None
            print("Vista libre activada")
        elif app.tipo_seleccion == 'camara' and app.objeto_seleccionado is not None:
            app.camara_actual = app.objeto_seleccionado
            print(f"Vista desde cámara {app.objeto_seleccionado}")
    
    elif k == '1':  # Toggle luces
        app.habilitar_luz = not app.habilitar_luz
        if app.habilitar_luz:
            glEnable(GL_LIGHTING)
        else:
            glDisable(GL_LIGHTING)
    
    elif k == '2':  # Cambiar modo de visualización
        app.modo_visualizacion = "wireframe" if app.modo_visualizacion == "solido" else "solido"
        print(f"Modo de visualización: {app.modo_visualizacion}")
    
    elif k == '3':  # Toggle textura
        app.textura_habilitada = not app.textura_habilitada
        print(f"Textura del terreno {'activada' if app.textura_habilitada else 'desactivada'}")
        if app.textura_habilitada and app.textura_terreno is None:
            aplicar_textura_objeto()
    
    elif k == '4':  # Toggle textura objetos
        app.textura_objetos_habilitada = not app.textura_objetos_habilitada
        print(f"Textura de objetos {'activada' if app.textura_objetos_habilitada else 'desactivada'}")
        if app.textura_objetos_habilitada and app.textura_figuras is None:
            aplicar_textura_objeto()

    elif k == '5':  # Toggle Z-buffer
        app.z_buffer_activo = not app.z_buffer_activo
        print(f"Z-Buffer {'activado' if app.z_buffer_activo else 'desactivado'}")
    
    elif k == '6':  # Toggle back-face culling
        app.back_face_culling = not app.back_face_culling
        print(f"Back-face culling {'activado' if app.back_face_culling else 'desactivado'}")
    
    elif k == '7':  # Toggle mostrar normales
        app.mostrar_normales = not app.mostrar_normales
        print(f"Mostrar normales {'activado' if app.mostrar_normales else 'desactivado'}")
    
    elif k == '8':  # Cambiar modo de visualización
        modos = ["solido", "wireframe", "puntos"]
        idx_actual = modos.index(app.modo_visualizacion)
        app.modo_visualizacion = modos[(idx_actual + 1) % len(modos)]
        print(f"Modo visualización: {app.modo_visualizacion}")
    
    glutPostRedisplay()

def teclado_especial(key, x, y):
    """Manejo de teclas especiales (flechas)"""
    if app.objeto_seleccionado is None:
        # Navegación normal si no hay objeto seleccionado
        if key == GLUT_KEY_UP:
            app.angulo_x -= 5
        elif key == GLUT_KEY_DOWN:
            app.angulo_x += 5
        elif key == GLUT_KEY_LEFT:
            app.angulo_y -= 5
        elif key == GLUT_KEY_RIGHT:
            app.angulo_y += 5
    else:
        # Transformaciones del objeto seleccionado
        if app.dragging:
            # Mover con flechas
            if key == GLUT_KEY_UP:
                mover_objeto_con_teclado(0, 0, -0.2)
            elif key == GLUT_KEY_DOWN:
                mover_objeto_con_teclado(0, 0, 0.2)
            elif key == GLUT_KEY_LEFT:
                mover_objeto_con_teclado(-0.2, 0, 0)
            elif key == GLUT_KEY_RIGHT:
                mover_objeto_con_teclado(0.2, 0, 0)
                
        elif app.rotando:
            # Rotar con flechas
            if key == GLUT_KEY_UP:
                rotar_objeto_con_teclado(5, 0, 0)
            elif key == GLUT_KEY_DOWN:
                rotar_objeto_con_teclado(-5, 0, 0)
            elif key == GLUT_KEY_LEFT:
                rotar_objeto_con_teclado(0, -5, 0)
            elif key == GLUT_KEY_RIGHT:
                rotar_objeto_con_teclado(0, 5, 0)
                
        elif app.escalando:
            # Escalar con flechas
            if key == GLUT_KEY_UP:
                escalar_objeto_con_teclado(1.1)
            elif key == GLUT_KEY_DOWN:
                escalar_objeto_con_teclado(0.9)
    
    glutPostRedisplay()

def mouse(btn, estado, x, y):
    app.mouse_anterior = (x, y)
    
    # Modo colocación de objetos (clic izquierdo)
    if app.modal_placing and btn == GLUT_LEFT_BUTTON and estado == GLUT_DOWN:
        pos = obtener_posicion_3d(x, y)
        if pos is None:
            print("No se puede determinar la posición del terreno")
            return
        
        app.punto_seleccionado = pos
        if app.modo_edicion == 'colocar_camara':
            agregar_camara(pos)
        elif app.modo_edicion == 'colocar_luz':
            agregar_luz(pos)
        elif app.modo_edicion == 'colocar_figura':
            # Esto se manejará en el submenú de figuras
            pass
        agregar_figura(pos,app.tipo_figura)
        app.modal_placing = False
        app.modo_edicion = None
        glutPostRedisplay()
        return
    
    # Selección con clic derecho
    elif btn == GLUT_RIGHT_BUTTON and estado == GLUT_DOWN:
        tipo, idx = seleccionar_objeto(x, y)
        if tipo:
            app.tipo_seleccion = tipo
            app.objeto_seleccionado = idx
            print(f"{tipo.capitalize()} {idx} seleccionado")
        else:
            app.objeto_seleccionado = None
            app.tipo_seleccion = None
            print("Selección cancelada")
        glutPostRedisplay()
        return
    
    # Clic izquierdo normal (para herramientas)
    elif btn == GLUT_LEFT_BUTTON and estado == GLUT_DOWN and not app.modal_placing:
        
        # Verificar clic en barra de herramientas
        if y < 40:
            if 10 <= x <= 110:  # Botón Seleccionar
                app.selection_mode = True
                app.modal_placing = False
                app.modo_edicion = None
                app.submenu_textura_visible = False
                app.submenu_figuras_visible = False
                print("Modo: Selección")
            elif 120 <= x <= 220:  # Botón Cámara
                app.modo_edicion = 'colocar_camara'
                app.modal_placing = True
                app.selection_mode = False
                app.submenu_textura_visible = False
                app.submenu_figuras_visible = False
                print("Modo: Colocar cámara")
            elif 230 <= x <= 330:  # Botón Luz
                app.modo_edicion = 'colocar_luz'
                app.modal_placing = True
                app.selection_mode = False
                app.submenu_textura_visible = False
                app.submenu_figuras_visible = False
                print("Modo: Colocar luz")
            elif 340 <= x <= 440:  # Botón Figuras
                app.submenu_figuras_visible = not app.submenu_figuras_visible
                app.submenu_textura_visible = False
            elif 450 <= x <= 550:  # Botón Textura
                app.submenu_textura_visible = not app.submenu_textura_visible
                app.submenu_figuras_visible = False
            elif 560 <= x <= 660:  # Botón Eliminar
                if app.objeto_seleccionado is not None:
                    eliminar_objeto_seleccionado()
                    print("Objeto eliminado")
            elif 670 <= x <= 770:  # Botón Vista Cam
                if app.tipo_seleccion == 'camara' and app.objeto_seleccionado is not None:
                    app.camara_actual = app.objeto_seleccionado
                    print(f"Vista desde cámara {app.objeto_seleccionado}")
            elif 780 <= x <= 880:  # Botón Vista Libre
                app.camara_actual = None
                print("Vista libre")
            elif 890 <= x <= 990:  # Botón Ocultas
                app.submenu_ocultas_visible = not app.submenu_ocultas_visible
                app.submenu_textura_visible = False
                app.submenu_figuras_visible = False
            elif 1000 <= x <= 1100:  # Botón Juego
                app.modo_juego = not app.modo_juego
                print(f"Modo juego {'activado' if app.modo_juego else 'desactivado'}")
                glutPostRedisplay()
            return
        
        # Submenú de figuras
        elif app.submenu_figuras_visible and 340 <= x <= 540 and 40 <= y <= 200:
            if 350 <= x <= 540:  # Ancho de las opciones
                if 60 <= y <= 80:  # Carro
                    app.modo_edicion = 'colocar_figura'
                    app.modal_placing = True
                    app.tipo_figura = 'carro'
                    app.submenu_figuras_visible = False
                    print("Modo: Colocar carro - Click en el terreno")
                elif 90 <= y <= 110:  # Árbol
                    app.modo_edicion = 'colocar_figura'
                    app.modal_placing = True
                    app.tipo_figura = 'arbol'
                    app.submenu_figuras_visible = False
                    print("Modo: Colocar árbol - Click en el terreno")
                elif 120 <= y <= 140:  # Arbusto
                    app.modo_edicion = 'colocar_figura'
                    app.modal_placing = True
                    app.tipo_figura = 'arbusto'
                    app.submenu_figuras_visible = False
                    print("Modo: Colocar arbusto - Click en el terreno")
                elif 150 <= y <= 170:  # Casa
                    app.modo_edicion = 'colocar_figura'
                    app.modal_placing = True
                    app.tipo_figura = 'casa'
                    app.submenu_figuras_visible = False
                    print("Modo: Colocar casa - Click en el terreno")
                elif 180 <= y <= 200:  # Montaña
                    app.modo_edicion = 'colocar_figura'
                    app.modal_placing = True
                    app.tipo_figura = 'montana'
                    app.submenu_figuras_visible = False
                    print("Modo: Colocar montaña - Click en el terreno")
            app.submenu_figuras_visible = False
            glutPostRedisplay()
            return
        
        # Submenú de ocultas
        elif app.submenu_ocultas_visible and 890 <= x <= 1070 and 40 <= y <= 160:
            if 900 <= x <= 1070:  # Ancho de las opciones
                if 55 <= y <= 65:  # Z-Buffer toggle
                    app.z_buffer_activo = not app.z_buffer_activo
                    print(f"Z-Buffer {'activado' if app.z_buffer_activo else 'desactivado'}")
                elif 75 <= y <= 85:  # Back-face culling toggle
                    app.back_face_culling = not app.back_face_culling
                    print(f"Back-face culling {'activado' if app.back_face_culling else 'desactivado'}")
                elif 95 <= y <= 105:  # Mostrar normales toggle
                    app.mostrar_normales = not app.mostrar_normales
                    print(f"Mostrar normales {'activado' if app.mostrar_normales else 'desactivado'}")
                elif 115 <= y <= 125:  # Modo wireframe
                    app.modo_visualizacion = "wireframe"
                    print("Modo: Wireframe")
                elif 135 <= y <= 145:  # Modo sólido
                    app.modo_visualizacion = "solido"
                    print("Modo: Sólido")
                elif 155 <= y <= 165:  # Modo puntos
                    app.modo_visualizacion = "puntos"
                    print("Modo: Puntos")
            app.submenu_ocultas_visible = False
            glutPostRedisplay()
            return
        
        # Submenú de textura
        elif app.submenu_textura_visible and 450 <= x <= 650 and 40 <= y <= 100:
            if 455 <= x <= 645:  # Área más amplia para las opciones
                if 45 <= y <= 65:  # Aplicar Color - área más amplia
                    aplicar_color_objeto()
                    app.submenu_textura_visible = False
                    glutPostRedisplay()
                    return
                elif 65 <= y <= 85:  # Aplicar Textura - área más amplia
                    aplicar_textura_objeto()
                    app.submenu_textura_visible = False
                    glutPostRedisplay()
                    return
            app.submenu_textura_visible = False
            glutPostRedisplay()
            return
        
        # Detectar cara para escalado si estamos en modo escalado
        if app.escalando:
            if app.tipo_seleccion == 'figura':
                app.cara_seleccionada = detectar_cara_figura(x, y)
            
            if app.cara_seleccionada:
                print(f"Dirección seleccionada para escalado: {app.cara_seleccionada}")
    
    # Liberación de botón
    elif btn == GLUT_LEFT_BUTTON and estado == GLUT_UP:
        if app.dragging:
            print("Movimiento finalizado")
        app.cara_seleccionada = None
        
    # Colocación de figuras después de seleccionar del submenú
    if app.modo_edicion == 'colocar_figura' and btn == GLUT_LEFT_BUTTON and estado == GLUT_DOWN:
        pos = obtener_posicion_3d(x, y)
        if pos is None:
            print("No se puede determinar la posición del terreno")
            return
        
        agregar_figura(pos, app.tipo_figura)
        glutPostRedisplay()

def motion(x, y):
    dx = x - app.mouse_anterior[0]
    dy = y - app.mouse_anterior[1]
    app.mouse_anterior = (x, y)
    
    # Mover objeto seleccionado
    if app.dragging and app.objeto_seleccionado is not None:
        pos = obtener_posicion_3d(x, y)
        if pos:
            if app.tipo_seleccion == 'camara':
                cam = app.camaras[app.objeto_seleccionado]
                altura_actual = cam['pos'][1]
                cam['pos'][0] = pos[0]
                cam['pos'][2] = pos[2]
                offset_x = cam['look_at'][0] - cam['pos'][0]
                offset_z = cam['look_at'][2] - cam['pos'][2]
                cam['look_at'][0] = pos[0] + offset_x
                cam['look_at'][2] = pos[2] + offset_z
                
            elif app.tipo_seleccion == 'luz':
                luz = app.luces[app.objeto_seleccionado]
                altura_actual = luz['pos'][1]
                luz['pos'][0] = pos[0]
                luz['pos'][2] = pos[2]
                configurar_luz(app.objeto_seleccionado)
                
            elif app.tipo_seleccion == 'figura':
                figura = app.figuras[app.objeto_seleccionado]
                figura['pos'][0] = pos[0]
                figura['pos'][1] = pos[1] if pos[1] > 0 else 0  # No permitir valores negativos en Y
                figura['pos'][2] = pos[2]
        
        glutPostRedisplay()
        return
    
    # Escalado por dirección específica
    elif app.escalando and app.cara_seleccionada:
        # Usar movimiento vertical del mouse para escalado
        escalar_objeto(app.cara_seleccionada, -dy)
        glutPostRedisplay()
        return
    
    # Rotación de la vista (si no hay objeto seleccionado y no estamos en modo arrastre)
    if (app.objeto_seleccionado is None and app.camara_actual is None and 
        not app.dragging and not app.modal_placing):
        app.angulo_y += dx * 0.5
        app.angulo_x -= dy * 0.5
        glutPostRedisplay()

def abrir_ventana_3d():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(app.WIDTH, app.HEIGHT)
    glutCreateWindow(b"Editor 3D Mejorado - Figuras Complejas")
    
    init()
    configurar_proyeccion()
    
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutSpecialFunc(teclado_especial)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutIdleFunc(idle)
    
    print("=== CONTROLES MEJORADOS ===")
    print("C - Colocar cámara")
    print("L - Colocar luz") 
    print("F - Colocar figura (carro, árbol, arbusto, casa, montaña)")
    print("S - Modo selección")
    print("Clic derecho - Seleccionar objeto")
    print("")
    print("=== TRANSFORMACIONES (con objeto seleccionado) ===")
    print("G - MOVER: Mouse o flechas del teclado")
    print("R - ROTAR: Flechas del teclado")  
    print("E - ESCALAR: Flechas (uniforme) o mouse en direcciones (no uniforme)")
    print("X - Eliminar objeto")
    print("")
    print("=== TEXTURAS ===")
    print("3 - Alternar textura del terreno")
    print("4 - Alternar textura de objetos")
    print("Click en botón Textura para:")
    print("  - Aplicar Color: Cambiar color del objeto seleccionado")
    print("  - Aplicar Textura: Cargar imagen como textura para el objeto")
    print("")
    print("=== OTROS ===")
    print("V - Cambiar vista cámara/libre")
    print("ESPACIO - Cancelar modo actual")
    print("ESC - Salir")
    
    while not app.salir_ventana:
        glutMainLoopEvent()
        idle()

if __name__ == "__main__":
    abrir_ventana_3d()