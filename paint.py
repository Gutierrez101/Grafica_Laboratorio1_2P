# Proyecto Paint con OpenGL y Pygame
# Computacion Grafica - ESPE

# Importaciones necesarias
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math  # Importar para el dibujo del circulo
import numpy as np  # Importar numpy para operaciones con matrices
from ventana_3D import abrir_ventana_3d  # Importar la ventana 3D para usarla en el paint
from numpy.linalg import inv

# Constantes
DENTRO = 0
IZQUIERDA = 1
DERECHA = 2
ABAJO = 4
ARRIBA = 8
SELECCIONAR = 'seleccionar'

# matriz de transformacion de traslacion
def crear_matriz_traslacion(tx, ty):
    return np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1]
    ])

# matriz de transformacion de rotacion
def crear_matriz_rotacion(angulo):
    rad = math.radians(angulo)
    cos = math.cos(rad)
    sin = math.sin(rad)
    return np.array([
        [cos, -sin, 0],
        [sin, cos, 0],
        [0, 0, 1]
    ])

# matriz de transformacion de escala
def crear_matriz_escala(sx, sy):
    return np.array([
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, 1]
    ])

def aplicar_transformacion(punto, matriz):
    x, y = punto
    punto_homogeneo = np.array([x, y, 1])
    transformado = matriz.dot(punto_homogeneo)
    return (transformado[0], transformado[1])

