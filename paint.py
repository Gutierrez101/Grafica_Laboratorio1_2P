import pygame
from pygame.locals import *  # <-- Mueve esta línea aquí
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
from numpy.linalg import inv

# Constantes
DENTRO = 0
IZQUIERDA = 1
DERECHA = 2
ABAJO = 4
ARRIBA = 8
SELECCIONAR = 'seleccionar'

# Funciones de transformación con matrices
def crear_matriz_traslacion(tx, ty):
    return np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1]
    ])

def crear_matriz_rotacion(angulo):
    rad = math.radians(angulo)
    cos=math.cos(rad)
    sin=math.sin(rad)
    return np.array([
        [cos, -sin, 0],
        [sin, cos, 0],
        [0, 0, 1]
    ])

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

def inicializar_pygame(ancho=800, alto=600):
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

def establecer_color(estado, r, g, b):
    estado['color_actual'] = (r/255.0, g/255.0, b/255.0)
    return estado

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
        if not (x - mitad <= circulo[0] <= x + mitad and y - mitad <= circulo[1] <= y + mitad)
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

def rotar_figura(estado, angulo):
    if not estado['figura_seleccionada']:
        return estado
    
    tipo, indice = estado['figura_seleccionada']
    
    if tipo == 'circulo':
        # Rotar un círculo no cambia su apariencia, pero podemos rotar su posición si queremos
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

    # Recorte destructivo para curvas (filtra puntos de la curva)
    nuevas_curvas = []
    for puntos_control, color, grosor in estado['curvas_almacenadas']:
        curva = calcular_b_spline(puntos_control)
        curva_recortada = [
            (x, y) for (x, y) in curva
            if x0 <= x <= x1 and y0 <= y <= y1
        ]
        if curva_recortada:
            # Guarda los puntos recortados como una curva "plana"
            nuevas_curvas.append((curva_recortada, color, grosor))
    estado['curvas_almacenadas'] = nuevas_curvas

    # Recorte destructivo para círculos (filtra puntos del círculo)
    nuevas_circulos = []
    for cx, cy, radio, color, grosor in estado['circulos_almacenados']:
        puntos = []
        for i in range(100):
            angulo = 2 * math.pi * i / 100
            x = cx + radio * math.cos(angulo)
            y = cy + radio * math.sin(angulo)
            if x0 <= x <= x1 and y0 <= y <= y1:
                puntos.append((x, y))
        if puntos:
            # Guarda los puntos recortados como una "curva" (igual que curva)
            nuevas_circulos.append((puntos, color, grosor))
    estado['circulos_almacenados'] = nuevas_circulos

    # Recorte destructivo para rectángulos (cada lado como línea)
    nuevas_rectangulos = []
    for x0_r, y0_r, x1_r, y1_r, color, grosor in estado['rectangulos_almacenados']:
        lados = [
            (x0_r, y0_r, x1_r, y0_r),  # arriba
            (x1_r, y0_r, x1_r, y1_r),  # derecha
            (x1_r, y1_r, x0_r, y1_r),  # abajo
            (x0_r, y1_r, x0_r, y0_r),  # izquierda
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
    if herramienta == "lapiz":
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 8, 30); glVertex2f(x + 22, 15)
        glEnd()
    elif herramienta == "linea":
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        if tool == "pencil":
            glVertex2f(x + 5, 30)
            glVertex2f(x + 25, 10)
        elif tool == "line":
            glVertex2f(x + 5, 30)
            glVertex2f(x + 25, 10)
        elif tool == "circle":
            for i in range(20):
                theta = 2 * math.pi * i / 20
                glVertex2f(x + 15 + 10 * math.cos(theta), 20 + 10 * math.sin(theta))
        elif tool == "curve":
            for t in np.linspace(0, 1, 20):
                x0, y0 = x + 5, 30
                x1, y1 = x + 15, 10
                x2, y2 = x + 25, 30
                xt = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t ** 2 * x2
                yt = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t ** 2 * y2
                glVertex2f(xt, yt)
        elif tool == "eraser":
            # Dibuja un cuadrado blanco con borde negro
            glEnd()
            glColor3f(1, 1, 1)
            glRecti(x + 7, 13, x + 23, 29)
            glColor3f(0, 0, 0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x + 7, 13)
            glVertex2f(x + 23, 13)
            glVertex2f(x + 23, 29)
            glVertex2f(x + 7, 29)
        glEnd()

    # Selección de colores: Rojo, Verde, Azul
    color_boxes = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    for i, color in enumerate(color_boxes):
        x = 210 + i * 40
        glColor3f(*color)
        glRecti(x, 5, x + 30, 35)

# Redibuja todo

