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
        print("Comando enviado: iniciar órbita")
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









# device = 'COM5'
# mySerial = serial.Serial(device, 9600)

device = "COM5"
try:
    mySerial = serial.Serial(device, 9600)
except:
    print("⚠ No se encontró el puerto COM5. Ejecutando en modo SIMULACIÓN.")
    class SerialFake:
        def init(self):
            self.in_waiting = 0
        def readline(self):
            return b""
        def write(self, x):
            print("SIMULACIÓN -> Arduino recibiría:", x.decode().strip())
        def reset_input_buffer(self):
            pass
    mySerial = SerialFake()


# Configurar la figura y el eje para la gráfica
fig, ax = plt.subplots(figsize=(6,4), dpi=100)
ax.set_xlim(0, 100)
ax.set_ylim(15, 35)
ax.grid(True, which='both', color = "gray", linewidth=0.5)
ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')



mediaT = None #Variable de la media de la temperatura



temperaturas = []
eje_x = []
i = 0
pararTemp = True  # Empieza parado
pararRad = True  # Empieza parado
threadRecepcion = None
periodoTH = 5
temperaturas_medias = []
mensaje = ""  

grafica_activa = None  # Puede ser: temperatura, radar...
error_activo = False

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

                    ax.cla()
                    ax.plot(eje_x, temperaturas, label="Temperatura", color="blue")
                    if len(temperaturas_medias) > 0:
                        ax.plot(eje_x[-len(temperaturas_medias):], temperaturas_medias, label="Media", color="orange", linestyle="--")
                    ax.set_xlim(max(0, i-15), i+5)
                    ax.set_ylim(15, 35)
                    ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')
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
                    temperaturas_medias.append(media)
                    mediaLabel.config(text=f"Media T:\n{media:.2f} °C")
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
    global pararTemp, threadRecepcion, i, temperaturas, eje_x, mensaje, grafica_activa
    
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
    global pararTemp, threadRecepcion, mensaje, grafica_activa
    
    mySerial.reset_input_buffer() # Limpiar buffer antes de reanudar
    pararTemp = False
    grafica_activa = "temperatura"  
    mensaje = "3:reanudar\n" # Enviar comando de reanudar
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
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
    global pararRad, threadRecepcion, grafica_activa
    
    
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

ventana_temp = None
ventana_radar = None
ventana_extra = None