# Función para inicializar Pygame y OpenGL
def inicializar_pygame(ancho, alto):
    pygame.init()
    pantalla = pygame.display.set_mode((ancho, alto), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Paint OpenGL")
    
    glViewport(0, 0, ancho, alto)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, ancho, alto, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    return {
        'ancho': ancho,
        'alto': alto,
        'dibujando': False,
        'herramienta_actual': "lapiz",
        'tamanho_borrador': 15,
        'grosor_linea': 3,
        'puntos': [],
        'puntos_control': [],
        'pixeles_almacenados': [],
        'lineas_almacenadas': [],
        'curvas_almacenadas': [],
        'circulos_almacenados': [],
        'rectangulos_almacenados': [],
        'color_actual': (1.0, 0.0, 0.0),
        'mostrar_cuadricula': True,
        'tamanio_cuadricula': 20,
        'area_recorte': None,
        'area_recorte_temporal': None,
        'figura_seleccionada': None,
        'tipo_figura_seleccionada': None,
        'angulo_rotacion': 0,
        'factor_escala': 1.0,
        'modo_transformacion': None,
        'centro_transformacion': None
    }

# Función para dibujar la cuadrícula
def dibujar_cuadricula(estado):
    if not estado['mostrar_cuadricula']:
        return
    
    glColor3f(0.9, 0.9, 0.9)
    glLineWidth(1)
    glBegin(GL_LINES)
    
    for x in range(0, estado['ancho'], estado['tamanio_cuadricula']):
        glVertex2f(x, 40)
        glVertex2f(x, estado['alto'])
    
    for y in range(40, estado['alto'], estado['tamanio_cuadricula']):
        glVertex2f(0, y)
        glVertex2f(estado['ancho'], y)
    
    glEnd()

# Función para establecer el color actual
def establecer_color(estado, r, g, b):
    estado['color_actual'] = (r/255.0, g/255.0, b/255.0)
    return estado

# Establacer los pixeles de las figuras
def dibujar_pixel(estado, x, y, almacenar=True, color=None, tamanho=None):
    if color is None:
        color = estado['color_actual']
    if tamanho is None:
        tamanho = estado['grosor_linea']
    if almacenar:
        estado['pixeles_almacenados'].append((x, y, color, tamanho))
    glColor3f(*color)
    glPointSize(tamanho)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()
    glPointSize(1)
    return estado

# Borrar en un area los pixeles
def borrar_en(estado, x, y):
    mitad = estado['tamanho_borrador'] // 2
    estado['pixeles_almacenados'] = [
        (px, py, color, tamaño) for (px, py, color, tamaño) in estado['pixeles_almacenados']
        if not (x - mitad <= px <= x + mitad and y - mitad <= py <= y + mitad)
    ]
    estado['lineas_almacenadas'] = [
        linea for linea in estado['lineas_almacenadas']
        if not ((x - mitad <= linea[0] <= x + mitad and y - mitad <= linea[1] <= y + mitad) or
                (x - mitad <= linea[2] <= x + mitad and y - mitad <= linea[3] <= y + mitad))
    ]
    estado['circulos_almacenados'] = [
        circulo for circulo in estado['circulos_almacenados']
        if ((len(circulo) == 5 and not (x - mitad <= circulo[0] <= x + mitad and y - mitad <= circulo[1] <= y + mitad)))
        or (len(circulo) == 3 and not any(x - mitad <= px <= x + mitad and y - mitad <= py <= y + mitad for (px, py) in circulo[0]))
    ]
    estado['curvas_almacenadas'] = [
        curva for curva in estado['curvas_almacenadas']
        if not any(x - mitad <= px <= x + mitad and y - mitad <= py <= y + mitad for (px, py) in curva[0])
    ]
    estado['rectangulos_almacenados'] = [
        rect for rect in estado['rectangulos_almacenados']
        if not ((x - mitad <= rect[0] <= x + mitad and y - mitad <= rect[1] <= y + mitad) or
                (x - mitad <= rect[2] <= x + mitad and y - mitad <= rect[3] <= y + mitad))
    ]
    return estado

# Dibujar una linea con Bresenham
def dibujar_linea_bresenham(estado, x0, y0, x1, y1, almacenar=True):
    if almacenar:
        estado['lineas_almacenadas'].append((x0, y0, x1, y1, estado['color_actual'], estado['grosor_linea']))
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    empinada = dy > dx
    if empinada:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    error = dx // 2
    paso_y = 1 if y0 < y1 else -1
    y = y0
    
    glColor3f(*estado['color_actual'])
    glPointSize(estado['grosor_linea'])
    glBegin(GL_POINTS)
    for x in range(int(x0), int(x1) + 1):
        coord = (y, x) if empinada else (x, y)
        glVertex2f(coord[0], coord[1])
        error -= dy
        if error < 0:
            y += paso_y
            error += dx
    glEnd()
    glPointSize(1)
    return estado

# Dibujar un circulo con puntos y parametrizacion con angulos
def dibujar_circulo(estado, cx, cy, radio, segmentos=100, almacenar=True):
    if almacenar:
        estado['circulos_almacenados'].append((cx, cy, radio, estado['color_actual'], estado['grosor_linea']))
    
    glColor3f(*estado['color_actual'])
    glPointSize(estado['grosor_linea'])
    glBegin(GL_POINTS)
    for i in range(segmentos):
        angulo = 2 * math.pi * i / segmentos
        x = cx + radio * math.cos(angulo)
        y = cy + radio * math.sin(angulo)
        glVertex2f(x, y)
    glEnd()
    glPointSize(1)
    return estado

# Dibujar un rectangulo funcion deshabilidada
def dibujar_rectangulo(estado, x0, y0, x1, y1, almacenar=True):
    if almacenar:
        estado['rectangulos_almacenados'].append((x0, y0, x1, y1, estado['color_actual'], estado['grosor_linea']))
    glColor3f(*estado['color_actual'])
    glLineWidth(estado['grosor_linea'])
    glBegin(GL_LINE_LOOP)
    glVertex2f(x0, y0)
    glVertex2f(x1, y0)
    glVertex2f(x1, y1)
    glVertex2f(x0, y1)
    glEnd()
    glLineWidth(1)
    return estado

# Codigo de Cohen-Sutherland
def calcular_codigo(x, y, rectangulo_recorte):
    codigo = DENTRO
    if x < rectangulo_recorte[0]:
        codigo |= IZQUIERDA
    elif x > rectangulo_recorte[2]:
        codigo |= DERECHA
    if y < rectangulo_recorte[1]:
        codigo |= ABAJO
    elif y > rectangulo_recorte[3]:
        codigo |= ARRIBA
    return codigo

# Funcion de recorte (algoritmo de cohen-sutherland)
def recortar_linea_cohen_sutherland(x0, y0, x1, y1, rectangulo_recorte):
    codigo0 = calcular_codigo(x0, y0, rectangulo_recorte)
    codigo1 = calcular_codigo(x1, y1, rectangulo_recorte)
    aceptar = False
    while True:
        if not (codigo0 | codigo1):
            aceptar = True
            break
        elif codigo0 & codigo1:
            break
        else:
            x, y = 0, 0
            codigo_fuera = codigo0 if codigo0 else codigo1

            if codigo_fuera & ARRIBA:
                x = x0 + (x1 - x0) * (rectangulo_recorte[3] - y0) / (y1 - y0)
                y = rectangulo_recorte[3]
            elif codigo_fuera & ABAJO:
                x = x0 + (x1 - x0) * (rectangulo_recorte[1] - y0) / (y1 - y0)
                y = rectangulo_recorte[1]
            elif codigo_fuera & DERECHA:
                y = y0 + (y1 - y0) * (rectangulo_recorte[2] - x0) / (x1 - x0)
                x = rectangulo_recorte[2]
            elif codigo_fuera & IZQUIERDA:
                y = y0 + (y1 - y0) * (rectangulo_recorte[0] - x0) / (x1 - x0)
                x = rectangulo_recorte[0]

            if codigo_fuera == codigo0:
                x0, y0 = x, y
                codigo0 = calcular_codigo(x0, y0, rectangulo_recorte)
            else:
                x1, y1 = x, y
                codigo1 = calcular_codigo(x1, y1, rectangulo_recorte)

    if aceptar:
        return (x0, y0, x1, y1)
    return None

# Funciones para verificar los puntos que hay en las figuras
def punto_en_circulo(punto, centro, radio):
    distancia = math.hypot(punto[0] - centro[0], punto[1] - centro[1])
    return distancia <= radio

def punto_en_rectangulo(punto, rect):
    x, y = punto
    x0, y0, x1, y1 = rect
    return min(x0, x1) <= x <= max(x0, x1) and min(y0, y1) <= y <= max(y0, y1)

def punto_en_linea(punto, linea, umbral=5):
    x, y = punto
    x0, y0, x1, y1 = linea
    
    if x0 == x1 and y0 == y1:
        return math.hypot(x - x0, y - y0) <= umbral
    
    longitud = math.hypot(x1 - x0, y1 - y0)
    if longitud == 0:
        return math.hypot(x - x0, y - y0) <= umbral
    
    t = ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / (longitud ** 2)
    t = max(0, min(1, t))
    proy_x = x0 + t * (x1 - x0)
    proy_y = y0 + t * (y1 - y0)
    
    distancia = math.hypot(x - proy_x, y - proy_y)
    return distancia <= umbral

# Seleccionar una figura en el area de recorte 
def seleccionar_figura(estado, x, y):
    for i, circulo in enumerate(estado['circulos_almacenados']):
        cx, cy, radio, color, grosor = circulo
        if punto_en_circulo((x, y), (cx, cy), radio + grosor):
            return ('circulo', i)
    
    for i, rect in enumerate(estado['rectangulos_almacenados']):
        x0, y0, x1, y1, color, grosor = rect
        if punto_en_rectangulo((x, y), (x0, y0, x1, y1)):
            return ('rectangulo', i)
    
    for i, linea in enumerate(estado['lineas_almacenadas']):
        x0, y0, x1, y1, color, grosor = linea
        if punto_en_linea((x, y), (x0, y0, x1, y1), grosor + 2):
            return ('linea', i)
    
    for i, curva in enumerate(estado['curvas_almacenadas']):
        puntos_control, color, grosor = curva
        for px, py in puntos_control:
            if math.hypot(x - px, y - py) <= grosor + 5:
                return ('curva', i)
    
    return None

# Funcion de rotar en base a la matriz de transformacion segun el tipo de figura
# Se aplica una matriz de rotación en base al centro de la figura
def rotar_figura(estado, angulo):
    if not estado['figura_seleccionada']:
        return estado
    
    tipo, indice = estado['figura_seleccionada']
    
    if tipo == 'circulo':
        cx, cy, radio, color, grosor = estado['circulos_almacenados'][indice]
        centro_x, centro_y = cx, cy
        
        T1 = crear_matriz_traslacion(-centro_x, -centro_y)
        R = crear_matriz_rotacion(angulo)
        T2 = crear_matriz_traslacion(centro_x, centro_y)
        M = T2.dot(R).dot(T1)
        
        nuevo_cx, nuevo_cy = aplicar_transformacion((cx, cy), M)
        estado['circulos_almacenados'][indice] = (nuevo_cx, nuevo_cy, radio, color, grosor)
    
    elif tipo == 'rectangulo':
        x0, y0, x1, y1, color, grosor = estado['rectangulos_almacenados'][indice]
        centro_x = (x0 + x1) / 2
        centro_y = (y0 + y1) / 2
        
        T1 = crear_matriz_traslacion(-centro_x, -centro_y)
        R = crear_matriz_rotacion(angulo)
        T2 = crear_matriz_traslacion(centro_x, centro_y)
        M = T2.dot(R).dot(T1)
        
        x0n, y0n = aplicar_transformacion((x0, y0), M)
        x1n, y1n = aplicar_transformacion((x1, y1), M)
        
        estado['rectangulos_almacenados'][indice] = (x0n, y0n, x1n, y1n, color, grosor)
    
    elif tipo == 'linea':
        x0, y0, x1, y1, color, grosor = estado['lineas_almacenadas'][indice]
        centro_x = (x0 + x1) / 2
        centro_y = (y0 + y1) / 2
        
        T1 = crear_matriz_traslacion(-centro_x, -centro_y)
        R = crear_matriz_rotacion(angulo)
        T2 = crear_matriz_traslacion(centro_x, centro_y)
        M = T2.dot(R).dot(T1)
        
        x0n, y0n = aplicar_transformacion((x0, y0), M)
        x1n, y1n = aplicar_transformacion((x1, y1), M)
        
        estado['lineas_almacenadas'][indice] = (x0n, y0n, x1n, y1n, color, grosor)
    
    elif tipo == 'curva':
        puntos_control, color, grosor = estado['curvas_almacenadas'][indice]
        centro_x = sum(p[0] for p in puntos_control) / len(puntos_control)
        centro_y = sum(p[1] for p in puntos_control) / len(puntos_control)
        
        T1 = crear_matriz_traslacion(-centro_x, -centro_y)
        R = crear_matriz_rotacion(angulo)
        T2 = crear_matriz_traslacion(centro_x, centro_y)
        M = T2.dot(R).dot(T1)
        
        nuevos_puntos = [aplicar_transformacion(p, M) for p in puntos_control]
        estado['curvas_almacenadas'][indice] = (nuevos_puntos, color, grosor)
    
    return estado

# Escala la figura seleccionada dependiento de la figura
# Se aplica una matriz de escala en base al centro de la figura
# y se actualizan las coordenadas de la figura almacenada
def escalar_figura(estado, factor):
    if not estado['figura_seleccionada']:
        return estado
    
    tipo, indice = estado['figura_seleccionada']
    estado['factor_escala'] *= factor
    
    if tipo == 'circulo':
        cx, cy, radio, color, grosor = estado['circulos_almacenados'][indice]
        estado['circulos_almacenados'][indice] = (cx, cy, radio * factor, color, grosor)
    
    elif tipo == 'rectangulo':
        x0, y0, x1, y1, color, grosor = estado['rectangulos_almacenados'][indice]
        centro_x = (x0 + x1) / 2
        centro_y = (y0 + y1) / 2
        
        T1 = crear_matriz_traslacion(-centro_x, -centro_y)
        S = crear_matriz_escala(factor, factor)
        T2 = crear_matriz_traslacion(centro_x, centro_y)
        M = T2.dot(S).dot(T1)
        
        x0n, y0n = aplicar_transformacion((x0, y0), M)
        x1n, y1n = aplicar_transformacion((x1, y1), M)
        
        estado['rectangulos_almacenados'][indice] = (x0n, y0n, x1n, y1n, color, grosor)
    
    elif tipo == 'linea':
        x0, y0, x1, y1, color, grosor = estado['lineas_almacenadas'][indice]
        centro_x = (x0 + x1) / 2
        centro_y = (y0 + y1) / 2
        
        T1 = crear_matriz_traslacion(-centro_x, -centro_y)
        S = crear_matriz_escala(factor, factor)
        T2 = crear_matriz_traslacion(centro_x, centro_y)
        M = T2.dot(S).dot(T1)
        
        x0n, y0n = aplicar_transformacion((x0, y0), M)
        x1n, y1n = aplicar_transformacion((x1, y1), M)
        
        estado['lineas_almacenadas'][indice] = (x0n, y0n, x1n, y1n, color, grosor)
    
    elif tipo == 'curva':
        puntos_control, color, grosor = estado['curvas_almacenadas'][indice]
        centro_x = sum(p[0] for p in puntos_control) / len(puntos_control)
        centro_y = sum(p[1] for p in puntos_control) / len(puntos_control)
        
        T1 = crear_matriz_traslacion(-centro_x, -centro_y)
        S = crear_matriz_escala(factor, factor)
        T2 = crear_matriz_traslacion(centro_x, centro_y)
        M = T2.dot(S).dot(T1)
        
        nuevos_puntos = [aplicar_transformacion(p, M) for p in puntos_control]
        estado['curvas_almacenadas'][indice] = (nuevos_puntos, color, grosor)
    
    return estado

# Se aplica el recorte a las figuras y dependiedo de la figura se recorta de diferente manera
def aplicar_recorte(estado):
    if not estado['area_recorte']:
        return estado
    x0, y0, x1, y1 = estado['area_recorte']

    estado['pixeles_almacenados'] = [
        (x, y, color, tamanho) for (x, y, color, tamanho) in estado['pixeles_almacenados']
        if x0 <= x <= x1 and y0 <= y <= y1
    ]

    estado['lineas_almacenadas'] = [
        (nx0, ny0, nx1, ny1, color, grosor)
        for (x0_l, y0_l, x1_l, y1_l, color, grosor) in estado['lineas_almacenadas']
        if (resultado := recortar_linea_cohen_sutherland(x0_l, y0_l, x1_l, y1_l, estado['area_recorte']))
        for (nx0, ny0, nx1, ny1) in [resultado]
    ]

    nuevas_curvas = []
    for puntos_control, color, grosor in estado['curvas_almacenadas']:
        curva = calcular_curva_lagrange(puntos_control) if len(puntos_control) == 3 else puntos_control
        curva_recortada = [
            (x, y) for (x, y) in curva
            if x0 <= x <= x1 and y0 <= y <= y1
        ]
        if curva_recortada:
            nuevas_curvas.append((puntos_control, color, grosor))
    estado['curvas_almacenadas'] = nuevas_curvas

    nuevas_circulos = []
    for datos in estado['circulos_almacenados']:
        if len(datos) == 5:
            cx, cy, radio, color, grosor = datos
            puntos = []
            for i in range(100):
                angulo = 2 * math.pi * i / 100
                x = cx + radio * math.cos(angulo)
                y = cy + radio * math.sin(angulo)
                if x0 <= x <= x1 and y0 <= y <= y1:
                    puntos.append((x, y))
            if puntos:
                nuevas_circulos.append((puntos, color, grosor))
        elif len(datos) == 3:
            puntos, color, grosor = datos
            puntos_recortados = [(x, y) for (x, y) in puntos if x0 <= x <= x1 and y0 <= y <= y1]
            if puntos_recortados:
                nuevas_circulos.append((puntos_recortados, color, grosor))
    estado['circulos_almacenados'] = nuevas_circulos

    nuevas_rectangulos = []
    for x0_r, y0_r, x1_r, y1_r, color, grosor in estado['rectangulos_almacenados']:
        lados = [
            (x0_r, y0_r, x1_r, y0_r),
            (x1_r, y0_r, x1_r, y1_r),
            (x1_r, y1_r, x0_r, y1_r),
            (x0_r, y1_r, x0_r, y0_r),
        ]
        for lx0, ly0, lx1, ly1 in lados:
            rec = recortar_linea_cohen_sutherland(lx0, ly0, lx1, ly1, estado['area_recorte'])
            if rec:
                nuevas_rectangulos.append((*rec, color, grosor))
    estado['rectangulos_almacenados'] = []
    estado['lineas_almacenadas'].extend(nuevas_rectangulos)

    estado['area_recorte'] = None
    return estado

def dibujar_icono(herramienta, x):
    if herramienta == "lapiz":  # Icono de lápiz
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_POINTS)
        glVertex2f(x + 8, 30)  # ; glVertex2f(x + 22, 15)
        glEnd()
    elif herramienta == "linea":  # Icono de línea
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 5, 30)
        glVertex2f(x + 25, 10)
        glEnd()
    elif herramienta == "circulo":  # Icono de círculo
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        for i in range(20):
            angulo = 2 * math.pi * i / 20
            glVertex2f(x + 15 + 10 * math.cos(angulo), 20 + 10 * math.sin(angulo))
        glEnd()
    elif herramienta == "curva":  # Icono de curva
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_STRIP)
        for t in np.linspace(0, 1, 20):
            x0, y0 = x + 5, 30
            x1, y1 = x + 15, 10
            x2, y2 = x + 25, 30
            xt = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t ** 2 * x2
            yt = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t ** 2 * y2
            glVertex2f(xt, yt)
        glEnd()
    elif herramienta == "borrador":  # Icono de borrador
        glColor3f(1, 1, 1)
        glRecti(x + 7, 13, x + 23, 29)
        glColor3f(0, 0, 0)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 7, 13)
        glVertex2f(x + 23, 13)
        glVertex2f(x + 23, 29)
        glVertex2f(x + 7, 29)
        glEnd()
    elif herramienta == "rectangulo":  # Icono de rectángulo
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 8, 12, x + 22, 28)
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 8, 12)
        glVertex2f(x + 22, 12)
        glVertex2f(x + 22, 28)
        glVertex2f(x + 8, 28)
        glEnd()
    elif herramienta == "recortar":  # Icono de recorte
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 5, 10, x + 25, 30)
        glColor3f(1, 1, 1)
        glRecti(x + 10, 15, x + 20, 25)
        glColor3f(0, 0, 0)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 5, 10)
        glVertex2f(x + 25, 10)
        glVertex2f(x + 25, 30)
        glVertex2f(x + 5, 30)
        glEnd()
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 7, 12)
        glVertex2f(x + 13, 18)
        glVertex2f(x + 23, 12)
        glVertex2f(x + 17, 18)
        glVertex2f(x + 13, 18)
        glVertex2f(x + 15, 20)
        glVertex2f(x + 17, 18)
        glVertex2f(x + 15, 20)
        glEnd()
    elif herramienta == SELECCIONAR:
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 5, 5, x + 25, 35)
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 8, 25)
        glVertex2f(x + 15, 15)
        glVertex2f(x + 15, 15)
        glVertex2f(x + 22, 25)
        glVertex2f(x + 15, 15)
        glVertex2f(x + 15, 30)
        glEnd()
    elif herramienta == "ventana3d":
        # Icono 3D mejorado
        glColor3f(0.2, 0.2, 0.7)
        glRecti(x + 30, 5, x + 25, 35)
        glColor3f(1, 1, 1)
        glLineWidth(2)
        glBegin(GL_LINES)
        # Cubo en perspectiva
        glVertex2f(x + 10, 15)
        glVertex2f(x + 20, 15)  # Línea frontal inferior
        glVertex2f(x + 20, 15)
        glVertex2f(x + 20, 25)  # Línea frontal derecha
        glVertex2f(x + 20, 25)
        glVertex2f(x + 10, 25)  # Línea frontal superior
        glVertex2f(x + 10, 25)
        glVertex2f(x + 10, 15)  # Línea frontal izquierda
        
        # Líneas de profundidad
        glVertex2f(x + 10, 15)
        glVertex2f(x + 13, 12)
        glVertex2f(x + 20, 15)
        glVertex2f(x + 23, 12)
        glVertex2f(x + 20, 25)
        glVertex2f(x + 23, 22)
        glVertex2f(x + 10, 25)
        glVertex2f(x + 13, 22)
        
        # Líneas traseras
        glVertex2f(x + 13, 12)
        glVertex2f(x + 23, 12)
        glVertex2f(x + 23, 12)
        glVertex2f(x + 23, 22)
        glVertex2f(x + 23, 22)
        glVertex2f(x + 13, 22)
        glVertex2f(x + 13, 22)
        glVertex2f(x + 13, 12)
        glEnd()

