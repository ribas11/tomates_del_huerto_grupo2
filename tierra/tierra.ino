#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX

// Función para calcular checksum (igual que en satélite)
uint8_t calcularChecksum(const String& mensaje) {
  uint8_t checksum = 0;
  for (int i = 0; i < mensaje.length(); i++) {
    checksum += (uint8_t)mensaje.charAt(i);
  }
  return checksum;
}

// Función para verificar checksum de un mensaje
// Formato esperado: "codigo:datos:checksum"
bool verificarChecksum(const String& mensajeCompleto) {
  int ultimoColon = mensajeCompleto.lastIndexOf(':');
  if (ultimoColon == -1 || ultimoColon == 0) return false;
  
  String mensajeSinChecksum = mensajeCompleto.substring(0, ultimoColon);
  String checksumStr = mensajeCompleto.substring(ultimoColon + 1);
  
  uint8_t checksumEsperado = calcularChecksum(mensajeSinChecksum);
  uint8_t checksumRecibido = (uint8_t)checksumStr.toInt();
  
  return checksumEsperado == checksumRecibido;
}

int i;

bool MediaTER = false;
int TempMax = 0;
long nextMillis1; 
long nextMillis2; 
long nextMillis3; 
long nextMillisLED;
long nextMillisError; // Control de envío de errores
int interval1 = 5000; // Intervalo de solicitud datos
const int interval2 = 1000; // Intervalo apagar LED 
const int interval3 = 7000; // Timeout de error
const int intervalError = 15000; // Intervalo mínimo entre errores (15 segundos)
const int intervalLED = 1000; // LEDs encendidos 
const int LedEarth = 2; 
const int LedComms = 7; 
const int LedErrorDatos = 4;
const int LedTempMax = 8;

