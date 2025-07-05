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
        if not (x - mitad <= circulo[0][0] <= x + mitad and y - mitad <= circulo[0][1] <= y + mitad)
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
            glVertex2f(xa, ya)
            glVertex2f(xb, yb)
    glEnd()
    glLineWidth(1)

def draw_grid():
    if not show_grid:
        return
        
    glColor3f(0.9, 0.9, 0.9)
    glLineWidth(1)
    glBegin(GL_LINES)
    
    # Líneas verticales
    for x in range(0, width, grid_size):
        glVertex2f(x, 40)
        glVertex2f(x, height)
    
    # Líneas horizontales
    for y in range(40, height, grid_size):
        glVertex2f(0, y)
        glVertex2f(width, y)
    
    glEnd()

def draw_icon(tool, x):
    if tool == "pencil":
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
    elif herramienta == SELECCIONAR:
        glColor3f(0.7, 0.7, 0.9)
        glRecti(x + 5, 5, x + 25, 35)
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x + 8, 25); glVertex2f(x + 15, 15)
        glVertex2f(x + 15, 15); glVertex2f(x + 22, 25)
        glVertex2f(x + 15, 15); glVertex2f(x + 15, 30)
        glEnd()
    elif herramienta == "ventana3d":
        glColor3f(0.2, 0.2, 0.7)
        glRecti(x + 8, 12, x + 22, 28)
        glColor3f(1, 1, 1)
        glBegin(GL_LINES)
        glVertex2f(x + 10, 15); glVertex2f(x + 20, 25)
        glVertex2f(x + 20, 15); glVertex2f(x + 10, 25)
        glEnd()

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
    
    herramientas = ["lapiz", "linea", "circulo", "curva", "borrador", "rectangulo", "recortar", SELECCIONAR]
    for i, herramienta in enumerate(herramientas):
        x = 10 + i * 40
        if herramienta == estado['herramienta_actual']:
            glColor3f(0.7, 0.7, 0.9)
            glRecti(x - 2, 3, x + 32, 37)
        glColor3f(0.8, 0.8, 0.8)
        glRecti(x, 5, x + 30, 35)
        dibujar_icono(herramienta, x)

    # Colores
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

    # Botón 3D mucho más a la derecha
    x3d = estado['ancho'] - 100
    glColor3f(0.8, 0.8, 0.8)
    glRecti(x3d, 5, x3d + 30, 35)
    dibujar_icono("ventana3d", x3d)

    # Botón 2D (esquina superior derecha en la ventana 3D)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, estado['ancho'], 0, estado['alto'], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    x2d = estado['ancho'] - 60
    glColor3f(0.8, 0.8, 0.8)
    glRecti(x2d, 5, x2d + 30, 35)
    glColor3f(0.2, 0.2, 0.2)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(x2d + 10, 15); glVertex2f(x2d + 20, 15)
    glVertex2f(x2d + 10, 25); glVertex2f(x2d + 20, 25)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

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

    if estado['figura_seleccionada']:
        glColor3f(0.2, 0.2, 0.2)
        glRasterPos2f(470, 10)
        texto = "R: Rotar | S: Escalar | Shift: Invertir"
        for char in texto:
            fuente = pygame.font.SysFont('Arial', 12)
            superficie_texto = fuente.render(char, True, (50, 50, 50))
            datos_textura = pygame.image.tostring(superficie_texto, "RGBA", True)
            glDrawPixels(superficie_texto.get_width(), superficie_texto.get_height(), 
                        GL_RGBA, GL_UNSIGNED_BYTE, datos_textura)
            glRasterPos2f(glGetDoublev(GL_CURRENT_RASTER_POSITION)[0] + superficie_texto.get_width(), 10)

