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
    earth_slice.remove()  # Elimina el círculo anterior
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

    btn_limpiar = tk.Button(frame_botones, text="Limpiar órbita", 
                           command=limpiar_datos, bg="lightcoral")
    btn_limpiar.pack(side="left", padx=5)

    btn_cerrar = tk.Button(frame_botones, text="Cerrar ventana", 
                          command=cerrar_ventana_orbita, bg="lightgray")
    btn_cerrar.pack(side="right", padx=5)

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
                line = mySerial.readline().decode('utf-8').rstrip()
                
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
                        print(f"Error convirtiendo coordenadas: {e}")
                        print(f"Línea problemática: '{line}'")
                        
                else:
                    # Línea no contiene datos de posición (puede ser otro tipo de mensaje)
                    if line.strip():  # Solo si no está vacía
                        print(f"Datos no reconocidos: '{line}'")
                        
            # Pequeña pausa para no saturar el CPU (10ms)
            time.sleep(0.01)
            
        except serial.SerialException as e:
            print(f"Error de comunicación serie: {e}")
            time.sleep(1)  # Esperar antes de reintentar
        except Exception as e:
            print(f"Error inesperado en hilo_posicion: {e}")
            time.sleep(0.5)









device = 'COM5'
mySerial = serial.Serial(device, 9600)



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
            line = mySerial.readline().decode('utf-8', errors='ignore').rstrip()
            trozos = line.split(':')

            # TEMPERATURA - solo si está activada
            if trozos[0] == '1' and pararTemp == False:
                CerrarVentanaError() 
                try:
                    temperatura = float(trozos[1])
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
                except ValueError:
                    print(f"Error lectura temperatura: {trozos[1]}")

            # MEDIA
            if trozos[0] == '4' and len(trozos) > 1:
                try:
                    media = float(trozos[1])
                    temperaturas_medias.append(media)
                    mediaLabel.config(text=f"Media T:\n{media:.2f} °C")
                    print(f"Media recibida: {media:.2f}°C")
                except:
                    print("Error lectura media")

            # RADAR - solo si está activado
            if trozos[0] == '2' and pararRad == False:
                try:
                    distancia = float(trozos[1])
                    angulo = float(trozos[2])
                    RadarAutomatico(distancia, angulo)
                except (ValueError, IndexError) as e:
                    print(f"Error lectura radar: {e}")

            # ERROR
            if trozos[0] == '0':
                print(f"Error del sistema: {trozos[1]}")
                registrar_evento("alarma", trozos[1])
                AbrirVentanaError(trozos[1])


def ModoAutomaticoClick():
    global modo_manual, mensaje
    modo_manual = False
    control_deslizante.config(state="disabled")  # Desactivar slider
    mensaje = "3:RadarAutomatico\n"
    mySerial.write(mensaje.encode('utf-8'))
    print("Radar en modo automático")
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
    global modo_manual, mensaje
    modo_manual = True
    control_deslizante.config(state="normal")  # Activar slider
    mensaje = "3:RadarManual\n"  # Solo activa modo manual
    mySerial.write(mensaje.encode('utf-8'))
    print("Radar en modo manual")
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



# ===== VENTANA PRINCIPAL =====
window = Tk()
window.geometry("1000x450")
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)  
window.rowconfigure(3, weight=1)
window.rowconfigure(4, weight=1)
window.rowconfigure(5, weight=1)
window.rowconfigure(6, weight=1)
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.columnconfigure(2, weight=1)
window.columnconfigure(3, weight=2)
window.columnconfigure(4, weight=2)
window.columnconfigure(5, weight=2)

#TITULO
tituloFrame = Frame(window, width=400, height=120) #Creamos frame con tamaño fijo, donde irá el label
tituloFrame.grid(row=0, column=0, columnspan=3, padx=3, pady=3)
tituloFrame.grid_propagate(False)   #Evitamos que el tamaño cambie por el contenido

# Label dentro del frame (puede tener la letra grande sin expandir nada)
tituloLabel = Label(tituloFrame, text="Versión 3 \n Mesa de Control", font=("Courier", 40, "italic"))
tituloLabel.pack(expand=True, fill="both")

ControlRadarFrame = tk.LabelFrame(window, text="Controlar radar", font=("Courier", 11, "bold"))
ControlRadarFrame.grid(row=2, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)

#-------------BOTONES TEMPERATURA-----------------

BotonesTemperatura = tk.LabelFrame(window, text="BOTONES TEMPERATURA", font=("Courier", 17, "bold"))
BotonesTemperatura.grid(row=1, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)

