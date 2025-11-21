from tkinter import *
import tkinter as tk
from tkinter import messagebox
from unicodedata import decimal
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import datetime






# device = 'COM5'



# try:
#     mySerial = serial.Serial(device, 9600)
# except:
#     print("⚠ No se encontró el puerto COM5. Ejecutando en modo SIMULACIÓN.")
   
#     class SerialFake:
#         def _init_(self):
#             self.in_waiting = 0
#         def readline(self):
#             return b""
#         def write(self, x):
#             print("SIMULACIÓN -> Arduino recibiría:", x.decode().strip())
#         def reset_input_buffer(self):
#             pass



#     mySerial = SerialFake()



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
parar = True  # Empieza parado
threadRecepcion = None
periodoTH = 3
temperaturas_medias = []
mensaje = ""  

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
        "temperatura": "registrotemphum.txt"
    }   
    # Escribir en el archivo correspondiente
    if tipo_comando in archivos:
        with open(archivos[tipo_comando], "a") as f:  # "a" = append (añadir)
            f.write(f"{fecha_hora} {detalles}\n")



def recepcion():
    global i, parar, temperaturas, eje_x, mySerial, periodoTH, mensaje, pararRad
    while parar == False:
        if mySerial.in_waiting > 0:
            line = mySerial.readline().decode('utf-8').rstrip()
            trozos = line.split(':')
            if trozos[0] == '1':
                CerrarVentanaError()
                try:
                    temperatura = float(trozos[1])
                    eje_x.append(i)
                    temperaturas.append(temperatura)
                    i += periodoTH



                    ax.cla()
                    ax.plot(eje_x, temperaturas, label="Temperatura", color="blue")



                    if len(temperaturas_medias) > 0:
                        # Dibujar la media solo si hay suficientes datos
                        ax.plot(eje_x[-len(temperaturas_medias):], temperaturas_medias, label="Media", color="orange", linestyle="--")
                    ax.set_xlim(max(0, i-15), i+5)
                    ax.set_ylim(15, 35)
                    ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')
                    ax.legend()
                    ax.grid(True, which='both', color = "gray", linewidth=0.5)
                    canvas.draw()
                    
                    registrar_evento("temperatura", f"Temp:{temperatura:.2f}°C Hum:{trozos[2] if len(trozos) > 2 else 'N/A'}")



                except ValueError:
                    print(f"Error lectura temperatura: {trozos[1]}")
                    trozos = ["0", "Error lectura temperatura"]
                    
            if trozos[0] == '0':
                print(f"Error del sistema: {trozos[1]}")
                registrar_evento("alarma", trozos[1])
                AbrirVentanaError(trozos[1])
            if trozos[0] == '4':
                try:
                    media = float(trozos[1])
                    temperaturas_medias.append(media)
                    mediaLabel.config(text=f"Media T:\n{media:.2f} °C")
                    print(f"Media recibida: {media:.2f}°C")
                except:
                    print("Error lectura media")
                    trozos = ["0", "Error lectura media"]

            # if len(eje_x) > 0:
            #     ax.cla()
            #     ax.plot(eje_x, temperaturas, label="Temperatura", color="blue")
            #     # Dibujar la media solo si hay suficientes datos
            #     if len(temperaturas_medias) > 0:
            #         ax.plot(eje_x[-len(temperaturas_medias):], temperaturas_medias, label="Media", color="orange", linestyle="--")
            #     ax.set_xlim(max(0, i-15), i+5)
            #     ax.set_ylim(15, 35)
            #     ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')
            #     ax.legend()
            #     ax.grid(True, which='both', color = "gray", linewidth=0.5)
            #     canvas.draw()

    while pararRad == False:
        if mySerial.in_waiting > 0:
            line = mySerial.readline().decode('utf-8').rstrip()
            trozos = line.split(':')
            if trozos[0] == '2':
                try:
                    distancia = float(trozos[1])
                    angulo = float(trozos[2])
                    RadarAutomatico(distancia, angulo)      
                except (ValueError, IndexError) as e:
                    print(f"Error lectura radar: {e}")


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