def redibujar_todo(estado):
    glClearColor(1, 1, 1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    dibujar_cuadricula(estado)
    
    for x, y, color, tamanho in estado['pixeles_almacenados']:
        dibujar_pixel(estado, x, y, almacenar=False, color=color, tamanho=tamanho)
    
    for i, (x0, y0, x1, y1, color, grosor) in enumerate(estado['lineas_almacenadas']):
        glColor3f(*color)
        glLineWidth(width)
        draw_line_bresenham(x0, y0, x1, y1, store=False)
    for pts, color, width in stored_curves:
        glColor3f(*color)
        glLineWidth(width)
        draw_bezier_curve(pts, store=False)
    for cx, cy, radius, color, width in stored_circles:
        glColor3f(*color)
        glLineWidth(width)
        draw_circle(cx, cy, radius, store=False)
    for x0, y0, x1, y1, color, width in stored_rectangles:
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
        
        glColor4f(0.7, 0.7, 0.9, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(width, 0)
        glVertex2f(width, height); glVertex2f(0, height)
        glEnd()
        glLineWidth(1)

        # Plano XY
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_LINES)
        for i in range(-3, 4):
            glVertex3f(i, -3, 0)
            glVertex3f(i, 3, 0)
            glVertex3f(-3, i, 0)
            glVertex3f(3, i, 0)
        glEnd()

        # Puntos
        glPointSize(8)
        glColor3f(1, 0, 0)
        glBegin(GL_POINTS)
        for px, py in puntos:
            glVertex3f(px, py, 0)
        glEnd()
    
    draw_toolbar()
    pygame.display.flip()

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
                    draw_pixel(x, y)
                elif current_tool == "eraser":
                    drawing = True
                    erase_at(x, y)
                elif current_tool == "line":
                    points.append((x, y))
                    if len(points) == 2:
                        draw_line_bresenham(*points[0], *points[1])
                        points.clear()
                elif current_tool == "circle":
                    points.append((x, y))
                    if len(points) == 2:
                        x0, y0 = points[0]
                        radius = int(math.hypot(x - x0, y - y0))
                        draw_circle(x0, y0, radius)
                        points.clear()
                elif current_tool == "rectangle":
                    points.append((x, y))
                    if len(points) == 2:
                        draw_rectangle(*points[0], *points[1])
                        points.clear()
                elif current_tool == "curve":
                    control_points.append((x, y))
                    if len(control_points) == 3:
                        draw_bezier_curve(control_points)
                        control_points.clear()
                elif current_tool == "crop":
                    points.append((x, y))
                    if len(points) == 2:
                        x0, y0 = min(points[0][0], points[1][0]), min(points[0][1], points[1][1])
                        x1, y1 = max(points[0][0], points[1][0]), max(points[0][1], points[1][1])
                        clipping_rect = (x0, y0, x1, y1)
                        points.clear()
                redraw_all()
            else:
                tools = ["pencil", "line", "circle", "curve", "eraser", "rectangle", "crop"]
                for i, tool in enumerate(tools):
                    if 10 + i * 40 <= x <= 40 + i * 40:
                        current_tool = tool
                        if tool != "crop":
                            clipping_rect = None
                
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
                for i, (r, g, b) in enumerate(colors):
                    if 290 + i * 35 <= x <= 320 + i * 35:
                        set_color(r, g, b)
                
                points.clear(); control_points.clear()
                redraw_all()
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
        elif event.type == pygame.MOUSEMOTION and drawing:
            x, y = event.pos
            if y > 40:
                if current_tool == "pencil":
                    draw_pixel(x, y)
                elif current_tool == "eraser":
                    erase_at(x, y)
                redraw_all()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                show_grid = not show_grid
                redraw_all()
            elif event.key == pygame.K_t:
                line_width = min(10, line_width + 1)
                redraw_all()
            elif event.key == pygame.K_g and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                line_width = max(1, line_width - 1)
                redraw_all()
            elif event.key == pygame.K_ESCAPE:
                clipping_rect = None
                redraw_all()
    
    pygame.time.wait(10)
pygame.quit()