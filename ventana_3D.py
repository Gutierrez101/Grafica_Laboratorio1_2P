# Ventana de visualización 3D con OpenGL - Versión Completa
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
import sys
import math
import numpy as np

# Estados de la aplicación
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


        self.punto_seleccionado=None
        self.modal_placing=False
        self.selection_mode=False

        self.modo_perspectiva = True
        self.zoom = 1.0
        self.angulo_x, self.angulo_y = 45.0, -45.0
        self.auto_rotar = False
        self.velocidad_auto = 0.2

        self.habilitar_luz = True
        self.habilitar_sombra = True
        self.modo_dibujo = "cubo"
        self.modo_visualizacion = "solido"
        
        # Terreno
        self.tamanio_terreno = 20
        self.divisiones_terreno = 50
        self.color_terreno = (0.2, 0.25, 0.3)  # Color azul-grisáceo
        self.color_lineas = (0.4, 0.4, 0.4)    # Color gris para las líneas
        
        # Cámaras
        self.camaras = []
        self.camara_actual = None
        
        # Luces
        self.luces = [{
            'pos': [2.0, 5.0, 2.0, 1.0],
            'color': [1.0, 1.0, 1.0, 1.0],
            'tipo': GL_LIGHT0,
            'activa': True,
            'tipo_luz': 'puntual',
            'angulo_spot': 45.0,
            'exponente_spot': 2.0,
            'direccion': [0.0, -1.0, 0.0]
        }]
        self.luz_actual = 0
        
        # Modos de edición
        self.modo_edicion = None
        self.objeto_seleccionado = None
        self.tipo_seleccion = None
        self.mouse_anterior = (0, 0)
        self.dragging = False
        self.rotando = False
        self.escalando = False
        
        # Menú contextual
        self.show_help=False
        self.panel_luz_visible=False
        self.menu_contextual_visible = False
        self.menu_pos = (0, 0)

        #Propiedades temporales
        self.color_luz_temp=[1.0,1.0,1.0,1.0]
        self.tipo_luz_temp='puntual'
        self.angulo_spot_temp=45.0
        self.exponente_spot_temp=2.0
        

        #Transformaciones
        self.centro_transformacion=None
        self.angulo_rotacion=0
        self.factor_escala=1.0

        self.opciones_menu = []

app = AppState()

def init():
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    configurar_luz(0)
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

