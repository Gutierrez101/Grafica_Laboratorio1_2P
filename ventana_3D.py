from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
import sys
import math
import numpy as np

class AppState:
    def __init__(self):
        self.salir_ventana = False
        self.ventana_activa = True
        self.WIDTH, self.HEIGHT = 1200, 800

        self.punto_seleccionado = None
        self.modal_placing = False
        self.selection_mode = False

        self.modo_perspectiva = True
        self.zoom = 1.0
        self.angulo_x, self.angulo_y = 45.0, -45.0
        self.auto_rotar = False
        self.velocidad_auto = 0.2

        self.habilitar_luz = True  # Añadido para control de luces
        self.habilitar_sombra = True
        self.modo_dibujo = "cubo"
        self.modo_visualizacion = "solido"
        
        # Terreno
        self.tamanio_terreno = 20
        self.divisiones_terreno = 50
        self.color_terreno = (0.2, 0.25, 0.3)
        self.color_lineas = (0.4, 0.4, 0.4)
        
        # Cámaras - ahora con todos los campos necesarios
        self.camaras = [{
            'pos': [5, 5, 10],
            'look_at': [0, 0, 0],
            'up': [0.0, 1.0, 0.0],
            'es_vista_activa': False,
            'color': [0.2, 0.5, 0.8],
            'nombre': "Cámara Principal"
        }]
        self.camara_actual = None  # None = vista libre
        
        # Luces - limitado a 8 luces (GL_LIGHT0 a GL_LIGHT7)
        self.luces = [{
            'pos': [2.0, 5.0, 2.0, 1.0],
            'color': [1.0, 1.0, 1.0, 1.0],
            'tipo': GL_LIGHT0,
            'activa': True,
            'tipo_luz': 'puntual',
            'angulo_spot': 45.0,
            'exponente_spot': 2.0,
            'direccion': [0.0, -1.0, 0.0],
            'nombre': "Luz Principal"
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
        
        # UI
        self.show_help = False
        self.panel_luz_visible = False
        self.menu_contextual_visible = False
        self.menu_pos = (0, 0)

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
    if index < 0 or index >= len(app.luces) or app.luces[index]['tipo'] > GL_LIGHT7:
        return
    
    luz = app.luces[index]
    if luz['activa']:
        glEnable(luz['tipo'])
        # Configurar posición según tipo de luz
        if luz['tipo_luz'] == 'directional':
            pos = [luz['pos'][0], luz['pos'][1], luz['pos'][2], 0.0]  # W=0 para direccional
        else:
            pos = luz['pos'].copy()  # W=1 para puntual/spot
        
        glLightfv(luz['tipo'], GL_POSITION, pos)
        glLightfv(luz['tipo'], GL_DIFFUSE, luz['color'])
        
        if luz['tipo_luz'] == 'spot':
            glLightf(luz['tipo'], GL_SPOT_CUTOFF, luz['angulo_spot'])
            glLightfv(luz['tipo'], GL_SPOT_DIRECTION, luz['direccion'])
    else:
        glDisable(luz['tipo'])

def obtener_posicion_3d(x, y):
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    winY = float(viewport[3] - y)
    
    # Intersección con el plano Y=0 (terreno)
    pos = gluUnProject(x, winY, 0.0, modelview, projection, viewport)
    if pos:
        return pos
    
    # Si no funciona, probar con otro valor de Z
    return gluUnProject(x, winY, 0.5, modelview, projection, viewport)

def seleccionar_objeto(x, y):
    pos = obtener_posicion_3d(x, y)
    if not pos:
        return None, None
    
    # Verificar cámaras
    for i, cam in enumerate(app.camaras):
        distancia = math.sqrt((cam['pos'][0]-pos[0])**2 + 
                            (cam['pos'][1]-pos[1])**2 + 
                            (cam['pos'][2]-pos[2])**2)
        if distancia < 0.8:
            return 'camara', i
    
    # Verificar luces
    for i, luz in enumerate(app.luces):
        distancia = math.sqrt((luz['pos'][0]-pos[0])**2 + 
                            (luz['pos'][1]-pos[1])**2 + 
                            (luz['pos'][2]-pos[2])**2)
        if distancia < 0.8:
            return 'luz', i
    
    return None, None

def dibujar_luz(pos, color, tipo, seleccionada=False):
    glDisable(GL_LIGHTING)
    
    if seleccionada:
        glColor3f(1, 1, 0)  # Amarillo para seleccionada
    else:
        glColor3f(color[0], color[1], color[2])
    
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    
    if tipo == 'puntual':
        glutSolidSphere(0.3, 12, 12)
        glBegin(GL_LINES)
        for i in range(12):
            ang = i * 30 * math.pi / 180
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
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        glutWireCone(math.tan(math.radians(45)), 1.0, 10, 2)
        glPopMatrix()
    
    glPopMatrix()
    glEnable(GL_LIGHTING)


def dibujar_ejes():
    """Dibuja los ejes X (rojo), Y (verde) y Z (azul)"""
    glLineWidth(3.0)  # Grosor de línea más visible
    
    glBegin(GL_LINES)
    # Eje X (Rojo)
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(5.0, 0.0, 0.0)
    
    # Eje Y (Verde)
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 5.0, 0.0)
    
    # Eje Z (Azul)
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 5.0)
    glEnd()
    
    glLineWidth(1.0)  # Restablecer grosor de línea

