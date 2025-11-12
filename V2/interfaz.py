from tkinter import *
import tkinter as tk
from tkinter import messagebox
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


device = 'COM5'
mySerial = serial.Serial(device, 9600)


# Configurar la figura y el eje para la gráfica
fig, ax = plt.subplots(figsize=(6,4), dpi=100)
ax.set_xlim(0, 100)
ax.set_ylim(20, 40)
ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')

temperaturas = []
eje_x = []
i = 0
parar = True  # Empieza parado
threadRecepcion = None
periodoTH = 3


def recepcion():
    global i, parar, temperaturas, eje_x, mySerial, periodoTH
    while parar == False:
        # Con el buffer inicial/limpio
        if mySerial.in_waiting > 0:
            line = mySerial.readline().decode('utf-8').rstrip()
            trozos = line.split(':')
            if trozos[0] == '1':
                try:
                    temperatura = float(trozos[1])
                    eje_x.append(i)
                    temperaturas.append(temperatura)
                    print(f"Temperatura recibida: {temperatura}°C en t={i}")
                    ax.cla()
                    ax.plot(eje_x, temperaturas)
                    ax.set_xlim(max(0, i-15), i+5)
                    ax.set_ylim(20, 40)
                    ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')
                    canvas.draw()
                    i = i + periodoTH
                except ValueError:
                    print(f"Error lectura temperatura: {trozos[1]}")
            if trozos[0] == '0':
                print(f"Error del sistema: {trozos[1]}")


def InicioClick():
    global parar, threadRecepcion, i, temperaturas, eje_x
    
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
    ax.set_ylim(20, 40)
    ax.set_title('Grafica dinamica Temperatura[ºC] - temps[s]:')
    canvas.draw()      # Redibuja la gráfica vacía
    
    # Enviar comando de inicio al Arduino
    parar = False
    mensaje = "3:inicio\n"    
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    
    # Iniciar recepcion
    threadRecepcion = threading.Thread(target=recepcion)
    threadRecepcion.daemon = True
    threadRecepcion.start()


def PararClick():
    global parar
    parar = True    
    mensaje = "3:parar\n"     # Enviar comando al Arduino para que pare de enviar datos
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    mySerial.reset_input_buffer()   # Limpiar buffer al parar


def ReanudarClick():
    global parar, threadRecepcion
    mySerial.reset_input_buffer()   # Limpiar buffer antes de reanudar
    parar = False
    mensaje = "3:reanudar\n"  # Enviar comando de reanudar
    print(mensaje)
    mySerial.write(mensaje.encode('utf-8'))
    
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
        



# ===== VENTANA PRINCIPAL =====
window = Tk()
window.geometry("900x450")
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)  
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.columnconfigure(2, weight=1)
window.columnconfigure(3, weight=2)


# Título
tituloLabel = Label(window, text="Versión 1 \n Control de Sensor", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)


# Botones de control (Inicio, Parar, Reanudar)
InicioButton = Button(window, text="Inicio", bg='green', fg="white", command=InicioClick)
InicioButton.grid(row=1, column=0, padx=1, pady=1, sticky=N + S + E + W)

PararButton = Button(window, text="Parar", bg='red', fg="white", command=PararClick)
PararButton.grid(row=1, column=1, padx=1, pady=1, sticky=N + S + E + W)

ReanudarButton = Button(window, text="Reanudar", bg='orange', fg="white", command=ReanudarClick)
ReanudarButton.grid(row=1, column=2, padx=1, pady=1, sticky=N + S + E + W)


# PERIODO
periodoFrame = tk.LabelFrame(window, text="Configuración del Período (ms)", font=("Courier", 11, "bold"))
periodoFrame.grid(row=2, column=0, columnspan=3, padx=3, pady=3, sticky=N + S + E + W)
# Etiqueta
periodoLabel = Label(periodoFrame, text="Período (milisegundos):", font=("Courier", 10))
periodoLabel.pack(side=LEFT, padx=5, pady=5)
# Casilla de entrada (Entry)
periodoEntry = tk.Entry(periodoFrame, font=("Courier", 10), width=15)
periodoEntry.insert(0, "1000")  # Valor por defecto
periodoEntry.pack(side=LEFT, padx=5, pady=5)
# Botón para enviar el período
EnviarButton = Button(periodoFrame, text="Enviar Período", bg='blue', fg="white", command=EnviarPeriodoClick)
EnviarButton.pack(side=LEFT, padx=5, pady=5)
# Información
infoLabel = Label(periodoFrame, text="(Ej: 1000 ms = 1 segundo)", font=("Courier", 9, "italic"))
infoLabel.pack(side=LEFT, padx=5, pady=5)


# Gráfica
graph_frame = tk.LabelFrame(window, text="Grafica temperatura en viu")
graph_frame.grid(row=0, column=3, rowspan=3, padx=1, pady=1, sticky=N+S+E+W)

canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

window.mainloop()