def configurar_luz(index):
    if index < 0 or index >= len(app.luces):
        return
    
    luz = app.luces[index]
    if luz['activa']:
        glEnable(luz['tipo'])
    else:
        glDisable(luz['tipo'])
    
    # Configurar posición/dirección según tipo de luz
    if luz['tipo_luz'] == 'directional':
        pos = [luz['pos'][0], luz['pos'][1], luz['pos'][2], 0.0]  # W=0 para luz direccional
    else:
        pos = luz['pos'].copy()
    
    glLightfv(luz['tipo'], GL_POSITION, pos)
    glLightfv(luz['tipo'], GL_DIFFUSE, luz['color'])
    glLightfv(luz['tipo'], GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    
    # Configuraciones específicas para luz spot
    if luz['tipo_luz'] == 'spot':
        glLightf(luz['tipo'], GL_SPOT_CUTOFF, luz['angulo_spot'])
        glLightf(luz['tipo'], GL_SPOT_EXPONENT, luz['exponente_spot'])
        glLightfv(luz['tipo'], GL_SPOT_DIRECTION, luz['direccion'])

def mostrar_menu_contextual_luz(x, y):
    """Muestra el menú contextual para una luz seleccionada"""
    app.menu_contextual_visible = True
    app.menu_pos = (x, app.HEIGHT - y)
    luz = app.luces[app.objeto_seleccionado]
    
    app.opciones_menu = [
        f"Tipo: {luz['tipo_luz']}",
        "Cambiar color",
        f"Ángulo: {luz['angulo_spot']:.1f}°" if luz['tipo_luz'] == 'spot' else "",
        f"Intensidad: {luz['color'][0]:.1f}",
        "Activar" if not luz['activa'] else "Desactivar",
        "Cerrar"
    ]
    # Eliminar opciones vacías
    app.opciones_menu = [op for op in app.opciones_menu if op]

def dibujar_menu_contextual():
    """Dibuja el menú contextual en pantalla"""
    if not app.menu_contextual_visible:
        return
    
    x, y = app.menu_pos
    ancho = 200
    alto = 30 * len(app.opciones_menu)
    
    # Ajustar posición si el menú sale de la pantalla
    if x + ancho > app.WIDTH:
        x = app.WIDTH - ancho
    if y - alto < 0:
        y = alto
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, app.WIDTH, app.HEIGHT, 0)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Fondo del menú
    glColor3f(0.2, 0.2, 0.25)
    glBegin(GL_QUADS)
    glVertex2f(x, y - alto)
    glVertex2f(x + ancho, y - alto)
    glVertex2f(x + ancho, y)
    glVertex2f(x, y)
    glEnd()
    
    # Borde del menú
    glColor3f(0.5, 0.5, 0.6)
    glLineWidth(1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y - alto)
    glVertex2f(x + ancho, y - alto)
    glVertex2f(x + ancho, y)
    glVertex2f(x, y)
    glEnd()
    
    # Opciones del menú
    glColor3f(1, 1, 1)
    for i, opcion in enumerate(app.opciones_menu):
        glRasterPos2f(x + 10, y - alto + 25 + i * 30)
        for char in opcion:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def procesar_menu_contextual(x, y):
    """Procesa la selección en el menú contextual"""
    if not app.menu_contextual_visible or app.tipo_seleccion != 'luz':
        return
    
    x_click, y_click = x, app.HEIGHT - y
    menu_x, menu_y = app.menu_pos
    ancho = 200
    alto = 30 * len(app.opciones_menu)
    
    # Verificar si el clic fue dentro del menú
    if not (menu_x <= x_click <= menu_x + ancho and 
            menu_y - alto <= y_click <= menu_y):
        return
    
    # Determinar qué opción se seleccionó
    opcion_idx = (y_click - (menu_y - alto)) // 30
    if opcion_idx < 0 or opcion_idx >= len(app.opciones_menu):
        return
    
    luz = app.luces[app.objeto_seleccionado]
    opcion = app.opciones_menu[opcion_idx]
    
    if "Tipo:" in opcion:
        # Cambiar tipo de luz
        tipos = ['puntual', 'directional', 'spot']
        current_idx = tipos.index(luz['tipo_luz'])
        luz['tipo_luz'] = tipos[(current_idx + 1) % len(tipos)]
        configurar_luz(app.objeto_seleccionado)
    
    elif "Cambiar color" in opcion:
        # Cambiar color aleatorio
        luz['color'] = [np.random.random() for _ in range(3)] + [1.0]
        configurar_luz(app.objeto_seleccionado)
    
    elif "Ángulo:" in opcion and luz['tipo_luz'] == 'spot':
        # Aumentar ángulo del spot
        luz['angulo_spot'] = min(90, luz['angulo_spot'] + 5)
        configurar_luz(app.objeto_seleccionado)
    
    elif "Intensidad:" in opcion:
        # Ajustar intensidad
        for i in range(3):
            luz['color'][i] = min(1.0, luz['color'][i] + 0.1)
        configurar_luz(app.objeto_seleccionado)
    
    elif "Activar" in opcion or "Desactivar" in opcion:
        luz['activa'] = not luz['activa']
        configurar_luz(app.objeto_seleccionado)
    
    app.menu_contextual_visible = False
    glutPostRedisplay() 


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
    
    # Dibujar el terreno como un gran cuadrado en lugar de muchos pequeños
    glBegin(GL_QUADS)
    glVertex3f(-mitad, 0, -mitad)
    glVertex3f(mitad, 0, -mitad)
    glVertex3f(mitad, 0, mitad)
    glVertex3f(-mitad, 0, mitad)
    glEnd()
    
    # Cuadrícula sobre el terreno (estilo Blender)
    glColor3f(*app.color_lineas)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    
    divisiones=app.divisiones_terreno
    paso=tamaño/divisiones

    # Líneas principales (más gruesas)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    for i in range(0, divisiones + 1, 5):
        x = i * paso - mitad
        glVertex3f(x, 0.01, -mitad)
        glVertex3f(x, 0.01, mitad)
        glVertex3f(-mitad, 0.01, x)
        glVertex3f(mitad, 0.01, x)
    glEnd()
    
    # Líneas secundarias (más delgadas)
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