def dibujar_terreno():
    """Dibuja un terreno cuadriculado similar al de Blender"""
    tamaño = app.tamanio_terreno
    divisiones = app.divisiones_terreno
    mitad = tamaño / 2
    
    # Dibujar superficie del terreno (relleno)
    glColor3f(*app.color_terreno)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glBegin(GL_QUADS)
    glVertex3f(-mitad, 0.0, -mitad)
    glVertex3f(mitad, 0.0, -mitad)
    glVertex3f(mitad, 0.0, mitad)
    glVertex3f(-mitad, 0.0, mitad)
    glEnd()
    
    # Dibujar cuadrícula (líneas)
    glColor3f(*app.color_lineas)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    
    # Líneas principales (más gruesas cada 5 divisiones)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    paso = tamaño / divisiones
    for i in range(0, divisiones + 1):
        if i % 5 == 0:  # Líneas principales
            x = -mitad + i * paso
            # Líneas paralelas al eje Z
            glVertex3f(x, 0.01, -mitad)
            glVertex3f(x, 0.01, mitad)
            # Líneas paralelas al eje X
            glVertex3f(-mitad, 0.01, x)
            glVertex3f(mitad, 0.01, x)
    glEnd()
    
    # Líneas secundarias (más delgadas)
    glLineWidth(0.5)
    glBegin(GL_LINES)
    for i in range(0, divisiones + 1):
        if i % 5 != 0:  # Líneas secundarias
            x = -mitad + i * paso
            # Líneas paralelas al eje Z
            glVertex3f(x, 0.01, -mitad)
            glVertex3f(x, 0.01, mitad)
            # Líneas paralelas al eje X
            glVertex3f(-mitad, 0.01, x)
            glVertex3f(mitad, 0.01, x)
    glEnd()
    
    # Restablecer valores por defecto
    glLineWidth(1.0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


def dibujar_camara(pos, look_at, up, seleccionada=False, es_vista_activa=False):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    
    dx = look_at[0]-pos[0]
    dz = look_at[2]-pos[2]
    if dx != 0 or dz != 0:
        angulo = math.degrees(math.atan2(dx, dz))
        glRotatef(angulo, 0, 1, 0)
    
    if es_vista_activa:
        glColor3f(0.0, 1.0, 0.0)  # Verde para cámara activa
    elif seleccionada:
        glColor3f(1.0, 1.0, 0.0)  # Amarillo para seleccionada
    else:
        glColor3f(0.2, 0.5, 0.8)  # Azul para normales

    glutSolidCube(0.5)
    
    # Lente de cámara
    glPushMatrix()
    glTranslatef(0, 0, -0.3)
    glColor3f(0.8, 0.8, 0.2)
    glutSolidCone(0.3, 0.5, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def agregar_camara(posicion):
    # Nueva cámara mirando hacia el centro de la escena
    nueva_camara = {
        'pos': [posicion[0], posicion[1], posicion[2]],
        'look_at': [0, 0, 0],
        'up': [0.0, 1.0, 0.0],
        'es_vista_activa': False,
        'color': [0.2, 0.5, 0.8],
        'nombre': f"Cámara {len(app.camaras)+1}"
    }
    app.camaras.append(nueva_camara)
    app.objeto_seleccionado = len(app.camaras) - 1
    app.tipo_seleccion = 'camara'
    print(f"Cámara colocada en {posicion}")

def agregar_luz(posicion):
    # Encuentra el siguiente GL_LIGHT disponible
    next_light = GL_LIGHT0 + len(app.luces)
    if next_light > GL_LIGHT7:
        print("No se pueden agregar más luces (límite de OpenGL)")
        return
    
    nueva_luz = {
        'pos': [posicion[0], posicion[1], posicion[2], 1.0],
        'color': [1.0, 1.0, 1.0, 1.0],
        'tipo': next_light,
        'activa': True,
        'tipo_luz': 'puntual',
        'angulo_spot': 45.0,
        'exponente_spot': 2.0,
        'direccion': [0.0, -1.0, 0.0],
        'nombre': f"Luz {len(app.luces)+1}"
    }
    app.luces.append(nueva_luz)
    app.objeto_seleccionado = len(app.luces) - 1
    app.tipo_seleccion = 'luz'
    configurar_luz(len(app.luces) - 1)
    print(f"Luz colocada en {posicion}")

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Configurar vista
    if app.camara_actual is not None and 0 <= app.camara_actual < len(app.camaras):
        cam = app.camaras[app.camara_actual]
        gluLookAt(cam['pos'][0], cam['pos'][1], cam['pos'][2],
                 cam['look_at'][0], cam['look_at'][1], cam['look_at'][2],
                 cam['up'][0], cam['up'][1], cam['up'][2])
    else:
        # Vista libre (modo editor)
        gluLookAt(5, 5, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(app.angulo_x, 1, 0, 0)
        glRotatef(app.angulo_y, 0, 1, 0)
    
    # Configurar luces
    if app.habilitar_luz:
        glEnable(GL_LIGHTING)
        for i in range(len(app.luces)):
            configurar_luz(i)
    else:
        glDisable(GL_LIGHTING)
    
    # Dibujar escena
    dibujar_terreno()
    dibujar_ejes()
    
    # Dibujar objetos
    for i, cam in enumerate(app.camaras):
        dibujar_camara(cam['pos'], cam['look_at'], cam['up'], 
                      app.objeto_seleccionado == i and app.tipo_seleccion == 'camara',
                      app.camara_actual == i)
    
    for i, luz in enumerate(app.luces):
        dibujar_luz(luz['pos'], luz['color'], luz['tipo_luz'],
                   app.objeto_seleccionado == i and app.tipo_seleccion == 'luz')
    
    glutSwapBuffers()

def teclado(key, x, y):
    k = key.decode("utf-8").lower()
    
    if k == "\x1b":  # ESC para salir
        app.salir_ventana = True
        glutDestroyWindow(glutGetWindow())
        return
    
    # Comandos generales
    if k == 'c':  # Colocar cámara
        app.modo_edicion = 'colocar_camara'
        app.modal_placing = True
        print("Click en el terreno para colocar cámara")
    
    elif k == 'l':  # Colocar luz
        app.modo_edicion = 'colocar_luz'
        app.modal_placing = True
        print("Click en el terreno para colocar luz")
    
    elif k == 'v' and app.tipo_seleccion == 'camara':  # Activar vista de cámara
        app.camara_actual = app.objeto_seleccionado
        print(f"Activada vista de {app.camaras[app.objeto_seleccionado]['nombre']}")
    
    elif k == '0':  # Volver a vista libre
        app.camara_actual = None
        print("Vista libre activada")
    
    elif k == '1':  # Alternar luces
        app.habilitar_luz = not app.habilitar_luz
        print(f"Luces {'activadas' if app.habilitar_luz else 'desactivadas'}")
    
    glutPostRedisplay()

def mouse(btn, estado, x, y):
    app.mouse_anterior = (x, y)
    
    if btn == GLUT_LEFT_BUTTON and estado == GLUT_DOWN:
        if app.modal_placing:
            pos = obtener_posicion_3d(x, y)
            if pos:
                if app.modo_edicion == 'colocar_camara':
                    agregar_camara(pos)
                elif app.modo_edicion == 'colocar_luz':
                    agregar_luz(pos)
                app.modal_placing = False
        else:
            # Selección normal
            tipo, idx = seleccionar_objeto(x, y)
            if tipo:
                app.tipo_seleccion = tipo
                app.objeto_seleccionado = idx
                print(f"{tipo.capitalize()} seleccionada")
    
    glutPostRedisplay()

def motion(x, y):
    dx = x - app.mouse_anterior[0]
    dy = y - app.mouse_anterior[1]
    app.mouse_anterior = (x, y)
    
    # Rotación de la vista en modo libre
    if app.camara_actual is None:
        app.angulo_y += dx * 0.5
        app.angulo_x -= dy * 0.5
        glutPostRedisplay()

def reshape(w, h):
    app.WIDTH, app.HEIGHT = max(1, w), max(1, h)
    glViewport(0, 0, app.WIDTH, app.HEIGHT)
    configurar_proyeccion()

def abrir_ventana_3d():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(app.WIDTH, app.HEIGHT)
    glutCreateWindow(b"Editor 3D Profesional")
    
    init()
    configurar_proyeccion()
    
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    
    glutMainLoop()

if __name__ == "__main__":
    abrir_ventana_3d()