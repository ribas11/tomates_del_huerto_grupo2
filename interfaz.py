from tkinter import *
import tkinter as tk
from tkinter import messagebox
from unicodedata import decimal
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import time
import datetime
import tkinter.scrolledtext as scrolledtext
import re
import matplotlib
import math

# Paleta de colores básica
COLOR_BG = "#f0f0f0"      
COLOR_PANEL = "#ffffff"   
COLOR_ACCENT = "#82bfe5"
COLOR_ACCENT2 = "#3b82f6"
COLOR_TEXT = "#000000"
COLOR_WARN = "#f97316"




matplotlib.use('TkAgg')

#Grafica Orbita
# ----------------- Constantes y datos -----------------
R_EARTH = 6371000  # Constante para la esfera terrestre

# Compilación regex
regex_posicion = re.compile(r"Position: \(X: ([\d\.-]+) m, Y: ([\d\.-]+) m, Z: ([\d\.-]+) m\)")

# Listas
x_vals_orbita = []
y_vals_orbita = []
z_vals_orbita = []

# Referencias a objetos para la gráfica
fig_orbita = None
ax_orbita = None
orbit_plot = None
last_point_plot = None
earth_slice = None
canvas_orbita = None

ventana_orbita_abierta = False

def draw_earth_slice(z):
    if abs(z) <= R_EARTH:
        slice_radius = math.sqrt(R_EARTH*2 - z*2)
    else:
        slice_radius = 0
    circle = plt.Circle((0, 0),
                        slice_radius,
                        color='orange',
                        fill=False,
                        linestyle='--')
    return circle

def inicializar_grafica_orbita(parent):
    """
    Inicializa la figura, ejes y elementos de la gráfica de órbita.
    parent: ventana Tkinter donde se incrustará la gráfica.
    """
    global fig_orbita, ax_orbita, orbit_plot, last_point_plot, earth_slice, canvas_orbita

    # Crear figura y ejes
    fig_orbita, ax_orbita = plt.subplots(figsize=(10, 8))

    # 1. Línea de la órbita (línea azul con puntos)
    orbit_plot, = ax_orbita.plot(
        [], [],                    # Datos iniciales vacíos
        'bo-',                     # Formato: puntos azules ('b') con línea ('-')
        markersize=2,              # Tamaño de los puntos
        label='Órbita satélite'    # Etiqueta para la leyenda
    )

    # 2. Último punto (punto rojo más grande)
    last_point_plot = ax_orbita.scatter(
        [], [],                    # Posición inicial vacía
        color='red',               # Color rojo
        s=50,                      # Tamaño del punto
        label='Última posición'    # Etiqueta
    )

    # 3. Círculo de la superficie de la Tierra (fijo)
    tierra = plt.Circle(
        (0, 0),                    # Centro en el origen
        R_EARTH,                   # Radio de la Tierra
        color='orange',            # Color naranja
        fill=False,                # Solo borde
        label='Superficie Tierra'  # Etiqueta
    )
    ax_orbita.add_artist(tierra)

    # 4. Círculo del corte inicial (z=0, radio máximo)
    earth_slice = draw_earth_slice(0)  # Corte en el ecuador
    ax_orbita.add_artist(earth_slice)

    # 5. Configuración de los ejes
    ax_orbita.set_xlim(-7e6, 7e6)      # Límites X iniciales (±7 millones de metros)
    ax_orbita.set_ylim(-7e6, 7e6)      # Límites Y iniciales
    ax_orbita.set_aspect('equal', 'box')  # Mantiene proporciones iguales
    ax_orbita.set_xlabel('X (metros)')     # Etiqueta eje X
    ax_orbita.set_ylabel('Y (metros)')     # Etiqueta eje Y
    ax_orbita.set_title('Órbita del satélite - Vista desde el polo norte')
    ax_orbita.grid(True)               # Activa la cuadrícula
    ax_orbita.legend()                 # Muestra la leyenda

    # 6. Incrustar la figura en Tkinter
    canvas_orbita = FigureCanvasTkAgg(fig_orbita, master=parent)
    canvas_orbita.draw()  # Dibuja la figura inicialmente
    canvas_widget = canvas_orbita.get_tk_widget()
    canvas_widget.pack(fill="both", expand=True)  # Ocupa todo el espacio disponible

def actualizar_grafica_orbita():
    """
    Actualiza todos los elementos de la gráfica de órbita con los datos más recientes.
    Se ejecuta cada vez que llega una nueva posición del satélite.
    """
    global orbit_plot, last_point_plot, earth_slice, canvas_orbita, ax_orbita

    # Verificaciones de seguridad
    if orbit_plot is None or last_point_plot is None or earth_slice is None:
        print("Gráfica no inicializada aún")
        return
    if len(x_vals_orbita) == 0:
        print("No hay datos de posición")
        return
    if not ventana_orbita_abierta:
        return

    # 1. Actualizar la línea de la órbita (toda la trayectoria)
    orbit_plot.set_data(x_vals_orbita, y_vals_orbita)

    # 2. Actualizar el último punto (punto rojo)
    ultimo_x = x_vals_orbita[-1]
    ultimo_y = y_vals_orbita[-1]
    last_point_plot.set_offsets([[ultimo_x, ultimo_y]])

    # 3. Actualizar el círculo de corte de la Tierra
    ultima_z = z_vals_orbita[-1]
    try:
        if earth_slice is not None:
            earth_slice.remove()  # Elimina el círculo anterior si existe
    except:
        pass  # Si falla, continuar
    nuevo_slice = draw_earth_slice(ultima_z)  # Crea uno nuevo con la z actual
    earth_slice = nuevo_slice  # Actualiza la referencia global
    ax_orbita.add_artist(earth_slice)  # Añade el nuevo círculo al eje 

    # 4. Ajustar límites de los ejes si es necesario
    xlim_actual = ax_orbita.get_xlim()
    ylim_actual = ax_orbita.get_ylim()
    
    # Si el nuevo punto está fuera de los límites actuales, expandir
    if (abs(ultimo_x) > max(abs(xlim_actual[0]), abs(xlim_actual[1])) or 
        abs(ultimo_y) > max(abs(ylim_actual[0]), abs(ylim_actual[1]))):
        
        # Calcular nuevos límites con un margen del 10%
        nuevo_xlim = max(abs(xlim_actual[0]), abs(xlim_actual[1]), abs(ultimo_x)) * 1.1
        nuevo_ylim = max(abs(ylim_actual[0]), abs(ylim_actual[1]), abs(ultimo_y)) * 1.1
        
        ax_orbita.set_xlim(-nuevo_xlim, nuevo_xlim)
        ax_orbita.set_ylim(-nuevo_ylim, nuevo_ylim)
        
        print(f"Límites actualizados: X=[{-nuevo_xlim:.0f}, {nuevo_xlim:.0f}], Y=[{-nuevo_ylim:.0f}, {nuevo_ylim:.0f}]")

    # 5. Redibujar la figura en el canvas de Tkinter
    canvas_orbita.draw()

    # Información de depuración (opcional)
    print(f"Órbita actualizada: {len(x_vals_orbita)} puntos, última posición (X={ultimo_x:.0f}, Y={ultimo_y:.0f}, Z={ultima_z:.0f})")