# Dibuja la barra de herramientas con los iconos de las herramientas
def dibujar_barra_herramientas(estado):
    glColor3f(0.9, 0.9, 0.9)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(estado['ancho'], 0)
    glVertex2f(estado['ancho'], 40)
    glVertex2f(0, 40)
    glEnd()
    
    glColor3f(0.6, 0.6, 0.6)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(0, 40)
    glVertex2f(estado['ancho'], 40)
    glEnd()
    
    # Lista de herramientas actualizada con ventana3d
    herramientas = ["lapiz", "linea", "circulo", "curva", "borrador",
                   "rectangulo", "recortar", "ventana3d", SELECCIONAR]
    
    # Calcula espaciado dinámico
    espaciado = min(40, (estado['ancho'] - 20) // len(herramientas))
    
    for i, herramienta in enumerate(herramientas):
        x = 10 + i * espaciado
        if herramienta == estado['herramienta_actual']:
            glColor3f(0.7, 0.7, 0.9)
            glRecti(x - 2, 3, x + espaciado - 10, 37)
        glColor3f(0.8, 0.8, 0.8)
        glRecti(x, 5, x + espaciado - 12, 35)
        dibujar_icono(herramienta, x)

    # Colores - Posición fija después de los botones de herramientas
    colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
    colores_x = 10 + len(herramientas) * espaciado + 10  # Posición después de los botones de herramientas
    
    for i, (r, g, b) in enumerate(colores):
        cx = colores_x + i * 35  # Posición de cada color
        glColor3f(r / 255.0, g / 255.0, b / 255.0)
        glRecti(cx, 5, cx + 30, 35)  # Dibuja el color
        glColor3f(0.3, 0.3, 0.3)    # Color del borde (negro/gris)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)          # Dibuja el borde
        glVertex2f(cx, 5)
        glVertex2f(cx + 30, 5)
        glVertex2f(cx + 30, 35)
        glVertex2f(cx, 35)
        glEnd()

    # Texto de información
    glColor3f(0.2, 0.2, 0.2)
    glRasterPos2f(colores_x + len(colores) * 35 + 20, 25)
    texto = f"Grosor: {estado['grosor_linea']} (T/Shift+G para cambiar)"
    for char in texto:
        pygame.font.init()
        fuente = pygame.font.SysFont('Arial', 12)
        superficie_texto = fuente.render(char, True, (50, 50, 50))
        datos_textura = pygame.image.tostring(superficie_texto, "RGBA", True)
        glDrawPixels(superficie_texto.get_width(), superficie_texto.get_height(),
                    GL_RGBA, GL_UNSIGNED_BYTE, datos_textura)
        glRasterPos2f(glGetDoublev(GL_CURRENT_RASTER_POSITION)[0] + superficie_texto.get_width(), 25)

    if estado['figura_seleccionada']:
        glColor3f(0.2, 0.2, 0.2)
        glRasterPos2f(colores_x + len(colores) * 35 + 20, 10)
        texto = "R: Rotar | S: Escalar | Shift: Invertir"
        for char in texto:
            fuente = pygame.font.SysFont('Arial', 12)
            superficie_texto = fuente.render(char, True, (50, 50, 50))
            datos_textura = pygame.image.tostring(superficie_texto, "RGBA", True)
            glDrawPixels(superficie_texto.get_width(), superficie_texto.get_height(),
                        GL_RGBA, GL_UNSIGNED_BYTE, datos_textura)
            glRasterPos2f(glGetDoublev(GL_CURRENT_RASTER_POSITION)[0] + superficie_texto.get_width(), 10)

# Vuelve a dibujar todo
def redibujar_todo(estado):
    glClearColor(1, 1, 1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    dibujar_cuadricula(estado)
    
    # Dibuja los pixeles almacenados si es que existen
    for x, y, color, tamanho in estado['pixeles_almacenados']:
        dibujar_pixel(estado, x, y, almacenar=False, color=color, tamanho=tamanho)
    
    # Dibuja las líneas almacenadas si es que existen
    for i, (x0, y0, x1, y1, color, grosor) in enumerate(estado['lineas_almacenadas']):
        glColor3f(*color)
        glLineWidth(grosor)
        dibujar_linea_bresenham(estado, x0, y0, x1, y1, almacenar=False)
        
        if estado['figura_seleccionada'] and estado['figura_seleccionada'][0] == 'linea' and estado['figura_seleccionada'][1] == i:
            glColor3f(0, 1, 1)
            glLineWidth(grosor + 2)
            dibujar_linea_bresenham(estado, x0, y0, x1, y1, almacenar=False)
    
    # Dibuja las curvas almacenadas si es que existen
    for i, (pts, color, grosor) in enumerate(estado['curvas_almacenadas']):
        glColor3f(*color)
        glLineWidth(grosor)
        glBegin(GL_LINE_STRIP)
        curva = calcular_curva_lagrange(pts) if len(pts) == 3 else pts
        for x, y in curva:
            if not estado['area_recorte'] or (
                estado['area_recorte'][0] <= x <= estado['area_recorte'][2] and
                estado['area_recorte'][1] <= y <= estado['area_recorte'][3]
            ):
                glVertex2f(x, y)
        glEnd()
        glLineWidth(1)

    # Dibuja los círculos almacenados si es que existen
    for i, datos in enumerate(estado['circulos_almacenados']):
        if len(datos) == 5:
            cx, cy, radio, color, grosor = datos
            glColor3f(*color)
            glPointSize(grosor)
            glBegin(GL_POINTS)
            for j in range(100):
                angulo = 2 * math.pi * j / 100
                x = cx + radio * math.cos(angulo)
                y = cy + radio * math.sin(angulo)
                if not estado['area_recorte'] or (
                    estado['area_recorte'][0] <= x <= estado['area_recorte'][2] and
                    estado['area_recorte'][1] <= y <= estado['area_recorte'][3]
                ):
                    glVertex2f(x, y)
            glEnd()
            glPointSize(1)
        elif len(datos) == 3:
            puntos, color, grosor = datos
            glColor3f(*color)
            glPointSize(grosor)
            glBegin(GL_POINTS)
            for x, y in puntos:
                glVertex2f(x, y)
            glEnd()
            glPointSize(1)

    # Dibuja los rectángulos almacenados si es que existen
    for i, (x0, y0, x1, y1, color, grosor) in enumerate(estado['rectangulos_almacenados']):
        lados = [
            (x0, y0, x1, y0),
            (x1, y0, x1, y1),
            (x1, y1, x0, y1),
            (x0, y1, x0, y0),
        ]
        glColor3f(*color)
        glLineWidth(grosor)
        for lx0, ly0, lx1, ly1 in lados:
            if estado['area_recorte']:
                rec = recortar_linea_cohen_sutherland(lx0, ly0, lx1, ly1, estado['area_recorte'])
                if rec:
                    dibujar_linea_bresenham(estado, *rec, almacenar=False)
            else:
                dibujar_linea_bresenham(estado, lx0, ly0, lx1, ly1, almacenar=False)
    glLineWidth(1)

    # Dibuja el área de recorte con el raton
    if estado['area_recorte']:
        x0, y0, x1, y1 = estado['area_recorte']
        glColor3f(0.5, 0.5, 0.8)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x0, y0)
        glVertex2f(x1, y0)
        glVertex2f(x1, y1)
        glVertex2f(x0, y1)
        glEnd()
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.7, 0.7, 0.9, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(estado['ancho'], 0)
        glVertex2f(estado['ancho'], y0)
        glVertex2f(0, y0)
        glVertex2f(0, y0)
        glVertex2f(x0, y0)
        glVertex2f(x0, y1)
        glVertex2f(0, y1)
        glVertex2f(x1, y0)
        glVertex2f(estado['ancho'], y0)
        glVertex2f(estado['ancho'], y1)
        glVertex2f(x1, y1)
        glVertex2f(0, y1)
        glVertex2f(estado['ancho'], y1)
        glVertex2f(estado['ancho'], estado['alto'])
        glVertex2f(0, estado['alto'])
        glEnd()
        glDisable(GL_BLEND)
    
    # Dibuja el área de recorte temporal
    if estado['area_recorte_temporal'] and len(estado['area_recorte_temporal']) == 1:
        x0, y0 = estado['area_recorte_temporal'][0]
        x1, y1 = pygame.mouse.get_pos()
        glColor3f(0.5, 0.5, 0.8)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x0, y0)
        glVertex2f(x1, y0)
        glVertex2f(x1, y1)
        glVertex2f(x0, y1)
        glEnd()
    
    # Dibuja la barra de herramientas
    dibujar_barra_herramientas(estado)
    pygame.display.flip()
    return estado

