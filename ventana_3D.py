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
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, app.WIDTH, app.HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Fondo de la barra de herramientas
    glColor3f(0.15, 0.15, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(app.WIDTH, 0)
    glVertex2f(app.WIDTH, 50)
    glVertex2f(0, 50)
    glEnd()
    
    # Botones
    herramientas = [
        ("colocar_camara", "Cámara (C)", (0.2, 0.5, 0.8)),
        ("colocar_luz", "Luz (L)", (0.8, 0.8, 0.2)),
        ("seleccionar", "Seleccionar (S)", (0.8, 0.3, 0.8)),
        ("eliminar", "Eliminar (DEL)", (0.8, 0.2, 0.2)),
        ("prop_luz", "Prop. Luz (P)", (0.5, 0.5, 0.9))
    ]
    
    for i, (id, texto, color) in enumerate(herramientas):
        x = 10 + i * 150
        # Resaltar si está seleccionado
        if app.modo_edicion == id or (id == "eliminar" and app.objeto_seleccionado is not None) or (id == "prop_luz" and app.panel_luz_visible):
            glColor3f(0.4, 0.4, 0.4)
            glBegin(GL_QUADS)
            glVertex2f(x-2, 5)
            glVertex2f(x+142, 5)
            glVertex2f(x+142, 45)
            glVertex2f(x-2, 45)
            glEnd()
        
        # Botón
        glColor3f(*color)
        glBegin(GL_QUADS)
        glVertex2f(x, 10)
        glVertex2f(x+140, 10)
        glVertex2f(x+140, 40)
        glVertex2f(x, 40)
        glEnd()
        
        # Borde del botón
        glColor3f(0.9, 0.9, 0.9)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, 10)
        glVertex2f(x+140, 10)
        glVertex2f(x+140, 40)
        glVertex2f(x, 40)
        glEnd()
        
        # Texto
        glColor3f(1, 1, 1)
        glRasterPos2f(x+10, 28)
        for ch in texto:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Información de estado
    glColor3f(1, 1, 1)
    glRasterPos2f(650, 28)
    estado_texto = f"Modo: {app.modo_edicion if app.modo_edicion else 'navegación'}"
    if app.objeto_seleccionado is not None:
        estado_texto += f" | Seleccionado: {app.tipo_seleccion} {app.objeto_seleccionado}"
    for ch in estado_texto:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Ayuda rápida
    if app.show_help:
        glColor3f(0.8, 0.8, 0.8)
        glRasterPos2f(10, app.HEIGHT - 20)
        ayuda = "Teclas: C=Cámara, L=Luz, S=Seleccionar, DEL=Eliminar, P=Prop. Luz, H=Ayuda, ESC=Salir"
        for ch in ayuda:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
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

