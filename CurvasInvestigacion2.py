import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def dibujar_cuadricula():
    """Dibuja una cuadrícula estilo AutoCAD con líneas muy finas"""
    glColor3f(0, 0, 0)  # Color gris claro
    glLineWidth(0.05)  # Líneas muy delgadas para la cuadrícula
    glBegin(GL_LINES)
    
    # Líneas verticales
    for x in range(-10, 21):
        glVertex2f(x, -10)
        glVertex2f(x, 20)
    
    # Líneas horizontales
    for y in range(-10, 21):
        glVertex2f(-10, y)
        glVertex2f(20, y)
    
    glEnd()

def dibujar_puntos(puntos, color, size=7):
    """Dibuja puntos en la pantalla"""
    glColor3f(*color)
    glPointSize(size)
    glBegin(GL_POINTS)
    for x, y in puntos:
        glVertex2f(x, y)
    glEnd()

def dibujar_linea(puntos, color, width=5):
    """Dibuja una línea conectando los puntos"""
    glColor3f(*color)
    glLineWidth(width)
    glBegin(GL_LINE_STRIP)
    for x, y in puntos:
        glVertex2f(x, y)
    glEnd()

def bspline_basis(t):
    """Calcula las funciones base de la B-Spline"""
    t2 = t * t
    t3 = t2 * t
    b0 = (1 - t)**3 / 6
    b1 = (3*t3 - 6*t2 + 4) / 6
    b2 = (-3*t3 + 3*t2 + 3*t + 1) / 6
    b3 = t3 / 6
    return [b0, b1, b2, b3]

def generar_bspline(puntos_control):
    """Genera la curva B-Spline a partir de los puntos de control"""
    if len(puntos_control) < 4:
        return []
    
    curva = []
    for i in range(len(puntos_control) - 3):
        p0, p1, p2, p3 = puntos_control[i:i+4]
        
        for t in [j/20 for j in range(21)]:
            b = bspline_basis(t)
            x = b[0]*p0[0] + b[1]*p1[0] + b[2]*p2[0] + b[3]*p3[0]
            y = b[0]*p0[1] + b[1]*p1[1] + b[2]*p2[1] + b[3]*p3[1]
            curva.append((x, y))
    
    return curva

def ingresar_puntos_teclado():
    """Solicita al usuario los puntos de control por teclado"""
    try:
        num = int(input("Ingrese número de puntos de control (mínimo 4): "))
        if num < 4:
            print("Se necesitan al menos 4 puntos")
            return None
        
        puntos = []
        print("Ingrese coordenadas x y (ejemplo: '2 3'):")
        for i in range(num):
            while True:
                try:
                    x, y = map(float, input(f"Punto {i+1}: ").split())
                    puntos.append((x, y))
                    break
                except:
                    print("Entrada inválida, intente nuevamente")
        return puntos
    except:
        print("Error en entrada")
        return None

def capturar_puntos_mouse():
    """Captura puntos de control mediante clics del mouse"""
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluOrtho2D(0, 20, 0, 20)
    glClearColor(1.0, 1.0, 1.0, 1.0)
    
    puntos = []
    font = pygame.font.Font(None, 36)
    
    print("\nInstrucciones:")
    print("- Clic izquierdo: Agregar punto")
    print("- Enter: Confirmar (mínimo 4 puntos)")
    print("- ESC: Cancelar")
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(puntos) >= 4:
                    pygame.quit()
                    return puntos
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                viewport = glGetIntegerv(GL_VIEWPORT)
                mouse_x, mouse_y = event.pos
                world_x = mouse_x / viewport[2] * 20
                world_y = (viewport[3] - mouse_y) / viewport[3] * 20
                puntos.append((world_x, world_y))
                print(f"Punto agregado: ({world_x:.2f}, {world_y:.2f})")
        
        glClear(GL_COLOR_BUFFER_BIT)
        dibujar_cuadricula()
        
        if puntos:
            dibujar_puntos(puntos, (1.0, 0.0, 0.0), 5)
            dibujar_linea(puntos, (0.5, 0.5, 0.5), 2)
            
            if len(puntos) >= 4:
                curva = generar_bspline(puntos)
                dibujar_linea(curva, (0.0, 0.0, 1.0), 4)
        
        pygame.display.flip()

def main():
    """Función principal"""
    print("¿Cómo desea ingresar los puntos?")
    print("1. Por teclado (ingrese 't')")
    print("2. Por mouse (ingrese 'm')")
    
    while True:
        opcion = input("Seleccione opción (t/m): ").lower()
        if opcion == 't':
            puntos = ingresar_puntos_teclado()
            break
        elif opcion == 'm':
            puntos = capturar_puntos_mouse()
            break
        else:
            print("Opción inválida, intente nuevamente")
    
    if not puntos:
        return
    
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluOrtho2D(0, 20, 0, 20)
    glClearColor(1.0, 1.0, 1.0, 1.0)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:  # Reiniciar con la tecla R
                    main()
                    return
        
        glClear(GL_COLOR_BUFFER_BIT)
        dibujar_cuadricula()
        dibujar_puntos(puntos, (1.0, 0.0, 0.0), 5)
        dibujar_linea(puntos, (0.5, 0.5, 0.5), 2)
        
        curva = generar_bspline(puntos)
        if curva:
            dibujar_linea(curva, (0.0, 0.0, 1.0), 4)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()