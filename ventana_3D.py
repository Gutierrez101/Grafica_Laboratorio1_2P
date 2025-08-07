# Ventana de visualización 3D con OpenGL - Versión Mejorada
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
import sys
import math
import numpy as np
from PIL import Image  # Para manejo de texturas
import tkinter as tk
from tkinter import colorchooser, filedialog

# Estados de la aplicación
class AppState:
    def __init__(self):
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
        self.cubos = []
        self.esferas = []
        self.torus = []
        
        # Texturas para objetos
        self.textura_cubo = None
        self.textura_esfera = None
        self.textura_torus = None
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
    glEnable(GL_LIGHTING)
    configurar_luz_global()
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)
    
    # Habilitar texturas
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

def dibujar_cubo(pos, escala=(1,1,1), rotacion=(0,0,0), seleccionado=False):
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
        glutWireCube(1.0)
        glEnable(GL_LIGHTING)
        
        # Dibujar ejes de transformación
        glDisable(GL_LIGHTING)
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        glEnable(GL_LIGHTING)
    else:
        if app.textura_cubo and app.textura_objetos_habilitada:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, app.textura_cubo)
            glColor3f(1, 1, 1)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.6, 0.6, 0.6)
        
        if app.modo_visualizacion == "wireframe":
            glutWireCube(1.0)
        else:
            glutSolidCube(1.0)
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()
    
    # Dibujar manipuladores de escalado si está seleccionado y en modo escalado
    if seleccionado and app.escalando and app.tipo_seleccion == 'cubo':
        dibujar_manipuladores_escalado(pos, escala)