def display():
    if not app.ventana_activa:
        return
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Configurar vista según cámara seleccionada o vista por defecto
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
    
    dibujar_terreno()
    dibujar_ejes()
    dibujar_objeto()
    
    # Dibujar cámaras
    for i, cam in enumerate(app.camaras):
        seleccionada = (app.tipo_seleccion == 'camara' and app.objeto_seleccionado == i)
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], seleccionada)
    
    # Dibujar luces
    for i, luz in enumerate(app.luces):
        seleccionada = (app.tipo_seleccion == 'luz' and app.objeto_seleccionado == i)
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'], seleccionada)
    
    dibujar_barra_herramientas()
    dibujar_panel_luz()
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
    
    # Tecla de ayuda
    if k == 'h':
        app.show_help = not app.show_help
        glutPostRedisplay()
        return
    
    # Comando para salir (ESC)
    if k == "\x1b":  # ESC
        app.salir_ventana = True
        app.ventana_activa = False
        glutDestroyWindow(glutGetWindow())
        return
    
    # Atajos de teclado para modos
    if k == 'c':
        app.modo_edicion = 'colocar_camara'
        glutPostRedisplay()
        return
    elif k == 'l':
        app.modo_edicion = 'colocar_luz'
        glutPostRedisplay()
        return
    elif k == 's':
        app.modo_edicion = 'seleccionar'
        glutPostRedisplay()
        return
    elif k == 'p' and app.objeto_seleccionado is not None and app.tipo_seleccion == 'luz':
        app.panel_luz_visible = not app.panel_luz_visible
        if app.panel_luz_visible:
            luz = app.luces[app.objeto_seleccionado]
            app.color_luz_temp = luz['color'].copy()
            app.tipo_luz_temp = luz['tipo_luz']
            app.angulo_spot_temp = luz['angulo_spot']
            app.exponente_spot_temp = luz['exponente_spot']
        glutPostRedisplay()
        return
    
    # Tecla para eliminar objeto seleccionado
    if k == '\x7f':  # Tecla DEL
        eliminar_objeto_seleccionado()
        glutPostRedisplay()
        return
    
    # Controles en panel de luz
    if app.panel_luz_visible and app.objeto_seleccionado is not None and app.tipo_seleccion == 'luz':
        if app.tipo_luz_temp == 'spot':
            if k == 'w':
                app.angulo_spot_temp = min(90.0, app.angulo_spot_temp + 5.0)
            elif k == 's':
                app.angulo_spot_temp = max(0.0, app.angulo_spot_temp - 5.0)
            elif k == 'a':
                app.exponente_spot_temp = max(0.0, app.exponente_spot_temp - 1.0)
            elif k == 'd':
                app.exponente_spot_temp = min(128.0, app.exponente_spot_temp + 1.0)
        glutPostRedisplay()
        return
    
    # Comandos en modo selección
    if app.objeto_seleccionado is not None:
        if k == 'w':  # Mover arriba
            if app.tipo_seleccion == 'camara':
                app.camaras[app.objeto_seleccionado]['pos'][1] += 0.2
            else:
                app.luces[app.objeto_seleccionado]['pos'][1] += 0.2
        elif k == 's':  # Mover abajo
            if app.tipo_seleccion == 'camara':
                app.camaras[app.objeto_seleccionado]['pos'][1] -= 0.2
            else:
                app.luces[app.objeto_seleccionado]['pos'][1] -= 0.2
        elif k == 'a':  # Mover izquierda
            if app.tipo_seleccion == 'camara':
                app.camaras[app.objeto_seleccionado]['pos'][0] -= 0.2
            else:
                app.luces[app.objeto_seleccionado]['pos'][0] -= 0.2
        elif k == 'd':  # Mover derecha
            if app.tipo_seleccion == 'camara':
                app.camaras[app.objeto_seleccionado]['pos'][0] += 0.2
            else:
                app.luces[app.objeto_seleccionado]['pos'][0] += 0.2
        elif k == 'q':  # Mover atrás
            if app.tipo_seleccion == 'camara':
                app.camaras[app.objeto_seleccionado]['pos'][2] -= 0.2
            else:
                app.luces[app.objeto_seleccionado]['pos'][2] -= 0.2
        elif k == 'e':  # Mover adelante
            if app.tipo_seleccion == 'camara':
                app.camaras[app.objeto_seleccionado]['pos'][2] += 0.2
            else:
                app.luces[app.objeto_seleccionado]['pos'][2] += 0.2
        glutPostRedisplay()
        return
    
    # Cambiar cámara activa
    if k == 'm' and app.camaras:
        app.camara_actual = (app.camara_actual + 1) % len(app.camaras) if app.camara_actual is not None else 0
        glutPostRedisplay()
        return
    
    # Toggle luz
    if k == '1':
        app.habilitar_luz = not app.habilitar_luz
        glutPostRedisplay()
        return
    
    # Cambiar perspectiva/ortográfica
    if k == '2':
        app.modo_perspectiva = not app.modo_perspectiva
        configurar_proyeccion()
        glutPostRedisplay()
        return
    
    glutPostRedisplay()

def mouse(btn, estado, x, y):
    app.mouse_anterior = (x, y)
    
    # Solo procesar clics del botón izquierdo
    if btn != GLUT_LEFT_BUTTON or estado != GLUT_DOWN:
        return
    
    # Verificar clic en la barra de herramientas
    if y < 50:
        if 10 <= x <= 150:  # Botón Cámara
            app.modo_edicion = 'colocar_camara'
            app.objeto_seleccionado = None
            app.tipo_seleccion = None
        elif 160 <= x <= 300:  # Botón Luz
            app.modo_edicion = 'colocar_luz'
            app.objeto_seleccionado = None
            app.tipo_seleccion = None
        elif 310 <= x <= 450:  # Botón Seleccionar
            app.modo_edicion = 'seleccionar'
            app.objeto_seleccionado = None
            app.tipo_seleccion = None
        elif 460 <= x <= 600:  # Botón Eliminar
            if app.objeto_seleccionado is not None:
                eliminar_objeto_seleccionado()
        elif 610 <= x <= 750:  # Botón Propiedades Luz
            if app.objeto_seleccionado is not None and app.tipo_seleccion == 'luz':
                app.panel_luz_visible = not app.panel_luz_visible
                if app.panel_luz_visible:
                    luz = app.luces[app.objeto_seleccionado]
                    app.color_luz_temp = luz['color'].copy()
                    app.tipo_luz_temp = luz['tipo_luz']
                    app.angulo_spot_temp = luz['angulo_spot']
                    app.exponente_spot_temp = luz['exponente_spot']
        glutPostRedisplay()
        return
    
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