def construir_ventana_temperatura():
    """Crea la ventana de temperatura con gráfica y controles."""
    global ventana_temp, mediaLabel, calculomediaLabel, periodoEntry, canvas

    if ventana_temp is not None and tk.Toplevel.winfo_exists(ventana_temp):
        ventana_temp.lift()
        return

    ventana_temp = tk.Toplevel(window)
    ventana_temp.title("Temperatura y humedad")
    ventana_temp.geometry("1100x650")
    ventana_temp.configure(bg="#f5f7fb")

    ventana_temp.columnconfigure(0, weight=1)
    ventana_temp.columnconfigure(1, weight=1)
    ventana_temp.rowconfigure(0, weight=3)
    ventana_temp.rowconfigure(1, weight=1)
    ventana_temp.rowconfigure(2, weight=1)
    ventana_temp.rowconfigure(3, weight=1)

    graph_frame = tk.LabelFrame(ventana_temp, text="Gráfica temperatura en vivo", font=("Courier", 15, "italic"))
    graph_frame.grid(row=0, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    botones_temp = tk.LabelFrame(ventana_temp, text="Control de temperatura", font=("Courier", 14, "bold"))
    botones_temp.grid(row=1, column=0, columnspan=2, padx=8, pady=4, sticky="nsew")
    botones_temp.grid_columnconfigure((0, 1, 2), weight=1)
    tk.Button(botones_temp, text="Inicio", bg='green', fg="white", font=("Arial", 18), command=InicioClick).grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
    tk.Button(botones_temp, text="Parar", bg='red', fg="white", font=("Arial", 18), command=PararClick).grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
    tk.Button(botones_temp, text="Reanudar", bg='orange', fg="white", font=("Arial", 18), command=ReanudarClick).grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

    medias_frame = tk.LabelFrame(ventana_temp, text="Medias", font=("Courier", 14, "bold"))
    medias_frame.grid(row=2, column=0, padx=8, pady=4, sticky="nsew")
    medias_frame.grid_columnconfigure((0, 1), weight=1)
    mediaLabel = tk.Label(medias_frame, text="Media T: --- °C", font=("Courier", 18), fg="blue")
    mediaLabel.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
    calculomediaLabel = tk.Label(medias_frame, text="Calculando media en:\n ---", font=("Courier", 15), fg="black")
    calculomediaLabel.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
    tk.Button(medias_frame, text="Media en satélite", bg='purple', fg='white', font=("Arial", 14), command=CalcularMediaTSat).grid(row=1, column=0, padx=6, pady=6, sticky="nsew")
    tk.Button(medias_frame, text="Media en tierra", bg='purple', fg='white', font=("Arial", 14), command=CalcularMediaTTER).grid(row=1, column=1, padx=6, pady=6, sticky="nsew")

    periodoFrame = tk.LabelFrame(ventana_temp, text="Configuración del período (ms)", font=("Courier", 14, "bold"))
    periodoFrame.grid(row=2, column=1, padx=8, pady=4, sticky="nsew")
    periodoFrame.grid_columnconfigure((0, 1, 2), weight=1)
    tk.Label(periodoFrame, text="Período:", font=("Courier", 11)).grid(row=0, column=0, padx=4, pady=6, sticky="e")
    periodoEntry = tk.Entry(periodoFrame, font=("Courier", 11))
    periodoEntry.insert(0, "3000")
    periodoEntry.grid(row=0, column=1, padx=4, pady=6, sticky="we")
    tk.Button(periodoFrame, text="Enviar", bg='blue', fg="white", command=EnviarPeriodoClick).grid(row=0, column=2, padx=4, pady=6, sticky="we")
    tk.Label(periodoFrame, text="Ej: 1000 ms = 1 s", font=("Courier", 9, "italic")).grid(row=1, column=0, columnspan=3, padx=4, pady=4)

    def cerrar():
        ventana_temp.destroy()
    ventana_temp.protocol("WM_DELETE_WINDOW", cerrar)


def construir_ventana_radar():
    """Crea la ventana del radar con controles y canvas."""
    global ventana_radar, radar_canvas, control_deslizante, valor_servo

    if ventana_radar is not None and tk.Toplevel.winfo_exists(ventana_radar):
        ventana_radar.lift()
        return

    ventana_radar = tk.Toplevel(window)
    ventana_radar.title("Radar del satélite")
    ventana_radar.geometry("1000x650")
    ventana_radar.configure(bg="#f5f7fb")
    ventana_radar.columnconfigure(0, weight=1)
    ventana_radar.columnconfigure(1, weight=1)
    ventana_radar.rowconfigure(0, weight=2)
    ventana_radar.rowconfigure(1, weight=1)
    ventana_radar.rowconfigure(2, weight=1)

    radar_frame = tk.LabelFrame(ventana_radar, text="Radar", font=("Courier", 15, "italic"))
    radar_frame.grid(row=0, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
    radar_canvas = Canvas(radar_frame, width=400, height=300, bg='green')
    radar_canvas.pack(fill=tk.BOTH, expand=True)

    botones_radar = tk.LabelFrame(ventana_radar, text="Control radar", font=("Courier", 14, "bold"))
    botones_radar.grid(row=1, column=0, columnspan=2, padx=8, pady=4, sticky="nsew")
    botones_radar.grid_columnconfigure((0, 1), weight=1)
    tk.Button(botones_radar, text="Inicio", bg='green', fg="white", font=("Arial", 18), command=InicioClickRad).grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
    tk.Button(botones_radar, text="Parar", bg='red', fg="white", font=("Arial", 18), command=PararClickRad).grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

    control_frame = tk.LabelFrame(ventana_radar, text="Modo servo", font=("Courier", 14, "bold"))
    control_frame.grid(row=2, column=0, columnspan=2, padx=8, pady=4, sticky="nsew")
    control_frame.grid_columnconfigure((0, 1), weight=1)
    valor_servo = tk.IntVar(value=100)
    control_deslizante = tk.Scale(control_frame, from_=0, to=180, orient=tk.HORIZONTAL, resolution=1,
                                  variable=valor_servo, length=300, command=EnviarServo, state="disabled")
    control_deslizante.grid(row=0, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")
    tk.Button(control_frame, text="Radar automático", bg='blue', fg="white", command=ModoAutomaticoClick).grid(row=1, column=0, padx=6, pady=6, sticky="nsew")
    tk.Button(control_frame, text="Radar manual", bg='orange', fg="white", command=RadarManual).grid(row=1, column=1, padx=6, pady=6, sticky="nsew")

    def on_resize(event):
        dibujar_radar_base()

    radar_canvas.bind("<Configure>", on_resize)

    def cerrar():
        if not pararRad:
            PararClickRad()
        ventana_radar.destroy()
    ventana_radar.protocol("WM_DELETE_WINDOW", cerrar)
    dibujar_radar_base()


def construir_ventana_extra():
    """Ventana de la función extra (placeholder)."""
    global ventana_extra
    if ventana_extra is not None and tk.Toplevel.winfo_exists(ventana_extra):
        ventana_extra.lift()
        return
    ventana_extra = tk.Toplevel(window)
    ventana_extra.title("Funcionalidad extra")
    ventana_extra.geometry("600x400")
    tk.Label(ventana_extra, text="Contenido pendiente de definir", font=("Arial", 16)).pack(expand=True, fill="both", padx=20, pady=20)


# ===== VENTANA PRINCIPAL =====
window = Tk()
window.geometry("1200x700")
window.configure(bg="#e9edf5")
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=2)
window.rowconfigure(2, weight=1)
window.columnconfigure(0, weight=1)

tituloFrame = Frame(window, bg="#0b1c33")
tituloFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
tituloLabel = Label(tituloFrame, text="Mesa de Control - Versión 3", font=("Helvetica", 38, "bold"), fg="white", bg="#0b1c33")
tituloLabel.pack(expand=True, fill="both", pady=10)

botonera = tk.Frame(window, bg="#e9edf5")
botonera.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
for c in range(4):
    botonera.columnconfigure(c, weight=1)
btn_temp = tk.Button(botonera, text="Temperatura", font=("Arial", 20, "bold"), bg="#1f77b4", fg="white", command=construir_ventana_temperatura)
btn_temp.grid(row=0, column=0, padx=10, pady=10, ipadx=10, ipady=20, sticky="nsew")
btn_radar = tk.Button(botonera, text="Radar", font=("Arial", 20, "bold"), bg="#2ca02c", fg="white", command=construir_ventana_radar)
btn_radar.grid(row=0, column=1, padx=10, pady=10, ipadx=10, ipady=20, sticky="nsew")
btn_posicion = tk.Button(botonera, text="Posición", font=("Arial", 20, "bold"), bg="#ff7f0e", fg="white", command=mostrar_ventana_orbita)
btn_posicion.grid(row=0, column=2, padx=10, pady=10, ipadx=10, ipady=20, sticky="nsew")
btn_extra = tk.Button(botonera, text="Extra", font=("Arial", 20, "bold"), bg="#8c564b", fg="white", command=construir_ventana_extra)
btn_extra.grid(row=0, column=3, padx=10, pady=10, ipadx=10, ipady=20, sticky="nsew")

panel_registros = tk.Frame(window, bg="#e9edf5")
panel_registros.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
panel_registros.columnconfigure(0, weight=1)
panel_registros.rowconfigure(0, weight=1)
panel_registros.rowconfigure(1, weight=1)

FicherosFrame = tk.LabelFrame(panel_registros, text="Ficheros de registro", font=("Courier", 14, "bold"))
FicherosFrame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
FicherosFrame.columnconfigure((0, 1, 2, 3), weight=1)
tk.Button(FicherosFrame, text="Registro de comandos", bg='purple', fg="white", font=("Arial", 14), command=PopUpComandosClick).grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
tk.Button(FicherosFrame, text="Registro de alarmas", bg='red', fg="white", font=("Arial", 14), command=PopUpAlarmasClick).grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
tk.Button(FicherosFrame, text="Registro de observaciones", bg='pink', fg="white", font=("Arial", 14), command=PopUpObservacionesClick).grid(row=0, column=2, padx=8, pady=8, sticky="nsew")
tk.Button(FicherosFrame, text="Registro de temperaturas", bg='orange', fg="white", font=("Arial", 14), command=PopUpTemperaturasClick).grid(row=0, column=3, padx=8, pady=8, sticky="nsew")

ObservacionesFrame = tk.LabelFrame(panel_registros, text="Registro de observaciones (SOLO PERSONAL AUTORIZADO)", font=("Courier", 14, "bold"))
ObservacionesFrame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
ObservacionesFrame.columnconfigure((0, 1, 2), weight=1)
ObservacionesLabel = Label(ObservacionesFrame, text="Observación a registrar:", font=("Courier", 11))
ObservacionesLabel.grid(row=0, column=0, padx=5, pady=8, sticky="e")
ObservacionesEntry = tk.Entry(ObservacionesFrame, font=("Courier", 11))
ObservacionesEntry.grid(row=0, column=1, padx=5, pady=8, sticky="we")
tk.Button(ObservacionesFrame, text="Registrar", bg='blue', fg="white", command=RegistrarObservacion).grid(row=0, column=2, padx=5, pady=8, sticky="we")

# Iniciar hilo para leer datos de posición de órbita
thread_posicion = threading.Thread(target=hilo_posicion)
thread_posicion.daemon = True
thread_posicion.start()

window.mainloop()