def dibujar_objeto():
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if app.modo_visualizacion == "wireframe" else GL_FILL)
    glColor3f(0.8, 0.2, 0.2)
    draw = {
        "cubo": glutSolidCube if app.modo_visualizacion == "solido" else glutWireCube,
        "esfera": glutSolidSphere if app.modo_visualizacion == "solido" else glutWireSphere,
        "cono": glutSolidCone if app.modo_visualizacion == "solido" else glutWireCone,
        "tetera": glutSolidTeapot if app.modo_visualizacion == "solido" else glutWireTeapot,
        "toro": glutSolidTorus if app.modo_visualizacion == "solido" else glutWireTorus,
    }[app.modo_dibujo]
    
    if app.modo_dibujo == "esfera":
        draw(1.0, 20, 20)
    elif app.modo_dibujo == "cono":
        draw(1.0, 2.0, 20, 20)
    elif app.modo_dibujo == "toro":
        draw(0.3, 1.0, 20, 20)
    else:
        draw(1.5 if app.modo_dibujo == "cubo" else 1.0)

def dibujar_camara(pos, look_at, up, seleccionada=False):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    
    # Dibujar cuerpo de la cámara
    glColor3f(0.0, 1.0, 0.0) if seleccionada else glColor3f(0.2, 0.2, 0.8)
    glutSolidCube(0.5)
    
    # Dibujar lente
    glPushMatrix()
    glTranslatef(0, 0, -0.3)
    glColor3f(0.8, 0.8, 0.2)
    glutSolidCone(0.3, 0.5, 10, 10)
    glPopMatrix()
    
    # Dibujar vector de dirección
    glBegin(GL_LINES)
    glColor3f(1, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(look_at[0]-pos[0], look_at[1]-pos[1], look_at[2]-pos[2])
    glEnd()
    
    glPopMatrix()

def dibujar_luz(pos, color, tipo, seleccionada=False):
    glDisable(GL_LIGHTING)
    
    # Color según selección
    if seleccionada:
        glColor3f(1, 1, 0)
    else:
        glColor3f(color[0], color[1], color[2])
    
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    
    # Representación visual según tipo de luz
    if tipo == 'puntual':
        glutSolidSphere(0.3, 12, 12)
        glBegin(GL_LINES)
        for i in range(12):
            ang = i * 30 * 3.1416 / 180
            glVertex3f(0, 0, 0)
            glVertex3f(0.8 * math.cos(ang), 0.8 * math.sin(ang), 0)
        glEnd()
    elif tipo == 'directional':
        glutSolidSphere(0.2, 10, 10)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, -1, 0)
        glEnd()
    elif tipo == 'spot':
        glutSolidSphere(0.25, 10, 10)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, -0.5, 0)
        glEnd()
        # Dibujar cono de luz spot
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        glutWireCone(math.tan(math.radians(app.angulo_spot_temp)), 1.0, 10, 2)
        glPopMatrix()
    
    glPopMatrix()
    if app.habilitar_luz:
        glEnable(GL_LIGHTING)