// MEDIA DE TEMPERATURA
bool calcularmedia = true;
int j = 0;                    // Indice para el vector de sumadatosT
bool contdatosT = false;      // Contador del numero de datos de temperatura enviados 
double sumadatosT[10];         // Suma de datos
double sumadatosFT;           // Suma de datos finales de temperatura del vector sumadatosT
double mediaT = 0;            // Media de la temperatura
const int Tmax = 32;          // Tempertura maxima que no volem superar
int Tmaxsobrepasada = 0;      // La temperatura màxima ha sigut  sobrepasada
double temp;
char info[5];

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  mySerial.println("Empezamos");
  i = 1;
  pinMode(LedEarth, OUTPUT);
  pinMode(LedComms, OUTPUT);
  pinMode(LedErrorDatos, OUTPUT);
  pinMode(LedTempMax, OUTPUT);
  digitalWrite(LedEarth, LOW);
  digitalWrite(LedComms, LOW);
  digitalWrite(LedErrorDatos, LOW);
  digitalWrite(LedTempMax , LOW);
  
  nextMillis1 = millis() + interval1;
  nextMillis2 = millis();
  nextMillis3 = millis() + interval3;
  nextMillisLED = millis();
  nextMillisError = 0; // Inicialmente permitir enviar error
}
void loop() {
  // ==== 1) ÓRDENES DESDE PC (Serial) ====
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');   // Ej: "3:MediaTER", "3:inicio", "4:3000"
    comando.trim();                                  // quita \r\n y espacios

    int fin = comando.indexOf(':');
    if (fin == -1) return;                           // formato incorrecto, salimos

    int codigo = comando.substring(0, fin).toInt();  // 3, 4, ...
    int inicio = fin + 1;
    String orden = comando.substring(inicio);        // texto después de ':'
    orden.trim();

    if (codigo == 3) {
      // 3:MediaTER / 3:MediaSAT / 3:inicio / 3:RadarManual... / 3:Orbita...
      if (orden == "MediaTER") {           // 3:MediaTER
        MediaTER = true;
      }
      else if (orden == "MediaSAT") {      // 3:MediaSAT
        MediaTER = false;
      }
      else if (orden == "inicio") {        // 3:inicio
        mySerial.println(comando);         // reenviar tal cual al satélite
      }
      else if (orden.startsWith("RadarManual")) {   // 3:RadarManual o 3:RadarManual:valor
        mySerial.println(comando);
      }
      else if (orden == "RadarAutomatico") {        // 3:RadarAutomatico
        mySerial.println(comando);
      }
      else if (orden == "OrbitaParar") {            // 3:OrbitaParar
        mySerial.println(comando);
      }
      else if (orden == "OrbitaInicio") {           // 3:OrbitaInicio
        mySerial.println(comando);
      }
      // si quisieras más casos de código 3, los añades aquí
    }
    else if (codigo == 4) {
      // 4:3000  (cambiar periodo de solicitud de datos al satélite)
      int nuevoIntervalo = orden.toInt();           // 'orden' ya es lo que hay tras ':'
      if (nuevoIntervalo > 0) {
        interval1 = nuevoIntervalo;
        Serial.print("Período actualizado a: ");
        Serial.println(interval1);
        mySerial.println(comando);                  // reenviar también al satélite
      }
    }
    else {
      // Otros códigos: reenviar tal cual al satélite
      mySerial.println(comando);
    }
  }

  // ==== 2) LÓGICA DE TIEMPOS DE LA TIERRA ====
  if (millis() >= nextMillis2) {
    digitalWrite(LedEarth, LOW);
  }

  if (millis() >= nextMillis1) {
    mySerial.print("1:");          // Código 1: Solicitud de datos al satélite
    mySerial.println(i);
    nextMillis1 = millis() + interval1;
    i = i + 1;
  }

  // ==== 3) RESPUESTA DESDE SATÉLITE (mySerial) ====
  if (mySerial.available()) {
    digitalWrite(LedComms, LOW);
    nextMillis3 = millis() + interval3;

    String mensajeCompleto = mySerial.readStringUntil('\n'); // p.ej. "1:25.3:60.0:123"
    mensajeCompleto.trim();
    
    // Validar que el mensaje no esté vacío y tenga formato válido
    if (mensajeCompleto.length() == 0) return;
    
    // Verificar que el mensaje comience con un número (código válido)
    if (!isDigit(mensajeCompleto.charAt(0))) return;
    
    // Verificar checksum antes de procesar
    if (!verificarChecksum(mensajeCompleto)) {
      // Mensaje corrupto, ignorar silenciosamente
      return;
    }
    
    // Extraer mensaje sin checksum (todo menos el último campo después del último :)
    int ultimoColon = mensajeCompleto.lastIndexOf(':');
    if (ultimoColon == -1 || ultimoColon == 0) return;
    String mensaje = mensajeCompleto.substring(0, ultimoColon);

    int fin = mensaje.indexOf(':');
    if (fin == -1 || fin == 0) return; // Debe tener ':' y el código no puede estar vacío

    int codigoRx = mensaje.substring(0, fin).toInt();  // 0,1,2,4,9,...
    // Validar que el código sea válido (0-9)
    if (codigoRx < 0 || codigoRx > 9) return;
    
    int inicio = fin + 1;

    if (codigoRx == 0) {
      digitalWrite(LedErrorDatos, HIGH);
      // Reenviar error al PC (sin checksum, interfaz.py no lo necesita)
      Serial.println(mensaje);
    }
    else if (codigoRx == 1) {
      // Código 1: Temperatura y humedad
      digitalWrite(LedEarth, HIGH);
      nextMillis2 = millis() + interval2;
      digitalWrite(LedErrorDatos, LOW);
      
      // Reenviar al PC (sin checksum)
      Serial.println(mensaje);

      if (MediaTER) {
        // mensaje: "1:TEMP:HUM"
        int ini = mensaje.indexOf(':', 0) + 1;
        int fini = mensaje.indexOf(':', ini);
        if (fini > ini) {
          String tempStr = mensaje.substring(ini, fini);
          temp = tempStr.toFloat();
          sumadatosT[j] = temp;
          j++;
          if (j == 10) {
            j = 0;
            contdatosT = true;
          }
          if (contdatosT) {
            sumadatosFT = 0;
            for (int a = 0; a < 10; a++) {
              sumadatosFT += sumadatosT[a];
            }
            mediaT = sumadatosFT / 10;
            Tmaxsobrepasada = (mediaT < Tmax) ? 0 : 1;
          }
        }
      }
    }
    else if (codigoRx == 2) {
      // Código 2: Datos de radar (distancia:angulo)
      // Reenviar al PC (sin checksum)
      Serial.println(mensaje);
    }
    else if (codigoRx == 4) {
      // Código 4: Media de temperatura
      // mensaje: "4:media:Tmaxsobrepasada"
      // Reenviar al PC (sin checksum)
      Serial.println(mensaje);
      
      int ini = mensaje.indexOf(':', 0) + 1;
      int fini = mensaje.indexOf(':', ini);
      if (fini > ini) {
        String TM = mensaje.substring(fini + 1);
        TempMax = TM.toInt();
        if (TempMax == 1) {
          digitalWrite(LedTempMax, HIGH);
        } else {
          digitalWrite(LedTempMax, LOW);
        }
      }
    }
    else if (codigoRx == 9) {
      // Código 9: Datos de órbita (time:x:y:z)
      // Convertir al formato que espera interfaz.py: "Position: (X: x m, Y: y m, Z: z m)"
      int ini1 = mensaje.indexOf(':', 0) + 1;
      int fin1 = mensaje.indexOf(':', ini1);
      int ini2 = fin1 + 1;
      int fin2 = mensaje.indexOf(':', ini2);
      int ini3 = fin2 + 1;
      int fin3 = mensaje.indexOf(':', ini3);
      int ini4 = fin3 + 1;
      
      // Validar que todos los campos existan
      if (fin1 > ini1 && fin2 > ini2 && fin3 > ini3 && ini4 < mensaje.length()) {
        String xStr = mensaje.substring(ini2, fin2);
        String yStr = mensaje.substring(ini3, fin3);
        String zStr = mensaje.substring(ini4);
        
        // Validar que sean números válidos
        if (xStr.length() > 0 && yStr.length() > 0 && zStr.length() > 0) {
          // Enviar al PC en el formato esperado
          Serial.print("Position: (X: ");
          Serial.print(xStr);
          Serial.print(" m, Y: ");
          Serial.print(yStr);
          Serial.print(" m, Z: ");
          Serial.print(zStr);
          Serial.println(" m)");
        }
      }
    }
    else {
      // Otros códigos: reenviar tal cual solo si tienen formato válido
      if (mensaje.length() > 2) { // Mínimo "X:Y"
        Serial.println(mensaje);
      }
    }
  }
  else if (millis() >= nextMillis3) {
    digitalWrite(LedComms, HIGH);
    // Solo enviar error de comunicación una vez cada intervalError segundos
    if (millis() >= nextMillisError) {
      Serial.println("0:ErrorComunicaciones");
      nextMillisError = millis() + intervalError;
    }
    // Resetear el timeout para la próxima verificación
    nextMillis3 = millis() + interval3;
  }
}

  