def dibujar_esfera(pos, escala=(1,1,1), rotacion=(0,0,0), seleccionada=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    if seleccionada:
        glDisable(GL_LIGHTING)
        glColor3f(1, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        glutWireSphere(0.5, 20, 20)
        glEnable(GL_LIGHTING)
        
        # Dibujar ejes de transformación
        glDisable(GL_LIGHTING)
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        glEnable(GL_LIGHTING)
    else:
        if app.textura_esfera and app.textura_objetos_habilitada:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, app.textura_esfera)
            glColor3f(1, 1, 1)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.6, 0.2, 0.2)
        
        if app.modo_visualizacion == "wireframe":
            glutWireSphere(0.5, 20, 20)
        else:
            # Para esferas texturizadas necesitamos implementar nuestras propias coordenadas de textura
            if app.textura_esfera and app.textura_objetos_habilitada:
                quad = gluNewQuadric()
                gluQuadricTexture(quad, GL_TRUE)
                gluSphere(quad, 0.5, 20, 20)
                gluDeleteQuadric(quad)
            else:
                glutSolidSphere(0.5, 20, 20)
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def dibujar_torus(pos, escala=(1,1,1), rotacion=(0,0,0), seleccionado=False):
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
        glutWireTorus(0.2, 0.5, 20, 20)
        glEnable(GL_LIGHTING)
        
        # Dibujar ejes de transformación
        glDisable(GL_LIGHTING)
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
        glEnable(GL_LIGHTING)
    else:
        if app.textura_torus and app.textura_objetos_habilitada:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, app.textura_torus)
            glColor3f(1, 1, 1)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.2, 0.6, 0.2)
        
        if app.modo_visualizacion == "wireframe":
            glutWireTorus(0.2, 0.5, 20, 20)
        else:
            glutSolidTorus(0.2, 0.5, 20, 20)
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def dibujar_camara(pos, look_at, up, escala=(1,1,1), rotacion=(0,0,0), seleccionada=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    dx, dy, dz = look_at[0]-pos[0], look_at[1]-pos[1], look_at[2]-pos[2]
    angulo = math.degrees(math.atan2(dx, dz))
    glRotatef(angulo, 0, 1, 0)
    
    glDisable(GL_LIGHTING)
    
    if seleccionada:
        glColor3f(1.0, 0.0, 0.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)
        glEnd()
    else:
        glColor3f(0.2, 0.2, 0.8)
    
    # Dibujar cuadrado (cuerpo de la cámara)
    glBegin(GL_QUADS)
    glVertex3f(-0.3, -0.3, 0)
    glVertex3f(0.3, -0.3, 0)
    glVertex3f(0.3, 0.3, 0)
    glVertex3f(-0.3, 0.3, 0)
    glEnd()
    
    # Dibujar círculo (lente)
    glColor3f(0.8, 0.8, 0.2)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, -0.1)
    for i in range(33):
        ang = i * 2 * math.pi / 32
        glVertex3f(0.15 * math.cos(ang), 0.15 * math.sin(ang), -0.1)
    glEnd()
    
    # Línea de visión
    glColor3f(1, 0, 0)
    glBegin(GL_LINES)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, -0.5)
    glEnd()
    
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

    # Botones (ahora incluyendo esfera y torus)
    botones = [
        ("Seleccionar", 10, app.selection_mode),
        ("Cámara", 120, app.modo_edicion == 'colocar_camara'),
        ("Luz", 230, app.modo_edicion == 'colocar_luz'),
        ("Cubo", 340, app.modo_edicion == 'colocar_cubo'),
        ("Esfera", 450, app.modo_edicion == 'colocar_esfera'),
        ("Torus", 560, app.modo_edicion == 'colocar_torus'),
        ("Textura", 670, False),
        ("Eliminar", 780, False),
        ("Vista Cam", 890, app.camara_actual is not None),
        ("Vista Libre", 1000, app.camara_actual is None)
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

    # Dibujar submenú de textura si está visible
    if app.submenu_textura_visible:
        glColor3f(0.3, 0.3, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(670, 40)
        glVertex2f(870, 40)
        glVertex2f(870, 80)
        glVertex2f(670, 80)
        glEnd()
        
        opciones = [
            ("Aplicar Color", 680, 50),
            ("Aplicar Textura", 680, 70)
        ]
        
        for texto, x, y in opciones:
            glColor3f(1, 1, 1)
            glRasterPos2f(x, y)
            for c in texto:
                glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
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
    
    for i, cam in enumerate(app.camaras):
        glPushName(1)
        glPushName(i)
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], cam['escala'], cam['rotacion'], False)
        glPopName()
        glPopName()
    
    for i, luz in enumerate(app.luces):
        glPushName(2)
        glPushName(i)
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'], luz['escala'], luz['rotacion'], False)
        glPopName()
        glPopName()
    
    for i, cubo in enumerate(app.cubos):
        glPushName(3)
        glPushName(i)
        dibujar_cubo(cubo['pos'], cubo['escala'], cubo['rotacion'], False)
        glPopName()
        glPopName()
    
    for i, esfera in enumerate(app.esferas):
        glPushName(4)
        glPushName(i)
        dibujar_esfera(esfera['pos'], esfera['escala'], esfera['rotacion'], False)
        glPopName()
        glPopName()
    
    for i, torus in enumerate(app.torus):
        glPushName(5)
        glPushName(i)
        dibujar_torus(torus['pos'], torus['escala'], torus['rotacion'], False)
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
            elif tipo == 3: return 'cubo', idx
            elif tipo == 4: return 'esfera', idx
            elif tipo == 5: return 'torus', idx
    
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
    
    elif app.tipo_seleccion == 'cubo' and app.objeto_seleccionado is not None:
        if 0 <= app.objeto_seleccionado < len(app.cubos):
            app.cubos.pop(app.objeto_seleccionado)
    
    elif app.tipo_seleccion == 'esfera' and app.objeto_seleccionado is not None:
        if 0 <= app.objeto_seleccionado < len(app.esferas):
            app.esferas.pop(app.objeto_seleccionado)
    
    elif app.tipo_seleccion == 'torus' and app.objeto_seleccionado is not None:
        if 0 <= app.objeto_seleccionado < len(app.torus):
            app.torus.pop(app.objeto_seleccionado)
    
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

def agregar_cubo(posicion):
    nuevo_cubo = {
        'pos': [posicion[0], 0.5, posicion[2]],
        'escala': [1.0, 1.0, 1.0],
        'rotacion': [0.0, 0.0, 0.0],
        'color': [0.8, 0.2, 0.2]
    }
    app.cubos.append(nuevo_cubo)
    app.objeto_seleccionado = len(app.cubos) - 1
    app.tipo_seleccion = 'cubo'
    print(f"Cubo agregado en: {posicion}")

def agregar_esfera(posicion):
    nueva_esfera = {
        'pos': [posicion[0], 0.5, posicion[2]],
        'escala': [1.0, 1.0, 1.0],
        'rotacion': [0.0, 0.0, 0.0],
        'color': [0.6, 0.2, 0.2]
    }
    app.esferas.append(nueva_esfera)
    app.objeto_seleccionado = len(app.esferas) - 1
    app.tipo_seleccion = 'esfera'
    print(f"Esfera agregada en: {posicion}")