# def dibujar_radar_base():
#     radar_canvas.delete("all")



#     Obtener tamaño REAL del canvas
#     w = radar_canvas.winfo_width()
#     h = radar_canvas.winfo_height()



#     if w <= 1 or h <= 1:
#         El canvas aún no está inicializado → esperar
#         radar_canvas.after(100, dibujar_radar_base)
#         return



#     Centro del radar (abajo en el medio)
#     x0 = w / 2
#     y0 = h



#     Radio máximo = 90% del alto
#     R = h * 0.9



#     Dibujar círculos
#     for f in range(1, 6):
#         r = (R / 5) * f
#         radar_canvas.create_oval(x0 - r, y0 - r, x0 + r, y0 + r, width=2)



#     Dibujar líneas angulares
#     for angle in range(0, 181, 30):
#         rad = math.radians(angle)
#         x_end = x0 + R * math.cos(rad)
#         y_end = y0 - R * math.sin(rad)
#         radar_canvas.create_line(x0, y0, x_end, y_end, width=2)



#     Dibujar textos
#     offset = 20
#     for angle in range(30, 180, 30):
#         rad = math.radians(angle)
#         xt = x0 + (R + offset) * math.cos(rad)
#         yt = y0 - (R + offset) * math.sin(rad)
#         radar_canvas.create_text(xt, yt, text=f"{angle}°", font=("Arial", 10, "bold"))







def InicioClick():
    global parar, threadRecepcion, i, temperaturas, eje_x, mensaje
   
    # Detener el hilo anterior si está corriendo
    if threadRecepcion is not None and threadRecepcion.is_alive():
        parar = True
        threadRecepcion.join(timeout=1)
    # Limpiar el buffer serial antes de empezar
    mySerial.reset_input_buffer()  
   
    # Reiniciar memeorias de datos
    temperaturas = []  # Vaciar lista de temperaturas
    eje_x = []         # Vaciar lista de tiempos
    i = 0              # Reiniciar contador
    # Reiniciar grafica
    ax.cla()           # Limpiar el eje
    ax.set_xlim(0, 100)
    ax.set_ylim(15, 35)
    ax.grid(True, which='both', color = "gray", linewidth=0.5)
    ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')
    canvas.draw()      # Redibuja la gráfica vacía
   
    # Enviar comando de inicio al Arduino
    parar = False
    mensaje = "3:inicio\n"    
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    calculomediaLabel.config(text="Calculando media en:\n Satélite")
    registrar_evento("comando", "Inicio")
   
    # Iniciar recepcion
    threadRecepcion = threading.Thread(target=recepcion)
    threadRecepcion.daemon = True
    threadRecepcion.start()





def PararClick():
    global parar, mensaje
    parar = True    
    mensaje = "3:parar\n"     # Enviar comando al Arduino para que pare de enviar datos
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    mySerial.reset_input_buffer()   # Limpiar buffer al parar
    registrar_evento("comando", "Parar")





def ReanudarClick():
    global parar, threadRecepcion, mensaje
    mySerial.reset_input_buffer()   # Limpiar buffer antes de reanudar
    parar = False
    mensaje = "3:reanudar\n"  # Enviar comando de reanudar
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    registrar_evento("comando", "Reanudar")
   
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
    registrar_evento("comando", f"Cambio de periodo a {periodo_sensor} ms")
    
       
def CalcularMediaTSat():
    global mensaje
    mensaje = "3:MediaSAT\n"
    mySerial.write(mensaje.encode('utf-8'))
    mediaLabel.config(text="Media T: \n(calculando...)")
    calculomediaLabel.config(text="Calculando media en:\n Satélite")
    registrar_evento("comando", "MediaSAT")