def mostrar_ventana_orbita():
    """
    Crea y muestra la ventana de la gráfica de órbita.
    Se llama cuando el usuario pulsa el botón "Mostrar órbita".
    """
    global ventana_orbita_abierta

    # Evitar abrir múltiples ventanas
    if ventana_orbita_abierta:
        print("La ventana de órbita ya está abierta")
        return

    # Marcar que la ventana está abierta
    ventana_orbita_abierta = True
    print("Abriendo ventana de órbita...")

    # Crear la nueva ventana (hija de la ventana principal)
    ventana_orbita = tk.Toplevel(window)
    ventana_orbita.title("Gráfica de órbita del satélite")
    ventana_orbita.geometry("900x700")  # Tamaño recomendado para la gráfica
    ventana_orbita.resizable(True, True)  # Permitir redimensionar

    # Función para manejar el cierre de la ventana
    def cerrar_ventana_orbita():
        global ventana_orbita_abierta
        ventana_orbita_abierta = False
        # Enviar comando para parar la órbita
        mensaje = "3:OrbitaParar\n"
        mySerial.write(mensaje.encode('utf-8'))
        print("Comando enviado: parar órbita")
        registrar_evento("comando", "OrbitaParar")
        print("Ventana de órbita cerrada")
        ventana_orbita.destroy()

    # Vincular el cierre de ventana al manejador
    ventana_orbita.protocol("WM_DELETE_WINDOW", cerrar_ventana_orbita)

    # Configurar la ventana para que la gráfica ocupe todo el espacio
    ventana_orbita.columnconfigure(0, weight=1)
    ventana_orbita.rowconfigure(0, weight=1)

    # Inicializar la gráfica dentro de esta ventana
    inicializar_grafica_orbita(ventana_orbita)

    # Botón opcional para limpiar datos (útil para pruebas)
    frame_botones = tk.Frame(ventana_orbita)
    frame_botones.pack(fill="x", padx=5, pady=5)
    
    def limpiar_datos():
        global x_vals_orbita, y_vals_orbita, z_vals_orbita
        x_vals_orbita.clear()
        y_vals_orbita.clear()
        z_vals_orbita.clear()
        actualizar_grafica_orbita()
        print("Datos de órbita limpiados")
    
    def iniciar_orbita():
        mensaje = "3:OrbitaInicio\n"
        mySerial.write(mensaje.encode('utf-8'))
        print("Comando enviado: 3:iniciar órbita")
        registrar_evento("comando", "OrbitaInicio")
    
    def parar_orbita():
        mensaje = "3:OrbitaParar\n"
        mySerial.write(mensaje.encode('utf-8'))
        print("Comando enviado: parar órbita")
        registrar_evento("comando", "OrbitaParar")

    btn_iniciar = tk.Button(frame_botones, text="Iniciar órbita", 
                           command=iniciar_orbita, bg="green", fg="white")
    btn_iniciar.pack(side="left", padx=5)
    
    btn_parar = tk.Button(frame_botones, text="Parar órbita", 
                         command=parar_orbita, bg="red", fg="white")
    btn_parar.pack(side="left", padx=5)

    btn_limpiar = tk.Button(frame_botones, text="Limpiar órbita", 
                           command=limpiar_datos, bg="lightcoral")
    btn_limpiar.pack(side="left", padx=5)

    btn_cerrar = tk.Button(frame_botones, text="Cerrar ventana", 
                          command=cerrar_ventana_orbita, bg="lightgray")
    btn_cerrar.pack(side="right", padx=5)

    # Enviar comando para iniciar la órbita al abrir la ventana
    iniciar_orbita()
    
    print("Ventana de órbita creada exitosamente")

def hilo_posicion():
    """
    Hilo independiente que lee continuamente del puerto serie buscando datos de posición.
    NO modifica directamente la GUI, solo añade datos a las listas y programa actualizaciones.
    """
    global mySerial, regex_posicion, ventana_orbita_abierta
    print("Hilo de posición iniciado - escuchando puerto serie...")

    while True:
        try:
            # Verificar si hay datos esperando en el puerto serie
            if mySerial.in_waiting > 0:
                # Leer una línea completa del puerto serie
                line = mySerial.readline().decode('utf-8', errors='ignore').rstrip()
                
                # Solo procesar líneas que contengan "Position:" (datos de órbita)
                if "Position:" in line:
                    # Buscar patrón de posición del satélite en la línea
                    match = regex_posicion.search(line)
                    
                    if match:
                        try:
                            # Extraer las coordenadas X, Y, Z
                            x = float(match.group(1))  # Grupo 1 = X
                            y = float(match.group(2))  # Grupo 2 = Y
                            z = float(match.group(3))  # Grupo 3 = Z
                            
                            # AÑADIR A LAS LISTAS GLOBALES (esto es seguro desde cualquier hilo)
                            x_vals_orbita.append(x)
                            y_vals_orbita.append(y)
                            z_vals_orbita.append(z)
                            
                            # Mostrar información en consola
                            print(f"Posición recibida: X={x:.0f}m, Y={y:.0f}m, Z={z:.0f}m")
                            print(f"Total puntos en órbita: {len(x_vals_orbita)}")
                            
                            # SI LA VENTANA ESTÁ ABIERTA, programar actualización en el hilo principal
                            if ventana_orbita_abierta:
                                # window.after(0, ...) ejecuta la función en el hilo principal de Tkinter
                                window.after(0, actualizar_grafica_orbita)
                            
                        except ValueError as e:
                            # Ignorar errores de conversión silenciosamente (datos corruptos)
                            pass
                    # Si no coincide con el patrón, ignorar silenciosamente (probablemente corrupto)
                # Si la línea no contiene "Position:", la ignoramos silenciosamente
                # (será procesada por recepcion() si corresponde)
                        
            # Pequeña pausa para no saturar el CPU (10ms)
            time.sleep(0.01)
            
        except serial.SerialException as e:
            print(f"Error de comunicación serie: {e}")
            time.sleep(1)  # Esperar antes de reintentar
        except UnicodeDecodeError:
            # Datos corruptos por LoRa, ignorar silenciosamente
            pass
        except Exception as e:
            print(f"Error inesperado en hilo_posicion: {e}")
            time.sleep(0.5)