def redraw_all():
    glClearColor(1, 1, 1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    dibujar_cuadricula(estado)
    
    for x, y, color, tamanho in estado['pixeles_almacenados']:
        dibujar_pixel(estado, x, y, almacenar=False, color=color, tamanho=tamanho)
    
    for i, (x0, y0, x1, y1, color, grosor) in enumerate(estado['lineas_almacenadas']):
        glColor3f(*color)
        glLineWidth(grosor)
        dibujar_linea_bresenham(estado, x0, y0, x1, y1, almacenar=False)
        
        if estado['figura_seleccionada'] and estado['figura_seleccionada'][0] == 'linea' and estado['figura_seleccionada'][1] == i:
            glColor3f(0, 1, 1)
            glLineWidth(grosor + 2)
            dibujar_linea_bresenham(estado, x0, y0, x1, y1, almacenar=False)
    
    for i, (pts, color, grosor) in enumerate(estado['curvas_almacenadas']):
        glColor3f(*color)
        glPointSize(grosor)
        glBegin(GL_POINTS)
        curva = calcular_b_spline(pts)
        for x, y in curva:
            if not estado['area_recorte'] or (
                estado['area_recorte'][0] <= x <= estado['area_recorte'][2] and
                estado['area_recorte'][1] <= y <= estado['area_recorte'][3]
            ):
                glVertex2f(x, y)
        glEnd()
    glPointSize(1)

    for i, (cx, cy, radio, color, grosor) in enumerate(estado['circulos_almacenados']):
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
    # Selección visual igual que arriba si quieres
    
    for i, (x0, y0, x1, y1, color, grosor) in enumerate(estado['rectangulos_almacenados']):
        lados = [
            (x0, y0, x1, y0),  # arriba
            (x1, y0, x1, y1),  # derecha
            (x1, y1, x0, y1),  # abajo
            (x0, y1, x0, y0),  # izquierda
        ]
        glColor3f(*color)
        draw_bezier_curve(pts, store=False)

    # Círculos
    for cx, cy, radius, color in stored_circles:
        glColor3f(*color)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x0, y0)
        glVertex2f(x1, y0)
        glVertex2f(x1, y1)
        glVertex2f(x0, y1)
        glEnd()

    draw_toolbar()
    # Puntos de control curva
    if current_tool == "curve" and control_points:
        glColor3f(0, 0, 1)
        glPointSize(5)
        glBegin(GL_POINTS)
        for px, py in control_points:
            glVertex2f(px, py)
        glEnd()
        glPointSize(1)

    pygame.display.flip()

# Bucle principal
running = True
redraw_all()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if y > 40:
                if current_tool == "pencil":
                    drawing = True
                    draw_pixel(x, y, size=3)
                    redraw_all()
                elif current_tool == "eraser":
                    drawing = True
                    erase_at(x, y)
                    redraw_all()
                elif current_tool == "line":
                    if not points:
                        points = [(x, y)]
                    else:
                        x0, y0 = points[0]
                        draw_line_bresenham(x0, y0, x, y)
                        points.clear()
                        redraw_all()
                elif current_tool == "circle":
                    if not points:
                        points = [(x, y)]
                    else:
                        x0, y0 = points[0]
                        radius = int(math.hypot(x - x0, y - y0))
                        draw_circle(x0, y0, radius)
                        points.clear()
                        redraw_all()
                elif current_tool == "curve":
                    if len(control_points) < 3:
                        control_points.append((x, y))
                        if len(control_points) == 3:
                            draw_bezier_curve(control_points)
                            control_points.clear()
                            redraw_all()
            else:
                # Interacción con toolbar
                if 10 <= x <= 40:
                    current_tool = "pencil"; points.clear(); control_points.clear()
                elif 50 <= x <= 80:
                    current_tool = "line"; points.clear(); control_points.clear()
                elif 90 <= x <= 120:
                    current_tool = "circle"; points.clear(); control_points.clear()
                elif 130 <= x <= 160:
                    current_tool = "curve"; points.clear(); control_points.clear()
                elif 170 <= x <= 200:
                    current_tool = "eraser"; points.clear(); control_points.clear()
                elif 210 <= x <= 240:
                    set_color(255, 0, 0)
                elif 250 <= x <= 280:
                    set_color(0, 255, 0)
                elif 290 <= x <= 320:
                    set_color(0, 0, 255)
                redraw_all()
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
        elif event.type == pygame.MOUSEMOTION and drawing:
            x, y = event.pos
            if y > 40:
                if current_tool == "pencil":
                    draw_pixel(x, y, size=3)
                    redraw_all()
                elif current_tool == "eraser":
                    erase_at(x, y)
                    redraw_all()
    pygame.time.wait(10)
pygame.quit()