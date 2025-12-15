# 🛰️ BIENVENIDO AL MEJOR PROYECTO JAMÁS VISTO!

![Grupo 2](imagendelgrupo2superrealista100x100realnofake.jpg)

## Videos explicativos
- Versión 1:       [![Watch video](https://img.youtube.com/vi/9xndj4gOBC0/0.jpg)](https://www.youtube.com/watch?v=9xndj4gOBC0)    https://youtu.be/9xndj4gOBC0
- Versión 2:       [![Watch video](https://img.youtube.com/vi/yomSmsEQIq0/0.jpg)](https://www.youtube.com/watch?v=yomSmsEQIq0)    https://youtu.be/yomSmsEQIq0
- Versión 3:       [![Watch video](https://img.youtube.com/vi/3UmEwXSwEw4/0.jpg)](https://www.youtube.com/watch?v=3UmEwXSwEw4)    https://youtu.be/3UmEwXSwEw4


## 📁 Estructura del Proyecto
### 🔌 Conexiones

#### Satélite (Arduino)
- **DHT11** → Pin 2 (Temperatura & Humedad)
- **Servomotor** → Pin 3 (Radar rotatorio)
- **HC-SR04 TRIG** → Pin 9 | **ECHO** → Pin 6 (Sensor de distancia)
- **LED Envío** → Pin 4 | **LED Error** → Pin 7 (Indicadores de estado)
- **SoftwareSerial RX** → Pin 10 | **TX** → Pin 11 (Comunicación con Tierra)

#### Estación de Tierra (Arduino)
- **LED Recepción** → Pin 2
- **LED Comunicación** → Pin 7
- **LED Error Datos** → Pin 4
- **LED Temp Max** → Pin 8 (Nuevo - indica alerta de temperatura)
- **SoftwareSerial RX** → Pin 10 | **TX** → Pin 11 (Comunicación con Satélite)

---

### 🚀 Funcionamiento

#### Protocolo de Comunicación
| Código | Función | Formato | Origen |
|--------|---------|---------|--------|
| 0 | Error | `0:tipoError:checksum` | Satélite/Tierra |
| 1 | Datos Temp/Hum | `1:temperatura:humedad:checksum` | Satélite |
| 2 | Sensor Distancia | `2:distancia:angulo:checksum` | Satélite |
| 3 | Control/Órdenes | `3:inicio/parar/reanudar/RadarManual:valor` | PC → Tierra → Satélite |
| 4 | Media Temperatura | `4:media:TmaxSobrepasada:checksum` | Satélite |
| 6 | Control Radar | `6:inicio/parar:checksum` | PC → Tierra → Satélite |
| 9 | Datos de Órbita | `9:tiempo:x:y:z:checksum` | Satélite |

#### Tiempos por Defecto
- 📊 **Envío datos**: 5 segundos
- 💡 **LEDs encendidos**: 1 segundo
- ⏱️ **Timeout comunicación**: 7 segundos
- 🔄 **Período mínimo error**: 15 segundos
- 🛰️ **Actualización órbita**: 10 segundos (con compresión 90x)

### 🔐 Validación de Datos
El protocolo incluye **checksum simple**:
- Suma de bytes de todos los caracteres antes del separador final
- Formato: `codigo:datos:checksum`
- Recalculado en recepción para verificar integridad
- Mensajes corrupto se ignoran silenciosamente

## 📝 Notas Importantes

- La interfaz Python requiere ajustar el puerto COM a la estación de tierra (`COM5` por defecto)
- **Python requiere**: `pip install pyserial matplotlib`
- **Arduino requiere**: Librería `DHT.h` (incluida en Arduino IDE)
- El satélite envía datos con checksum, la Tierra los verifica y reenvía sin checksum al PC
- Los LEDs ofrecen realimentación visual del estado del sistema
- Período configurable en tiempo real desde la interfaz Python
- Máximo de datos en gráfica de temperatura: últimos 100 puntos
- Las medias de temperatura usan últimos 10 valores
- Alerta de temperatura máxima (32°C) activable en satélite o estación