# device = 'COM7'
# mySerial = serial.Serial(device, 9600)

device = "COM7"
try:
    mySerial = serial.Serial(device, 9600)
except:
    print("⚠ No se encontró el puerto COM5. Ejecutando en modo SIMULACIÓN.")
    class SerialFake:
        def _init_(self):
            self.in_waiting = 0
        def readline(self):
            return b""
        def write(self, x):
            print("SIMULACIÓN -> Arduino recibiría:", x.decode().strip())
        def reset_input_buffer(self):
            pass
    mySerial = SerialFake()
# Forzar modo manual en el satélite al iniciar
try:
    mySerial.write(b"3:RadarManual\n")
except Exception as e:
    print(f"No se pudo enviar comando inicial de radar manual: {e}")



# Configurar la figura y el eje para la gráfica
fig, ax = plt.subplots(figsize=(6,4), dpi=100)
fig.patch.set_facecolor(COLOR_PANEL)
ax.set_xlim(0, 100)
ax.set_ylim(15, 35)
ax.grid(True, which='both', color = "gray", linewidth=0.5)
ax.set_title('Gráfica dinámica Temperatura[ºC] - Tiempo[s]:')
ax.set_facecolor("#ffffff")



mediaT = None #Variable de la media de la temperatura



temperaturas = []
eje_x = []
i = 0
pararTemp = True  # Empieza parado
pararRad = True  # Empieza parado
threadRecepcion = None
periodoTH = 5
ultimas_temperaturas = []
medias_plot_x = []
medias_plot_val = []
mensaje = ""  

grafica_activa = None  # Puede ser: temperatura, radar...
error_activo = False
modo_manual = True  # Arranca en manual
radar_canvas = None
control_deslizante = None
valor_servo = None
temp_window = None
radar_window = None
extra_window = None
canvas = None
last_start_ts = 0  # Para suprimir falsos errores de comunicaciones al inicio
GRACE_ERROR_SEC = 8

# ==== FICHEROS DE EVENTOS ====
def limpiar_archivos():
    archivos = ["comandos.txt", "alarmas.txt", "registrotemphum.txt", "observaciones.txt"]
    for archivo in archivos:
        with open(archivo, "w") as f:  
            f.write("")  
limpiar_archivos()
def registrar_evento(tipo_comando, detalles=""):
    ahora = datetime.datetime.now()
    fecha_hora = ahora.strftime("%d-%m-%Y %H:%M:%S")
    # Diccionario con los nombres de archivos
    archivos = {
        "comando": "comandos.txt",
        "alarma": "alarmas.txt",
        "temperatura": "registrotemphum.txt",
        "observacion": "observaciones.txt"
    }   
    # Escribir en el archivo correspondiente
    if tipo_comando in archivos:
        with open(archivos[tipo_comando], "a") as f:  # "a" = append (añadir)
            f.write(f"{fecha_hora} {detalles}\n")
            f.flush()
def PopUp(fichero):
    fichero = str(fichero)
    ventana_popup = tk.Toplevel()
    ventana_popup.title("Contenido del archivo")
    ventana_popup.geometry("600x400")
    texto = scrolledtext.ScrolledText(ventana_popup, wrap=tk.WORD)
    texto.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    contenido = open(fichero, "r", encoding="utf-8").read()
    texto.insert(tk.END, contenido)
    texto.config(state=tk.DISABLED)  
    boton = tk.Button(ventana_popup, text="Cerrar", command=ventana_popup.destroy)
    boton.pack(pady=10)
def PopUpComandosClick():
    tipofichero = "comandos.txt"
    PopUp(tipofichero)
def PopUpAlarmasClick():
    tipofichero = "alarmas.txt"
    PopUp(tipofichero)
def PopUpTemperaturasClick():
    tipofichero = "registrotemphum.txt"
    PopUp(tipofichero)  
def PopUpObservacionesClick():
    tipofichero = "observaciones.txt"
    PopUp(tipofichero)
# =============================