def dibujar_barra_herramientas():
    # Guardar la matriz de proyección actual
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, app.WIDTH, app.HEIGHT, 0)
    
    # Guardar la matriz de modelo-vista
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Deshabilitar características 3D
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Dibujar fondo de la barra
    glColor3f(0.1, 0.1, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(app.WIDTH, 0)
    glVertex2f(app.WIDTH, 30)
    glVertex2f(0, 30)
    glEnd()
    
    # Dibujar botones (ejemplo para el botón de cámara)
    herramientas = ["cámara", "luz", "seleccionar"]
    for i, herramienta in enumerate(herramientas):
        x = 10 + i * 100
        glColor3f(0.2, 0.4, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(x, 5)
        glVertex2f(x + 90, 5)
        glVertex2f(x + 90, 25)
        glVertex2f(x, 25)
        glEnd()
        
        # Texto
        glColor3f(1, 1, 1)
        glRasterPos2f(x + 10, 15)
        for char in herramienta:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    # Restaurar estado GL
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    # Restaurar matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def dibujar_panel_luz():
    if not app.panel_luz_visible or app.objeto_seleccionado is None or app.tipo_seleccion != 'luz':
        return
    
    luz = app.luces[app.objeto_seleccionado]
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, app.WIDTH, app.HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Fondo del panel
    glColor3f(0.1, 0.1, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(app.WIDTH-300, 50)
    glVertex2f(app.WIDTH-50, 50)
    glVertex2f(app.WIDTH-50, 350)
    glVertex2f(app.WIDTH-300, 350)
    glEnd()
    
    # Título
    glColor3f(1, 1, 1)
    glRasterPos2f(app.WIDTH-290, 70)
    for ch in f"Propiedades de Luz {app.objeto_seleccionado}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Selector de tipo de luz
    glColor3f(0.3, 0.3, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(app.WIDTH-290, 90)
    glVertex2f(app.WIDTH-60, 90)
    glVertex2f(app.WIDTH-60, 120)
    glVertex2f(app.WIDTH-290, 120)
    glEnd()
    
    glColor3f(1, 1, 1)
    glRasterPos2f(app.WIDTH-280, 110)
    for ch in f"Tipo: {app.tipo_luz_temp}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Selector de color
    glColor3f(app.color_luz_temp[0], app.color_luz_temp[1], app.color_luz_temp[2])
    glBegin(GL_QUADS)
    glVertex2f(app.WIDTH-290, 130)
    glVertex2f(app.WIDTH-60, 130)
    glVertex2f(app.WIDTH-60, 160)
    glVertex2f(app.WIDTH-290, 160)
    glEnd()
    
    glColor3f(1, 1, 1)
    glRasterPos2f(app.WIDTH-280, 150)
    for ch in "Color de Luz (click para cambiar)":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Controles para luz spot
    if app.tipo_luz_temp == 'spot':
        glColor3f(0.3, 0.3, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(app.WIDTH-290, 170)
        glVertex2f(app.WIDTH-60, 170)
        glVertex2f(app.WIDTH-60, 200)
        glVertex2f(app.WIDTH-290, 200)
        glEnd()
        
        glColor3f(1, 1, 1)
        glRasterPos2f(app.WIDTH-280, 190)
        for ch in f"Ángulo: {app.angulo_spot_temp:.1f} (W/S para ajustar)":
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
        
        glBegin(GL_QUADS)
        glVertex2f(app.WIDTH-290, 210)
        glVertex2f(app.WIDTH-60, 210)
        glVertex2f(app.WIDTH-60, 240)
        glVertex2f(app.WIDTH-290, 240)
        glEnd()
        
        glRasterPos2f(app.WIDTH-280, 230)
        for ch in f"Exponente: {app.exponente_spot_temp:.1f} (A/D para ajustar)":
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Botones
    glColor3f(0.2, 0.7, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(app.WIDTH-290, 270)
    glVertex2f(app.WIDTH-170, 270)
    glVertex2f(app.WIDTH-170, 310)
    glVertex2f(app.WIDTH-290, 310)
    glEnd()
    
    glColor3f(1, 1, 1)
    glRasterPos2f(app.WIDTH-260, 300)
    for ch in "Aplicar":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    glColor3f(0.7, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(app.WIDTH-160, 270)
    glVertex2f(app.WIDTH-60, 270)
    glVertex2f(app.WIDTH-60, 310)
    glVertex2f(app.WIDTH-160, 310)
    glEnd()
    
    glRasterPos2f(app.WIDTH-140, 300)
    for ch in "Cancelar":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def obtener_posicion_3d(x, y):
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    
    winY = float(viewport[3] - y)
    
    # Obtener posición en el plano Z=0
    pos = gluUnProject(x, winY, 0.0, modelview, projection, viewport)
    if pos:
        return pos
    
    # Si no funciona, probar con Z=0.5
    return gluUnProject(x, winY, 0.5, modelview, projection, viewport)

def seleccionar_objeto(x, y):
    pos = obtener_posicion_3d(x, y)
    if not pos:
        return None, None
    
    # Verificar cámaras (prioridad a selección)
    for i, cam in enumerate(app.camaras):
        distancia = math.sqrt((cam['pos'][0]-pos[0])**2 + 
                            (cam['pos'][1]-pos[1])**2 + 
                            (cam['pos'][2]-pos[2])**2)
        if distancia < 0.8:  # Radio de selección más grande
            return 'camara', i
    
    # Verificar luces
    for i, luz in enumerate(app.luces):
        distancia = math.sqrt((luz['pos'][0]-pos[0])**2 + 
                            (luz['pos'][1]-pos[1])**2 + 
                            (luz['pos'][2]-pos[2])**2)
        if distancia < 0.8:  # Radio de selección más grande
            return 'luz', i
    
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
            glDisable(app.luces[app.objeto_seleccionado]['tipo'])
            app.luces.pop(app.objeto_seleccionado)
            if app.luz_actual == app.objeto_seleccionado:
                app.luz_actual = 0 if app.luces else None
            elif app.luz_actual is not None and app.luz_actual > app.objeto_seleccionado:
                app.luz_actual -= 1
    
    app.objeto_seleccionado = None
    app.tipo_seleccion = None

def agregar_camara(posicion):
    nueva_camara = {
        'pos': [posicion[0], posicion[1], posicion[2]],
        'look_at': [posicion[0], posicion[1], posicion[2]-1],
        'up': [0.0, 1.0, 0.0]
    }
    app.camaras.append(nueva_camara)
    app.objeto_seleccionado = len(app.camaras) - 1
    app.tipo_seleccion = 'camara'

def agregar_luz(posicion):
    nueva_luz = {
        'pos': [posicion[0], posicion[1], posicion[2], 1.0],
        'color': [1.0, 1.0, 1.0, 1.0],
        'tipo': GL_LIGHT0 + len(app.luces),
        'activa': True,
        'tipo_luz': 'puntual'
    }
    app.luces.append(nueva_luz)
    app.objeto_seleccionado = len(app.luces) - 1
    app.tipo_seleccion = 'luz'


def mostrar_coordenadas():
    if app.objeto_seleccionado is not None:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, app.WIDTH, app.HEIGHT, 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glColor3f(1, 1, 1)
        glRasterPos2f(10, 30)
        
        if app.tipo_seleccion == 'camara':
            pos = app.camaras[app.objeto_seleccionado]['pos']
            texto = f"Cámara: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        else:
            pos = app.luces[app.objeto_seleccionado]['pos']
            texto = f"Luz: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f}"
        
        for char in texto:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        
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
    
    # Configurar luces
    if app.habilitar_luz:
        glEnable(GL_LIGHTING)
        for i, luz in enumerate(app.luces):
            if luz['activa']:
                configurar_luz(i)
    else:
        glDisable(GL_LIGHTING)
    
    # Dibujar escena
    dibujar_terreno()
    dibujar_ejes()
    dibujar_objeto()
    
    # Dibujar objetos
    for i, cam in enumerate(app.camaras):
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], 
                      app.objeto_seleccionado == i and app.tipo_seleccion == 'camara')
    
    for i, luz in enumerate(app.luces):
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'],
                   app.objeto_seleccionado == i and app.tipo_seleccion == 'luz')
    
    # Feedback visual para colocación
    if app.modal_placing:
        glDisable(GL_LIGHTING)
        glColor3f(1, 1, 0)  # Amarillo
        glBegin(GL_LINES)
        glVertex3f(-1, 0, 0)
        glVertex3f(1, 0, 0)
        glVertex3f(0, 0, -1)
        glVertex3f(0, 0, 1)
        glEnd()
        glEnable(GL_LIGHTING)
    
    # Dibujar UI
    dibujar_barra_herramientas()
    dibujar_menu_contextual()
    
    # Mostrar coordenadas del objeto seleccionado
    if app.objeto_seleccionado is not None:
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
    
    # Modos de edición
    if k == 'c':  # Colocar cámara
        app.modo_edicion = 'colocar_camara'
        app.modal_placing = True
        print("Click en el terreno para colocar cámara")
    
    elif k == 'l':  # Colocar luz
        app.modo_edicion = 'colocar_luz'
        app.modal_placing = True
        print("Click en el terreno para colocar luz")
    
    elif k == 's':  # Modo selección
        app.selection_mode = True
        app.modal_placing = False
        print("Modo selección activado")
    
    # Transformación de objetos seleccionados
    if app.objeto_seleccionado is not None:
        if k == 'g':  # Mover
            app.dragging = True
        elif k == 'r':  # Rotar
            app.rotando = True
        elif k == 's':  # Escalar
            app.escalando = True
        elif k == 'x':  # Eliminar
            eliminar_objeto_seleccionado()
    
    # Navegación
    if not app.objeto_seleccionado:
        if k == 'w':  # Adelante
            app.angulo_x -= 5
        elif k == 's':  # Atrás
            app.angulo_x += 5
        elif k == 'a':  # Izquierda
            app.angulo_y -= 5
        elif k == 'd':  # Derecha
            app.angulo_y += 5
    
    # Visualización
    if k == 'v':  # Cambiar vista
        app.modo_visualizacion = "wireframe" if app.modo_visualizacion == "solido" else "solido"
    elif k == '1':  # Luces
        app.habilitar_luz = not app.habilitar_luz
    
    glutPostRedisplay()

def mouse(btn, estado, x, y):
    app.mouse_anterior = (x, y)
    
    # Modo colocación de objetos (clic izquierdo)
    if app.modal_placing and btn == GLUT_LEFT_BUTTON and estado == GLUT_DOWN:
        pos = obtener_posicion_3d(x, y)
        if pos:
            app.punto_seleccionado = pos
            if app.modo_edicion == 'colocar_camara':
                agregar_camara(pos)
            elif app.modo_edicion == 'colocar_luz':
                agregar_luz(pos)
            app.modal_placing = False
        glutPostRedisplay()
        return
    
    # Selección con clic derecho
    elif btn == GLUT_RIGHT_BUTTON and estado == GLUT_DOWN:
        # Primero verificar si hay menú contextual abierto
        if app.menu_contextual_visible:
            procesar_menu_contextual(x, y)
            app.menu_contextual_visible = False
            glutPostRedisplay()
            return
        
        # Selección normal de objetos
        tipo, idx = seleccionar_objeto(x, y)
        if tipo:
            app.tipo_seleccion = tipo
            app.objeto_seleccionado = idx
            if tipo == 'luz':
                mostrar_menu_contextual_luz(x, y)
        else:
            app.objeto_seleccionado = None
            app.tipo_seleccion = None
        glutPostRedisplay()
        return
    
    # Clic izquierdo normal (para herramientas)
    elif btn == GLUT_LEFT_BUTTON and estado == GLUT_DOWN and not app.modal_placing:
        # Verificar clic en barra de herramientas
        if y < 30:
            if 10 <= x <= 150:  # Botón Cámara
                app.modo_edicion = 'colocar_camara'
                app.modal_placing = True
            elif 160 <= x <= 300:  # Botón Luz
                app.modo_edicion = 'colocar_luz'
                app.modal_placing = True
            elif 310 <= x <= 450:  # Botón Seleccionar
                app.selection_mode = True
                app.modal_placing = False
            glutPostRedisplay()
            return
        
        # Lógica para otras herramientas...
        pass
    
    # Liberación de botón
    elif btn == GLUT_LEFT_BUTTON and estado == GLUT_UP:
        app.dragging = False
        app.rotando = False
        app.escalando = False
    
    # Manejar clics en el panel de luz
    if app.panel_luz_visible and (app.WIDTH-300 <= x <= app.WIDTH-50) and (50 <= y <= 350):
        # Tipo de luz
        if 90 <= y <= 120:
            tipos = ['puntual', 'directional', 'spot']
            idx = tipos.index(app.tipo_luz_temp)
            app.tipo_luz_temp = tipos[(idx + 1) % len(tipos)]
        # Color de luz
        elif 130 <= y <= 160:
            app.color_luz_temp = [np.random.random(), np.random.random(), np.random.random(), 1.0]
        # Aplicar cambios
        elif 270 <= y <= 310 and app.WIDTH-290 <= x <= app.WIDTH-170:
            luz = app.luces[app.objeto_seleccionado]
            luz['color'] = app.color_luz_temp.copy()
            luz['tipo_luz'] = app.tipo_luz_temp
            luz['angulo_spot'] = app.angulo_spot_temp
            luz['exponente_spot'] = app.exponente_spot_temp
            configurar_luz(app.objeto_seleccionado)
            app.panel_luz_visible = False
        # Cancelar
        elif 270 <= y <= 310 and app.WIDTH-160 <= x <= app.WIDTH-60:
            app.panel_luz_visible = False
        glutPostRedisplay()
        return
    
    # Modo colocar cámara
    if app.modo_edicion == 'colocar_camara':
        pos = obtener_posicion_3d(x, y)
        if pos:
            nueva_camara = {
                'pos': [pos[0], pos[1], pos[2]],
                'look_at': [pos[0], pos[1], pos[2]-1],
                'up': [0.0, 1.0, 0.0]
            }
            app.camaras.append(nueva_camara)
            app.objeto_seleccionado = len(app.camaras) - 1
            app.tipo_seleccion = 'camara'
            glutPostRedisplay()
        return
    
    # Modo colocar luz
    if app.modo_edicion == 'colocar_luz':
        pos = obtener_posicion_3d(x, y)
        if pos:
            nueva_luz = {
                'pos': [pos[0], pos[1], pos[2], 1.0],
                'color': [1.0, 1.0, 1.0, 1.0],
                'tipo': GL_LIGHT0 + len(app.luces) if (GL_LIGHT0 + len(app.luces)) <= GL_LIGHT7 else GL_LIGHT0,
                'activa': True,
                'tipo_luz': 'puntual',
                'angulo_spot': 45.0,
                'exponente_spot': 2.0,
                'direccion': [0.0, -1.0, 0.0]
            }
            app.luces.append(nueva_luz)
            app.objeto_seleccionado = len(app.luces) - 1
            app.tipo_seleccion = 'luz'
            glutPostRedisplay()
        return
    
    # Modo selección
    if app.modo_edicion == 'seleccionar' or app.modo_edicion is None:
        tipo, idx = seleccionar_objeto(x, y)
        if tipo is not None:
            app.tipo_seleccion = tipo
            app.objeto_seleccionado = idx
            app.dragging = True
        else:
            app.objeto_seleccionado = None
            app.tipo_seleccion = None
        glutPostRedisplay()
        return

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
                cam['pos'][0] = pos[0]
                cam['pos'][1] = pos[1]
                cam['pos'][2] = pos[2]
            elif app.tipo_seleccion == 'luz':
                luz = app.luces[app.objeto_seleccionado]
                luz['pos'][0] = pos[0]
                luz['pos'][1] = pos[1]
                luz['pos'][2] = pos[2]
        glutPostRedisplay()
        return
    
    # Rotación de la vista (si no hay objeto seleccionado)
    if app.objeto_seleccionado is None:
        app.angulo_y += dx * 0.5
        app.angulo_x -= dy * 0.5
        glutPostRedisplay()

def abrir_ventana_3d():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(app.WIDTH, app.HEIGHT)
    glutCreateWindow(b"Editor 3D - Paint OpenGL")
    
    init()
    configurar_proyeccion()
    
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutIdleFunc(idle)
    
    while not app.salir_ventana:
        glutMainLoopEvent()
        idle()

if __name__ == "__main__":
    abrir_ventana_3d()