def agregar_torus(posicion):
    nuevo_torus = {
        'pos': [posicion[0], 0.5, posicion[2]],
        'escala': [1.0, 1.0, 1.0],
        'rotacion': [0.0, 0.0, 0.0],
        'color': [0.2, 0.6, 0.2]
    }
    app.torus.append(nuevo_torus)
    app.objeto_seleccionado = len(app.torus) - 1
    app.tipo_seleccion = 'torus'
    print(f"Torus agregado en: {posicion}")

def detectar_cara_cubo(x, y):
    """Detectar qué cara del cubo se está seleccionando para escalado"""
    if app.tipo_seleccion != 'cubo' or app.objeto_seleccionado is None:
        return None
    
    cubo = app.cubos[app.objeto_seleccionado]
    pos_3d = obtener_posicion_3d(x, y)
    if pos_3d is None:
        return None
    
    # Determinar cara más cercana basada en la posición
    centro = cubo['pos']
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

def detectar_cara_esfera(x, y):
    """Detectar dirección de escalado para esfera"""
    if app.tipo_seleccion != 'esfera' or app.objeto_seleccionado is None:
        return None
    
    esfera = app.esferas[app.objeto_seleccionado]
    pos_3d = obtener_posicion_3d(x, y)
    if pos_3d is None:
        return None
    
    centro = esfera['pos']
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

def detectar_cara_torus(x, y):
    """Detectar dirección de escalado para torus"""
    if app.tipo_seleccion != 'torus' or app.objeto_seleccionado is None:
        return None
    
    torus = app.torus[app.objeto_seleccionado]
    pos_3d = obtener_posicion_3d(x, y)
    if pos_3d is None:
        return None
    
    centro = torus['pos']
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
    
    if app.tipo_seleccion == 'cubo':
        cubo = app.cubos[app.objeto_seleccionado]
        if cara == 'x+' or cara == 'x-':
            cubo['escala'][0] *= factor
            if cara == 'x+':
                cubo['pos'][0] += (factor - 1) * cubo['escala'][0] * 0.5
            else:
                cubo['pos'][0] -= (factor - 1) * cubo['escala'][0] * 0.5
        elif cara == 'y+' or cara == 'y-':
            cubo['escala'][1] *= factor
            if cara == 'y+':
                cubo['pos'][1] += (factor - 1) * cubo['escala'][1] * 0.5
            else:
                cubo['pos'][1] -= (factor - 1) * cubo['escala'][1] * 0.5
        elif cara == 'z+' or cara == 'z-':
            cubo['escala'][2] *= factor
            if cara == 'z+':
                cubo['pos'][2] += (factor - 1) * cubo['escala'][2] * 0.5
            else:
                cubo['pos'][2] -= (factor - 1) * cubo['escala'][2] * 0.5
    
    elif app.tipo_seleccion == 'esfera':
        esfera = app.esferas[app.objeto_seleccionado]
        if cara == 'x+' or cara == 'x-':
            esfera['escala'][0] *= factor
        elif cara == 'y+' or cara == 'y-':
            esfera['escala'][1] *= factor
        elif cara == 'z+' or cara == 'z-':
            esfera['escala'][2] *= factor
    
    elif app.tipo_seleccion == 'torus':
        torus = app.torus[app.objeto_seleccionado]
        if cara == 'x+' or cara == 'x-':
            torus['escala'][0] *= factor
        elif cara == 'y+' or cara == 'y-':
            torus['escala'][1] *= factor
        elif cara == 'z+' or cara == 'z-':
            torus['escala'][2] *= factor

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
            texto = f"Cámara seleccionada: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        elif app.tipo_seleccion == 'luz':
            pos = app.luces[app.objeto_seleccionado]['pos']
            texto = f"Luz seleccionada: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        elif app.tipo_seleccion == 'cubo':
            pos = app.cubos[app.objeto_seleccionado]['pos']
            texto = f"Cubo seleccionado: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        elif app.tipo_seleccion == 'esfera':
            pos = app.esferas[app.objeto_seleccionado]['pos']
            texto = f"Esfera seleccionada: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        elif app.tipo_seleccion == 'torus':
            pos = app.torus[app.objeto_seleccionado]['pos']
            texto = f"Torus seleccionado: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        
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
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

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
        
    elif app.tipo_seleccion == 'cubo':
        cubo = app.cubos[app.objeto_seleccionado]
        cubo['pos'][0] += dx
        cubo['pos'][1] += dy
        cubo['pos'][2] += dz
    
    elif app.tipo_seleccion == 'esfera':
        esfera = app.esferas[app.objeto_seleccionado]
        esfera['pos'][0] += dx
        esfera['pos'][1] += dy
        esfera['pos'][2] += dz
    
    elif app.tipo_seleccion == 'torus':
        torus = app.torus[app.objeto_seleccionado]
        torus['pos'][0] += dx
        torus['pos'][1] += dy
        torus['pos'][2] += dz

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
        
    elif app.tipo_seleccion == 'cubo':
        cubo = app.cubos[app.objeto_seleccionado]
        cubo['rotacion'][0] += rx
        cubo['rotacion'][1] += ry
        cubo['rotacion'][2] += rz
    
    elif app.tipo_seleccion == 'esfera':
        esfera = app.esferas[app.objeto_seleccionado]
        esfera['rotacion'][0] += rx
        esfera['rotacion'][1] += ry
        esfera['rotacion'][2] += rz
    
    elif app.tipo_seleccion == 'torus':
        torus = app.torus[app.objeto_seleccionado]
        torus['rotacion'][0] += rx
        torus['rotacion'][1] += ry
        torus['rotacion'][2] += rz

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
            
    elif app.tipo_seleccion == 'cubo':
        cubo = app.cubos[app.objeto_seleccionado]
        for i in range(3):
            cubo['escala'][i] *= factor
    
    elif app.tipo_seleccion == 'esfera':
        esfera = app.esferas[app.objeto_seleccionado]
        for i in range(3):
            esfera['escala'][i] *= factor
    
    elif app.tipo_seleccion == 'torus':
        torus = app.torus[app.objeto_seleccionado]
        for i in range(3):
            torus['escala'][i] *= factor