def recepcion():
    global i, pararTemp, temperaturas, eje_x, mySerial, periodoTH, mensaje, pararRad
    mySerial.reset_input_buffer()
    while (pararTemp == False or pararRad == False):
        if mySerial.in_waiting > 0:
            try:
                line = mySerial.readline().decode('utf-8', errors='ignore').rstrip()
                print(line)
            except:
                continue  # Si hay error de decodificación, ignorar la línea
            
            # Ignorar líneas vacías o muy cortas (probablemente corruptas)
            if len(line) < 2:
                continue
            
            # Ignorar líneas de órbita (son procesadas por hilo_posicion)
            if "Position:" in line:
                continue
            
            # Validar que la línea comienza con un dígito (código válido)
            if not line[0].isdigit():
                continue
            
            trozos = line.split(':')
            
            # Validar que hay al menos un código y un valor
            if len(trozos) < 2:
                continue

            # TEMPERATURA - solo si está activada
            if trozos[0] == '1' and pararTemp == False and len(trozos) >= 3:
                CerrarVentanaError() 
                try:
                    temperatura = float(trozos[1])
                    # Validar que la temperatura esté en un rango razonable (-50 a 100°C)
                    if temperatura < -50 or temperatura > 100:
                        continue  # Ignorar datos fuera de rango (probablemente corruptos)
                    eje_x.append(i)
                    temperaturas.append(temperatura)
                    i += periodoTH

                    # Actualizar buffer para media rápida en tierra
                    ultimas_temperaturas.append(temperatura)
                    if len(ultimas_temperaturas) > 10:
                        ultimas_temperaturas.pop(0)
                    if len(ultimas_temperaturas) == 10:
                        media_local = sum(ultimas_temperaturas) / 10
                        medias_plot_x.append(eje_x[-1])
                        medias_plot_val.append(media_local)
                        safe_set_label(mediaLabel, f"Media T:\n{media_local:.2f} °C")
                        safe_set_label(calculomediaLabel, "Calculando media en:\n Estación Tierra")
                        print(f"Media local (10 muestras): {media_local:.2f}°C")

                    ax.cla()
                    ax.plot(eje_x, temperaturas, label="Temperatura", color="blue")
                    if len(medias_plot_val) > 0:
                        ax.plot(medias_plot_x, medias_plot_val, label="Media (10)", color="orange", linestyle="--")
                    ax.set_xlim(max(0, i-15), i+5)
                    ax.set_ylim(15, 35)
                    ax.set_title('Gráfica dinámica Temperatura[ºC] - Tiempo[s]:')
                    ax.legend()
                    ax.grid(True, which='both', color="gray", linewidth=0.5)
                    canvas.draw()

                    registrar_evento("temperatura", f"Temp:{temperatura:.2f}C Hum:{trozos[2] if len(trozos) > 2 else 'N/A'}%")
                except (ValueError, IndexError):
                    # Ignorar datos corruptos silenciosamente
                    continue

            # MEDIA
            if trozos[0] == '4' and len(trozos) >= 2:
                try:
                    media = float(trozos[1])
                    # Validar que la media esté en un rango razonable
                    if media < -50 or media > 100:
                        continue  # Ignorar datos fuera de rango
                    # Sincronizar con el último punto recibido
                    x_media = eje_x[-1] if len(eje_x) > 0 else len(medias_plot_x) * periodoTH
                    medias_plot_x.append(x_media)
                    medias_plot_val.append(media)
                    safe_set_label(mediaLabel, f"Media T:\n{media:.2f} °C")
                    safe_set_label(calculomediaLabel, "Calculando media en:\n Satélite")
                    print(f"Media recibida: {media:.2f}°C")
                except (ValueError, IndexError):
                    # Ignorar datos corruptos silenciosamente
                    continue

            # RADAR - solo si está activado
            if trozos[0] == '2' and pararRad == False and len(trozos) >= 3:
                try:
                    distancia = float(trozos[1])
                    angulo = float(trozos[2])
                    # Validar rangos razonables
                    if distancia < 0 or distancia > 500 or angulo < 0 or angulo > 180:
                        continue  # Ignorar datos fuera de rango
                    RadarAutomatico(distancia, angulo)
                except (ValueError, IndexError):
                    # Ignorar datos corruptos silenciosamente
                    continue

            # ERROR
            if trozos[0] == '0' and len(trozos) >= 2:
                try:
                    error_msg = trozos[1] if len(trozos) > 1 else "Error desconocido"
                    # Validar que el mensaje de error sea exactamente uno de los errores conocidos
                    # Esto previene mostrar mensajes corruptos por LoRa
                    errores_validos = ["ErrorComunicaciones", "ErrorCapturaDatos", "ErrorSensorDistancia"]
                    error_valido = False
                    
                    # Verificar si el mensaje coincide exactamente con algún error conocido
                    for error_conocido in errores_validos:
                        if error_msg == error_conocido:
                            error_valido = True
                            break
                    
                    # También verificar si el mensaje contiene el error conocido (para tolerar pequeñas corrupciones)
                    if not error_valido:
                        for error_conocido in errores_validos:
                            # Verificar si el mensaje es similar al error conocido (tolerar hasta 2 caracteres diferentes)
                            if len(error_msg) >= len(error_conocido) - 2 and len(error_msg) <= len(error_conocido) + 2:
                                # Verificar que contenga la mayoría de los caracteres del error conocido
                                coincidencias = sum(1 for c in error_conocido if c in error_msg)
                                if coincidencias >= len(error_conocido) * 0.7:  # Al menos 70% de coincidencia
                                    error_valido = True
                                    error_msg = error_conocido  # Usar el error conocido en lugar del corrupto
                                    break
                    
                    if error_valido:
                        # Suprimir errores de comunicación en los primeros segundos tras un inicio
                        if error_msg == "ErrorComunicaciones" and (time.time() - last_start_ts) < GRACE_ERROR_SEC:
                            continue
                        print(f"Error del sistema: {error_msg}")
                        registrar_evento("alarma", error_msg)
                        # Solo mostrar ventana si no es ErrorComunicaciones (ya que se repite mucho)
                        # o si es otro tipo de error más crítico
                        if error_msg != "ErrorComunicaciones":
                            AbrirVentanaError(error_msg)
                        # Para ErrorComunicaciones, solo registrar en el archivo, no mostrar ventana popup
                except:
                    pass  # Ignorar errores corruptos silenciosamente


def ModoAutomaticoClick():
    global modo_manual, mensaje, valor_servo
    modo_manual = False
    valor_servo.set(100)  # Volver el deslizante a 100 grados
    control_deslizante.config(state="disabled")  # Desactivar slider
    mensaje = "3:RadarAutomatico\n"
    mySerial.write(mensaje.encode('utf-8'))
    print("Radar en modo automático - deslizante en 100 grados")
    registrar_evento("comando", "RadarAutomatico")



           
def RadarAutomatico(distancia, angulo):
    if radar_canvas is None:
        return  # Ventana de radar no abierta
    # Obtener tamaño real del canvas
    width = radar_canvas.winfo_width()
    height = radar_canvas.winfo_height()



    if width <= 1 or height <= 1:
        return  # Canvas aún no inicializado



    # Centro del radar
    x0 = width / 2
    y0 = height



    # Radio máximo
    max_radius = min(width/2, height * 0.9)



    # Escala (distancia en cm → píxeles aproximadamente)
    escala = max_radius / 50  # 50 = distancia máxima enviada por Arduino



    # Calcular posición del punto rojo
    x = x0 + distancia * escala * math.cos(math.radians(angulo))
    y = y0 - distancia * escala * math.sin(math.radians(angulo))



    # Dibujar punto rojo
    punto_id = radar_canvas.create_oval(x-10, y-10, x+10, y+10, fill="red", width=0)



    # Eliminarlo tras 200 ms
    radar_canvas.after(200, lambda: radar_canvas.delete(punto_id))







