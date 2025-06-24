import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

# Constantes
DENTRO = 0
IZQUIERDA = 1
DERECHA = 2
ABAJO = 4
ARRIBA = 8
#Funcion para inicializar pygame y OpenGL
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
        'tamanho_cuadricula': 20,
        'area_recorte': None,
        'area_recorte_temporal': None
    }
#Funciones de recorte de lineas
# Algoritmo de recorte de Cohen-Sutherland
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

# Funciones de dibujo
# Establecer el color actual
def establecer_color(estado, r, g, b):
    estado['color_actual'] = (r/255.0, g/255.0, b/255.0)
    return estado
# Dibujar un pixel
# Esta función dibuja un pixel en la posición (x, y) con el color y
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

# Borrar en una posición (x, y)
# Esta función borra un área cuadrada centrada en (x, y) del tamaño
def borrar_en(estado, x, y):
    mitad = estado['tamanho_borrador'] // 2
    estado['pixeles_almacenados'] = [
        (px, py, color, tamanho) for (px, py, color, tamanho) in estado['pixeles_almacenados']
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

# Dibujar una línea usando el algoritmo de Bresenham
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
    glLineWidth(estado['grosor_linea'])
    glBegin(GL_POINTS)
    for x in range(int(x0), int(x1) + 1):
        coord = (y, x) if empinada else (x, y)
        glVertex2f(coord[0], coord[1])
        error -= dy
        if error < 0:
            y += paso_y
            error += dx
    glEnd()
    glLineWidth(1)
    return estado

# Dibujar una curva Bezier cuadrática
# Esta función dibuja una curva Bezier cuadrática usando tres puntos de control
def dibujar_curva_bezier(estado, puntos_control, segmentos=100, almacenar=True):
    if almacenar:
        estado['curvas_almacenadas'].append((puntos_control.copy(), estado['color_actual'], estado['grosor_linea']))
    
    glColor3f(*estado['color_actual'])
    glLineWidth(estado['grosor_linea'])
    glBegin(GL_LINE_STRIP)
    for i in range(segmentos + 1):
        t = i / segmentos
        x = (1 - t) ** 2 * puntos_control[0][0] + 2 * (1 - t) * t * puntos_control[1][0] + t ** 2 * puntos_control[2][0]
        y = (1 - t) ** 2 * puntos_control[0][1] + 2 * (1 - t) * t * puntos_control[1][1] + t ** 2 * puntos_control[2][1]
        glVertex2f(x, y)
    glEnd()
    glLineWidth(1)
    return estado

# Dibujar un círculo
# Esta función dibuja un círculo centrado en (cx, cy) con un radio dado
def dibujar_circulo(estado, cx, cy, radio, segmentos=100, almacenar=True):
    if almacenar:
        estado['circulos_almacenados'].append((cx, cy, radio, estado['color_actual'], estado['grosor_linea']))
    
    glColor3f(*estado['color_actual'])
    glLineWidth(estado['grosor_linea'])
    glBegin(GL_LINE_LOOP)
    for i in range(segmentos):
        angulo = 2 * math.pi * i / segmentos
        x = cx + radio * math.cos(angulo)
        y = cy + radio * math.sin(angulo)
        glVertex2f(x, y)
    glEnd()
    glLineWidth(1)
    return estado

# Dibujar un rectángulo
# Esta función dibuja un rectángulo definido por dos esquinas opuestas (x0, y0) y (x1, y1)
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

# Dibujar una cuadrícula
# Esta función dibuja una cuadrícula en el fondo de la ventana
def dibujar_cuadricula(estado):
    if not estado['mostrar_cuadricula']:
        return
    
    glColor3f(0.9, 0.9, 0.9)
    glLineWidth(1)
    glBegin(GL_LINES)
    
    for x in range(0, estado['ancho'], estado['tamanho_cuadricula']):
        glVertex2f(x, 40)
        glVertex2f(x, estado['alto'])
    
    for y in range(40, estado['alto'], estado['tamanho_cuadricula']):
        glVertex2f(0, y)
        glVertex2f(estado['ancho'], y)
    
    glEnd()

# Dibujar iconos de herramientas
# Esta función dibuja los iconos de las herramientas en la barra de herramientas
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
        glVertex2f(x + 5, 30); glVertex2f(x + 25, 10)
        glEnd()
    elif herramienta == "circulo":
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        for i in range(20):
            angulo = 2 * math.pi * i / 20
            glVertex2f(x + 15 + 10 * math.cos(angulo), 20 + 10 * math.sin(angulo))
        glEnd()
    elif herramienta == "curva":
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
    elif herramienta == "borrador":
        glColor3f(1, 1, 1)
        glRecti(x + 7, 13, x + 23, 29)
        glColor3f(0, 0, 0)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 7, 13); glVertex2f(x + 23, 13)
        glVertex2f(x + 23, 29); glVertex2f(x + 7, 29)
        glEnd()
    elif herramienta == "rectangulo":
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 8, 12, x + 22, 28)
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 8, 12); glVertex2f(x + 22, 12)
        glVertex2f(x + 22, 28); glVertex2f(x + 8, 28)
        glEnd()
    elif herramienta == "recortar":
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 5, 10, x + 25, 30)
        glColor3f(1, 1, 1)
        glRecti(x + 10, 15, x + 20, 25)
        glColor3f(0, 0, 0)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 5, 10); glVertex2f(x + 25, 10)
        glVertex2f(x + 25, 30); glVertex2f(x + 5, 30)
        glEnd()
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 7, 12); glVertex2f(x + 13, 18)
        glVertex2f(x + 23, 12); glVertex2f(x + 17, 18)
        glVertex2f(x + 13, 18); glVertex2f(x + 15, 20)
        glVertex2f(x + 17, 18); glVertex2f(x + 15, 20)
        glEnd()