BotonesTemperatura.grid_rowconfigure(0, weight=1)
BotonesTemperatura.grid_columnconfigure(0, weight=1)
BotonesTemperatura.grid_columnconfigure(1, weight=1)
BotonesTemperatura.grid_columnconfigure(2, weight=1)

# Botones de control (Inicio, Parar, Reanudar, cambiar donde calcula T)
InicioButtonTemp = Button(BotonesTemperatura, text="Inicio", bg='green', fg="white",font=("Arial",20), command=InicioClick)
InicioButtonTemp.grid(row=0, column=0, padx=1, pady=1, sticky=N + S + E + W)

PararButtonTemp = Button(BotonesTemperatura, text="Parar", bg='red', fg="white", font=("Arial",20), command=PararClick)
PararButtonTemp.grid(row=0, column=1, padx=1, pady=1, sticky=N + S + E + W)
ReanudarButtonTemp = Button(BotonesTemperatura, text="Reanudar", bg='orange', fg="white", font=("Arial",20), command=ReanudarClick)
ReanudarButtonTemp.grid(row=0, column=2, padx=1, pady=1, sticky=N + S + E + W)

#-------------BOTONES RADAR-----------------

BotonesRadar = tk.LabelFrame(window, text="BOTONES RADAR", font=("Courier", 17, "bold"))
BotonesRadar.grid(row=4, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)

BotonesRadar.grid_rowconfigure(0, weight=1)
BotonesRadar.grid_columnconfigure(0, weight=1)
BotonesRadar.grid_columnconfigure(1, weight=1)

InicioButtonRad = Button(BotonesRadar, text="Inicio", bg='green', fg="white",font=("Arial",20), command=InicioClickRad)
InicioButtonRad.grid(row=0, column=0, padx=1, pady=1, sticky=N + S + E + W)

PararButtonRad = Button(BotonesRadar, text="Parar", bg='red', fg="white", font=("Arial",20), command=PararClickRad)
PararButtonRad.grid(row=0, column=1, padx=1, pady=1, sticky=N + S + E + W)

#Etiquitas para ver en tiempo real la media de temperatura
mediaLabel = Label(window, text="Media T: --- °C", font=("Courier", 18), fg="blue")
mediaLabel.grid(row=3, column=2, padx=5, pady=5, ipady=0, sticky=N + E + W)

calculomediaLabel = Label(window, text="Calculando media en:\n ---", font=("Courier", 15), fg="black")
calculomediaLabel.grid(row=3, column=2, padx=5, pady=5, ipady=0,sticky=S + E + W)

ModoButton = Button(window, text="Calcular media \ntemperatura \nen Satélite", bg='purple', fg='white', font=("Arial",20), width=13, command=CalcularMediaTSat)
ModoButton.grid(row=3, column=0, rowspan=1, padx=1, pady=1, sticky=N + S + E + W)

ModoButton = Button(window, text="Calcular media \ntemperatura \nen Estación Tierra", bg='purple', fg='white', font=("Arial",20), width=13,command=CalcularMediaTTER)
ModoButton.grid(row=3, column=1, rowspan=1, padx=1, pady=1, sticky=N + S + E + W)

# Cambiar periodo
periodoFrame = tk.LabelFrame(window, text="Configuración del Período (ms)", font=("Courier", 14, "bold"))
periodoFrame.grid(row=2, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)

periodoLabel = Label(periodoFrame, text="Período (milisegundos):", font=("Courier", 10))
periodoLabel.pack(side=LEFT, padx=5, pady=5)

periodoEntry = tk.Entry(periodoFrame, font=("Courier", 10), width=15)
periodoEntry.insert(0, "3000")  # Valor por defecto
periodoEntry.pack(side=LEFT, padx=5, pady=5)

EnviarButton = Button(periodoFrame, text="Enviar Período", bg='blue', fg="white", command=EnviarPeriodoClick)
EnviarButton.pack(side=LEFT, padx=5, pady=5)

infoLabel = Label(periodoFrame, text="(Ej: 1000 ms = 1 segundo)", font=("Courier", 9, "italic"))
infoLabel.pack(side=LEFT, padx=5, pady=5)

# Servomotor y ultrasonidos
ControlRadarFrame = tk.LabelFrame(window, text="Control Radar", font=("Courier", 11, "bold"))
ControlRadarFrame.grid(row=5, column=3, rowspan=2, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)
ControlRadarFrame.columnconfigure(0, weight=1) #Dentro del frame hacemos 2 columnas y 1 fila
ControlRadarFrame.columnconfigure(1, weight=1)
ControlRadarFrame.rowconfigure(0, weight=1)