def dibujar_radar_base():
    if radar_canvas is None:
        return
    # Limpiar el canvas
    radar_canvas.delete("all")
   
    # Dimensiones
    width = radar_canvas.winfo_width()
    height = radar_canvas.winfo_height()
   
    x0, y0 = width/2, height
    max_radius = min(width/2, height*0.9)
   
    # Dibujar punto central
    radar_canvas.create_oval(x0-5, y0-5, x0+5, y0+5, width=2, fill="black")
   
    # Dibujar semicírculos
    for r in range(1,6):
        radar_canvas.create_oval(x0-r*max_radius/5, y0-r*max_radius/5, x0+r*max_radius/5, y0+r*max_radius/5, width=2)
   
    # Textos de distancias
    radar_canvas.create_text(x0 + max_radius/5 + 30, y0 - 15, text="10", fill="black", font=("Arial", 13, "bold"))
    radar_canvas.create_text(x0 + 2*max_radius/5 + 30, y0 - 15, text="20", fill="black", font=("Arial", 13, "bold"))
    radar_canvas.create_text(x0 + 3*max_radius/5 + 30, y0 - 15, text="30", fill="black", font=("Arial", 13, "bold"))
    radar_canvas.create_text(x0 + 4*max_radius/5 + 30, y0 - 15, text="40", fill="black", font=("Arial", 13, "bold"))
    radar_canvas.create_text(x0 + max_radius + 30, y0 - 15, text="50", fill="black", font=("Arial", 13, "bold"))
   
    # Dibujar líneas de ángulo  
    for angle in range(0, 181, 30):
        rad = math.radians(angle)
        x_end = x0 + max_radius * math.cos(rad)
        y_end = y0 - max_radius * math.sin(rad)
        radar_canvas.create_line(x0, y0, x_end, y_end, width=1, fill="#ffffff")
   
    # Textos de ángulos
    offset = max_radius*0.06  # separación del borde del semicírculo
    for angle in range(30, 180, 30):
        rad = math.radians(angle)
        x_text = x0 + (max_radius + offset) * math.cos(rad)
        y_text = y0 - (max_radius + offset) * math.sin(rad)
        radar_canvas.create_text(x_text, y_text, text=f"{angle}°", fill="black", font=("Arial", 15, "bold"))


def InicioClick():
    global pararTemp, threadRecepcion, i, temperaturas, eje_x, mensaje, grafica_activa, last_start_ts
    
    if grafica_activa == "radar":
        PararClickRad()
        messagebox.showwarning("Aviso", "Se detuvo el radar para activar temperatura")
        return
    
    # Detener el hilo anterior si está corriendo
    if threadRecepcion is not None and threadRecepcion.is_alive():
        pararTemp = True
        threadRecepcion.join(timeout=1)
    
    # Limpiar el buffer serial antes de empezar
    mySerial.reset_input_buffer()
    
    # Reiniciar memeorias de datos
    temperaturas = [] # Vaciar lista de temperaturas
    eje_x = [] # Vaciar lista de tiempos
    i = 0 # Reiniciar contador
    ultimas_temperaturas = []
    medias_plot_x = []
    medias_plot_val = []
    
    # Reiniciar grafica
    ax.cla() # Limpiar el eje
    ax.set_xlim(0, 100)
    ax.set_ylim(15, 35)
    ax.grid(True, which='both', color = "gray", linewidth=0.5)
    ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')
    canvas.draw() # Redibuja la gráfica vacía
    
    # Enviar comando de inicio al Arduino
    pararTemp = False
    grafica_activa = "temperatura"  
    mensaje = "3:inicio\n"
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    last_start_ts = time.time()
    calculomediaLabel.config(text="Calculando media en:\n Satélite")
    registrar_evento("comando", "Inicio gráfica temperatura")
    
    # Iniciar recepcion
    threadRecepcion = threading.Thread(target=recepcion)
    threadRecepcion.daemon = True
    threadRecepcion.start()






def PararClick():
    global pararTemp, mensaje, grafica_activa
    
    pararTemp = True
    grafica_activa = None  
    mensaje = "3:parar\n" # Enviar comando al Arduino para que pare de enviar datos
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    mySerial.reset_input_buffer() # Limpiar buffer al parar
    registrar_evento("comando", "Pausa gráfica temperatura")






def ReanudarClick():
    global pararTemp, threadRecepcion, mensaje, grafica_activa, last_start_ts
    
    mySerial.reset_input_buffer() # Limpiar buffer antes de reanudar
    pararTemp = False
    grafica_activa = "temperatura"  
    mensaje = "3:reanudar\n" # Enviar comando de reanudar
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    last_start_ts = time.time()
    registrar_evento("comando", "Reactivación gráfica temperatura")
    
    threadRecepcion = threading.Thread(target=recepcion)
    threadRecepcion.daemon = True
    threadRecepcion.start()

   





def EnviarPeriodoClick(): # SOLUCIONAR QUE NO VA A MES DE 3 SEGONS
    global periodo_sensor, periodoTH
    periodo_input = periodoEntry.get()  # Obtener entrada
    periodo_sensor = int(periodo_input)
    if periodo_input == "" or periodo_sensor <= 0:  
        messagebox.showwarning("Advertencia", "Por favor, introduce un período válido")
        return
    mensaje = f"4:{periodo_sensor}\n"
    print(f"Enviando período: {mensaje}")
    mySerial.write(mensaje.encode('utf-8'))
    periodoTH = int(periodo_sensor/1000)
    messagebox.showinfo("Éxito", f"Período configurado a {periodo_sensor} ms")
    registrar_evento("comando", f"Cambio de periodo temperatura a {periodo_sensor} ms")
    
       
def CalcularMediaTSat():
    global mensaje
    mensaje = "3:MediaSAT\n"
    mySerial.write(mensaje.encode('utf-8'))
    mediaLabel.config(text="Media T: \n(calculando...)")
    calculomediaLabel.config(text="Calculando media en:\n Satélite")
    registrar_evento("comando", "Calculando la media de temperatura en el satelite")
def CalcularMediaTTER():
    global mensaje
    mensaje = "3:MediaTER\n"
    mySerial.write(mensaje.encode('utf-8'))
    mediaLabel.config(text="Media T:\n (calculando...)")
    calculomediaLabel.config(text="Calculando media en:\n Estación Tierra")
    registrar_evento("comando", "Calculando la media de temperatura en estación de tierra")

def InicioClickRad():
    global pararRad, threadRecepcion, grafica_activa, last_start_ts
    
    
    if grafica_activa == "temperatura":
        PararClick()
        messagebox.showwarning("Aviso", "Se detuvo temperatura para activar radar")
        return
    
    if threadRecepcion is not None and threadRecepcion.is_alive():
        pararRad = True
        threadRecepcion.join(timeout=1)
    
    pararRad = False
    grafica_activa = "radar"  
    mensaje = "6:inicio\n"
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    last_start_ts = time.time()
    threadRecepcion = threading.Thread(target=recepcion)
    threadRecepcion.daemon = True
    threadRecepcion.start()
    registrar_evento("comando", "Inicio gráfica radar")

def PararClickRad():
    global pararRad, threadRecepcion, grafica_activa
    
    pararRad = True
    grafica_activa = None  
    mensaje = "6:parar\n" # Enviar comando al Arduino para que pare de enviar datos
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    mySerial.reset_input_buffer() # Limpiar buffer al parar
    registrar_evento("comando", "Pausa gráfica radar")


