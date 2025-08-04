# Ventana de visualización 3D con OpenGL - Versión Corregida
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
import sys
import math
import numpy as np

# Estados de la aplicación
class AppState:
    def __init__(self):
        self.salir_ventana = False
        self.ventana_activa = True
        self.WIDTH, self.HEIGHT = 1200, 800

        self.punto_seleccionado = None
        self.modal_placing = False
        self.selection_mode = False
        self.modo_edicion = None  # Agregar esta línea que faltaba

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
        
        # Objetos 3D
        self.objetos = []
        self.camaras = []
        self.luces = []
        self.cubos = []
        
        # Selección CORREGIDA
        self.objeto_seleccionado = None
        self.tipo_seleccion = None
        self.mouse_anterior = (0, 0)
        self.dragging = False
        self.rotando = False
        self.escalando = False
        
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

        # Propiedades temporales
        self.color_luz_temp = [1.0, 1.0, 1.0, 1.0]
        self.tipo_luz_temp = 'puntual'
        self.angulo_spot_temp = 45.0
        self.exponente_spot_temp = 2.0

        # Cámara actual
        self.camara_actual = None
        self.luz_actual = 0

app = AppState()

def init():
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    configurar_luz_global()
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)

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
    luz_id = GL_LIGHT1 + index  # Usar LIGHT1 en adelante para luces del usuario
    
    if luz['activa']:
        glEnable(luz_id)
    else:
        glDisable(luz_id)
    
    # Configurar posición/dirección según tipo de luz
    if luz['tipo_luz'] == 'directional':
        pos = [luz['pos'][0], luz['pos'][1], luz['pos'][2], 0.0]
    else:
        pos = [luz['pos'][0], luz['pos'][1], luz['pos'][2], 1.0]
    
    glLightfv(luz_id, GL_POSITION, pos)
    glLightfv(luz_id, GL_DIFFUSE, luz['color'])
    glLightfv(luz_id, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    
    # Configuraciones específicas para luz spot
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
    glColor3f(*app.color_terreno)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    tamaño = app.tamanio_terreno
    mitad = tamaño / 2
    
    # Dibujar el terreno como un gran cuadrado
    glBegin(GL_QUADS)
    glVertex3f(-mitad, 0, -mitad)
    glVertex3f(mitad, 0, -mitad)
    glVertex3f(mitad, 0, mitad)
    glVertex3f(-mitad, 0, mitad)
    glEnd()
    
    # Cuadrícula sobre el terreno
    glColor3f(*app.color_lineas)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    
    divisiones = app.divisiones_terreno
    paso = tamaño / divisiones

    # Líneas principales
    glLineWidth(1.5)
    glBegin(GL_LINES)
    for i in range(0, divisiones + 1, 5):
        x = i * paso - mitad
        glVertex3f(x, 0.01, -mitad)
        glVertex3f(x, 0.01, mitad)
        glVertex3f(-mitad, 0.01, x)
        glVertex3f(mitad, 0.01, x)
    glEnd()
    
    # Líneas secundarias
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

def dibujar_cubo(pos, escala=(1,1,1), rotacion=(0,0,0), seleccionado=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    if seleccionado:
        # Cubo seleccionado - BORDE ROJO
        glDisable(GL_LIGHTING)
        glColor3f(1, 0, 0)  # ROJO para selección
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        glutWireCube(1.0)
        glEnable(GL_LIGHTING)
        
        # Dibujar ejes de transformación
        glDisable(GL_LIGHTING)
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)  # Eje X
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)  # Eje Y
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)  # Eje Z
        glEnd()
        glEnable(GL_LIGHTING)
    else:
        # Cubo normal (gris)
        glColor3f(0.6, 0.6, 0.6)
        if app.modo_visualizacion == "wireframe":
            glutWireCube(1.0)
        else:
            glutSolidCube(1.0)
    
    glPopMatrix()

