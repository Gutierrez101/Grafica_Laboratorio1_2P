import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

class PaintOpenGL:
    def __init__(self):
        # Inicialización
        pygame.init()
        self.ancho, self.alto = 800, 600
        pygame.display.set_mode((self.ancho, self.alto), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Paint OpenGL")

        # Configuración de OpenGL
        glViewport(0, 0, self.ancho, self.alto)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.ancho, self.alto, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Estado de la aplicación
        self.dibujando = False
        self.herramienta_actual = "lapiz"
        self.tamanho_borrador = 15
        self.grosor_linea = 3
        self.puntos = []
        self.puntos_control = []
        self.pixeles_almacenados = []
        self.lineas_almacenadas = []
        self.curvas_almacenadas = []
        self.circulos_almacenados = []
        self.rectangulos_almacenados = []
        self.color_actual = (1.0, 0.0, 0.0)
        self.mostrar_cuadricula = True
        self.tamanho_cuadricula = 20
        self.area_recorte = None
        self.area_recorte_temporal = None

        # Códigos para el algoritmo de Cohen-Sutherland
        self.DENTRO = 0
        self.IZQUIERDA = 1
        self.DERECHA = 2
        self.ABAJO = 4
        self.ARRIBA = 8

    def calcular_codigo(self, x, y, rectangulo_recorte):
        codigo = self.DENTRO
        if x < rectangulo_recorte[0]:
            codigo |= self.IZQUIERDA
        elif x > rectangulo_recorte[2]:
            codigo |= self.DERECHA
        if y < rectangulo_recorte[1]:
            codigo |= self.ABAJO
        elif y > rectangulo_recorte[3]:
            codigo |= self.ARRIBA
        return codigo

    def recortar_linea_cohen_sutherland(self, x0, y0, x1, y1, rectangulo_recorte):
        codigo0 = self.calcular_codigo(x0, y0, rectangulo_recorte)
        codigo1 = self.calcular_codigo(x1, y1, rectangulo_recorte)
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

                if codigo_fuera & self.ARRIBA:
                    x = x0 + (x1 - x0) * (rectangulo_recorte[3] - y0) / (y1 - y0)
                    y = rectangulo_recorte[3]
                elif codigo_fuera & self.ABAJO:
                    x = x0 + (x1 - x0) * (rectangulo_recorte[1] - y0) / (y1 - y0)
                    y = rectangulo_recorte[1]
                elif codigo_fuera & self.DERECHA:
                    y = y0 + (y1 - y0) * (rectangulo_recorte[2] - x0) / (x1 - x0)
                    x = rectangulo_recorte[2]
                elif codigo_fuera & self.IZQUIERDA:
                    y = y0 + (y1 - y0) * (rectangulo_recorte[0] - x0) / (x1 - x0)
                    x = rectangulo_recorte[0]

                if codigo_fuera == codigo0:
                    x0, y0 = x, y
                    codigo0 = self.calcular_codigo(x0, y0, rectangulo_recorte)
                else:
                    x1, y1 = x, y
                    codigo1 = self.calcular_codigo(x1, y1, rectangulo_recorte)

        if aceptar:
            return (x0, y0, x1, y1)
        else:
            return None

    def establecer_color(self, r, g, b):
        self.color_actual = (r/255.0, g/255.0, b/255.0)

    def dibujar_pixel(self, x, y, almacenar=True, color=None, tamanho=3):
        if color is None:
            color = self.color_actual
        if almacenar:
            self.pixeles_almacenados.append((x, y, color, tamanho))
        glColor3f(*color)
        glPointSize(tamanho)
        glBegin(GL_POINTS)
        glVertex2f(x, y)
        glEnd()
        glPointSize(1)

    def borrar_en(self, x, y):
        mitad = self.tamanho_borrador // 2
        self.pixeles_almacenados = [
            (px, py, color, tamanho) for (px, py, color, tamanho) in self.pixeles_almacenados
            if not (x - mitad <= px <= x + mitad and y - mitad <= py <= y + mitad)
        ]
        self.lineas_almacenadas = [
            (x0, y0, x1, y1, color, grosor) for (x0, y0, x1, y1, color, grosor) in self.lineas_almacenadas
            if not ((x - mitad <= x0 <= x + mitad and y - mitad <= y0 <= y + mitad) or
                    (x - mitad <= x1 <= x + mitad and y - mitad <= y1 <= y + mitad))
        ]
        self.circulos_almacenados = [
            (cx, cy, radio, color, grosor) for (cx, cy, radio, color, grosor) in self.circulos_almacenados
            if not (x - mitad <= cx <= x + mitad and y - mitad <= cy <= y + mitad)
        ]
        self.curvas_almacenadas = [
            (pts, color, grosor) for (pts, color, grosor) in self.curvas_almacenadas
            if not any(x - mitad <= px <= x + mitad and y - mitad <= py <= y + mitad for (px, py) in pts)
        ]
        self.rectangulos_almacenados = [
            (x0, y0, x1, y1, color, grosor) for (x0, y0, x1, y1, color, grosor) in self.rectangulos_almacenados
            if not ((x - mitad <= x0 <= x + mitad and y - mitad <= y0 <= y + mitad) or
                    (x - mitad <= x1 <= x + mitad and y - mitad <= y1 <= y + mitad))
        ]

    def dibujar_linea_bresenham(self, x0, y0, x1, y1, almacenar=True):
        if almacenar:
            self.lineas_almacenadas.append((x0, y0, x1, y1, self.color_actual, self.grosor_linea))
        
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
        
        glColor3f(*self.color_actual)
        glLineWidth(self.grosor_linea)
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

    def dibujar_curva_bezier(self, puntos_control, segmentos=100, almacenar=True):
        if almacenar:
            self.curvas_almacenadas.append((puntos_control.copy(), self.color_actual, self.grosor_linea))
        
        glColor3f(*self.color_actual)
        glLineWidth(self.grosor_linea)
        glBegin(GL_LINE_STRIP)
        for i in range(segmentos + 1):
            t = i / segmentos
            x = (1 - t) ** 2 * puntos_control[0][0] + 2 * (1 - t) * t * puntos_control[1][0] + t ** 2 * puntos_control[2][0]
            y = (1 - t) ** 2 * puntos_control[0][1] + 2 * (1 - t) * t * puntos_control[1][1] + t ** 2 * puntos_control[2][1]
            glVertex2f(x, y)
        glEnd()
        glLineWidth(1)

    def dibujar_circulo(self, cx, cy, radio, segmentos=100, almacenar=True):
        if almacenar:
            self.circulos_almacenados.append((cx, cy, radio, self.color_actual, self.grosor_linea))
        
        glColor3f(*self.color_actual)
        glLineWidth(self.grosor_linea)
        glBegin(GL_LINE_LOOP)
        for i in range(segmentos):
            angulo = 2 * math.pi * i / segmentos
            x = cx + radio * math.cos(angulo)
            y = cy + radio * math.sin(angulo)
            glVertex2f(x, y)
        glEnd()
        glLineWidth(1)

    def dibujar_rectangulo(self, x0, y0, x1, y1, almacenar=True):
        if almacenar:
            self.rectangulos_almacenados.append((x0, y0, x1, y1, self.color_actual, self.grosor_linea))
        
        glColor3f(*self.color_actual)
        glLineWidth(self.grosor_linea)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x0, y0)
        glVertex2f(x1, y0)
        glVertex2f(x1, y1)
        glVertex2f(x0, y1)
        glEnd()
        glLineWidth(1)

    def dibujar_cuadricula(self):
        if not self.mostrar_cuadricula:
            return
            
        glColor3f(0.9, 0.9, 0.9)
        glLineWidth(1)
        glBegin(GL_LINES)
        
        for x in range(0, self.ancho, self.tamanho_cuadricula):
            glVertex2f(x, 40)
            glVertex2f(x, self.alto)
        
        for y in range(40, self.alto, self.tamanho_cuadricula):
            glVertex2f(0, y)
            glVertex2f(self.ancho, y)
        
        glEnd()

    def dibujar_icono(self, herramienta, x):
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

    def dibujar_barra_herramientas(self):
        glColor3f(0.9, 0.9, 0.9)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.ancho, 0)
        glVertex2f(self.ancho, 40)
        glVertex2f(0, 40)
        glEnd()
        
        glColor3f(0.6, 0.6, 0.6)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(0, 40)
        glVertex2f(self.ancho, 40)
        glEnd()
        
        herramientas = ["lapiz", "linea", "circulo", "curva", "borrador", "rectangulo", "recortar"]
        for i, herramienta in enumerate(herramientas):
            x = 10 + i * 40
            if herramienta == self.herramienta_actual:
                glColor3f(0.7, 0.7, 0.9)
                glRecti(x - 2, 3, x + 32, 37)
            
            glColor3f(0.8, 0.8, 0.8)
            glRecti(x, 5, x + 30, 35)
            self.dibujar_icono(herramienta, x)
        
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
        texto = f"Grosor: {self.grosor_linea} (T/Shift+G para cambiar)"
        for char in texto:
            pygame.font.init()
            fuente = pygame.font.SysFont('Arial', 12)
            superficie_texto = fuente.render(char, True, (50, 50, 50))
            datos_textura = pygame.image.tostring(superficie_texto, "RGBA", True)
            glDrawPixels(superficie_texto.get_width(), superficie_texto.get_height(), 
                        GL_RGBA, GL_UNSIGNED_BYTE, datos_textura)
            glRasterPos2f(glGetDoublev(GL_CURRENT_RASTER_POSITION)[0] + superficie_texto.get_width(), 25)

    def aplicar_recorte(self):
        if not self.area_recorte:
            return
        
        x0, y0, x1, y1 = self.area_recorte
        
        # Filtrar elementos que están completamente fuera del área de recorte
        self.pixeles_almacenados = [
            (x, y, color, tamanho) for (x, y, color, tamanho) in self.pixeles_almacenados
            if x0 <= x <= x1 and y0 <= y <= y1
        ]
        
        self.lineas_almacenadas = [
            (nx0, ny0, nx1, ny1, color, grosor) 
            for (x0_l, y0_l, x1_l, y1_l, color, grosor) in self.lineas_almacenadas
            if (resultado := self.recortar_linea_cohen_sutherland(x0_l, y0_l, x1_l, y1_l, self.area_recorte))
            for (nx0, ny0, nx1, ny1) in [resultado]
        ]
        
        self.circulos_almacenados = [
            (cx, cy, radio, color, grosor) 
            for (cx, cy, radio, color, grosor) in self.circulos_almacenados
            if (x0 <= cx - radio and cx + radio <= x1 and 
                y0 <= cy - radio and cy + radio <= y1)
        ]
        
        self.rectangulos_almacenados = [
            (max(x0_r, x0), max(y0_r, y0), min(x1_r, x1), min(y1_r, y1), color, grosor)
            for (x0_r, y0_r, x1_r, y1_r, color, grosor) in self.rectangulos_almacenados
            if not (x1_r < x0 or x0_r > x1 or y1_r < y0 or y0_r > y1)
        ]
        
        self.curvas_almacenadas = [
            (pts, color, grosor) 
            for (pts, color, grosor) in self.curvas_almacenadas
            if all(x0 <= px <= x1 and y0 <= py <= y1 for (px, py) in pts)
        ]
        
        self.area_recorte = None

    def redibujar_todo(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        self.dibujar_cuadricula()
        
        # Dibujar elementos con recorte si está activo
        for x, y, color, tamanho in self.pixeles_almacenados:
            if not self.area_recorte or (self.area_recorte[0] <= x <= self.area_recorte[2] and self.area_recorte[1] <= y <= self.area_recorte[3]):
                self.dibujar_pixel(x, y, almacenar=False, color=color, tamanho=tamanho)
        
        for x0, y0, x1, y1, color, grosor in self.lineas_almacenadas:
            glColor3f(*color)
            glLineWidth(grosor)
            if self.area_recorte:
                resultado = self.recortar_linea_cohen_sutherland(x0, y0, x1, y1, self.area_recorte)
                if resultado:
                    self.dibujar_linea_bresenham(*resultado, almacenar=False)
            else:
                self.dibujar_linea_bresenham(x0, y0, x1, y1, almacenar=False)
        
        for pts, color, grosor in self.curvas_almacenadas:
            glColor3f(*color)
            glLineWidth(grosor)
            if self.area_recorte:
                if all(self.area_recorte[0] <= px <= self.area_recorte[2] and self.area_recorte[1] <= py <= self.area_recorte[3] for (px, py) in pts):
                    self.dibujar_curva_bezier(pts, almacenar=False)
            else:
                self.dibujar_curva_bezier(pts, almacenar=False)
        
        for cx, cy, radio, color, grosor in self.circulos_almacenados:
            glColor3f(*color)
            glLineWidth(grosor)
            if self.area_recorte:
                if (self.area_recorte[0] <= cx - radio and cx + radio <= self.area_recorte[2] and 
                    self.area_recorte[1] <= cy - radio and cy + radio <= self.area_recorte[3]):
                    self.dibujar_circulo(cx, cy, radio, almacenar=False)
            else:
                self.dibujar_circulo(cx, cy, radio, almacenar=False)
        
        for x0, y0, x1, y1, color, grosor in self.rectangulos_almacenados:
            glColor3f(*color)
            glLineWidth(grosor)
            if self.area_recorte:
                puntos_rect = [(max(x0, self.area_recorte[0]), max(y0, self.area_recorte[1]), 
                               min(x1, self.area_recorte[2]), min(y1, self.area_recorte[3]))]
                glBegin(GL_LINE_LOOP)
                glVertex2f(puntos_rect[0][0], puntos_rect[0][1])
                glVertex2f(puntos_rect[0][2], puntos_rect[0][1])
                glVertex2f(puntos_rect[0][2], puntos_rect[0][3])
                glVertex2f(puntos_rect[0][0], puntos_rect[0][3])
                glEnd()
            else:
                self.dibujar_rectangulo(x0, y0, x1, y1, almacenar=False)
        
        # Dibujar área de recorte si existe
        if self.area_recorte:
            x0, y0, x1, y1 = self.area_recorte
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
            glVertex2f(0, 0); glVertex2f(self.ancho, 0)
            glVertex2f(self.ancho, y0); glVertex2f(0, y0)
            glVertex2f(0, y0); glVertex2f(x0, y0)
            glVertex2f(x0, y1); glVertex2f(0, y1)
            glVertex2f(x1, y0); glVertex2f(self.ancho, y0)
            glVertex2f(self.ancho, y1); glVertex2f(x1, y1)
            glVertex2f(0, y1); glVertex2f(self.ancho, y1)
            glVertex2f(self.ancho, self.alto); glVertex2f(0, self.alto)
            glEnd()
            glDisable(GL_BLEND)
        
        # Dibujar rectángulo de recorte temporal
        if self.area_recorte_temporal and len(self.area_recorte_temporal) == 1:
            x0, y0 = self.area_recorte_temporal[0]
            x1, y1 = pygame.mouse.get_pos()
            glColor3f(0.5, 0.5, 0.8)
            glLineWidth(1)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x0, y0)
            glVertex2f(x1, y0)
            glVertex2f(x1, y1)
            glVertex2f(x0, y1)
            glEnd()
        
        self.dibujar_barra_herramientas()
        pygame.display.flip()

    def ejecutar(self):
        ejecutando = True
        self.redibujar_todo()
        
        while ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    x, y = evento.pos
                    if y > 40:
                        if self.herramienta_actual == "lapiz":
                            self.dibujando = True
                            self.dibujar_pixel(x, y)
                        elif self.herramienta_actual == "borrador":
                            self.dibujando = True
                            self.borrar_en(x, y)
                        elif self.herramienta_actual == "linea":
                            self.puntos.append((x, y))
                            if len(self.puntos) == 2:
                                self.dibujar_linea_bresenham(*self.puntos[0], *self.puntos[1])
                                self.puntos.clear()
                        elif self.herramienta_actual == "circulo":
                            self.puntos.append((x, y))
                            if len(self.puntos) == 2:
                                x0, y0 = self.puntos[0]
                                radio = int(math.hypot(x - x0, y - y0))
                                self.dibujar_circulo(x0, y0, radio)
                                self.puntos.clear()
                        elif self.herramienta_actual == "rectangulo":
                            self.puntos.append((x, y))
                            if len(self.puntos) == 2:
                                self.dibujar_rectangulo(*self.puntos[0], *self.puntos[1])
                                self.puntos.clear()
                        elif self.herramienta_actual == "curva":
                            self.puntos_control.append((x, y))
                            if len(self.puntos_control) == 3:
                                self.dibujar_curva_bezier(self.puntos_control)
                                self.puntos_control.clear()
                        elif self.herramienta_actual == "recortar":
                            self.area_recorte_temporal = [(x, y)]
                        self.redibujar_todo()
                    else:
                        herramientas = ["lapiz", "linea", "circulo", "curva", "borrador", "rectangulo", "recortar"]
                        for i, herramienta in enumerate(herramientas):
                            if 10 + i * 40 <= x <= 40 + i * 40:
                                self.herramienta_actual = herramienta
                                if herramienta != "recortar":
                                    self.area_recorte = None
                        
                        colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 255)]
                        for i, (r, g, b) in enumerate(colores):
                            if 290 + i * 35 <= x <= 320 + i * 35:
                                self.establecer_color(r, g, b)
                        
                        self.puntos.clear()
                        self.puntos_control.clear()
                        self.redibujar_todo()
                elif evento.type == pygame.MOUSEBUTTONUP:
                    if self.herramienta_actual == "recortar" and self.area_recorte_temporal and len(self.area_recorte_temporal) == 1:
                        x, y = pygame.mouse.get_pos()
                        self.area_recorte_temporal.append((x, y))
                        x0, y0 = self.area_recorte_temporal[0]
                        x1, y1 = self.area_recorte_temporal[1]
                        self.area_recorte = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
                        self.area_recorte_temporal = None
                        self.redibujar_todo()
                    self.dibujando = False
                elif evento.type == pygame.MOUSEMOTION and self.dibujando:
                    x, y = evento.pos
                    if y > 40:
                        if self.herramienta_actual == "lapiz":
                            self.dibujar_pixel(x, y)
                        elif self.herramienta_actual == "borrador":
                            self.borrar_en(x, y)
                        self.redibujar_todo()
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_g and not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        self.mostrar_cuadricula = not self.mostrar_cuadricula
                        self.redibujar_todo()
                    elif evento.key == pygame.K_t:
                        self.grosor_linea = min(10, self.grosor_linea + 1)
                        self.redibujar_todo()
                    elif evento.key == pygame.K_g and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        self.grosor_linea = max(1, self.grosor_linea - 1)
                        self.redibujar_todo()
                    elif evento.key == pygame.K_ESCAPE:
                        self.area_recorte = None
                        self.area_recorte_temporal = None
                        self.redibujar_todo()
                    elif evento.key == pygame.K_c and self.herramienta_actual == "recortar" and self.area_recorte:
                        self.aplicar_recorte()
                        self.redibujar_todo()
            
            if self.herramienta_actual == "recortar" and self.area_recorte_temporal and len(self.area_recorte_temporal) == 1:
                self.redibujar_todo()
            
            pygame.time.wait(10)

# Crear y ejecutar la aplicación
def main():
    app = PaintOpenGL()
    app.ejecutar()
    pygame.quit()

main()