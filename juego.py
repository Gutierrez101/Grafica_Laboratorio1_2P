from OpenGL.GL import *



from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

# Variables de estado
carro_visible = False
arboles_visibles = False
carretera_visible = False
posicion_carro = [0, 0, 0]
rotacion_carro = 0
arboles = []
carretera_puntos = []

def inicializar_juego():
    global arboles, carretera_puntos
    # Generar algunos árboles aleatorios
    arboles = []
    for _ in range(5):
        x = random.uniform(-5, 5)
        z = random.uniform(-5, 5)
        arboles.append({
            'pos': (x, 0, z),
            'escala': random.uniform(0.5, 1.2),
            'angulo': random.uniform(0, 360),
            'iteraciones': random.randint(2, 4)
        })
    
    # Definir puntos de control para la carretera
    carretera_puntos = [
        (-8, 0.01, -5),
        (-4, 0.01, 0),
        (0, 0.01, -3),
        (4, 0.01, 0),
        (8, 0.01, -5)
    ]

def dibujar_carro(pos=(0, 0, 0), escala=(1, 1, 1), rotacion=(0, 0, 0)):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(rotacion[0], 1, 0, 0)
    glRotatef(rotacion[1], 0, 1, 0)
    glRotatef(rotacion[2], 0, 0, 1)
    glScalef(*escala)
    
    # Color del carro (rojo)
    glColor3f(0.8, 0.2, 0.2)
    
    # Cuerpo principal del carro
    glPushMatrix()
    glScalef(1.5, 0.5, 0.8)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Techo del carro
    glPushMatrix()
    glTranslatef(0, 0.4, 0)
    glScalef(0.8, 0.3, 0.6)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Ruedas
    glColor3f(0.1, 0.1, 0.1)  # Negro para las ruedas
    pos_ruedas = [
        (0.6, -0.3, 0.5),
        (-0.6, -0.3, 0.5),
        (0.6, -0.3, -0.5),
        (-0.6, -0.3, -0.5)
    ]
    
    for rueda_pos in pos_ruedas:
        glPushMatrix()
        glTranslatef(*rueda_pos)
        glutSolidTorus(0.05, 0.15, 10, 10)
        glPopMatrix()
    
    # Faros
    glColor3f(1.0, 1.0, 0.7)  # Amarillo claro para faros
    glPushMatrix()
    glTranslatef(0.8, 0, 0.3)
    glutSolidSphere(0.1, 10, 10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0.8, 0, -0.3)
    glutSolidSphere(0.1, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def dibujar_arbol_fractal(pos=(0, 0, 0), escala=1, angulo=0, iteraciones=3, longitud=1, grosor=0.1):
    def rama(iteracion, posicion, direccion, longitud_actual, grosor_actual):
        if iteracion <= 0:
            return
            
        # Calcular punto final de esta rama
        fin = (
            posicion[0] + longitud_actual * math.sin(math.radians(direccion[0])) * math.cos(math.radians(direccion[1])),
            posicion[1] + longitud_actual * math.sin(math.radians(direccion[1])),
            posicion[2] + longitud_actual * math.cos(math.radians(direccion[0])) * math.cos(math.radians(direccion[1]))
        )
        
        # Dibujar la rama
        glLineWidth(grosor_actual * 10)
        glBegin(GL_LINES)
        glVertex3f(*posicion)
        glVertex3f(*fin)
        glEnd()
        
        # Recursión para ramas hijas
        nuevas_direcciones = [
            (direccion[0] + random.randint(-30, 30), 
             max(min(direccion[1] + random.randint(-20, 10), 80), -80)),
            (direccion[0] + random.randint(-30, 30), 
             max(min(direccion[1] + random.randint(-20, 10), 80), -80))
        ]
        
        for nueva_dir in nuevas_direcciones:
            rama(iteracion-1, fin, (nueva_dir[0], nueva_dir[1]), 
                 longitud_actual * random.uniform(0.6, 0.8), 
                 grosor_actual * 0.7)
    
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(angulo, 0, 1, 0)
    glScalef(escala, escala, escala)
    
    glColor3f(0.4, 0.2, 0.1)  # Color marrón para el tronco
    rama(iteraciones, (0, 0, 0), (0, 90, 0), longitud, grosor)
    
    # Hojas (esfera en la parte superior)
    glColor3f(0.2, 0.6, 0.2)
    glTranslatef(0, longitud * 0.8, 0)
    glutSolidSphere(longitud * 0.3, 10, 10)
    
    glPopMatrix()

def dibujar_carretera_curva(puntos_control=None, ancho=1.0, segmentos=50):
    if puntos_control is None:
        puntos_control = carretera_puntos
    
    def curva_bezier(t, puntos):
        n = len(puntos) - 1
        x, y, z = 0, 0, 0
        
        for i, punto in enumerate(puntos):
            # Coeficiente binomial
            coef = math.factorial(n) / (math.factorial(i) * math.factorial(n - i))
            # Término de la curva de Bézier
            term = coef * (1 - t)**(n - i) * t**i
            x += term * punto[0]
            y += term * punto[1]
            z += term * punto[2]
        
        return (x, y, z)
    
    glColor3f(0.3, 0.3, 0.3)  # Color gris para la carretera
    
    # Dibujar la curva
    puntos_curva = []
    for i in range(segmentos + 1):
        t = i / segmentos
        punto = curva_bezier(t, puntos_control)
        puntos_curva.append(punto)
    
    # Dibujar la carretera como una serie de quads
    glBegin(GL_QUAD_STRIP)
    for i in range(len(puntos_curva)):
        if i < len(puntos_curva) - 1:
            dx = puntos_curva[i+1][0] - puntos_curva[i][0]
            dz = puntos_curva[i+1][2] - puntos_curva[i][2]
            angulo = math.atan2(dz, dx)
            
            # Puntos laterales
            x1 = puntos_curva[i][0] + math.sin(angulo) * ancho/2
            z1 = puntos_curva[i][2] - math.cos(angulo) * ancho/2
            x2 = puntos_curva[i][0] - math.sin(angulo) * ancho/2
            z2 = puntos_curva[i][2] + math.cos(angulo) * ancho/2
            
            glVertex3f(x1, puntos_curva[i][1] + 0.01, z1)
            glVertex3f(x2, puntos_curva[i][1] + 0.01, z2)
    
    glEnd()
    
    # Dibujar líneas divisorias
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_STRIP)
    for punto in puntos_curva:
        glVertex3f(punto[0], punto[1] + 0.02, punto[2])
    glEnd()
    glLineWidth(1.0)