def RadarManual():
    global modo_manual, mensaje, valor_servo
    modo_manual = True
    valor_servo.set(100)  # Volver el deslizante a 100 grados
    control_deslizante.config(state="normal")  # Activar slider
    mensaje = "3:RadarManual\n"  # Solo activa modo manual (servo volverá a 100)
    mySerial.write(mensaje.encode('utf-8'))
    print("Radar en modo manual - deslizante en 100 grados")
    registrar_evento("comando", "Radar en modo manual")



def EnviarServo(valor):
    if modo_manual:  # Solo enviar si estamos en manual
        valor_int = int(float(valor))
        mensaje = f"3:RadarManual:{valor_int}\n"
        mySerial.write(mensaje.encode('utf-8'))
        print(f"Enviando valor servo: {valor_int}")
        registrar_evento("comando", f"Cambio valor del servo a: {valor_int}")

def on_resize(event):
    dibujar_radar_base()

def safe_set_label(lbl, text):
    try:
        if lbl is not None and lbl.winfo_exists():
            lbl.config(text=text)
    except Exception:
        pass

# ==== FUNCION ERROR ====
def AbrirVentanaError(error):
    global error_activo, VenEr
    if error_activo == False:
        error_activo = True
        VenEr = tk.Toplevel(window)
        VenEr.geometry("600x300")
        VenEr.title("ERROR")
        VenEr.configure(bg="#2600FF")
        tk.Label(
            VenEr,
            text="¡" + error + "!",
            font=("Arial", 20, "bold"),
            fg="red",
            bg="#FFE5E5"
        ).pack(pady=(20, 10))  
        tk.Label(
            VenEr,
            text="No se ha captar datos de\ntemperatura y humedad.\nPor favor, revisa el sistema.",
            font=("Arial", 14),
            fg="darkred",
            bg="#FFE5E5",
            justify="center"  
        ).pack(pady=5)
        def evitar_cierre():
            messagebox.showwarning("Aviso", "No puedes cerrar esta ventana, el error aun persiste.")
        if error_activo == True:
            VenEr.protocol("WM_DELETE_WINDOW", evitar_cierre)
        elif error_activo == False:
            VenEr.destroy()
def CerrarVentanaError():
    global VenEr, error_activo
    if error_activo == True:
        error_activo = False
        VenEr.destroy()

# Registro observaciones
def RegistrarObservacion():
    observacion = ObservacionesEntry.get()  
    messagebox.showinfo("Éxito", "Éxito, observación registrada")
    registrar_evento("observacion", observacion)
    ObservacionesEntry.delete(0, tk.END)



# ===== VENTANA PRINCIPAL Y SUBVENTANAS =====
window = Tk()
window.withdraw()  # Ocultar ventana principal hasta usuario sea correcto
window.title("Mesa de Control")
window.geometry("1100x600")
window.configure(bg=COLOR_BG)
window.rowconfigure(2, weight=1)
window.columnconfigure(0, weight=1)

temp_window = None
radar_window = None
extra_window = None
radar_canvas = None
canvas = None

def cerrar_ventana_temperatura():
    global temp_window, canvas, mediaLabel, calculomediaLabel
    PararClick()
    if temp_window is not None:
        temp_window.destroy()
        temp_window = None
    canvas = None
    mediaLabel = None
    calculomediaLabel = None

def cerrar_ventana_radar():
    global radar_window, radar_canvas
    PararClickRad()
    radar_canvas = None
    if radar_window is not None:
        radar_window.destroy()
        radar_window = None

def cerrar_ventana_extra():
    global extra_window
    if extra_window is not None:
        extra_window.destroy()
        extra_window = None