def aplicar_color_objeto():
    """Aplicar un color al objeto seleccionado"""
    if app.objeto_seleccionado is None:
        return
    
    # Abrir el selector de color
    color = colorchooser.askcolor(title="Seleccionar color")
    if color[0] is None:  # El usuario canceló
        return
    
    # Convertir el color de 0-255 a 0.0-1.0
    r, g, b = color[0]
    color_normalizado = (r/255.0, g/255.0, b/255.0)
    
    if app.tipo_seleccion == 'cubo':
        app.cubos[app.objeto_seleccionado]['color'] = color_normalizado
    elif app.tipo_seleccion == 'esfera':
        app.esferas[app.objeto_seleccionado]['color'] = color_normalizado
    elif app.tipo_seleccion == 'torus':
        app.torus[app.objeto_seleccionado]['color'] = color_normalizado
    
    print(f"Color aplicado: {color_normalizado}")

def aplicar_textura_objeto():
    """Aplicar una textura al objeto seleccionado"""
    if app.objeto_seleccionado is None:
        return
    
    # Abrir diálogo para seleccionar archivo
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Seleccionar textura", 
                                          filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if not file_path:
        return
    
    # Cargar la textura
    textura_id = cargar_textura(file_path)
    if textura_id is None:
        return
    
    # Asignar la textura al objeto correspondiente
    if app.tipo_seleccion == 'cubo':
        if app.textura_cubo:
            glDeleteTextures([app.textura_cubo])
        app.textura_cubo = textura_id
    elif app.tipo_seleccion == 'esfera':
        if app.textura_esfera:
            glDeleteTextures([app.textura_esfera])
        app.textura_esfera = textura_id
    elif app.tipo_seleccion == 'torus':
        if app.textura_torus:
            glDeleteTextures([app.textura_torus])
        app.textura_torus = textura_id
    
    print(f"Textura aplicada: {file_path}")

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
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
    
    dibujar_terreno()
    
    for i, cam in enumerate(app.camaras):
        seleccionada = (app.objeto_seleccionado == i and app.tipo_seleccion == 'camara')
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], 
                        cam['escala'], cam['rotacion'], seleccionada)
    
    for i, luz in enumerate(app.luces):
        seleccionada = (app.objeto_seleccionado == i and app.tipo_seleccion == 'luz')
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'],
                    luz['escala'], luz['rotacion'], seleccionada)
    
    for i, cubo in enumerate(app.cubos):
        seleccionado = (app.objeto_seleccionado == i and app.tipo_seleccion == 'cubo')
        glColor3f(*cubo['color'])
        dibujar_cubo(cubo['pos'], cubo['escala'], cubo['rotacion'], seleccionado)
    
    for i, esfera in enumerate(app.esferas):
        seleccionada = (app.objeto_seleccionado == i and app.tipo_seleccion == 'esfera')
        glColor3f(*esfera['color'])
        dibujar_esfera(esfera['pos'], esfera['escala'], esfera['rotacion'], seleccionada)
    
    for i, torus in enumerate(app.torus):
        seleccionado = (app.objeto_seleccionado == i and app.tipo_seleccion == 'torus')
        glColor3f(*torus['color'])
        dibujar_torus(torus['pos'], torus['escala'], torus['rotacion'], seleccionado)
    
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
        print("Modos reseteados")
    
    # Modos de edición
    if k == 'c':  # Colocar cámara
        app.modo_edicion = 'colocar_camara'
        app.modal_placing = True
        app.selection_mode = False
        app.submenu_textura_visible = False
        print("Modo: Colocar cámara - Click en el terreno")
    
    elif k == 'l':  # Colocar luz
        app.modo_edicion = 'colocar_luz'
        app.modal_placing = True
        app.selection_mode = False
        app.submenu_textura_visible = False
        print("Modo: Colocar luz - Click en el terreno")
    
    elif k == 'b':  # Colocar cubo
        app.modo_edicion = 'colocar_cubo'
        app.modal_placing = True
        app.selection_mode = False
        app.submenu_textura_visible = False
        print("Modo: Colocar cubo - Click en el terreno")
    
    elif k == 'p':  # Colocar esfera
        app.modo_edicion = 'colocar_esfera'
        app.modal_placing = True
        app.selection_mode = False
        app.submenu_textura_visible = False
        print("Modo: Colocar esfera - Click en el terreno")
    
    elif k == 't':  # Colocar torus
        app.modo_edicion = 'colocar_torus'
        app.modal_placing = True
        app.selection_mode = False
        app.submenu_textura_visible = False
        print("Modo: Colocar torus - Click en el terreno")
    
    elif k == 's':  # Modo selección
        app.selection_mode = True
        app.modal_placing = False
        app.modo_edicion = None
        app.submenu_textura_visible = False
        print("Modo: Selección - Click derecho en objetos")
    
    # Transformación de objetos seleccionados
    if app.objeto_seleccionado is not None:
        if k == 'g':  # Mover
            app.dragging = True
            app.rotando = False
            app.escalando = False
            app.cara_seleccionada = None
            app.submenu_textura_visible = False
            print("Modo: Mover objeto (mouse o flechas)")
        elif k == 'r':  # Rotar
            app.rotando = True
            app.dragging = False
            app.escalando = False
            app.cara_seleccionada = None
            app.submenu_textura_visible = False
            print("Modo: Rotar objeto (flechas del teclado)")
        elif k == 'e':  # Escalar
            app.escalando = True
            app.dragging = False
            app.rotando = False
            app.submenu_textura_visible = False
            print("Modo: Escalar objeto (flechas o mouse)")
        elif k == 'x':  # Eliminar
            eliminar_objeto_seleccionado()
            app.submenu_textura_visible = False
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
    
    elif k == '4':  # Toggle textura objetos
        app.textura_objetos_habilitada = not app.textura_objetos_habilitada
        print(f"Textura de objetos {'activada' if app.textura_objetos_habilitada else 'desactivada'}")
    
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
        elif app.modo_edicion == 'colocar_cubo':
            agregar_cubo(pos)
        elif app.modo_edicion == 'colocar_esfera':
            agregar_esfera(pos)
        elif app.modo_edicion == 'colocar_torus':
            agregar_torus(pos)
        
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
                print("Modo: Selección")
            elif 120 <= x <= 220:  # Botón Cámara
                app.modo_edicion = 'colocar_camara'
                app.modal_placing = True
                app.selection_mode = False
                app.submenu_textura_visible = False
                print("Modo: Colocar cámara")
            elif 230 <= x <= 330:  # Botón Luz
                app.modo_edicion = 'colocar_luz'
                app.modal_placing = True
                app.selection_mode = False
                app.submenu_textura_visible = False
                print("Modo: Colocar luz")
            elif 340 <= x <= 440:  # Botón Cubo
                app.modo_edicion = 'colocar_cubo'
                app.modal_placing = True
                app.selection_mode = False
                app.submenu_textura_visible = False
                print("Modo: Colocar cubo")
            elif 450 <= x <= 550:  # Botón Esfera
                app.modo_edicion = 'colocar_esfera'
                app.modal_placing = True
                app.selection_mode = False
                app.submenu_textura_visible = False
                print("Modo: Colocar esfera")
            elif 560 <= x <= 660:  # Botón Torus
                app.modo_edicion = 'colocar_torus'
                app.modal_placing = True
                app.selection_mode = False
                app.submenu_textura_visible = False
                print("Modo: Colocar torus")
            elif 670 <= x <= 770:  # Botón Textura
                app.submenu_textura_visible = not app.submenu_textura_visible
            elif 780 <= x <= 880:  # Botón Eliminar
                if app.objeto_seleccionado is not None:
                    eliminar_objeto_seleccionado()
                    print("Objeto eliminado")
            elif 890 <= x <= 990:  # Botón Vista Cam
                if app.tipo_seleccion == 'camara' and app.objeto_seleccionado is not None:
                    app.camara_actual = app.objeto_seleccionado
                    print(f"Vista desde cámara {app.objeto_seleccionado}")
            elif 1000 <= x <= 1100:  # Botón Vista Libre
                app.camara_actual = None
                print("Vista libre")
            glutPostRedisplay()
            return
        elif app.submenu_textura_visible and 670 <= x <= 870 and 40 <= y <= 80:
            # Submenú de textura
            if 680 <= x <= 830:  # Ancho aproximado de las opciones
                if 50 <= y <= 60:  # Aplicar Color
                    aplicar_color_objeto()
                elif 70 <= y <= 80:  # Aplicar Textura
                    aplicar_textura_objeto()
            app.submenu_textura_visible = False
            glutPostRedisplay()
            return
        
        # Detectar cara para escalado si estamos en modo escalado
        if app.escalando:
            if app.tipo_seleccion == 'cubo':
                app.cara_seleccionada = detectar_cara_cubo(x, y)
            elif app.tipo_seleccion == 'esfera':
                app.cara_seleccionada = detectar_cara_esfera(x, y)
            elif app.tipo_seleccion == 'torus':
                app.cara_seleccionada = detectar_cara_torus(x, y)
            
            if app.cara_seleccionada:
                print(f"Dirección seleccionada para escalado: {app.cara_seleccionada}")
    
    # Liberación de botón
    elif btn == GLUT_LEFT_BUTTON and estado == GLUT_UP:
        if app.dragging:
            print("Movimiento finalizado")
        app.cara_seleccionada = None

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
                
            elif app.tipo_seleccion == 'cubo':
                cubo = app.cubos[app.objeto_seleccionado]
                cubo['pos'][0] = pos[0]
                cubo['pos'][1] = pos[1] if pos[1] > 0 else 0  # No permitir valores negativos en Y
                cubo['pos'][2] = pos[2]
            
            elif app.tipo_seleccion == 'esfera':
                esfera = app.esferas[app.objeto_seleccionado]
                esfera['pos'][0] = pos[0]
                esfera['pos'][1] = pos[1] if pos[1] > 0 else 0  # No permitir valores negativos en Y
                esfera['pos'][2] = pos[2]
            
            elif app.tipo_seleccion == 'torus':
                torus = app.torus[app.objeto_seleccionado]
                torus['pos'][0] = pos[0]
                torus['pos'][1] = pos[1] if pos[1] > 0 else 0  # No permitir valores negativos en Y
                torus['pos'][2] = pos[2]
        
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
    glutCreateWindow(b"Editor 3D Mejorado - Transformaciones Directas")
    
    init()
    configurar_proyeccion()
    
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutSpecialFunc(teclado_especial)  # Agregar manejo de teclas especiales
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutIdleFunc(idle)
    
    print("=== CONTROLES MEJORADOS ===")
    print("C - Colocar cámara")
    print("L - Colocar luz") 
    print("B - Colocar cubo")
    print("P - Colocar esfera")
    print("T - Colocar torus (dona)")
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