# Algoritmo para dibujar una curva
def calcular_curva_lagrange(puntos_control, segmentos=100):
    if len(puntos_control) != 3:
        return []
    p0, p1, p2 = puntos_control
    curva = []
    for i in range(segmentos + 1):
        t = i / segmentos
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        curva.append((x, y))
    return curva

# Funcion principal
def main():
    estado = inicializar_pygame(1000, 600)
    estado = redibujar_todo(estado)
    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = evento.pos
                if y > 40:
                    estado['dibujando'] = True
                    if estado['herramienta_actual'] == "linea":
                        if not estado['puntos']:
                            estado['puntos'].append((x, y))
                        else:
                            x0, y0 = estado['puntos'][0]
                            estado = dibujar_linea_bresenham(estado, x0, y0, x, y)
                            estado['puntos'] = []
                            estado = redibujar_todo(estado)
                    elif estado['herramienta_actual'] == "circulo":
                        if not estado['puntos']:
                            estado['puntos'].append((x, y))
                        else:
                            x0, y0 = estado['puntos'][0]
                            radio = int(((x - x0) ** 2 + (y - y0) ** 2) ** 0.5)
                            estado = dibujar_circulo(estado, x0, y0, radio)
                            estado['puntos'] = []
                            estado = redibujar_todo(estado)
                    elif estado['herramienta_actual'] == "curva":
                        estado['puntos_control'].append((x, y))
                        if len(estado['puntos_control']) == 3:
                            curva = calcular_curva_lagrange(estado['puntos_control'])
                            estado['curvas_almacenadas'].append((curva, estado['color_actual'], estado['grosor_linea']))
                            estado['puntos_control'] = []
                            estado = redibujar_todo(estado)
                    elif estado['herramienta_actual'] == SELECCIONAR:
                        seleccion = seleccionar_figura(estado, x, y)
                        estado['figura_seleccionada'] = seleccion
                        estado = redibujar_todo(estado)
                    elif estado['herramienta_actual'] == "recortar":
                        if not estado['area_recorte_temporal']:
                            estado['area_recorte_temporal'] = [(x, y)]
                else:
                    herramientas = ["lapiz", "linea", "circulo", "curva", "borrador",
                                  "rectangulo", "recortar", SELECCIONAR, "ventana3d"]
                    espaciado = min(40, (estado['ancho'] - 20) // len(herramientas))
                    
                    for i, herramienta in enumerate(herramientas):
                        if 10 + i * espaciado <= x <= 10 + (i + 1) * espaciado:
                            estado['herramienta_actual'] = herramienta
                            if herramienta == "ventana3d":
                                try:
                                    abrir_ventana_3d()
                                    pygame.display.quit()
                                    pygame.display.init()
                                    estado = inicializar_pygame(1000, 600)
                                    estado = redibujar_todo(estado)
                                except Exception as e:
                                    print(f"Error al abrir ventana 3D: {e}")
                            elif herramienta != "recortar":
                                estado['area_recorte'] = None
                            if herramienta != SELECCIONAR:
                                estado['figura_seleccionada'] = None

                    # Manejo de clics en los botones de color
                    colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
                    colores_x = 10 + len(herramientas) * espaciado + 10
                    
                    for i, (r, g, b) in enumerate(colores):
                        if colores_x + i * 35 <= x <= colores_x + (i + 1) * 35:
                            estado = establecer_color(estado, r, g, b)

                    estado['puntos'].clear()
                    estado['puntos_control'].clear()
                    estado = redibujar_todo(estado)
            
            elif evento.type == pygame.MOUSEBUTTONUP:
                if estado['herramienta_actual'] == "recortar" and estado['area_recorte_temporal'] and len(estado['area_recorte_temporal']) == 1:
                    x, y = pygame.mouse.get_pos()
                    estado['area_recorte_temporal'].append((x, y))
                    x0, y0 = estado['area_recorte_temporal'][0]
                    x1, y1 = estado['area_recorte_temporal'][1]
                    estado['area_recorte'] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
                    estado['area_recorte_temporal'] = None
                    estado = redibujar_todo(estado)
                estado['dibujando'] = False
            
            elif evento.type == pygame.MOUSEMOTION and estado['dibujando']:
                x, y = evento.pos
                if y > 40:
                    if estado['herramienta_actual'] == "lapiz":
                        estado = dibujar_pixel(estado, x, y)
                    elif estado['herramienta_actual'] == "borrador":
                        estado = borrar_en(estado, x, y)
                    estado = redibujar_todo(estado)
            
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_g and not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    estado['mostrar_cuadricula'] = not estado['mostrar_cuadricula']
                    estado = redibujar_todo(estado)
                elif evento.key == pygame.K_t:
                    estado['grosor_linea'] = min(10, estado['grosor_linea'] + 1)
                    estado = redibujar_todo(estado)
                elif evento.key == pygame.K_g and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    estado['grosor_linea'] = max(1, estado['grosor_linea'] - 1)
                    estado = redibujar_todo(estado)
                elif evento.key == pygame.K_ESCAPE:
                    estado['area_recorte'] = None
                    estado['area_recorte_temporal'] = None
                    estado['figura_seleccionada'] = None
                    estado = redibujar_todo(estado)
                elif evento.key == pygame.K_c and estado['herramienta_actual'] == "recortar" and estado['area_recorte']:
                    estado = aplicar_recorte(estado)
                    estado = redibujar_todo(estado)
                elif evento.key == pygame.K_f:
                    estado['herramienta_actual'] = SELECCIONAR
                    estado = redibujar_todo(estado)
                elif evento.key == pygame.K_r:
                    if estado['figura_seleccionada']:
                        angulo = 15
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            angulo = -15
                        estado = rotar_figura(estado, angulo)
                        estado = redibujar_todo(estado)
                elif evento.key == pygame.K_s:
                    if estado['figura_seleccionada']:
                        factor = 1.1
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            factor = 0.9
                        estado = escalar_figura(estado, factor)
                        estado = redibujar_todo(estado)
        
        if estado['herramienta_actual'] == "recortar" and estado['area_recorte_temporal'] and len(estado['area_recorte_temporal']) == 1:
            estado = redibujar_todo(estado)
        
        pygame.time.wait(10)
    
    pygame.quit()

# Funcion para iniciar el programa
if __name__ == "__main__":
    main()