def abrir_ventana_temperatura():
    global temp_window, canvas, mediaLabel, calculomediaLabel, periodoEntry
    if temp_window is not None:
        temp_window.lift()
        return
    temp_window = tk.Toplevel(window)
    temp_window.title("Temperatura y Humedad")
    temp_window.geometry("900x600")
    temp_window.configure(bg=COLOR_BG)
    temp_window.protocol("WM_DELETE_WINDOW", cerrar_ventana_temperatura)

    frame_graph = tk.LabelFrame(temp_window, text="Gráfica temperatura", font=("Courier", 15, "italic"), bg=COLOR_PANEL, fg=COLOR_TEXT)
    frame_graph.pack(fill="both", expand=True, padx=5, pady=5)

    # Re-emplazar canvas en este contenedor
    canvas = FigureCanvasTkAgg(fig, master=frame_graph)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    frame_controles = tk.Frame(temp_window, bg=COLOR_BG)
    frame_controles.pack(fill="x", padx=5, pady=5)

    btn_inicio = tk.Button(frame_controles, text="Inicio", bg=COLOR_ACCENT, fg="white", font=("Arial", 30), command=InicioClick)
    btn_inicio.pack(side="left", padx=3, pady=3, expand=True, fill="x")
    btn_parar = tk.Button(frame_controles, text="Parar", bg=COLOR_WARN, fg="white", font=("Arial", 30), command=PararClick)
    btn_parar.pack(side="left", padx=3, pady=3, expand=True, fill="x")
    btn_reanudar = tk.Button(frame_controles, text="Reanudar", bg=COLOR_ACCENT2, fg="white", font=("Arial", 30), command=ReanudarClick)
    btn_reanudar.pack(side="left", padx=3, pady=3, expand=True, fill="x")

    btn_media_sat = tk.Button(frame_controles, text="Media en Satélite", bg='#7c3aed', fg='white', font=("Arial", 25), command=CalcularMediaTSat)
    btn_media_sat.pack(side="left", padx=3, pady=3)
    btn_media_ter = tk.Button(frame_controles, text="Media en Tierra", bg='#7c3aed', fg='white', font=("Arial", 25), command=CalcularMediaTTER)
    btn_media_ter.pack(side="left", padx=3, pady=3)

    frame_periodo = tk.LabelFrame(temp_window, text="Período (ms)", font=("Courier", 12, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXT)
    frame_periodo.pack(fill="x", padx=5, pady=5)
    periodoEntry = tk.Entry(frame_periodo, font=("Courier", 12), width=10, bg="#fdfdfd", fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
    periodoEntry.insert(0, "5000")
    periodoEntry.pack(side="left", padx=5, pady=5)
    btn_periodo = tk.Button(frame_periodo, text="Enviar", bg=COLOR_ACCENT2, fg="white", command=EnviarPeriodoClick)
    btn_periodo.pack(side="left", padx=5, pady=5)

    frame_medias = tk.Frame(temp_window, bg=COLOR_PANEL, pady=8)
    frame_medias.pack(fill="x", padx=5, pady=5)
    mediaLabel = tk.Label(frame_medias, text="Media T: --- °C", font=("Courier", 18, "bold"), fg=COLOR_ACCENT, bg=COLOR_PANEL)
    mediaLabel.pack(side="left", padx=10)
    calculomediaLabel = tk.Label(frame_medias, text="Calculando media en:\n ---", font=("Courier", 14), fg=COLOR_TEXT, bg=COLOR_PANEL, justify="left")
    calculomediaLabel.pack(side="left", padx=10)

def abrir_ventana_radar():
    global radar_window, radar_canvas, control_deslizante, valor_servo
    if radar_window is not None:
        radar_window.lift()
        return
    radar_window = tk.Toplevel(window)
    radar_window.title("Radar")
    radar_window.geometry("750x600")
    radar_window.configure(bg=COLOR_BG)
    radar_window.protocol("WM_DELETE_WINDOW", cerrar_ventana_radar)

    radar_frame = tk.LabelFrame(radar_window, text="Radar satélite", font=("Courier", 15, "italic"), bg=COLOR_PANEL, fg=COLOR_TEXT)
    radar_frame.pack(fill="both", expand=True, padx=5, pady=5)

    radar_canvas = Canvas(radar_frame, width=400, height=300, bg="#247c32", highlightthickness=0)
    radar_canvas.pack(fill=tk.BOTH, expand=True)
    radar_canvas.bind("<Configure>", on_resize)
    dibujar_radar_base()

    frame_botones = tk.Frame(radar_window, bg=COLOR_BG)
    frame_botones.pack(fill="x", padx=5, pady=5)
    btn_inicio = tk.Button(frame_botones, text="Inicio", bg=COLOR_ACCENT, fg="white", font=("Arial", 30), command=InicioClickRad)
    btn_inicio.pack(side="left", padx=3, pady=3, expand=True, fill="x")
    btn_parar = tk.Button(frame_botones, text="Parar", bg=COLOR_WARN, fg="white", font=("Arial", 30), command=PararClickRad)
    btn_parar.pack(side="left", padx=3, pady=3, expand=True, fill="x")

    control_frame = tk.LabelFrame(radar_window, text="Control Servomotor", font=("Courier", 12, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXT)
    control_frame.pack(fill="x", padx=5, pady=5)

    valor_servo = tk.IntVar(value=100)
    control_deslizante = tk.Scale(
        control_frame,
        from_=0,
        to=180,
        orient=tk.HORIZONTAL,
        resolution=20,
        variable=valor_servo,
        length=250,
        command=EnviarServo,
        state="normal",
        bg=COLOR_PANEL,
        fg=COLOR_TEXT,
        troughcolor="#ffffff",
        highlightthickness=0
    )
    control_deslizante.pack(side="left", padx=5, pady=5, expand=True, fill="x")

    btn_auto = tk.Button(control_frame, text="Automático", bg=COLOR_ACCENT2, fg="white", command=ModoAutomaticoClick)
    btn_auto.pack(side="left", padx=5, pady=5)
    btn_manual = tk.Button(control_frame, text="Manual", bg=COLOR_WARN, fg="white", command=RadarManual)
    btn_manual.pack(side="left", padx=5, pady=5)

def abrir_ventana_extra():
    global extra_window
    if extra_window is not None:
        extra_window.lift()
        return
    extra_window = tk.Toplevel(window)
    extra_window.title("Extra")
    extra_window.geometry("500x300")
    extra_window.configure(bg=COLOR_BG)
    extra_window.protocol("WM_DELETE_WINDOW", cerrar_ventana_extra)
    tk.Label(extra_window, text="Cámara", font=("Courier", 16), fg=COLOR_TEXT, bg=COLOR_BG).pack(expand=True, fill="both", padx=10, pady=10)

# Distribución general de la ventana principal
window.rowconfigure(0, weight=1)   # título
window.rowconfigure(1, weight=3)   # botones grandes
window.rowconfigure(2, weight=2)   # registros
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)

# ===== TÍTULO ARRIBA =====
titulo = tk.Label(
    window,
    text="MESA DE CONTROL\nVersión 4",
    font=("Courier", 32, "bold"),
    fg=COLOR_TEXT,
    bg=COLOR_BG,
    justify="center"
)
titulo.grid(row=0, column=0, columnspan=2, pady=10)

# ===== BLOQUE CENTRAL: 4 BOTONES GRANDES =====
frame_central = tk.Frame(window, bg=COLOR_BG)
frame_central.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
frame_central.rowconfigure(0, weight=1)
frame_central.rowconfigure(1, weight=1)
frame_central.columnconfigure(0, weight=1)
frame_central.columnconfigure(1, weight=1)

btn_temp = tk.Button(
    frame_central,
    text="Ventana Temperaturas",
    font=("Arial", 20, "bold"),
    bg=COLOR_ACCENT,
    fg="black",
    command=abrir_ventana_temperatura
)
btn_temp.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

btn_radar = tk.Button(
    frame_central,
    text="Ventana Radar",
    font=("Arial", 20, "bold"),
    bg="#90ee90",   # verde claro estilo mockup
    fg="black",
    command=abrir_ventana_radar
)
btn_radar.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

btn_pos = tk.Button(
    frame_central,
    text="Ventana Gráficas Posición",
    font=("Arial", 20, "bold"),
    bg="#ffd166",
    fg="black",
    command=mostrar_ventana_orbita
)
btn_pos.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

btn_ver4 = tk.Button(
    frame_central,
    text="Ventana Versión 4",
    font=("Arial", 20, "bold"),
    bg="#ffb3ba",
    fg="black",
    command=abrir_ventana_extra
)
btn_ver4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

# ===== PARTE INFERIOR: REGISTROS =====
frame_logs = tk.LabelFrame(
    window,
    text="Ficheros de registro de eventos",
    font=("Courier", 12, "bold"),
    bg=COLOR_PANEL,
    fg=COLOR_TEXT
)
frame_logs.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0, 5))

# Más peso a la fila de observaciones para que crezca hacia arriba/abajo
frame_logs.rowconfigure(0, weight=1)   # fila de botones de registro
frame_logs.rowconfigure(1, weight=2)   # fila de “Observación a registrar”
for c in range(4):
    frame_logs.columnconfigure(c, weight=1)

config_reg = [
    ("Registro de comandos", PopUpComandosClick, "#b2f2ff"),
    ("Registro de alarmas", PopUpAlarmasClick, "#ffc9de"),
    ("Registro de temperaturas", PopUpTemperaturasClick, "#ffe066"),
    ("Registro de observaciones", PopUpObservacionesClick, "#caffbf"),
]

