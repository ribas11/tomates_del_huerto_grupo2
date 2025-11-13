## 📋 Descripción

Proyecto IoT que implementa una comunicación bidireccional entre dos Arduino mediante comunicación serial:
- **Satélite (Arduino 1)**: Adquiere datos de temperatura/humedad (DHT11) y controla un servomotor
- **Estación de Tierra (Arduino 2)**: Recibe los datos y controla la comunicación
- **Interfaz (Python)**: Visualiza los datos en tiempo real con gráficas dinámicas


## 📁 Estructura del Proyecto
### 🔌 Conexiones

#### Satélite
- DHT11 → Pin 2
- Servo → Pin 3
- HC-SR04 TRIG → Pin 9 | ECHO → Pin 6
- LED Envío → Pin 4 | LED Error → Pin 7
- RX (SoftSerial) → Pin 10 | TX → Pin 11

#### Estación de Tierra
- LED Recepción → Pin 2
- LED Comunicación → Pin 7
- LED Error Datos → Pin 4
- RX (SoftSerial) → Pin 10 | TX → Pin 11

---

### 🚀 Funcionamiento

#### Protocolo de Comunicación
| Código | Función | Formato |
|--------|---------|---------|
| 1 | Datos Temp/Hum | `1:temperatura:humedad` |
| 2 | Sensor Distancia | `2:distancia:angulo` |
| 3 | Control | `3:inicio/parar/reanudar` |
| 4 | Cambiar Período | `4:milisegundos` |
| 0 | Error | `0:tipoError` |

#### Tiempos por Defecto
- 📊 Envío datos: **3 segundos**
- 💡 LEDs encendidos: **1 segundo**
- ⏱️ Timeout comunicación: **7 segundos**

## 📝 Notas Importantes

- La interfaz Python requiere ajustar el puerto COM (`COM5` por defecto)
- Python requiere: pip install pyserial matplotlib
- Arduino requiere: Libreria: DHT.h