def CalcularMediaTTER():
    global mensaje
    mensaje = "3:MediaTER\n"
    mySerial.write(mensaje.encode('utf-8'))
    mediaLabel.config(text="Media T:\n (calculando...)")
    calculomediaLabel.config(text="Calculando media en:\n Estación Tierra")
    registrar_evento("comando", "MediaTER")

def InicioClickRad():
    global pararRad, threadRecepcion
    if threadRecepcion is not None and threadRecepcion.is_alive():
        pararRad = True
        threadRecepcion.join(timeout=1)
    pararRad = False
    mensaje = "6:inicio\n"    
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    threadRecepcion = threading.Thread(target=recepcion)
    threadRecepcion.daemon = True
    threadRecepcion.start()
def PararClickRad():
    global pararRad, threadRecepcion
    pararRad = True    
    mensaje = "6:parar\n"     # Enviar comando al Arduino para que pare de enviar datos
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    mySerial.reset_input_buffer()   # Limpiar buffer al parar

def RadarManual():
    global modo_manual, mensaje
    modo_manual = True
    control_deslizante.config(state="normal")  # Activar slider
    mensaje = "3:RadarManual\n"  # Solo activa modo manual
    mySerial.write(mensaje.encode('utf-8'))
    print("Radar en modo manual")
    registrar_evento("comando", "RadarManual")



def EnviarServo(valor):
    if modo_manual:  # Solo enviar si estamos en manual
        valor_int = int(float(valor))
        mensaje = f"3:RadarManual:{valor_int}\n"
        mySerial.write(mensaje.encode('utf-8'))
        print(f"Enviando valor servo: {valor_int}")

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

# PERIODO
periodoFrame = tk.LabelFrame(window, text="Configuración del Período (ms)", font=("Courier", 14, "bold"))
periodoFrame.grid(row=2, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)
# Etiqueta
periodoLabel = Label(periodoFrame, text="Período (milisegundos):", font=("Courier", 10))
periodoLabel.pack(side=LEFT, padx=5, pady=5)
# Casilla de entrada (Entry)
periodoEntry = tk.Entry(periodoFrame, font=("Courier", 10), width=15)
periodoEntry.insert(0, "3000")  # Valor por defecto
periodoEntry.pack(side=LEFT, padx=5, pady=5)
# Botón para enviar el período
EnviarButton = Button(periodoFrame, text="Enviar Período", bg='blue', fg="white", command=EnviarPeriodoClick)
EnviarButton.pack(side=LEFT, padx=5, pady=5)
# Información
infoLabel = Label(periodoFrame, text="(Ej: 1000 ms = 1 segundo)", font=("Courier", 9, "italic"))
infoLabel.pack(side=LEFT, padx=5, pady=5)


ControlRadarFrame = tk.LabelFrame(window, text="Control Radar", font=("Courier", 11, "bold"))
ControlRadarFrame.grid(row=5, column=3,columnspan=3, padx=3, pady=3, sticky=N + S + E + W)
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



# Gráfica
graph_frame = tk.LabelFrame(window, text="Gráfica temperatura en viu", font=("Courier", 15, "italic"))
graph_frame.grid(row=0, column=3, rowspan=2, columnspan=2,padx=1, pady=1, sticky=N+S+E+W)

radar_frame = tk.LabelFrame(window, text="Radar satélite", font=("Courier", 15, "italic"))
radar_frame.grid(row=2, column=3, rowspan=3,columnspan=2,padx=1, pady=1, sticky=N+S+E+W)

radar_canvas = Canvas(radar_frame, width=400, height=300, bg='green')
radar_canvas.pack(fill=tk.BOTH, expand=True)

def on_resize(event): #Cada vez que se redimensiona el canvas, recibe un objeto event con información del nuevo tamaño
    dibujar_radar_base() #Redibuja de cero llamando a esta función

radar_canvas.bind("<Configure>", on_resize) #Cuando se redimensiona el canvas, llama a on_resize


canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

window.mainloop()