# Dibujar la barra de herramientas
# Esta función dibuja la barra de herramientas en la parte superior de la ventana
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
    
    herramientas = ["lapiz", "linea", "circulo", "curva", "borrador", "rectangulo", "recortar"]
    for i, herramienta in enumerate(herramientas):
        x = 10 + i * 40
        if herramienta == estado['herramienta_actual']:
            glColor3f(0.7, 0.7, 0.9)
            glRecti(x - 2, 3, x + 32, 37)
        
        glColor3f(0.8, 0.8, 0.8)
        glRecti(x, 5, x + 30, 35)
        dibujar_icono(herramienta, x)
    
    colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
    for i, (r, g, b) in enumerate(colores):
        cx = 290 + i * 35
        glColor3f(r / 255.0, g / 255.0, b / 255.0)
        glRecti(cx, 5, cx + 30, 35)
        glColor3f(0.3, 0.3, 0.3)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx, 5); glVertex2f(cx + 30, 5)
        glVertex2f(cx + 30, 35); glVertex2f(cx, 35)
        glEnd()
    
    glColor3f(0.2, 0.2, 0.2)
    glRasterPos2f(470, 25)
    texto = f"Grosor: {estado['grosor_linea']} (T/Shift+G para cambiar)"
    for char in texto:
        pygame.font.init()
        fuente = pygame.font.SysFont('Arial', 12)
        superficie_texto = fuente.render(char, True, (50, 50, 50))
        datos_textura = pygame.image.tostring(superficie_texto, "RGBA", True)
        glDrawPixels(superficie_texto.get_width(), superficie_texto.get_height(), 
                    GL_RGBA, GL_UNSIGNED_BYTE, datos_textura)
        glRasterPos2f(glGetDoublev(GL_CURRENT_RASTER_POSITION)[0] + superficie_texto.get_width(), 25)

# Aplicar recorte a los elementos almacenados
# Esta función recorta los elementos almacenados según el área de recorte definida
def aplicar_recorte(estado):
    if not estado['area_recorte']:
        return estado
    
    x0, y0, x1, y1 = estado['area_recorte']
    
    # Filtrar elementos fuera del área de recorte
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
    
    estado['circulos_almacenados'] = [
        (cx, cy, radio, color, grosor) 
        for (cx, cy, radio, color, grosor) in estado['circulos_almacenados']
        if (x0 <= cx - radio and cx + radio <= x1 and 
            y0 <= cy - radio and cy + radio <= y1)
    ]
    
    estado['rectangulos_almacenados'] = [
        (max(x0_r, x0), max(y0_r, y0), min(x1_r, x1), min(y1_r, y1), color, grosor)
        for (x0_r, y0_r, x1_r, y1_r, color, grosor) in estado['rectangulos_almacenados']
        if not (x1_r < x0 or x0_r > x1 or y1_r < y0 or y0_r > y1)
    ]
    
    estado['curvas_almacenadas'] = [
        (pts, color, grosor) 
        for (pts, color, grosor) in estado['curvas_almacenadas']
        if all(x0 <= px <= x1 and y0 <= py <= y1 for (px, py) in pts)
    ]
    
    estado['area_recorte'] = None
    return estado