def dibujar_camara(pos, look_at, up, escala=(1,1,1), rotacion=(0,0,0), seleccionada=False):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    # Orientar cámara hacia look_at
    dx, dy, dz = look_at[0]-pos[0], look_at[1]-pos[1], look_at[2]-pos[2]
    angulo = math.degrees(math.atan2(dx, dz))
    glRotatef(angulo, 0, 1, 0)
    
    glDisable(GL_LIGHTING)
    
    if seleccionada:
        # Cámara seleccionada - BORDE ROJO
        glColor3f(1.0, 0.0, 0.0)  # ROJO para selección
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        
        # Dibujar ejes de transformación
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)  # Eje X
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)  # Eje Y
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)  # Eje Z
        glEnd()
    else:
        glColor3f(0.2, 0.2, 0.8)  # Azul normal
    
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
        # Luz seleccionada - BORDE ROJO
        glColor3f(1, 0, 0)  # ROJO para selección
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(4)
        glutWireSphere(0.25, 16, 16)
        
        # Dibujar ejes de transformación
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1.5, 0, 0)  # Eje X
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1.5, 0)  # Eje Y
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1.5)  # Eje Z
        glEnd()
    else:
        # Luz normal
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

    # Botones con estado visual
    botones = [
        ("Seleccionar", 10, app.selection_mode),
        ("Cámara", 120, app.modo_edicion == 'colocar_camara'),
        ("Luz", 230, app.modo_edicion == 'colocar_luz'),
        ("Cubo", 340, app.modo_edicion == 'colocar_cubo'),
        ("Eliminar", 450, False),
        ("Vista Cam", 560, app.camara_actual is not None),
        ("Vista Libre", 670, app.camara_actual is None),
        ("Mover", 780, app.dragging),
        ("Rotar", 890, app.rotando),
        ("Escalar", 1000, app.escalando)
    ]
    
    for nombre, x, activo in botones:
        # Color del botón según estado
        if activo:
            glColor3f(0.4, 0.6, 0.4)  # Verde si está activo
        else:
            glColor3f(0.22, 0.22, 0.32)  # Gris normal
        
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

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def obtener_posicion_3d(x, y):
    """FUNCIÓN CORREGIDA para obtener posición 3D desde coordenadas de pantalla"""
    # Configurar matrices como en display()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Aplicar la misma transformación de vista que en display()
    if app.camara_actual is not None and app.camaras:
        cam = app.camaras[app.camara_actual]
        gluLookAt(cam['pos'][0], cam['pos'][1], cam['pos'][2],
                 cam['look_at'][0], cam['look_at'][1], cam['look_at'][2],
                 cam['up'][0], cam['up'][1], cam['up'][2])
    else:
        gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(app.angulo_x, 1, 0, 0)
        glRotatef(app.angulo_y, 0, 1, 0)
    
    # Obtener matrices actuales
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    
    glPopMatrix()
    
    winY = float(viewport[3] - y)
    
    try:
        # Obtener dos puntos en el rayo de la cámara
        pos1 = gluUnProject(x, winY, 0.0, modelview, projection, viewport)
        pos2 = gluUnProject(x, winY, 1.0, modelview, projection, viewport)
        
        if pos1 and pos2:
            # Calcular intersección con el plano Y=0 (terreno)
            dir_ray = np.subtract(pos2, pos1)
            if abs(dir_ray[1]) > 1e-6:  # Evitar división por cero
                t = -pos1[1] / dir_ray[1]
                if t >= 0:  # Solo intersecciones hacia adelante
                    pos = np.add(pos1, np.multiply(dir_ray, t))
                    
                    # Limitar posición dentro del terreno
                    mitad = app.tamanio_terreno / 2
                    pos[0] = max(-mitad, min(mitad, pos[0]))
                    pos[1] = 0
                    pos[2] = max(-mitad, min(mitad, pos[2]))
                    return [pos[0], pos[1], pos[2]]
    except Exception as e:
        print(f"Error en obtener_posicion_3d: {e}")
    
    return None

