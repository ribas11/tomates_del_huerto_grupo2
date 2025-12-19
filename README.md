# 🛰️ BIENVENIDO AL MEJOR PROYECTO JAMÁS VISTO!

![Grupo 2](imagendelgrupo2superrealista100x100realnofake.jpg)

## Videos explicativos
- Versión 1:       [![Watch video](https://img.youtube.com/vi/9xndj4gOBC0/0.jpg)](https://www.youtube.com/watch?v=9xndj4gOBC0)    https://youtu.be/9xndj4gOBC0
- Versión 2:       [![Watch video](https://img.youtube.com/vi/yomSmsEQIq0/0.jpg)](https://www.youtube.com/watch?v=yomSmsEQIq0)    https://youtu.be/yomSmsEQIq0
- Versión 3:       [![Watch video](https://img.youtube.com/vi/3UmEwXSwEw4/0.jpg)](https://www.youtube.com/watch?v=3UmEwXSwEw4)    https://youtu.be/3UmEwXSwEw4
- Versión 4 (final):       [![Watch video](https://img.youtube.com/vi/EDOCNlF2mHQ/0.jpg)](https://www.youtube.com/watch?v=EDOCNlF2mHQ)    https://youtu.be/EDOCNlF2mHQ


## 📁 Estructura del Proyecto
### 🔌 Conexiones

#### Satélite (Arduino)
- **DHT11** → Pin 2 (Temperatura & Humedad)
- **Servomotor** → Pin 3 
- **HC-SR04 TRIG** → Pin 9 | **ECHO** → Pin 6 (Sensor de distancia)
- **LED Envío** → Pin 4 | **LED Error** → Pin 7 (Indicadores de estado)
- **SoftwareSerial RX** → Pin 10 | **TX** → Pin 11 (Comunicación con Tierra)

#### Estación de Tierra (Arduino)
- **LED Recepción** → Pin 2
- **LED Comunicación** → Pin 7
- **LED Error Datos** → Pin 4
- **LED Temp Max** → Pin 8 (Alerta de temperatura máxima)
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

## FUNCIÓN ADICIONAL

A mayores, el proyecto cuenta con una cámara capaz de tomar una imagen a resolución 160x120 en escala de grises. Debido a las limitaciones físicas del hardware utilizado, al tomar esta fotografía hay que tener en cuenta ciertos aspectos:
- Las comunicaciones deben ser por cable y el puerto serie debe abrirse a 1M Baudios en ambas direcciones.
- La resolución es de 160x120 píxeles, que pueden tomar diferentes tonos de blanco, gris y negro.
- Para eliminar (hasta cierto grado) la corrupción de la imagen, la cámara debe tomar más de una fotografía y el objetivo debe permanecer quieto a lo largo del proceso de muestreo.
- Además, el retraso en las comunicaciones desfasa la imagen, lo que deja una línea diagonal como consecuencia de la corrección.


EXPLICACIÓN DETALLADA DE LAS LIMITACIONES DEL HARDWARE:

El módulo de cámara del que disponemos (OV7670) es solo eso: una cámara, no cuenta con un módulo FIFO ni ningún tipo de memoria adicional. En consecuencia, lo único que puede hacer es tomar una foto de un momento particular, lo que resulta en una larga fila de bytes que entran por un pin al Arduino UNO. Los píxeles van en parejas y cada una está representada por cuatro bytes, y sus bits contienen datos como el color o la iluminación; esto son 160 x 120 x 2 = 38400 bytes o 38KB. El problema es que, como el Arduino UNO no tiene más de 2KB de memoria RAM, no puede almacenar la imagen, así que tiene que enviar los bytes al mismo tiempo que los recibe.

Sin embargo, nuestro puerto serie está limitado a 1M Baudios, incluso menos (9600) si las comunicaciones se efectúan a través de LoRa, lo que es demasiado lento y causa desfases en la línea de bytes. De este modo el programa puede corromper algunos píxeles de manera ocasional, ya que confunde, por ejemplo, los valores de iluminación y color rojo. La frecuencia de estas corrupciones aumenta cuando disminuimos los Baudios del puerto serie.

Si hubiéramos dispuesto de un hardware de mayor potencia, con FIFO o un Arduino UNO con mayor capacidad de memoria RAM, no tendríamos estos inconvenientes. Por ejemplo, con una memoria RAM más grande seríamos capaces de almacenar toda la cadena de bytes de la imagen y enviarla al ritmo pertinente. Con un módulo de cámara con FIFO, la cámara es capaz de ejecutar más variedad de acciones más complejas, con lo que podríamos, por ejemplo, dividir la imagen en trozos para no tener que leerla toda de una vez.


EXPLICACIÓN DETALLADA DE LOS PARCHES DE SOFTWARE:

Asumimos que el programa de Python en el PC recibirá una cadena de bytes que representan los niveles de gris de cada píxel, y una cantidad significativa de estos estarán corruptos. Así que los guardamos en un array de dos dimensiones de 160 por 120, y repetimos el proceso por cada imagen tomada hasta contar con las suficientes (especificadas en el programa). Después, el programa hace, para cada píxel, la media aritmética de los valores de gris de cada imagen tomada, así conseguimos suavizar la imagen y "corregir" buena parte de la corrupción.

En este punto el contenido de la imagen ya es difícilmente distinguible, ya que, debido a la lentitud de las comunicaciones y el desfase de la información de la imagen, los píxeles de cada columna están un poco más arriba que los de la columna de al lado. Por eso, después de crear la imagen, movemos cada columna una cantidad de píxeles hacia abajo proporcional al número de columna. Finalmente, giramos la imagen 90 grados para que esté del derecho.

El resultado es una imagen en 160 por 120 píxeles, en blanco y negro, borrosa y suave, poco distinguible pero con pocas corrupciones.