# Redibujar todo el contenido de la ventana
# Esta función redibuja todos los elementos almacenados y la cuadrícula
def redibujar_todo(estado):
    glClearColor(1, 1, 1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    dibujar_cuadricula(estado)
    
    # Dibujar elementos almacenados
    for x, y, color, tamanho in estado['pixeles_almacenados']:
        dibujar_pixel(estado, x, y, almacenar=False, color=color, tamanho=tamanho)
    
    for x0, y0, x1, y1, color, grosor in estado['lineas_almacenadas']:
        glColor3f(*color)
        glLineWidth(grosor)
        dibujar_linea_bresenham(estado, x0, y0, x1, y1, almacenar=False)
    
    for pts, color, grosor in estado['curvas_almacenadas']:
        glColor3f(*color)
        glLineWidth(grosor)
        dibujar_curva_bezier(estado, pts, almacenar=False)
    
    for cx, cy, radio, color, grosor in estado['circulos_almacenados']:
        glColor3f(*color)
        glLineWidth(grosor)
        dibujar_circulo(estado, cx, cy, radio, almacenar=False)
    
    for x0, y0, x1, y1, color, grosor in estado['rectangulos_almacenados']:
        glColor3f(*color)
        glLineWidth(grosor)
        dibujar_rectangulo(estado, x0, y0, x1, y1, almacenar=False)
    
    # Dibujar área de recorte si existe
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
        glVertex2f(0, 0); glVertex2f(estado['ancho'], 0)
        glVertex2f(estado['ancho'], y0); glVertex2f(0, y0)
        glVertex2f(0, y0); glVertex2f(x0, y0)
        glVertex2f(x0, y1); glVertex2f(0, y1)
        glVertex2f(x1, y0); glVertex2f(estado['ancho'], y0)
        glVertex2f(estado['ancho'], y1); glVertex2f(x1, y1)
        glVertex2f(0, y1); glVertex2f(estado['ancho'], y1)
        glVertex2f(estado['ancho'], estado['alto']); glVertex2f(0, estado['alto'])
        glEnd()
        glDisable(GL_BLEND)
    
    # Dibujar rectángulo de recorte temporal
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
    
    dibujar_barra_herramientas(estado)
    pygame.display.flip()
    return estado

# Función principal del programa
# Esta función inicializa Pygame, configura el estado inicial y maneja el bucle
def main():
    estado = inicializar_pygame()
    estado = redibujar_todo(estado)
    
    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = evento.pos
                if y > 40:
                    if estado['herramienta_actual'] == "lapiz":
                        estado['dibujando'] = True
                        estado = dibujar_pixel(estado, x, y)
                    elif estado['herramienta_actual'] == "borrador":
                        estado['dibujando'] = True
                        estado = borrar_en(estado, x, y)
                    elif estado['herramienta_actual'] == "linea":
                        estado['puntos'].append((x, y))
                        if len(estado['puntos']) == 2:
                            estado = dibujar_linea_bresenham(estado, *estado['puntos'][0], *estado['puntos'][1])
                            estado['puntos'].clear()
                    elif estado['herramienta_actual'] == "circulo":
                        estado['puntos'].append((x, y))
                        if len(estado['puntos']) == 2:
                            x0, y0 = estado['puntos'][0]
                            radio = int(math.hypot(x - x0, y - y0))
                            estado = dibujar_circulo(estado, x0, y0, radio)
                            estado['puntos'].clear()
                    elif estado['herramienta_actual'] == "rectangulo":
                        estado['puntos'].append((x, y))
                        if len(estado['puntos']) == 2:
                            estado = dibujar_rectangulo(estado, *estado['puntos'][0], *estado['puntos'][1])
                            estado['puntos'].clear()
                    elif estado['herramienta_actual'] == "curva":
                        estado['puntos_control'].append((x, y))
                        if len(estado['puntos_control']) == 3:
                            estado = dibujar_curva_bezier(estado, estado['puntos_control'])
                            estado['puntos_control'].clear()
                    elif estado['herramienta_actual'] == "recortar":
                        estado['area_recorte_temporal'] = [(x, y)]
                    estado = redibujar_todo(estado)
                else:
                    herramientas = ["lapiz", "linea", "circulo", "curva", "borrador", "rectangulo", "recortar"]
                    for i, herramienta in enumerate(herramientas):
                        if 10 + i * 40 <= x <= 40 + i * 40:
                            estado['herramienta_actual'] = herramienta
                            if herramienta != "recortar":
                                estado['area_recorte'] = None
                    
                    colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
                    for i, (r, g, b) in enumerate(colores):
                        if 290 + i * 35 <= x <= 320 + i * 35:
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
                    estado = redibujar_todo(estado)
                elif evento.key == pygame.K_c and estado['herramienta_actual'] == "recortar" and estado['area_recorte']:
                    estado = aplicar_recorte(estado)
                    estado = redibujar_todo(estado)
        
        if estado['herramienta_actual'] == "recortar" and estado['area_recorte_temporal'] and len(estado['area_recorte_temporal']) == 1:
            estado = redibujar_todo(estado)
        
        pygame.time.wait(10)
    
    pygame.quit()

#Funcion principal
main()