def seleccionar_objeto(x, y):
    """Sistema mejorado de selección usando color picking"""
    # Configurar buffer de selección
    glSelectBuffer(512)
    glRenderMode(GL_SELECT)
    glInitNames()
    
    # Configurar vista para selección
    viewport = glGetIntegerv(GL_VIEWPORT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluPickMatrix(x, viewport[3]-y, 5, 5, viewport)
    
    # Misma proyección que en display()
    aspect = app.WIDTH / app.HEIGHT
    if app.modo_perspectiva:
        gluPerspective(45 * app.zoom, aspect, 0.1, 100.0)
    else:
        glOrtho(-5 * app.zoom, 5 * app.zoom, -5 * app.zoom, 5 * app.zoom, 0.1, 100.0)
    
    # Misma vista que en display()
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
    
    # Dibujar objetos con identificadores
    # Dibujar cámaras con ID
    for i, cam in enumerate(app.camaras):
        glPushName(1)  # Tipo cámara
        glPushName(i)  # Índice
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], cam['escala'], cam['rotacion'], False)
        glPopName()
        glPopName()
    
    # Dibujar luces con ID
    for i, luz in enumerate(app.luces):
        glPushName(2)  # Tipo luz
        glPushName(i)  # Índice
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'], luz['escala'], luz['rotacion'], False)
        glPopName()
        glPopName()
    
    # Dibujar cubos con ID
    for i, cubo in enumerate(app.cubos):
        glPushName(3)  # Tipo cubo
        glPushName(i)  # Índice
        dibujar_cubo(cubo['pos'], cubo['escala'], cubo['rotacion'], False)
        glPopName()
        glPopName()
    
    # Restaurar vista normal
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glFlush()
    
    # Procesar hits
    hits = glRenderMode(GL_RENDER)
    
    if hits:
        # Tomar el objeto más cercano
        hit = hits[0]
        if len(hit.names) >= 2:
            tipo = hit.names[0]
            idx = hit.names[1]
            
            if tipo == 1: return 'camara', idx
            elif tipo == 2: return 'luz', idx
            elif tipo == 3: return 'cubo', idx
    
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
            # Desactivar la luz antes de eliminarla
            luz_id = GL_LIGHT1 + app.objeto_seleccionado
            glDisable(luz_id)
            app.luces.pop(app.objeto_seleccionado)
    
    elif app.tipo_seleccion == 'cubo' and app.objeto_seleccionado is not None:
        if 0 <= app.objeto_seleccionado < len(app.cubos):
            app.cubos.pop(app.objeto_seleccionado)
    
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
        
        for char in texto:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Configurar vista
    if app.camara_actual is not None and app.camaras:
        cam = app.camaras[app.camara_actual]
        gluLookAt(cam['pos'][0], cam['pos'][1], cam['pos'][2],
                 cam['look_at'][0], cam['look_at'][1], cam['look_at'][2],
                 cam['up'][0], cam['up'][1], cam['up'][2])
    else:
        gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(app.angulo_x, 1, 0, 0)
        glRotatef(app.angulo_y, 0, 1, 0)
    
    # Dibujar terreno
    dibujar_terreno()
    
    # Dibujar todos los objetos
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
        dibujar_cubo(cubo['pos'], cubo['escala'], cubo['rotacion'], seleccionado)
    
    # UI
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
    
    # Comandos generales
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
        print("Modos reseteados")
    
    # Modos de edición
    if k == 'c':  # Colocar cámara
        app.modo_edicion = 'colocar_camara'
        app.modal_placing = True
        app.selection_mode = False
        print("Modo: Colocar cámara - Click en el terreno")
    
    elif k == 'l':  # Colocar luz
        app.modo_edicion = 'colocar_luz'
        app.modal_placing = True
        app.selection_mode = False
        print("Modo: Colocar luz - Click en el terreno")
    
    elif k == 'b':  # Colocar cubo
        app.modo_edicion = 'colocar_cubo'
        app.modal_placing = True
        app.selection_mode = False
        print("Modo: Colocar cubo - Click en el terreno")
    
    elif k == 's':  # Modo selección
        app.selection_mode = True
        app.modal_placing = False
        app.modo_edicion = None
        print("Modo: Selección - Click derecho en objetos")
    
    # Transformación de objetos seleccionados
    if app.objeto_seleccionado is not None:
        if k == 'g':  # Mover
            app.dragging = True
            app.rotando = False
            app.escalando = False
            print("Modo: Mover objeto")
        elif k == 'r':  # Rotar
            app.rotando = True
            app.dragging = False
            app.escalando = False
            print("Modo: Rotar objeto (WASD)")
        elif k == 'e':  # Escalar
            app.escalando = True
            app.dragging = False
            app.rotando = False
            print("Modo: Escalar objeto (WASD)")
        elif k == 'x':  # Eliminar
            eliminar_objeto_seleccionado()
            print("Objeto eliminado")
        
        # Rotación específica
        if app.rotando:
            if k == 'w':  # Rotar en X
                if app.tipo_seleccion == 'camara':
                    app.camaras[app.objeto_seleccionado]['rotacion'][0] += 5
                elif app.tipo_seleccion == 'luz':
                    app.luces[app.objeto_seleccionado]['rotacion'][0] += 5
                elif app.tipo_seleccion == 'cubo':
                    app.cubos[app.objeto_seleccionado]['rotacion'][0] += 5
            elif k == 's':  # Rotar en X (reverso)
                if app.tipo_seleccion == 'camara':
                    app.camaras[app.objeto_seleccionado]['rotacion'][0] -= 5
                elif app.tipo_seleccion == 'luz':
                    app.luces[app.objeto_seleccionado]['rotacion'][0] -= 5
                elif app.tipo_seleccion == 'cubo':
                    app.cubos[app.objeto_seleccionado]['rotacion'][0] -= 5
            elif k == 'a':  # Rotar en Y
                if app.tipo_seleccion == 'camara':
                    app.camaras[app.objeto_seleccionado]['rotacion'][1] += 5
                elif app.tipo_seleccion == 'luz':
                    app.luces[app.objeto_seleccionado]['rotacion'][1] += 5
                elif app.tipo_seleccion == 'cubo':
                    app.cubos[app.objeto_seleccionado]['rotacion'][1] += 5
            elif k == 'd':  # Rotar en Y (reverso)
                if app.tipo_seleccion == 'camara':
                    app.camaras[app.objeto_seleccionado]['rotacion'][1] -= 5
                elif app.tipo_seleccion == 'luz':
                    app.luces[app.objeto_seleccionado]['rotacion'][1] -= 5
                elif app.tipo_seleccion == 'cubo':
                    app.cubos[app.objeto_seleccionado]['rotacion'][1] -= 5
        
        # Escalado específico
        elif app.escalando:
            if k == 'w':  # Escalar más
                factor = 1.1
                if app.tipo_seleccion == 'camara':
                    for i in range(3):
                        app.camaras[app.objeto_seleccionado]['escala'][i] *= factor
                elif app.tipo_seleccion == 'luz':
                    for i in range(3):
                        app.luces[app.objeto_seleccionado]['escala'][i] *= factor
                elif app.tipo_seleccion == 'cubo':
                    for i in range(3):
                        app.cubos[app.objeto_seleccionado]['escala'][i] *= factor
            elif k == 's':  # Escalar menos
                factor = 0.9
                if app.tipo_seleccion == 'camara':
                    for i in range(3):
                        app.camaras[app.objeto_seleccionado]['escala'][i] *= factor
                elif app.tipo_seleccion == 'luz':
                    for i in range(3):
                        app.luces[app.objeto_seleccionado]['escala'][i] *= factor
                elif app.tipo_seleccion == 'cubo':
                    for i in range(3):
                        app.cubos[app.objeto_seleccionado]['escala'][i] *= factor
    
    # Navegación (solo si no hay objeto seleccionado)
    if not app.objeto_seleccionado and not app.rotando and not app.escalando:
        if k == 'w':  # Adelante
            app.angulo_x -= 5
        elif k == 's':  # Atrás
            app.angulo_x += 5
        elif k == 'a':  # Izquierda
            app.angulo_y -= 5
        elif k == 'd':  # Derecha
            app.angulo_y += 5
    
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
                print("Modo: Selección")
            elif 120 <= x <= 220:  # Botón Cámara
                app.modo_edicion = 'colocar_camara'
                app.modal_placing = True
                app.selection_mode = False
                print("Modo: Colocar cámara")
            elif 230 <= x <= 330:  # Botón Luz
                app.modo_edicion = 'colocar_luz'
                app.modal_placing = True
                app.selection_mode = False
                print("Modo: Colocar luz")
            elif 340 <= x <= 440:  # Botón Cubo
                app.modo_edicion = 'colocar_cubo'
                app.modal_placing = True
                app.selection_mode = False
                print("Modo: Colocar cubo")
            elif 450 <= x <= 550:  # Botón Eliminar
                if app.objeto_seleccionado is not None:
                    eliminar_objeto_seleccionado()
                    print("Objeto eliminado")
            elif 560 <= x <= 660:  # Botón Vista Cam
                if app.tipo_seleccion == 'camara' and app.objeto_seleccionado is not None:
                    app.camara_actual = app.objeto_seleccionado
                    print(f"Vista desde cámara {app.objeto_seleccionado}")
            elif 670 <= x <= 770:  # Botón Vista Libre
                app.camara_actual = None
                print("Vista libre")
            elif 780 <= x <= 880:  # Botón Mover
                if app.objeto_seleccionado is not None:
                    app.dragging = True
                    app.rotando = False
                    app.escalando = False
                    print("Modo: Mover")
            elif 890 <= x <= 990:  # Botón Rotar
                if app.objeto_seleccionado is not None:
                    app.rotando = True
                    app.dragging = False
                    app.escalando = False
                    print("Modo: Rotar")
            elif 1000 <= x <= 1100:  # Botón Escalar
                if app.objeto_seleccionado is not None:
                    app.escalando = True
                    app.dragging = False
                    app.rotando = False
                    print("Modo: Escalar")
            glutPostRedisplay()
            return
    
    # Liberación de botón
    elif btn == GLUT_LEFT_BUTTON and estado == GLUT_UP:
        if app.dragging:
            app.dragging = False
            print("Movimiento finalizado")

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
                # Mantener altura relativa
                altura_actual = cam['pos'][1]
                cam['pos'][0] = pos[0]
                cam['pos'][2] = pos[2]
                # Ajustar look_at manteniendo dirección
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
                cubo['pos'][2] = pos[2]
        
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
    glutCreateWindow(b"Editor 3D Corregido - Paint OpenGL")
    
    init()
    configurar_proyeccion()
    
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutIdleFunc(idle)
    
    print("=== CONTROLES ===")
    print("C - Colocar cámara")
    print("L - Colocar luz") 
    print("B - Colocar cubo")
    print("S - Modo selección")
    print("Clic derecho - Seleccionar objeto")
    print("G - Mover objeto seleccionado")
    print("R - Rotar objeto (WASD)")
    print("E - Escalar objeto (W/S)")
    print("X - Eliminar objeto")
    print("V - Cambiar vista cámara/libre")
    print("ESPACIO - Cancelar modo actual")
    print("ESC - Salir")
    
    while not app.salir_ventana:
        glutMainLoopEvent()
        idle()

if __name__ == "__main__":
    abrir_ventana_3d()