valor_servo = tk.IntVar(value=90)  # Valor inicial en 90 grados
control_deslizante = tk.Scale(ControlRadarFrame, from_=0, to=180, orient=tk.HORIZONTAL, resolution=1, variable=valor_servo, length=200, command=EnviarServo) # Configuramos el control deslizante para que vaya de 0 a 180, con una resolución de 1 y lo orientamos horizontalmente

control_deslizante.grid(row=0, column=0, rowspan=1, padx=5, pady=5, sticky=N + S + E + W) #Dentro del frame lo ponemos en la fila 0, columna 0

ModoAutomatico = Button(ControlRadarFrame, text="Radar\nAutomático", bg='blue', fg="white", command=ModoAutomaticoClick)
ModoAutomatico.grid(row=1, column=0,padx=5, pady=5, sticky=N + S + E + W)

ModoManual = Button(ControlRadarFrame, text="Radar\nManual", bg='orange', fg="white", command=RadarManual)
ModoManual.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

# Abrir ficheros de eventos
FicherosFrame = tk.LabelFrame(window, text="Ficheros de registro de eventos", font=("Courier", 14, "bold"))
FicherosFrame.grid(row=5, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)
ComandosButton = Button(FicherosFrame, text="Registro de comandos", bg='purple', fg="white", 
                        font=("Arial", 15), command=PopUpComandosClick)
ComandosButton.pack(side=LEFT, padx=10, pady=5, fill="both", expand=True)
AlarmasButton = Button(FicherosFrame, text="Registro de alarmas", bg='red', fg="white", 
                         font=("Arial", 15), command=PopUpAlarmasClick)
AlarmasButton.pack(side=LEFT, padx=10, pady=5, fill="both", expand=True)
FObservacionesButton = Button(FicherosFrame, text="Registro de observaciones", bg='pink', fg="white", 
                         font=("Arial", 15), command=PopUpObservacionesClick)
FObservacionesButton.pack(side=LEFT, padx=10, pady=5, fill="both", expand=True)
TemperaturasButton = Button(FicherosFrame, text="Registro de temperaturas", bg='orange', fg="white", 
                         font=("Arial", 15), command=PopUpTemperaturasClick)
TemperaturasButton.pack(side=LEFT, padx=10, pady=5, fill="both", expand=True)

#Label observaciones
ObservacionesFrame = tk.LabelFrame(window, text="Registro de obervaciones (SOLO PERSONAL AUTORIZADO)", font=("Courier", 14, "bold"))
ObservacionesFrame.grid(row=6, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)
ObservacionesLabel = Label(ObservacionesFrame, text="Observación a registrar:", font=("Courier", 10))
ObservacionesLabel.pack(side=LEFT, padx=5, pady=5)

ObservacionesEntry = tk.Entry(ObservacionesFrame, font=("Courier", 10), width=15)
ObservacionesEntry.pack(side=LEFT, padx=5, pady=5)

EnviarButton = Button(ObservacionesFrame, text="Registrar", bg='blue', fg="white", command=RegistrarObservacion)
EnviarButton.pack(side=LEFT, padx=5, pady=5)

# Gráfica
graph_frame = tk.LabelFrame(window, text="Gráfica temperatura en viu", font=("Courier", 15, "italic"))
graph_frame.grid(row=0, column=3, rowspan=2, columnspan=2,padx=1, pady=1, sticky=N+S+E+W)

radar_frame = tk.LabelFrame(window, text="Radar satélite", font=("Courier", 15, "italic"))
radar_frame.grid(row=2, column=3, rowspan=3,columnspan=2,padx=1, pady=1, sticky=N+S+E+W)

radar_canvas = Canvas(radar_frame, width=400, height=300, bg='green')
radar_canvas.pack(fill=tk.BOTH, expand=True)

InicioButtonOrb = Button(window, text="Inicio", bg='green', fg="white",font=("Arial",20), command=mostrar_ventana_orbita)
InicioButtonOrb.grid(row=0, column=5, padx=1, pady=1, sticky=N + S + E + W)


def on_resize(event): #Cada vez que se redimensiona el canvas, recibe un objeto event con información del nuevo tamaño
    dibujar_radar_base() #Redibuja de cero llamando a esta función

radar_canvas.bind("<Configure>", on_resize) #Cuando se redimensiona el canvas, llama a on_resize


canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

window.mainloop()