def dibujar_opciones_juego():
    # Dibujar menú de opciones del juego
    glColor3f(1, 1, 1)
    glRasterPos2f(-0.9, 0.9)
    for c in "Opciones del Juego:":
        glutBitmapCharacter(GLUT_BITMAP9_HELVETICA_15, ord(c))

    glRasterPos2f(-0.9, 0.7)
    for c in "1. Crear carro":
        glutBitmapCharacter(GLUT_BITMAP9_HELVETICA_15, ord(c))

    glRasterPos2f(-0.9, 0.6)
    for c in "2. Crear arboles fractales":
        glutBitmapCharacter(GLUT_BITMAP9_HELVETICA_15, ord(c))

    glRasterPos2f(-0.9, 0.5)
    for c in "3. Mostrar/ocultar carretera":
        glutBitmapCharacter(GLUT_BITMAP9_HELVETICA_15, ord(c))

def manejar_opcion_juego(opcion):
    global carro_visible, arboles_visibles, carretera_visible, posicion_carro, rotacion_carro
    
    if opcion == 1:  # Crear carro
        carro_visible = not carro_visible
        if carro_visible:
            posicion_carro = [0, 0, 0]
            rotacion_carro = 0
    
    elif opcion == 2:  # Crear árboles fractales
        arboles_visibles = not arboles_visibles
        if arboles_visibles and not arboles:
            inicializar_juego()
    
    elif opcion == 3:  # Mostrar/ocultar carretera
        carretera_visible = not carretera_visible

def dibujar_escena_juego():
    # Dibujar carro si está visible
    if carro_visible:
        dibujar_carro(
            pos=(posicion_carro[0], posicion_carro[1] + 0.5, posicion_carro[2]),
            escala=(0.5, 0.5, 0.5),
            rotacion=(0, rotacion_carro, 0)
        )
    
    # Dibujar árboles si están visibles
    if arboles_visibles:
        for arbol in arboles:
            dibujar_arbol_fractal(
                pos=arbol['pos'],
                escala=arbol['escala'],
                angulo=arbol['angulo'],
                iteraciones=arbol['iteraciones']
            )
    
    # Dibujar carretera si está visible
    if carretera_visible:
        dibujar_carretera_curva()