for col, (txt, cmd, color) in enumerate(config_reg):
    tk.Button(
        frame_logs,
        text=txt,
        command=cmd,
        font=("Arial", 14, "bold"),
        bg=color,
        fg="black"
    ).grid(row=0, column=col, sticky="nsew", padx=3, pady=3)

frame_obs = tk.Frame(frame_logs, bg=COLOR_PANEL)
frame_obs.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(5, 3))

tk.Label(
    frame_obs,
    text="Observación a registrar:",
    font=("Courier", 11),
    bg=COLOR_PANEL,
    fg=COLOR_TEXT
).grid(row=0, column=0, padx=5, sticky="w")

ObservacionesEntry = tk.Entry(
    frame_obs,
    font=("Courier", 11),
    width=60,
    bg="#ffffff",
    fg=COLOR_TEXT,
    insertbackground=COLOR_TEXT
)
ObservacionesEntry.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

tk.Button(
    frame_obs,
    text="Registrar",
    bg=COLOR_ACCENT2,
    fg="white",
    command=RegistrarObservacion
).grid(row=0, column=2, padx=5, pady=5, sticky="e")


# Iniciar hilo para leer datos de posición de órbita
thread_posicion = threading.Thread(target=hilo_posicion)
thread_posicion.daemon = True
thread_posicion.start()

#Funciones Log In
def mostrar_credenciales():
    top = tk.Toplevel(login)
    top.title("SOLO PERSONAL AUTORIZADO")
    top.geometry("650x220")
    top.configure(bg="#0d1b2a")

    tk.Label(
        top,
        text="USUARIO: miguelespacial",
        font=("Helvetica", 14, "bold"),
        fg="white",
        bg="#0d1b2a"
    ).pack(pady=(25, 10))

    tk.Label(
        top,
        text="CONTRASEÑA: contraseña",
        font=("Helvetica", 14, "bold"),
        fg="white",
        bg="#0d1b2a"
    ).pack(pady=(0, 20))

    tk.Button(
        top,
        text="Cerrar",
        font=("Helvetica", 12, "bold"),
        bg="#1b263b",
        fg="white",
        command=top.destroy
    ).pack(pady=5)


def validar_login(usuario_entry, pass_entry, info_label, error_label):
    usuario = usuario_entry.get().strip()
    contrasena = pass_entry.get().strip()

    if usuario == "miguelespacial" and contrasena == "contraseña":
        login.destroy()        # 👈 cerrar login
        window.deiconify()     # 👈 mostrar ventana principal
    else:
        error_label.config(text="Credenciales incorrectas", fg="red")
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")


def construir_login():
    login.geometry("900x600")
    login.configure(bg="#0d1b2a")
    login.columnconfigure(0, weight=1)
    login.rowconfigure(0, weight=1)

    contenedor = tk.Frame(login, bg="#0d1b2a")
    contenedor.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
    contenedor.columnconfigure(0, weight=1)
    contenedor.rowconfigure(0, weight=2)
    contenedor.rowconfigure(1, weight=1)
    contenedor.rowconfigure(2, weight=1)
    contenedor.rowconfigure(3, weight=1)
    contenedor.rowconfigure(4, weight=1)
    contenedor.rowconfigure(5, weight=1)

    # BOTÓN SOLO PERSONAL AUTORIZADO
    boton_aut = tk.Button(
        contenedor,
        text="SOLO PERSONAL AUTORIZADO",
        font=("Helvetica", 28, "bold"),
        bg="#e63946",
        fg="white",
        command=mostrar_credenciales      # abre la ventana con usuario/contraseña
    )
    boton_aut.grid(row=0, column=0, pady=(10, 20), sticky="n")

    # Título descriptivo
    subtitulo = tk.Label(
        contenedor,
        text="Introduce tus credenciales para acceder",
        font=("Helvetica", 22, "bold"),
        fg="#fdfdfd",
        bg="#0d1b2a"
    )
    subtitulo.grid(row=1, column=0, pady=(0, 25))

    # FORMULARIO usuario / contraseña
    formulario = tk.Frame(contenedor, bg="#0d1b2a")
    formulario.grid(row=2, column=0, pady=10, sticky="n")
    formulario.columnconfigure(0, weight=1)
    formulario.columnconfigure(1, weight=2)

    tk.Label(
        formulario,
        text="Usuario:",
        font=("Helvetica", 16),
        fg="white",
        bg="#0d1b2a"
    ).grid(row=0, column=0, padx=12, pady=10, sticky="e")
    usuario_entry = tk.Entry(formulario, font=("Helvetica", 16), width=28)
    usuario_entry.grid(row=0, column=1, padx=12, pady=10, sticky="w")

    tk.Label(
        formulario,
        text="Contraseña:",
        font=("Helvetica", 16),
        fg="white",
        bg="#0d1b2a"
    ).grid(row=1, column=0, padx=12, pady=10, sticky="e")
    pass_entry = tk.Entry(formulario, font=("Helvetica", 16), width=28, show="*")
    pass_entry.grid(row=1, column=1, padx=12, pady=10, sticky="w")

    # Texto de ayuda (azul) que no se borra
    info_label = tk.Label(
        contenedor,
        text="(Apretar en SOLO PERSONAL AUTORIZADO si no recuerdas usuario y contraseña)",
        font=("Helvetica", 12),
        fg="#9baec8",
        bg="#0d1b2a"
    )
    info_label.grid(row=3, column=0, pady=(10, 5))

    # Texto de error rojo separado
    error_label = tk.Label(
        contenedor,
        text="",
        font=("Helvetica", 13, "bold"),
        fg="red",
        bg="#0d1b2a"
    )
    error_label.grid(row=4, column=0, pady=(0, 5))

    # Botón iniciar sesión
    btn_login = tk.Button(
        contenedor,
        text="Iniciar sesión",
        font=("Helvetica", 18, "bold"),
        bg="#1b263b",
        fg="white",
        command=lambda: validar_login(usuario_entry, pass_entry, info_label, error_label)
    )
    btn_login.grid(row=5, column=0, pady=20, ipadx=12, ipady=6)

    # Enter también hace login
    login.bind(
        "<Return>",
        lambda event: validar_login(usuario_entry, pass_entry, info_label, error_label)
    )


# ===== ARRANQUE (crea la ventana de inicio de sesión) =====
login = Toplevel(window)  # ✅
construir_login()

window.mainloop()